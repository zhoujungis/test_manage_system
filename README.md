# 测试管理系统 — 需求规格说明书

## 1. 项目概述

### 1.1 项目背景

测试管理系统是一个面向软件质量保证（QA）团队的内部测试管理平台，旨在统一管理软件测试的完整生命周期，包括测试用例设计、测试计划制定、测试执行跟踪、缺陷管理以及项目与团队协作。

### 1.2 项目目标

- 提供统一的测试用例库，支持按产品线组织和管理测试用例
- 支持测试计划制定与测试执行跟踪，实现测试流程闭环
- 提供缺陷跟踪能力，连接测试执行与缺陷修复流程
- 提供项目管理功能，支持多项目、多团队协作
- 实现细粒度角色权限控制，满足不同岗位的访问需求

### 1.3 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | Python 3.13+, Django 4.2+, Django REST Framework 3.14+ |
| 数据库 | PostgreSQL |
| 认证 | JWT (djangorestframework-simplejwt) |
| 前端框架 | Vue 3 (Composition API, `<script setup>`) |
| 构建工具 | Vite 8+ |
| UI 组件库 | Element Plus 2.14 |
| 状态管理 | Pinia 3 |
| 路由 | Vue Router 4 |

---

## 2. 用户角色与权限

### 2.1 角色定义

| 角色 | 标识 | 权限描述 |
|------|------|----------|
| 管理员 | admin | 系统全部权限，包括用户管理和权限配置 |
| 测试工程师 | tester | 可参与项目管理、用例库查看、我的项目、测试执行 |
| 测试开发工程师 | developer | 可参与项目管理、用例库管理（含编辑）、我的项目、测试执行 |
| 观察者 | viewer | 只读访问权限 |

### 2.2 细粒度权限

| 权限标识 | 描述 |
|----------|------|
| can_access_projects | 可访问项目管理模块 |
| can_access_testcase_library | 可查看测试用例库 |
| can_manage_testcase_library | 可管理（增删改）测试用例库 |
| can_access_my_projects | 可访问"我的项目"并执行测试 |

### 2.3 认证规则

- 邮箱限制：仅允许 `@glazero.com` 域名邮箱注册
- 注册流程：需通过邮箱验证码验证
- 登录方式：邮箱 + 密码
- Token 策略：Access Token 有效期 1 小时，Refresh Token 有效期 8 小时，支持 Token 轮换
- 速率限制：登录和验证码发送端点需有限流保护

---

## 3. 功能需求

### 3.1 用户认证模块

**3.1.1 注册**
- 用户输入邮箱（仅限 @glazero.com），系统发送验证码到该邮箱
- 用户输入验证码、密码、确认密码完成注册
- 注册成功后自动分配默认角色

**3.1.2 登录**
- 邮箱 + 密码登录，返回 JWT Token 对
- 登录失败速率限制，防止暴力破解

**3.1.3 密码管理**
- 忘记密码：通过邮箱验证码重置密码
- 修改密码：登录状态下可修改密码，需验证旧密码

**3.1.4 个人信息**
- 查看当前登录用户信息（角色、权限）

### 3.2 项目管理模块

**3.2.1 项目 CRUD**
- 创建项目：名称、描述、产品线（摄像头/门铃）、状态（active/archived）
- 编辑项目信息
- 删除项目（软删除或状态标记）
- 项目列表：支持状态筛选

**3.2.2 项目成员管理**
- 添加/移除项目成员
- 设置成员角色：项目负责人（leader）、测试工程师（tester）、开发工程师（developer）

**3.2.3 模块管理**
- 项目下模块的树形层级结构（支持父子关系）
- 模块 CRUD 操作
- 支持多级嵌套

**3.2.4 项目任务管理**
- 创建任务：关联项目、提测轮次、优先级、状态、负责人、截止日期
- 编辑与删除任务
- 任务列表查看与筛选

### 3.3 测试用例管理模块

**3.3.1 用例库**
- 按产品线（摄像头/门铃）组织的集中用例库
- 用例属性：标题、优先级（P0-P4）、类型（功能/接口/UI/性能）、状态（草稿/启用/废弃）、前置条件、所属模块
- 支持搜索：按标题模糊搜索
- 支持筛选：项目、模块、优先级、类型、状态、产品线
- 分页查看，同时支持 "全部" 模式用于导出

**3.3.2 用例步骤**
- 每个用例包含有序的测试步骤
- 每个步骤包含：操作描述、预期结果
- 步骤顺序可调整

**3.3.3 用例操作**
- 新建用例
- 编辑用例（含步骤增删改）
- 删除用例
- 从 Excel 批量导入用例（Django 管理命令）

### 3.4 用例分配与执行模块

**3.4.1 用例分配**
- 将库中用例分配至项目、任务、成员
- 批量分配与批量状态更新
- 分配状态：待执行（pending）、通过（passed）、失败（failed）、不适用（not_applicable）、未测试（not_tested）
- 支持附件上传（单个文件不超过 15MB）

**3.4.2 审批流程**
- 对用例分配结果进行审核
- 审核结果：通过 / 不通过
- 支持批量审批

**3.4.3 测试执行**
- 从"我的项目"入口查看分配给自己的测试任务
- 对每个用例操作：通过（Pass）、失败（Fail）、阻塞（Blocked）、跳过（Skip）
- 填写实际结果描述
- 一个用例可关联多个测试结果

### 3.5 测试计划模块

**3.5.1 计划管理**
- 创建测试计划：关联项目、计划日期范围、状态（draft/active/completed）
- 编辑与删除计划

**3.5.2 用例管理**
- 从用例库中选择用例添加到计划
- 从计划中移除用例
- 用例在计划内可排序

### 3.6 测试执行模块

**3.6.1 执行管理**
- 基于测试计划创建测试执行
- 执行状态：pending / running / completed
- 启动执行、完成执行

**3.6.2 结果管理**
- 创建执行时自动根据计划中的用例生成 TestResult 条目
- 更新单个用例的执行结果：通过/失败/阻塞/跳过
- 填写实际结果备注

### 3.7 缺陷跟踪模块

**3.7.1 缺陷属性**
- 标题、描述、严重程度（S0-S4）、状态（open/in_progress/resolved/closed）
- 关联项目、可选关联测试结果
- 指派给用户

**3.7.2 缺陷操作**
- 新建缺陷
- 编辑缺陷信息
- 状态流转：打开 → 处理中 → 已解决 → 已关闭
- 筛选：按状态、严重程度、指派人

### 3.8 仪表盘模块

**3.8.1 统计概览**
- 项目总数
- 用例总数
- 计划总数
- 执行总数
- 测试结果分布（通过/失败/阻塞/跳过）
- 缺陷统计（未处理/已修复数量）
- 用例优先级分布
- 用例类型分布
- 最近执行记录

### 3.9 管理后台模块

**3.9.1 用户管理**
- 管理员可创建新用户
- 管理员可删除用户
- 查看用户列表

**3.9.2 权限管理**
- 管理员可修改非管理员用户的角色
- 管理员可配置用户的细粒度权限标志

### 3.10 批量导入模块

- Django 管理命令 `import_camera_cases`：从 Excel 文件导入摄像头测试用例
- 自动检测列标题
- 按工作表名称自动分组为模块
- 自动编号步骤
- 支持标准和备用列格式

---

## 4. 非功能需求

### 4.1 安全性

- 所有 API 端点（除登录/注册/密码重置外）需 JWT 认证
- 密码加密存储
- 敏感操作限流保护
- CORS 配置限制允许的来源
- 文件上传大小限制（最大 15MB）

### 4.2 性能

- 测试用例列表支持分页，避免大数据量查询
- 前端构建使用 vendor 分块和 gzip/brotli 压缩优化加载速度
- 数据库查询优化（关联查询使用 select_related/prefetch_related）

### 4.3 可用性

- 前端界面使用中文
- UI 采用 Element Plus 组件库，提供一致的用户体验
- 响应式布局，适配不同屏幕尺寸
- 错误提示友好，操作结果有明确反馈

### 4.4 可维护性

- 后端采用 Django 标准项目结构（config + apps），模块分离清晰
- 前端采用组件化架构，API 层、状态管理、视图层分离
- 统一的 Axios 拦截器处理 Token 刷新和错误处理

### 4.5 兼容性

- 支持主流现代浏览器（Chrome、Firefox、Edge）
- 后端兼容 PostgreSQL 数据库
- 开发环境可使用 SQLite

---

## 5. 数据模型概要

### 5.1 核心实体

```
User (Django 内置)
  └── UserProfile (扩展：角色、权限标志)
  └── VerificationCode (邮箱验证码)

Project (项目)
  ├── Module (模块，自引用树形结构)
  ├── ProjectMember (项目成员)
  ├── ProjectTask (项目任务)
  └── TestCaseAssignment (用例分配)
        └── AssignmentAttachment (分配附件)

TestCase (测试用例)
  └── TestCaseStep (测试步骤)

TestPlan (测试计划)
  └── TestPlanCase (计划中的用例)

TestRun (测试执行)
  └── TestResult (执行结果)
        └── Defect (缺陷)
```

### 5.2 关键关系

- Project 1:N Module（树形层级）
- Project 1:N ProjectMember M:1 User
- Project 1:N TestCaseAssignment M:1 TestCase
- TestPlan 1:N TestPlanCase M:1 TestCase
- TestPlan 1:N TestRun 1:N TestResult M:1 TestCase
- TestResult 1:N Defect

---

## 6. API 设计概要

### 6.1 RESTful 端点总览

| 模块 | 前缀 | 主要操作 |
|------|------|----------|
| 认证 | `/api/auth/` | login, register, refresh, reset-password, change-password, send-code |
| 用户管理 | `/api/auth/admin/` | 用户 CRUD, 权限配置 |
| 项目 | `/api/projects/` | CRUD, 成员/模块/任务/用例分配管理 |
| 模块 | `/api/modules/` | CRUD |
| 成员 | `/api/project-members/` | CRUD |
| 任务 | `/api/project-tasks/` | CRUD |
| 用例分配 | `/api/case-assignments/` | CRUD, 附件上传, 批量审批 |
| 测试用例 | `/api/testcases/` | CRUD, 分页, 筛选, 搜索 |
| 测试计划 | `/api/testplans/` | CRUD, 添加/移除用例 |
| 测试执行 | `/api/testruns/` | CRUD, 启动/完成, 更新结果 |
| 缺陷 | `/api/defects/` | CRUD, 筛选 |
| 仪表盘 | `/api/dashboard/stats/` | 聚合统计 |

### 6.2 响应规范

- 成功响应：返回 HTTP 200/201，数据在响应体中
- 错误响应：返回对应 HTTP 状态码（400/401/403/404/500），包含错误信息
- 分页响应：包含 count、next、previous、results 字段

---

## 7. 前端路由设计

| 路径 | 视图 | 说明 |
|------|------|------|
| `/login` | LoginView | 登录/注册/忘记密码/修改密码 |
| `/home` | HomeView | 仪表盘主页，功能入口 |
| `/projects` | ProjectListView | 项目管理列表 |
| `/projects/:id/*` | ProjectLayout | 项目详情（含子路由） |
| `/testcases/:product_line` | TestCaseManagementView | 用例库浏览 |
| `/testcases/:product_line/new` | TestCaseDetailView | 新建用例 |
| `/testcases/:product_line/:tid` | TestCaseDetailView | 编辑用例 |
| `/tm` | PersonalProjectsView | 我的项目 |
| `/tm/:id/execute` | MyTestExecuteView | 测试执行 |
| `/admin/permissions` | AdminPermissionsView | 权限管理 |
| `/admin/users` | AdminUsersView | 用户管理 |

路由守卫：未登录用户自动跳转 `/login`；权限不足显示提示。

---

## 8. 部署与运行

### 8.1 后端启动

```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

### 8.2 前端启动

```bash
cd frontend
npm install
npm run dev
```

前端开发服务器默认运行在 `http://localhost:5173`，API 请求通过 Vite 代理转发至后端 `http://localhost:8000`。

### 8.3 环境变量

后端通过 `.env` 文件配置数据库连接、SECRET_KEY、邮件服务等敏感信息。

---

## 9. 术语表

| 术语 | 说明 |
|------|------|
| 产品线 | 产品分类维度，当前值为：摄像头、门铃 |
| 提测轮次 | 项目中提测的轮次编号，用于区分不同批次的测试任务 |
| 用例分配 | 将测试用例从用例库分配至具体项目、任务和测试人员 |
| 测试执行 | 基于测试计划进行的一轮测试活动 |
| 严重程度 | 缺陷等级，S0（最严重）到 S4（最轻微） |
| 前置条件 | 执行测试用例前需要满足的环境或数据条件 |
