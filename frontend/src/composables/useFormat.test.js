// H28 fix: useFormat 烟雾测试 —— 状态/优先级/严重程度的 type + label 映射，
// H43 修复验证：P1 在 priorityType 应是 danger（统一红色）。
import { describe, it, expect } from 'vitest'
import { useFormat } from './useFormat.js'

describe('useFormat', () => {
  const f = useFormat()

  it('priorityType P0/P1 都是 danger', () => {
    expect(f.priorityType('P0')).toBe('danger')
    expect(f.priorityType('P1')).toBe('danger')   // H43: 之前 MyTestExecuteView 是 warning
    expect(f.priorityType('P2')).toBe('warning')
    expect(f.priorityType('P3')).toBe('info')
    expect(f.priorityType('P4')).toBe('')
    expect(f.priorityType('UNKNOWN')).toBe('')
  })

  it('priorityLabel 走中文', () => {
    expect(f.priorityLabel('P0')).toBe('P0-紧急')
    expect(f.priorityLabel('P1')).toBe('P1-高')
    expect(f.priorityLabel('P9')).toBe('P9')   // fallback 原值
  })

  it('defectSeverityType S0/S1 红、S2 黄、S3 灰、S4 空', () => {
    expect(f.severityType('S0')).toBe('danger')
    expect(f.severityType('S1')).toBe('danger')
    expect(f.severityType('S2')).toBe('warning')
    expect(f.severityType('S3')).toBe('info')
    expect(f.severityType('S4')).toBe('')
  })

  it('defectStatusLabel 中文', () => {
    expect(f.defectStatusLabel('open')).toBe('未处理')
    expect(f.defectStatusLabel('in_progress')).toBe('处理中')
    expect(f.defectStatusLabel('resolved')).toBe('已修复')
    expect(f.defectStatusLabel('closed')).toBe('已关闭')
  })

  it('productLineLabel', () => {
    expect(f.productLineLabel('camera')).toBe('摄像头')
    expect(f.productLineLabel('doorbell')).toBe('门铃')
    expect(f.productLineLabel('xyz')).toBe('xyz')
  })
})