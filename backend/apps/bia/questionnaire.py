from django.utils import timezone
from rest_framework import serializers


class QuestionnaireSerializer(serializers.Serializer):
    business_objective = serializers.CharField(max_length=4000, required=False, allow_blank=True)
    operating_schedule = serializers.CharField(max_length=200, required=False, allow_blank=True)
    minimum_service_level = serializers.CharField(max_length=4000, required=False, allow_blank=True)
    dependency_assumptions = serializers.CharField(
        max_length=4000, required=False, allow_blank=True
    )
    recovery_prerequisites = serializers.CharField(
        max_length=4000, required=False, allow_blank=True
    )
    service_delivery_impact = serializers.CharField(
        max_length=4000, required=False, allow_blank=True
    )


class EvidenceSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    type = serializers.ChoiceField(
        choices=["DOCUMENT", "INTERVIEW", "MEASUREMENT", "REGULATION", "OTHER"]
    )
    source_reference = serializers.CharField(max_length=1000)
    responsible_person = serializers.CharField(max_length=200)
    collection_date = serializers.DateField()
    assessment_date = serializers.DateField()
    justification = serializers.CharField(max_length=4000)
    quality = serializers.ChoiceField(choices=["HIGH", "MEDIUM", "LOW"])
    review_status = serializers.CharField(read_only=True, default="UNREVIEWED")

    def validate(self, attrs):
        if (
            attrs["collection_date"] > attrs["assessment_date"]
            or attrs["assessment_date"] > timezone.localdate()
        ):
            raise serializers.ValidationError("Yig‘ish sanasi ≤ baholash sanasi ≤ bugun bo‘lsin.")
        # Dates remain JSON-compatible; raw references are never dereferenced.
        for key in ["collection_date", "assessment_date"]:
            attrs[key] = attrs[key].isoformat()
        attrs["review_status"] = "UNREVIEWED"
        return attrs


def missing_evidence(bia):
    missing = []
    if not bia.evidence:
        missing.append("evidence")
    for key in [
        "business_objective",
        "minimum_service_level",
        "dependency_assumptions",
        "recovery_prerequisites",
    ]:
        if not bia.questionnaire.get(key, "").strip():
            missing.append(key)
    if not bia.rationale.strip():
        missing.append("rationale")
    if not bia.impacts.exists():
        missing.append("impacts")
    return missing
