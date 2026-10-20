from rest_framework import views, status, serializers
from rest_framework.response import Response
from apps.engine.calculator import RiskCalculator, PriorityEngine, StrategyEvaluator
from apps.processes.models import BusinessProcess
from apps.authentication.permissions import IsTenantMember


class RiskInput(serializers.Serializer):
    likelihood = serializers.IntegerField(min_value=1, max_value=5)
    impact = serializers.IntegerField(min_value=1, max_value=5)
    rto_hours = serializers.DecimalField(max_digits=12, decimal_places=4, min_value=0)
    rpo_minutes = serializers.IntegerField(min_value=0)
    backup_interval_minutes = serializers.IntegerField(min_value=0)


class PriorityInput(serializers.Serializer):
    process_id = serializers.IntegerField(min_value=1, required=False)


class StrategyInput(serializers.Serializer):
    target_rto_hours = serializers.DecimalField(max_digits=12, decimal_places=4, min_value=0)
    target_rpo_minutes = serializers.IntegerField(min_value=0)
    strategies = serializers.ListField(child=serializers.DictField())


class PriorityAnalysisView(views.APIView):
    """
    FR-07: Ustuvorlikni hisoblash (/api/v1/analyses/priority).
    Jarayon yoki butun tashkilot bo'yicha ustuvorlik ballarini hisoblaydi va saralaydi.
    """
    permission_classes = [IsTenantMember]

    def post(self, request):
        payload = PriorityInput(data=request.data)
        payload.is_valid(raise_exception=True)
        process_id = payload.validated_data.get('process_id')
        user = request.user
        
        if process_id:
            try:
                proc = BusinessProcess.objects.get(id=process_id, organization=user.organization, is_deleted=False)
            except BusinessProcess.DoesNotExist:
                return Response({'error': 'Jarayon topilmadi.'}, status=status.HTTP_404_NOT_FOUND)
            
            try:
                result = PriorityEngine.calculate_priority(proc)
            except ValueError as exc:
                raise serializers.ValidationError({'data_quality': str(exc)}) from None
            return Response(result, status=status.HTTP_200_OK)

        # Butun tashkilot bo'yicha hisoblash
        procs = BusinessProcess.objects.filter(organization=user.organization, is_deleted=False)
        try:
            results = [PriorityEngine.calculate_priority(p) for p in procs]
        except ValueError as exc:
            raise serializers.ValidationError({'data_quality': str(exc)}) from None
        results.sort(key=lambda x: (-x['priority_score'], x['process_id']))

        return Response({
            'total_processes': len(results),
            'ranked_processes': results
        }, status=status.HTTP_200_OK)


class EvaluateRiskAlgorithmView(views.APIView):
    """
    FR-07 va Hujjat 10.1 namunaviy API:
    So'rov: {"process_id": 12, "likelihood": 4, "impact": 5, "rto_hours": 4, "rpo_minutes": 60, "backup_interval_minutes": 360}
    Javob: {"risk_score": 20, "risk_class": "high", "rpo_gap": true, "observations": ["Zaxiralash intervali RPO talabidan katta"]}
    """
    permission_classes = [IsTenantMember]

    def post(self, request):
        payload = RiskInput(data=request.data)
        payload.is_valid(raise_exception=True)
        likelihood = payload.validated_data['likelihood']
        impact = payload.validated_data['impact']
        rpo_minutes = payload.validated_data['rpo_minutes']
        backup_interval = payload.validated_data['backup_interval_minutes']

        score = RiskCalculator.calculate_score(likelihood, impact)
        org = request.user.organization
        low_t = org.risk_low_threshold if org else 6
        med_t = org.risk_medium_threshold if org else 14
        risk_class = RiskCalculator.classify_risk(score, low_t, med_t)

        rpo_gap = backup_interval > rpo_minutes
        observations = []
        if rpo_gap:
            observations.append("Zaxiralash intervali RPO talabidan katta")

        return Response({
            'risk_score': score,
            'risk_class': risk_class,
            'rpo_gap': rpo_gap,
            'observations': observations
        }, status=status.HTTP_200_OK)


class EvaluateStrategyView(views.APIView):
    """
    FR-08: Tiklash strategiyasini baholash va optimalini tanlash.
    """
    permission_classes = [IsTenantMember]

    def post(self, request):
        payload = StrategyInput(data=request.data)
        payload.is_valid(raise_exception=True)
        data = payload.validated_data
        try:
            res = StrategyEvaluator.evaluate_strategies(data['target_rto_hours'], data['target_rpo_minutes'], data['strategies'])
        except ValueError as exc:
            raise serializers.ValidationError({'error': str(exc)}) from None
        return Response(res, status=status.HTTP_200_OK)
