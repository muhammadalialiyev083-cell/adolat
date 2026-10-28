import csv
import io
from datetime import timedelta

from django.db import IntegrityError, transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from openpyxl import Workbook
from rest_framework import views
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from apps.authentication.permissions import IsBCMSManagerRole, IsTenantMember
from apps.core.audit import record_audit
from apps.imports.files import read_table
from apps.imports.models import ImportBatch, ImportIdentity
from apps.imports.service import FIELDS, REQUIRED, SERIALIZERS, find_existing, fingerprint, preview
from apps.organizations.models import Organization


class ImportAccess(views.APIView):
    permission_classes = [IsTenantMember, IsBCMSManagerRole]

    def batch(self, request, pk, lock=False):
        queryset = ImportBatch.objects.filter(organization=request.user.organization, created_by=request.user)
        if lock:
            queryset = queryset.select_for_update()
        batch = get_object_or_404(queryset, pk=pk)
        if batch.expires_at <= timezone.now():
            raise ValidationError({'batch': 'Import muddati tugagan. Faylni qayta yuklang.'})
        return batch


class ImportUploadView(ImportAccess):
    parser_classes = [MultiPartParser]

    def post(self, request):
        entity = request.data.get('entity')
        if entity not in SERIALIZERS:
            raise ValidationError({'entity': 'Qo‘llab-quvvatlanadigan resursni tanlang.'})
        upload = request.FILES.get('file')
        if not upload:
            raise ValidationError({'file': 'Faylni tanlang.'})
        if ImportBatch.objects.filter(created_by=request.user, expires_at__gt=timezone.now(), committed_at__isnull=True).count() >= 5:
            raise ValidationError({'batch': 'Bir vaqtda beshtagacha import ruxsat etiladi.'})
        headers, rows = read_table(upload)
        batch = ImportBatch.objects.create(organization=request.user.organization, created_by=request.user, entity=entity, headers=headers, rows=rows, expires_at=timezone.now() + timedelta(minutes=30))
        return Response({'id': str(batch.pk), 'headers': headers, 'sample': rows[:5], 'count': len(rows), 'fields': FIELDS[entity], 'required': REQUIRED[entity], 'expires_at': batch.expires_at}, status=201)


class ImportPreviewView(ImportAccess):
    @transaction.atomic
    def post(self, request, pk):
        batch = self.batch(request, pk, lock=True)
        if batch.committed_at:
            raise ValidationError('Bu import allaqachon bajarilgan.')
        mapping = request.data.get('mapping')
        batch.preview = preview(batch, mapping, request)
        batch.mapping = mapping
        batch.save(update_fields=['mapping', 'preview'])
        return Response({'rows': batch.preview, 'valid': sum(not r['errors'] for r in batch.preview), 'invalid': sum(bool(r['errors']) for r in batch.preview)})


class ImportCommitView(ImportAccess):
    def post(self, request, pk):
        try:
            return self.commit(request, pk)
        except IntegrityError:
            raise ValidationError({'batch': 'Yozuv o‘zgargan yoki kalit takrorlangan. Yangi preview yarating; hech narsa saqlanmadi.'}) from None

    @transaction.atomic
    def commit(self, request, pk):
        batch = self.batch(request, pk, lock=True)
        if request.data.get('confirm') is not True:
            raise ValidationError({'confirm': 'Importni aniq tasdiqlang.'})
        if batch.committed_at:
            return Response(batch.summary)
        if not batch.preview:
            raise ValidationError({'batch': 'Avval tekshirish va ko‘rish bosqichini bajaring.'})
        decisions = request.data.get('decisions')
        if not isinstance(decisions, dict) or set(decisions) != {str(r['row']) for r in batch.preview}:
            raise ValidationError({'decisions': 'Har bir qator uchun create/update/skip tanlang.'})
        Organization.objects.select_for_update().get(pk=batch.organization_id)
        summary = {'created': 0, 'updated': 0, 'skipped': 0}
        cls = SERIALIZERS[batch.entity]
        for row in batch.preview:
            decision = decisions[str(row['row'])]
            if decision == 'skip':
                summary['skipped'] += 1
                continue
            if row['errors'] or decision != ('update' if row['existing_id'] else 'create'):
                raise ValidationError({'row': row['row'], 'detail': 'Xato qatorni o‘tkazing yoki to‘g‘ri amalni tanlang.'})
            instance = find_existing(batch.entity, row['key'], row['data'], batch.organization, lock=True)
            if (instance.pk if instance else None) != row['existing_id'] or (instance and fingerprint(instance, cls, request) != row['fingerprint']):
                raise ValidationError({'row': row['row'], 'detail': 'Previewdan keyin yozuv o‘zgargan. Qayta tekshiring; import bekor qilindi.'})
            serializer = cls(instance, data=row['data'], partial=bool(instance), context={'request': request})
            serializer.is_valid(raise_exception=True)
            before = cls(instance, context={'request': request}).data if instance else {}
            saved = serializer.save(organization=batch.organization)
            ImportIdentity.objects.update_or_create(organization=batch.organization, entity=batch.entity, external_key=row['key'], defaults={'object_id': saved.pk})
            summary['updated' if instance else 'created'] += 1
            record_audit(request, action='UPDATE' if instance else 'CREATE', entity=saved.__class__.__name__, entity_id=saved.pk, before_state=before, after_state=serializer.data)
        batch.committed_at = timezone.now()
        batch.summary, batch.rows, batch.preview, batch.mapping, batch.headers = summary, [], [], {}, []
        batch.save()
        record_audit(request, action='CREATE', entity='ImportBatch', entity_id=batch.pk, after_state=summary)
        return Response(summary)


class ImportTemplateView(ImportAccess):
    def get(self, request, entity):
        if entity not in FIELDS:
            raise ValidationError({'entity': 'Resurs topilmadi.'})
        if request.query_params.get('file_format') == 'xlsx':
            book = Workbook()
            book.active.append(FIELDS[entity])
            stream = io.BytesIO()
            book.save(stream)
            data, mime, extension = stream.getvalue(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'xlsx'
        else:
            stream = io.StringIO()
            csv.writer(stream).writerow(FIELDS[entity])
            data, mime, extension = '\ufeff' + stream.getvalue(), 'text/csv; charset=utf-8', 'csv'
        response = HttpResponse(data, content_type=mime)
        response['Content-Disposition'] = f'attachment; filename="{entity}-template.{extension}"'
        return response
