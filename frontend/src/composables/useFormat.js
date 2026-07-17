// H25 fix: 之前 priority / status / severity / 缺陷状态 等 type/label 映射在
// 10+ 个 view 重复定义，且 P1 颜色在两处不一致。统一到这里。
// 同时也包含日期格式（参见 utils/dateFormat.js）。

import { formatDateTime, formatDate } from '@/utils/dateFormat'

// --- priority (P0-P4) ---
// H43 fix: P1 在两处颜色不一致（TestCaseListView 红 / MyTestExecuteView 黄），
// 统一按"越严重越红"：P0/P1 = danger, P2 = warning, P3 = info, P4 = ''
const PRIORITY_TYPE = { P0: 'danger', P1: 'danger', P2: 'warning', P3: 'info', P4: '' }
const PRIORITY_LABEL = { P0: 'P0-紧急', P1: 'P1-高', P2: 'P2-中', P3: 'P3-低', P4: 'P4-建议' }

// --- 测试用例状态 ---
const TESTCASE_STATUS_TYPE = { draft: 'info', active: 'success', deprecated: 'warning' }
const TESTCASE_STATUS_LABEL = { draft: '草稿', active: '活跃', deprecated: '已废弃' }

// --- 缺陷严重程度 (S0-S4) ---
const SEVERITY_TYPE = { S0: 'danger', S1: 'danger', S2: 'warning', S3: 'info', S4: '' }
const SEVERITY_LABEL = { S0: 'S0-致命', S1: 'S1-严重', S2: 'S2-一般', S3: 'S3-轻微', S4: 'S4-建议' }

// --- 缺陷状态 ---
const DEFECT_STATUS_TYPE = { open: 'danger', in_progress: 'warning', resolved: 'success', closed: 'info' }
const DEFECT_STATUS_LABEL = { open: '未处理', in_progress: '处理中', resolved: '已修复', closed: '已关闭' }

// --- 测试计划状态 ---
const PLAN_STATUS_TYPE = { draft: 'info', active: 'warning', completed: 'success' }
const PLAN_STATUS_LABEL = { draft: '草稿', active: '执行中', completed: '已完成' }

// --- 测试执行状态 ---
const RUN_STATUS_TYPE = { pending: 'info', running: 'warning', completed: 'success' }
const RUN_STATUS_LABEL = { pending: '待执行', running: '执行中', completed: '已完成' }

// --- 用例分配 / 执行结果 ---
const ASSIGNMENT_STATUS_TYPE = {
  pending: 'info', in_progress: 'warning', passed: 'success', failed: 'danger',
  not_applicable: '', not_tested: 'info', blocked: 'warning', skip: '',
}
const ASSIGNMENT_STATUS_LABEL = {
  pending: '待测试', in_progress: '测试中', passed: '通过', failed: '失败',
  not_applicable: '不适用', not_tested: '未测试', blocked: '阻塞', skip: '跳过',
}

// --- 任务状态 ---
const TASK_STATUS_TYPE = { todo: 'info', in_progress: 'warning', done: 'success', blocked: 'danger' }
const TASK_STATUS_LABEL = { todo: '待开始', in_progress: '进行中', done: '已完成', blocked: '阻塞' }

// --- 项目状态 ---
const PROJECT_STATUS_TYPE = { active: 'success', archived: 'info' }
const PROJECT_STATUS_LABEL = { active: '活跃', archived: '已归档' }

// --- 产品线 ---
const PRODUCT_LINE_LABEL = { camera: '摄像头', doorbell: '门铃' }

export function useFormat() {
  return {
    // type maps（el-tag :type 用）
    priorityType: (p) => PRIORITY_TYPE[p] || '',
    testCaseStatusType: (s) => TESTCASE_STATUS_TYPE[s] || 'info',
    severityType: (s) => SEVERITY_TYPE[s] || '',
    defectStatusType: (s) => DEFECT_STATUS_TYPE[s] || 'info',
    planStatusType: (s) => PLAN_STATUS_TYPE[s] || 'info',
    runStatusType: (s) => RUN_STATUS_TYPE[s] || 'info',
    runResultType: (s) => ASSIGNMENT_STATUS_TYPE[s] || 'info',
    assignmentStatusType: (s) => ASSIGNMENT_STATUS_TYPE[s] || 'info',
    taskStatusType: (s) => TASK_STATUS_TYPE[s] || 'info',
    projectStatusType: (s) => PROJECT_STATUS_TYPE[s] || 'info',

    // label maps（中文显示用）
    priorityLabel: (p) => PRIORITY_LABEL[p] || p,
    testCaseStatusLabel: (s) => TESTCASE_STATUS_LABEL[s] || s,
    severityLabel: (s) => SEVERITY_LABEL[s] || s,
    defectStatusLabel: (s) => DEFECT_STATUS_LABEL[s] || s,
    planStatusLabel: (s) => PLAN_STATUS_LABEL[s] || s,
    runStatusLabel: (s) => RUN_STATUS_LABEL[s] || s,
    runResultLabel: (s) => ASSIGNMENT_STATUS_LABEL[s] || s,
    assignmentStatusLabel: (s) => ASSIGNMENT_STATUS_LABEL[s] || s,
    taskStatusLabel: (s) => TASK_STATUS_LABEL[s] || s,
    projectStatusLabel: (s) => PROJECT_STATUS_LABEL[s] || s,
    productLineLabel: (k) => PRODUCT_LINE_LABEL[k] || k,

    // 日期
    formatDateTime,
    formatDate,
  }
}