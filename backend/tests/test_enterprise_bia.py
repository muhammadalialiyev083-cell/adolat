import pytest
from rest_framework.test import APIClient

from apps.authentication.models import User
from apps.bia.models import BIAAssessment
from apps.organizations.models import Organization, Service
from apps.processes.models import BusinessProcess

pytestmark = pytest.mark.django_db


@pytest.fixture
def questionnaire():
    org = Organization.objects.create(name='Evidence test', sector='Synthetic', separation_of_duties=True)
    author = User.objects.create_user(username='author', role='ADMIN', organization=org)
    reviewer = User.objects.create_user(username='reviewer', role='APPROVER', organization=org)
    process = BusinessProcess.objects.create(organization=org, service=Service.objects.create(organization=org, name='S'), name='P', owner=author)
    client = APIClient()
    client.force_authenticate(author)
    data = {'process':process.pk, 'rto_hours':'2', 'mtpd_hours':'8', 'rpo_minutes':30, 'backup_interval_minutes':60, 'rationale':'Suhbatda asoslangan', 'evidence_required':True, 'questionnaire':{'business_objective':'Xizmatni yetkazish','minimum_service_level':'Qo‘lda minimal xizmat','dependency_assumptions':'Tasdiqlangan inventar','recovery_prerequisites':'Jamoa va zaxira'}, 'impacts':[{'horizon_hours':'2', 'financial_loss':'100', 'operational_score':2, 'legal_score':1, 'reputational_score':2}], 'evidence':[{'title':'Test interview', 'type':'INTERVIEW', 'source_reference':'SYNTHETIC:test-01', 'responsible_person':'Test author', 'collection_date':'2026-01-01', 'assessment_date':'2026-01-02', 'justification':'Test fixture only', 'quality':'MEDIUM', 'review_status':'REVIEWED'}]}
    return client, author, reviewer, process, data


def test_evidence_approval_snapshot_revision_and_separation(questionnaire):
    client, author, reviewer, process, data = questionnaire
    response = client.post('/api/v1/bia/', data, format='json')
    assert response.status_code == 201, response.data
    ident = response.data['id']
    assert response.data['created_by'] == author.pk
    assert response.data['evidence'][0]['review_status'] == 'UNREVIEWED'
    assert client.post(f'/api/v1/bia/{ident}/approve/').status_code == 400
    client.force_authenticate(reviewer)
    approved = client.post(f'/api/v1/bia/{ident}/approve/')
    assert approved.status_code == 200, approved.data
    snapshot = approved.data['bia']['approved_snapshot']
    assert snapshot['evidence'][0]['review_status'] == 'REVIEWED'
    assert snapshot['process_context']['name'] == 'P'
    process.name = 'Changed'
    process.save()
    assert client.get(f'/api/v1/bia/{ident}/summary/').json()['process_context']['name'] == 'P'
    client.force_authenticate(author)
    assert client.patch(f'/api/v1/bia/{ident}/', {'rationale':'mutate'}, format='json').status_code == 400
    revised = client.post(f'/api/v1/bia/{ident}/revise/')
    assert revised.status_code == 201, revised.data
    assert revised.data['revision'] == 2
    assert revised.data['evidence'][0]['review_status'] == 'UNREVIEWED'
    assert revised.data['approved_snapshot'] == {}
    assert BIAAssessment.objects.get(pk=ident).approved_snapshot == snapshot


def test_missing_evidence_review_and_time_constraints(questionnaire):
    client, _, reviewer, _, data = questionnaire
    data['evidence'] = []
    response = client.post('/api/v1/bia/', data, format='json')
    ident = response.data['id']
    assert 'evidence' in response.data['missing_evidence']
    assert client.patch(f'/api/v1/bia/{ident}/', {'evidence_required':False}, format='json').status_code == 400
    client.force_authenticate(reviewer)
    assert client.post(f'/api/v1/bia/{ident}/approve/').status_code == 400
    assert client.post(f'/api/v1/bia/{ident}/review/', {'decision':'request_changes', 'notes':'Dalil kerak'}, format='json').status_code == 200
    assert client.post(f'/api/v1/bia/{ident}/review/', {'decision':'reject', 'notes':'Asos yo‘q'}, format='json').data['status'] == 'REJECTED'
    client.force_authenticate(questionnaire[1])
    data['rto_hours'] = data['mtpd_hours']
    assert client.post('/api/v1/bia/', data, format='json').status_code == 400


def test_invalid_evidence_and_foreign_process_rejected(questionnaire):
    client, _, _, process, data = questionnaire
    data['evidence'][0]['assessment_date'] = '2099-01-01'
    assert client.post('/api/v1/bia/', data, format='json').status_code == 400
    data['evidence'][0]['assessment_date'] = '2026-01-02'
    org = Organization.objects.create(name='Foreign', sector='Synthetic')
    process.organization = org
    process.save()
    response = client.post('/api/v1/bia/', data, format='json')
    assert response.status_code == 400
