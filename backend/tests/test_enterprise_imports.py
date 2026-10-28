import io
import zipfile
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.utils import timezone
from openpyxl import Workbook
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.authentication.models import User
from apps.core.models import AuditLog
from apps.imports.files import read_table
from apps.imports.models import ImportBatch
from apps.organizations.models import Department, Organization, Service

pytestmark = pytest.mark.django_db


@pytest.fixture
def importer():
    org = Organization.objects.create(name='Import test', sector='Synthetic test')
    user = User.objects.create_user(username='importer', organization=org, role='BCMS_MANAGER')
    client = APIClient()
    client.force_authenticate(user)
    return client, user, org


def upload(client, content='key,name,head_name\nb-1,O‘quv bo‘limi,Mas’ul\n', entity='departments', filename='data.csv'):
    return client.post('/api/v1/imports/upload', {'entity': entity, 'file': SimpleUploadedFile(filename, content.encode('utf-8'))}, format='multipart')


def prepare(client, content='key,name,head_name\nb-1,O‘quv bo‘limi,Mas’ul\n', entity='departments'):
    result = upload(client, content, entity)
    assert result.status_code == 201, result.data
    ident = result.data['id']
    result = client.post(f'/api/v1/imports/{ident}/preview', {'mapping': {h:h for h in result.data['headers']}}, format='json')
    assert result.status_code == 200, result.data
    return ident, result.data


def commit(client, ident, decisions=None):
    return client.post(f'/api/v1/imports/{ident}/commit', {'confirm': True, 'decisions': decisions or {'2':'create'}}, format='json')


def test_preview_commit_repeat_and_explicit_update(importer):
    client, _, org = importer
    ident, result = prepare(client)
    assert result['valid'] == 1
    assert not Department.objects.exists()
    assert commit(client, ident).data == {'created':1, 'updated':0, 'skipped':0}
    assert commit(client, ident).data['created'] == 1
    assert Department.objects.filter(organization=org).count() == 1
    assert ImportBatch.objects.get(pk=ident).rows == []
    ident, result = prepare(client, 'key,name,head_name\nb-1,Yangi nom,Yangi mas’ul\n')
    assert result['rows'][0]['existing_id']
    assert commit(client, ident).status_code == 400
    assert commit(client, ident, {'2':'update'}).data['updated'] == 1
    assert Department.objects.get().name == 'Yangi nom'
    assert AuditLog.objects.filter(entity='Department').count() == 2


def test_invalid_mapping_duplicates_and_cross_tenant_fk(importer):
    client, _, _ = importer
    ident, data = prepare(client, 'key,name\nb-1,A\nb-1,B\n')
    assert data['invalid'] == 1
    assert commit(client, ident, {'2':'create','3':'create'}).status_code == 400
    assert Department.objects.count() == 0
    other = Organization.objects.create(name='Other', sector='Synthetic')
    service = Service.objects.create(organization=other, name='Private service')
    _, data = prepare(client, f'key,name,service\np-1,Jarayon,{service.pk}\n', 'processes')
    assert data['invalid'] == 1
    assert 'Private service' not in str(data)
    missing = upload(client, 'name\nA\n')
    assert client.post(f"/api/v1/imports/{missing.data['id']}/preview", {'mapping': {'name':'name'}}, format='json').status_code == 400


def test_rollback_on_storage_failure(importer):
    client, _, _ = importer
    ident, _ = prepare(client, 'key,name\nk-1,A\nk-2,B\n')
    original = Department.save
    calls = []
    def save(obj, *args, **kwargs):
        calls.append(obj.name)
        if len(calls) == 2:
            raise IntegrityError('test storage failure')
        return original(obj, *args, **kwargs)
    with patch.object(Department, 'save', save):
        response = commit(client, ident, {'2':'create','3':'create'})
    assert response.status_code == 400
    assert Department.objects.count() == 0
    assert AuditLog.objects.filter(entity='Department').count() == 0
    assert ImportBatch.objects.get(pk=ident).committed_at is None


def test_stale_preview_and_batch_tenant_access(importer):
    client, user, org = importer
    department = Department.objects.create(organization=org, name='A')
    ident, _ = prepare(client, 'key,name\nk-1,A\n')
    department.head_name = 'Changed'
    department.save()
    assert commit(client, ident, {'2':'update'}).status_code == 400
    other = Organization.objects.create(name='Other', sector='Synthetic')
    user2 = User.objects.create_user(username='another', organization=other, role='ADMIN')
    client.force_authenticate(user2)
    assert commit(client, ident).status_code == 404
    user2.role = 'AUDITOR'
    user2.save()
    assert upload(client).status_code == 403
    client.force_authenticate(user)
    ImportBatch.objects.filter(pk=ident).update(expires_at=timezone.now()-timedelta(seconds=1))
    assert commit(client, ident).status_code == 400


@pytest.mark.parametrize('content,filename', [('key,name\na,=SUM(A1)\n','x.csv'), ('key,name\na,@cmd\n','x.csv'), ('<html>oops</html>','x.xlsx'), ('key,name\na,A\n','x.exe'), ('key,name\na,' + 'A'*4001,'x.csv')])
def test_unsafe_input_rejected(importer, content, filename):
    assert upload(importer[0], content, filename=filename).status_code == 400


def test_xlsx_content_formula_external_and_size_limits(importer):
    book = Workbook()
    book.active.append(['key','name'])
    book.active.append(['xlsx-1','O‘zbekcha'])
    stream = io.BytesIO()
    book.save(stream)
    headers, rows = read_table(SimpleUploadedFile('valid.xlsx', stream.getvalue()))
    assert headers == ['key','name'] and rows == [['xlsx-1','O‘zbekcha']]
    book.active['B2'] = '=1+1'
    stream = io.BytesIO()
    book.save(stream)
    with pytest.raises(ValidationError):
        read_table(SimpleUploadedFile('formula.xlsx', stream.getvalue()))
    book.active['B2'] = 'text'
    book.active['B2'].hyperlink = 'https://example.invalid/'
    stream = io.BytesIO()
    book.save(stream)
    with pytest.raises(ValidationError):
        read_table(SimpleUploadedFile('link.xlsx', stream.getvalue()))
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('xl/worksheets/sheet1.xml', 'a' * 100000)
    with pytest.raises(ValidationError):
        read_table(SimpleUploadedFile('bomb.xlsx', stream.getvalue()))
    assert upload(importer[0], 'a' * (2*1024*1024 + 1)).status_code == 400


def test_templates_and_invalid_bia_import(importer):
    client = importer[0]
    assert client.get('/api/v1/imports/templates/departments').status_code == 200
    assert upload(client, 'key,rto_hours,mtpd_hours\nb,9,2\n', 'bia').status_code == 400
