from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Q
from apps.accounts.permissions import accessible_project_ids
from apps.projects.models import Project
from apps.testcases.models import TestCase
from apps.testcases.views import _parse_int_query_param
from apps.testplans.models import TestPlan
from apps.testruns.models import TestRun, TestResult
from apps.defects.models import Defect


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def stats(request):
    scoped = accessible_project_ids(request.user)
    if scoped is None:
        # admin / 有项目管理权限 → 不限
        proj_pk_q = Q()      # Project 主键过滤 (id)
        proj_q = Q()         # 外键 project_id 过滤 (TestCase/TestPlan/Defect)
        plan_q = Q()
        via_plan_q = Q()
    else:
        proj_pk_q = Q(id__in=scoped)              # Project 用 pk
        proj_q = Q(project_id__in=scoped)
        plan_q = Q(project_id__in=scoped)
        via_plan_q = Q(test_plan__project_id__in=scoped)

    project_id, err = _parse_int_query_param(request, 'project')
    if err: return err
    if project_id is not None:
        # C1 fix: ?project= drill-down 必须落在 scope 内，做交集防止 IDOR
        # （之前直接 Q(project_id=project_id) 覆盖了 scope 过滤）
        # 再叠加 C-重审 fix: Project 用 id，其它外键用 project_id；
        # 否则 Project.objects.filter(Q(project_id=...)) 直接 FieldError 500
        if scoped is None:
            proj_pk_q = Q(id=project_id)
            proj_q = Q(project_id=project_id)
            plan_q = Q(project_id=project_id)
            via_plan_q = Q(test_plan__project_id=project_id)
        else:
            proj_pk_q = Q(id=project_id, id__in=scoped)
            proj_q = Q(project_id=project_id, project_id__in=scoped)
            plan_q = Q(project_id=project_id, project_id__in=scoped)
            via_plan_q = Q(
                test_plan__project_id=project_id,
                test_plan__project_id__in=scoped,
            )

    total_projects = Project.objects.filter(proj_pk_q).count()
    total_testcases = TestCase.objects.filter(proj_q).count()
    total_testplans = TestPlan.objects.filter(plan_q).count()

    testruns_qs = TestRun.objects.filter(via_plan_q)
    total_testruns = testruns_qs.count()

    # TestResult 走 test_run→test_plan→project 路径更准确（独立 test_case.project 可空）
    results_qs = TestResult.objects.filter(via_plan_q)

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
    defect_agg = Defect.objects.filter(proj_q).aggregate(
        total=Count('id'),
        open=Count('id', filter=Q(status='open')),
        resolved=Count('id', filter=Q(status='resolved')),
    )

    open_defects = defect_agg['open']
    resolved_defects = defect_agg['resolved']

    # Test cases by priority
    priority_dist = TestCase.objects.filter(proj_q).values('priority').annotate(
        count=Count('id')).order_by('priority')

    # Test cases by type
    type_dist = TestCase.objects.filter(proj_q).values('type').annotate(
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
