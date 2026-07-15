from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Q
from apps.projects.models import Project
from apps.testcases.models import TestCase
from apps.testplans.models import TestPlan
from apps.testruns.models import TestRun, TestResult
from apps.defects.models import Defect


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def stats(request):
    project_id = request.query_params.get('project')

    # SECURITY/C6 修复：TestRun 没有 project 字段（旧代码直接 project_id 触发 FieldError→500）。
    # 正确路径是 test_run→test_plan→project；TestCase/TestPlan 仍有 project 直接 FK，保持原样。
    if project_id:
        # 同一份 project_id 字典不能直接复用：分发到正确的字段名上
        direct_fk_filter = {'project_id': project_id}
        via_plan_filter = {'test_plan__project_id': project_id}
    else:
        direct_fk_filter = {}
        via_plan_filter = {}

    total_projects = Project.objects.count()
    total_testcases = TestCase.objects.filter(**direct_fk_filter).count()
    total_testplans = TestPlan.objects.filter(**direct_fk_filter).count()

    testruns_qs = TestRun.objects.filter(**via_plan_filter)
    total_testruns = testruns_qs.count()

    if project_id:
        # TestResult 走 test_run→test_plan→project 路径更准确（独立 test_case.project 可空）
        results_qs = TestResult.objects.filter(**via_plan_filter)
    else:
        results_qs = TestResult.objects.all()

    # Consolidate 5 status count queries into 1 aggregate
    result_agg = results_qs.aggregate(
        total=Count('id'),
        passed=Count('id', filter=Q(status='pass')),
        failed=Count('id', filter=Q(status='fail')),
        blocked=Count('id', filter=Q(status='blocked')),
        skipped=Count('id', filter=Q(status='skip')),
        pending=Count('id', filter=Q(status='pending')),
    )

    total_results = result_agg['total']
    passed = result_agg['passed']
    failed = result_agg['failed']
    blocked = result_agg['blocked']
    skipped = result_agg['skipped']
    pending = result_agg['pending']

    # Consolidate defect counts into 1 aggregate
    if project_id:
        defect_filter = direct_fk_filter
    else:
        defect_filter = {}
    defect_agg = Defect.objects.filter(**defect_filter).aggregate(
        total=Count('id'),
        open=Count('id', filter=Q(status='open')),
        resolved=Count('id', filter=Q(status='resolved')),
    )

    open_defects = defect_agg['open']
    resolved_defects = defect_agg['resolved']

    # Test cases by priority
    priority_dist = TestCase.objects.filter(**direct_fk_filter).values('priority').annotate(
        count=Count('id')).order_by('priority')

    # Test cases by type
    type_dist = TestCase.objects.filter(**direct_fk_filter).values('type').annotate(
        count=Count('id')).order_by('type')

    # Recent test runs
    recent_runs = testruns_qs.order_by('-created_at')[:5].values('id', 'name', 'status', 'created_at')

    return Response({
        'total_projects': total_projects,
        'total_testcases': total_testcases,
        'total_testplans': total_testplans,
        'total_testruns': total_testruns,
        'results': {
            'total': total_results,
            'passed': passed,
            'failed': failed,
            'blocked': blocked,
            'skipped': skipped,
            'pending': pending,
            'pass_rate': round(passed / total_results * 100, 1) if total_results > 0 else 0,
        },
        'defects': {
            'total': defect_agg['total'],
            'open': open_defects,
            'resolved': resolved_defects,
        },
        'priority_distribution': list(priority_dist),
        'type_distribution': list(type_dist),
        'recent_runs': list(recent_runs),
    })
