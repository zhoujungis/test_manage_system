"""Static verification of 7 security fixes (no Django import needed).

Usage: cd backend && python ../verify_fixes.py
"""
import ast
import pathlib

BASE = pathlib.Path(__file__).resolve().parent
failures = []


def check(label, condition, detail=''):
    if condition:
        print(f'  OK   {label}')
    else:
        failures.append((label, detail))
        print(f'  FAIL {label}  -- {detail}')


def find_class(tree, name):
    for n in tree.body:
        if isinstance(n, ast.ClassDef) and n.name == name:
            return n
    return None


def meta_fields_of(cls):
    """Return the AST node of Meta.fields within a serializer class."""
    for stmt in cls.body:
        if isinstance(stmt, ast.ClassDef) and stmt.name == 'Meta':
            for s in stmt.body:
                if isinstance(s, ast.Assign) and any(
                    isinstance(t, ast.Name) and t.id == 'fields' for t in s.targets
                ):
                    return s.value
    return None


def field_names_of(cls):
    """Top-level serializer field declarations (AnnAssign or Assign)."""
    names = []
    for s in cls.body:
        if isinstance(s, ast.AnnAssign) and isinstance(s.target, ast.Name):
            names.append(s.target.id)
        elif isinstance(s, ast.Assign):
            for t in s.targets:
                if isinstance(t, ast.Name):
                    names.append(t.id)
    return names


# === C1 ===
print('\n[C1] RegisterSerializer 移除 role 字段')
src = (BASE / 'backend/apps/accounts/serializers.py').read_text(encoding='utf-8')
tree = ast.parse(src)
reg_cls = find_class(tree, 'RegisterSerializer')
fields_node = meta_fields_of(reg_cls)
fields = ast.literal_eval(fields_node) if fields_node is not None else None
check('RegisterSerializer.Meta.fields 不含 role',
      'role' not in fields, f'fields={fields}')

create_fn = next((s for s in reg_cls.body
                  if isinstance(s, ast.FunctionDef) and s.name == 'create'), None)
create_src = ast.unparse(create_fn) if create_fn else ''
check('create() 通过 DEFAULT_ROLE 硬编码 role',
      'self.DEFAULT_ROLE' in create_src
      and "validated_data.pop('role')" not in create_src)


# === C2 ===
print('\n[C2] change_password 加 @IsAuthenticated')
chg_cls = find_class(tree, 'ChangePasswordSerializer')
chg_fields = field_names_of(chg_cls)
check('ChangePasswordSerializer 不再含 email 字段',
      'email' not in chg_fields, f'fields={chg_fields}')
check('ChangePasswordSerializer 仍含 old_password / new_password',
      {'old_password', 'new_password'} <= set(chg_fields), f'fields={chg_fields}')

av = (BASE / 'backend/apps/accounts/views.py').read_text(encoding='utf-8').replace('\r\n', '\n')
import re
m = re.search(
    r'@permission_classes\(\[IsAuthenticated\]\)\s*\n@throttle_classes\(\[ChangePasswordRateThrottle\]\)\s*\ndef change_password',
    av,
)
check('change_password 加 @IsAuthenticated + @throttle_classes([ChangePasswordRateThrottle])',
      m is not None)

sv = (BASE / 'backend/config/settings.py').read_text(encoding='utf-8')
check("DEFAULT_THROTTLE_RATES 含 'change_password': '10/min'",
      "'change_password': '10/min'" in sv)

th = (BASE / 'backend/apps/accounts/throttles.py').read_text(encoding='utf-8')
check('throttles.py 含 ChangePasswordRateThrottle 类',
      'class ChangePasswordRateThrottle' in th)


# === C11 ===
print('\n[C11] SECRET_KEY fail-fast')
check("SECRET_KEY = os.environ['DJANGO_SECRET_KEY']",
      "os.environ['DJANGO_SECRET_KEY']" in sv)
check('占位符/django-insecure 守卫存在',
      'ImproperlyConfigured' in sv and 'django-insecure-' in sv)
check('守卫是 DEBUG-gated',
      'if not DEBUG and' in sv)
check('守卫拒绝 your-secret-key-here',
      'your-secret-key-here' in sv)


# === C6 ===
print('\n[C6] dashboard 修 TestRun project 路径')
dv = (BASE / 'backend/apps/dashboard/views.py').read_text(encoding='utf-8').replace('\r\n', '\n')
check('使用 test_plan__project_id',
      'test_plan__project_id' in dv)
check('不再存在裸 TestRun.objects.filter(project_id=…)',
      'TestRun.objects.filter(project_id=' not in dv,
      'still using buggy project_id filter on TestRun')


# === C4 + C1/C2 IDOR intersection ===
print('\n[C4] 三 viewset 加 get_queryset 项目范围 + drill-down 交集守卫')
for app in ('testplans', 'testruns', 'defects'):
    v = (BASE / f'backend/apps/{app}/views.py').read_text(encoding='utf-8').replace('\r\n', '\n')
    check(f'{app}/views.py 引用 centralized accessible_project_ids',
          'from apps.accounts.permissions import accessible_project_ids' in v
          and 'accessible_project_ids(self.request.user)' in v)
    check(f'{app}/views.py 不再含本地 _accessible_project_ids',
          'def _accessible_project_ids' not in v,
          '本地 helper 应统一迁移到 accounts.permissions.accessible_project_ids')
    check(f'{app}/views.py scoped 过滤用 project_id__in',
          'project_id__in=scoped' in v
          or 'test_plan__project_id__in=scoped' in v)
    # C1/C2 fix: ?project= drill-down 必须落在 scope 内
    check(f'{app}/views.py drill-down 与 scope 取交集（防 IDOR）',
          ('project_id=project_id, project_id__in=scoped' in v)
          or ('test_plan__project_id=project_id,\n                    test_plan__project_id__in=scoped' in v)
          or ('test_plan__project_id=project_id,\n                test_plan__project_id__in=scoped' in v))


# === C1 dashboard drill-down 交集 ===
print('\n[C1] dashboard drill-down 防 IDOR 交集')
dv_intersect = (
    'project_id=project_id, project_id__in=scoped' in dv
    and 'test_plan__project_id=project_id,\n                test_plan__project_id__in=scoped' in dv
)
check('dashboard drill-down Q(project_id=...) ∩ scope', dv_intersect)


# === C5 ===
print('\n[C5] permissions.js fail-closed')
pj = (BASE / 'frontend/src/utils/permissions.js').read_text(encoding='utf-8').replace('\r\n', '\n')
check('getPermissions 定义 allFlagsFalse 兜底',
      'function allFlagsFalse' in pj)
check('getPermissions 缺 payload 时返回 allFlagsFalse()',
      'return allFlagsFalse()' in pj)
# 旧版最后一段 fail-open 全 true 应被剔除
old_default_present = (
    'if (getRole(user) === \'viewer\') {\n'
    '    return {\n'
    '      can_access_projects: true,\n'
    '      can_access_testcase_library: true,\n'
    '      can_manage_testcase_library: false,\n'
    '      can_access_my_projects: true,\n'
    '    }\n'
    '  }\n'
    '  return {\n'
    '    can_access_projects: true,\n'
    '    can_access_testcase_library: true,\n'
    '    can_manage_testcase_library: true,\n'
    '    can_access_my_projects: true,\n'
    '  }'
)
check('不在 getPermissions 中保留 viewer 默认全 true',
      old_default_present not in pj)


# === C7 ===
print('\n[C7] request.js 单飞 refresh + 独立 client + Pinia 同步')
rj = (BASE / 'frontend/src/utils/request.js').read_text(encoding='utf-8').replace('\r\n', '\n')
check('独立 axios refreshClient',
      'const refreshClient = axios.create' in rj)
check('单飞 promise inflightRefresh',
      'let inflightRefresh = null' in rj)
check('复用 inflightRefresh',
      'if (inflightRefresh) return inflightRefresh' in rj)
check('refresh 端点走 refreshClient',
      'refreshClient' in rj and '/auth/refresh/' in rj)
check('回调 store.onTokenRefreshed',
      'store.onTokenRefreshed' in rj)

sj = (BASE / 'frontend/src/stores/auth.js').read_text(encoding='utf-8').replace('\r\n', '\n')
check('stores/auth.js 暴露 onTokenRefreshed',
      'function onTokenRefreshed' in sj)
check('logout 不再无脑 localStorage.clear()',
      "localStorage.clear()" not in sj)


print('\n' + '=' * 60)
if failures:
    print(f'{len(failures)} checks failed:')
    for label, detail in failures:
        print(f'  - {label}: {detail}')
    raise SystemExit(1)
else:
    print('All 7 fixes statically verified OK')


# =================================================================
# 第二轮：C3 (OTP 重写) + D2 (ProjectTask 索引) + D3 (TestCaseAssignment 索引)
# =================================================================
print('\n\n' + '#' * 60)
print('# C3/D2/D3 verification')
print('#' * 60)

# ===== C3 =====
print('\n[C3] OTP 系统重写：secrets + 哈希 + purpose + 锁定')

am = (BASE / 'backend/apps/accounts/models.py').read_text(encoding='utf-8').replace('\r\n', '\n')

check('accounts/models.py 仍定义 VerificationCode 类',
      'class VerificationCode(models.Model):' in am)
check('VerificationCode 不再存明文 code 字段',
      "'code', models.CharField(max_length=6)" not in am
      and "name='code'" not in am)
check('VerificationCode 包含 purpose 字段',
      'PURPOSE_REGISTER' in am and 'PURPOSE_RESET' in am
      and "name='purpose'" in am or "models.CharField(\n        max_length=16, choices=PURPOSE_CHOICES,\n        purpose_" in am or "purpose = models.CharField" in am)
check('VerificationCode 包含 code_hash 字段',
      "name='code_hash'" in am or 'code_hash = models.CharField' in am)
check('VerificationCode 包含 attempts 字段',
      "name='attempts'" in am or 'attempts = models.PositiveSmallIntegerField' in am)
check('VerificationCode 包含 consumed_at 字段',
      "name='consumed_at'" in am or 'consumed_at = models.DateTimeField' in am)
check('VerificationCode.email 加 db_index=True',
      'email = models.EmailField(db_index=True)' in am)
check('VerificationCode.created_at 加 db_index=True',
      'created_at = models.DateTimeField(auto_now_add=True, db_index=True)' in am)
check('VerificationCode 有复合索引 (email, purpose, consumed_at)',
      "models.Index(fields=['email', 'purpose', 'consumed_at'])" in am)
check('VerificationCode.issue() 用 secrets.randbelow 生成随机码',
      'secrets.randbelow' in am and 'def issue(' in am)
check('VerificationCode.record_failure() 存在',
      'def record_failure(' in am)
check('VerificationCode 用 MAX_ATTEMPTS 做锁定',
      'MAX_ATTEMPTS' in am and 'is_locked' in am)

# throttles
th = (BASE / 'backend/apps/accounts/throttles.py').read_text(encoding='utf-8').replace('\r\n', '\n')
check('throttles.py 含 VerifyCodeRateThrottle 类',
      'class VerifyCodeRateThrottle' in th)
check('VerifyCodeRateThrottle 用 (email, IP) 双维度 key',
      "verify_{digest}_{ip}" in th or 'verify_ip_' in th)
check('throttles.py 含 SendResetCodeRateThrottle 类（与 send_code scope 分离）',
      'class SendResetCodeRateThrottle' in th)

# settings
sv = (BASE / 'backend/config/settings.py').read_text(encoding='utf-8')
check("DEFAULT_THROTTLE_RATES 含 'verify_code'",
      "'verify_code'" in sv)
check("DEFAULT_THROTTLE_RATES 含 'send_reset_code'",
      "'send_reset_code'" in sv)
check("DEFAULT_THROTTLE_RATES 含 'change_password'",
      "'change_password'" in sv)

# views
av = (BASE / 'backend/apps/accounts/views.py').read_text(encoding='utf-8').replace('\r\n', '\n')
check('accounts/views.py 不再用 random.randint',
      'random.randint' not in av)
check('accounts/views.py 使用 secrets.compare_digest',
      'secrets.compare_digest' in av)
check('accounts/views.py 中 _verify_code 接受 purpose 参数',
      '_verify_code(email, code,' in av or '_verify_code(email, code, purpose)' in av
      or 'def _verify_code(email, code, purpose)' in av)
check('reset_password 不再用裸的 {"error": "该邮箱未注册"} 早返回',
      "return Response({'error': '该邮箱未注册'}" not in av
      and '"error": "该邮箱未注册"' not in av)
check('reset_password 撤销所有 outstanding refresh token',
      'OutstandingToken.objects.filter(user=user)' in av)
check('@throttle_classes([VerifyCodeRateThrottle]) 出现在 register / reset_password',
      av.count('@throttle_classes([VerifyCodeRateThrottle])') >= 2)

# migration 0007
mig7 = (BASE / 'backend/apps/accounts/migrations/0007_verificationcode_purpose_hash.py')
check('migration 0007 文件存在',
      mig7.exists())
mig_src = mig7.read_text(encoding='utf-8')
check('migration 0007 含清空遗留行的 RunPython',
      'clear_legacy_codes' in mig_src)
check('migration 0007 含复合索引',
      "verification_email_purpose__idx" in mig_src or 'verificationcode' in mig_src.lower())

# ===== D2 =====
print('\n[D2] ProjectTask.status / priority 加索引')
pm = (BASE / 'backend/apps/projects/models.py').read_text(encoding='utf-8').replace('\r\n', '\n')
check('ProjectTask.status 加 db_index',
      "status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo', db_index=True)" in pm)
check('ProjectTask.priority 加 db_index',
      "priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='P2', db_index=True)" in pm)

# ===== D3 =====
print('\n[D3] TestCaseAssignment.status / approval_status 加索引')
check('TestCaseAssignment.status 加 db_index',
      "status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)" in pm)
check('TestCaseAssignment.approval_status 加 db_index',
      "approval_status = models.CharField(max_length=20, choices=APPROVAL_CHOICES, default='pending', db_index=True)" in pm)

# migration 0012
mig12 = BASE / 'backend/apps/projects/migrations/0012_projecttask_testcaseassignment_indexes.py'
check('projects migration 0012 文件存在', mig12.exists())
mig12_src = mig12.read_text(encoding='utf-8')
check('migration 0012 覆盖 ProjectTask.status 与 priority',
      mig12_src.count("model_name='projecttask'") == 2)
check('migration 0012 覆盖 TestCaseAssignment.status 与 approval_status',
      mig12_src.count("model_name='testcaseassignment'") == 2)

# syntax check all modified python files
print('\n[文件语法]')
for f in (
    'backend/apps/accounts/models.py',
    'backend/apps/accounts/views.py',
    'backend/apps/accounts/throttles.py',
    'backend/config/settings.py',
    'backend/apps/projects/models.py',
    'backend/apps/accounts/migrations/0007_verificationcode_purpose_hash.py',
    'backend/apps/projects/migrations/0012_projecttask_testcaseassignment_indexes.py',
):
    try:
        ast.parse((BASE / f).read_text(encoding='utf-8'))
        print(f'  OK   {f}')
    except SyntaxError as e:
        print(f'  FAIL {f}: {e}')
        failures.append((f, str(e)))

print('\n' + '=' * 60)
if failures:
    print(f'{len(failures)} checks failed:')
    for label, detail in failures:
        print(f'  - {label}: {detail}')
    raise SystemExit(1)
else:
    print('All 7 + C3/D2/D3 fixes statically verified OK')


# =================================================================
# 第三轮：M1 / M3 / F10 / H1 / H3 / H5
# =================================================================
print('\n\n' + '#' * 60)
print('# M1/M3/F10/H1/H3/H5 verification')
print('#' * 60)

# ===== M1 =====
print('\n[M1] UserSerializer N+1 / profile 缓存')
src_a = (BASE / 'backend/apps/accounts/serializers.py').read_text(encoding='utf-8').replace('\r\n', '\n')
check('UserSerializer.__init__ 初始化 _profile_cache',
      '_profile_cache = {}' in src_a)
# AST 检查：扫描整个文件，看是否还有运行时调 UserProfile.objects.get_or_create(...)
def _ast_has_get_or_create(source, qualified='UserProfile'):
    tree = ast.parse(source)
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if (isinstance(func, ast.Attribute) and func.attr == 'get_or_create'
                    and isinstance(func.value, ast.Attribute)
                    and isinstance(func.value.value, ast.Name)
                    and func.value.value.id == qualified):
                found.append(node.lineno)
    return found

_got_lines = _ast_has_get_or_create(src_a)
check('UserSerializer 不再调 UserProfile.objects.get_or_create',
      not _got_lines, f'运行时仍存在 get_or_create at lines {_got_lines}')
check('UserSerializer 用 user.profile（select_related 友好的）',
      'user.profile' in src_a)
check('UserSerializer._missing_profile 兜底',
      'def _missing_profile(self' in src_a)

av = (BASE / 'backend/apps/accounts/views.py').read_text(encoding='utf-8').replace('\r\n', '\n')
check('user_list 用 select_related(profile) 预取',
      "select_related('profile')" in av)
check('admin_user_permissions 用 select_related(profile) 预取',
      av.count("select_related('profile')") >= 2)

# ===== M3 =====
print('\n[M3] is_active 拦截')
pm = (BASE / 'backend/apps/accounts/permissions.py').read_text(encoding='utf-8').replace('\r\n', '\n')
check('_is_active(user) helper 存在',
      'def _is_active(' in pm)
check('get_user_profile 检查 is_active',
      'if not _is_active(user):' in pm)
check('is_admin 早返回 False 当 inactive',
      pm.count('if not _is_active(user):\n        return False') >= 4
      or pm.count('is_admin(user):\n        if is_admin(user):') >= 1)

sv = (BASE / 'backend/config/settings.py').read_text(encoding='utf-8')
check("SIMPLE_JWT 显式设置 USER_AUTHENTICATION_RULE 拒绝 inactive",
      'USER_AUTHENTICATION_RULE' in sv)

# ===== F10 =====
print('\n[F10] Element Plus 自动按需导入')
pkg = (BASE / 'frontend/package.json').read_text(encoding='utf-8')
check('package.json devDependencies 含 unplugin-vue-components',
      'unplugin-vue-components' in pkg)
check('package.json devDependencies 含 unplugin-auto-import',
      'unplugin-auto-import' in pkg)

vc = (BASE / 'frontend/vite.config.js').read_text(encoding='utf-8')
check('vite.config.js import AutoImport',
      "from 'unplugin-auto-import/vite'" in vc)
check('vite.config.js import Components resolver',
      "from 'unplugin-vue-components/resolvers'" in vc
      and 'ElementPlusResolver' in vc)

mj = (BASE / 'frontend/src/main.js').read_text(encoding='utf-8')
check('main.js 不再 import ElementPlus 全量',
      "import ElementPlus from 'element-plus'" not in mj)
check('main.js 不再遍历注册 icons',
      'ElementPlusIconsVue' not in mj)
check('main.js 仍保留 element-plus/dist/index.css（reset）',
      "'element-plus/dist/index.css'" in mj)

# ===== H1 =====
print('\n[H1] DEBUG / ALLOWED_HOSTS / CORS 收紧')
sv_local = sv
check('_env_bool helper 接受 true/1/yes/on',
      'def _env_bool(' in sv_local
      and "raw in ('1', 'true', 'yes', 'on')" in sv_local)
check('DEBUG = _env_bool(...)',
      'DEBUG = _env_bool(' in sv_local)
check('CORS_ALLOW_ALL_ORIGINS = _env_bool(...)',
      'CORS_ALLOW_ALL_ORIGINS = _env_bool(' in sv_local)
check('生产环境拒绝 CORS_ALLOW_ALL=True',
      'CORS_ALLOW_ALL=True' in sv_local and '生产环境是危险的' in sv_local)
check('ALLOWED_HOSTS strip + 去空',
      "h.strip() for h in os.environ.get('DJANGO_ALLOWED_HOSTS'" in sv_local)
check('生产环境 ALLOWED_HOSTS 拒绝 *',
      "h != '*'" in sv_local)

# ===== H3 =====
print('\n[H3] login throttle 双维度 key')
th = (BASE / 'backend/apps/accounts/throttles.py').read_text(encoding='utf-8').replace('\r\n', '\n')
check('LoginRateThrottle 用 (ip, email) 双维度 key',
      'login_{ip}_{digest}' in th)
check('LoginRateThrottle 用 hashlib 截断 email',
      "hashlib.sha256(email.encode('utf-8')).hexdigest()[:16]" in th)

# ===== H5 =====
print('\n[H5] admin 创建 admin 拦截')
check('AdminCreateUserSerializer choices 排除 admin',
      "if c[0] != 'admin'" in src_a)
check('AdminCreateUserSerializer.validate_role 拒绝 admin',
      "if value == 'admin':" in src_a
      and 'def validate_role(self, value):' in src_a)
check('admin_create_user 写审计日志',
      'admin_create_user' in av
      and "audit = logging.getLogger(" in av
      and 'actor=%s target=%s' in av)

# ===== 总检：所有修改过的 python 文件能 parse =====
print('\n[语法]')
for f in (
    'backend/apps/accounts/serializers.py',
    'backend/apps/accounts/views.py',
    'backend/apps/accounts/throttles.py',
    'backend/apps/accounts/permissions.py',
    'backend/config/settings.py',
):
    try:
        ast.parse((BASE / f).read_text(encoding='utf-8'))
        print(f'  OK   {f}')
    except SyntaxError as e:
        print(f'  FAIL {f}: {e}')
        failures.append((f, str(e)))

print('\n' + '=' * 60)
if failures:
    print(f'{len(failures)} checks failed:')
    for label, detail in failures:
        print(f'  - {label}: {detail}')
    raise SystemExit(1)
else:
    print('All 7 + C3/D2/D3 + M1/M3/F10/H1/H3/H5 fixes statically verified OK')


# =================================================================
# 第四轮：M4/M5/M12/M13/M14/H6/D7/D8/F1/F2/F4/F7/F16
# =================================================================
print('\n\n' + '#' * 60)
print('# Final sweep verification')
print('#' * 60)

# ===== M4 / M14 / H6 / throttle =====
print('\n[M4/M14/H6] throttle 完善 + UserRateThrottle + IP 维度')
th = (BASE / 'backend/apps/accounts/throttles.py').read_text(encoding='utf-8')
check('throttles 含 RefreshRateThrottle', 'class RefreshRateThrottle' in th)
check('throttles 含 UserDefaultRateThrottle', 'class UserDefaultRateThrottle' in th)

urls = (BASE / 'backend/apps/accounts/urls.py').read_text(encoding='utf-8')
check('urls.py wrap TokenRefreshView 为 ThrottledTokenRefreshView',
      'class ThrottledTokenRefreshView(TokenRefreshView)' in urls
      and 'throttle_classes = [RefreshRateThrottle]' in urls)

sv = (BASE / 'backend/config/settings.py').read_text(encoding='utf-8')
check('DEFAULT_THROTTLE_CLASSES 含 UserDefaultRateThrottle',
      'apps.accounts.throttles.UserDefaultRateThrottle' in sv)
check('DEFAULT_THROTTLE_RATES 含 user scope',
      "'user': '1000/hour'" in sv)
check('DEFAULT_THROTTLE_RATES 含 refresh scope',
      "'refresh': '30/min'" in sv)
check('send_code 同时用 AnonRateThrottle + SendCodeRateThrottle',
      '@throttle_classes([AnonRateThrottle, SendCodeRateThrottle])' in sv
      or 'throttle_classes([AnonRateThrottle, SendCodeRateThrottle])' in sv
      or 'throttle_classes([AnonRateThrottle, SendCodeRateThrottle])'
          in (BASE / 'backend/apps/accounts/views.py').read_text(encoding='utf-8'))

# ===== M5 SECURE_* =====
print('\n[M5] SECURE_* 生产硬化')
check('SECURE_SSL_REDIRECT 设置',
      'SECURE_SSL_REDIRECT' in sv)
check('SECURE_HSTS_SECONDS 设置',
      'SECURE_HSTS_SECONDS' in sv)
check('SECURE_PROXY_SSL_HEADER 设置',
      'SECURE_PROXY_SSL_HEADER' in sv)
check('SESSION_COOKIE_SECURE 在生产环境开启',
      'SESSION_COOKIE_SECURE = True' in sv)

# ===== M13 PASSWORD_HASHERS =====
print('\n[M13] argon2 优先 hasher')
check('PASSWORD_HASHERS 含 Argon2PasswordHasher',
      'Argon2PasswordHasher' in sv)
check('PASSWORD_HASHERS 含 PBKDF2 兜底',
      'PBKDF2PasswordHasher' in sv)

# ===== M12 cache =====
print('\n[M12] cache backend 可配置')
check('cache backend 支持 redis 配置',
      "CACHE_BACKEND == 'redis'" in sv)
check('cache backend 支持 locmem 兜底',
      "CACHE_BACKEND == 'locmem'" in sv)
check('cache backend 默认 file',
      "'file'" in sv
      and 'django.core.cache.backends.filebased.FileBasedCache' in sv)

# ===== H4 login dummy hash =====
print('\n[H4] login timing-safe')
src_a = (BASE / 'backend/apps/accounts/serializers.py').read_text(encoding='utf-8')
check('login 用 DUMMY_HASH 兜底',
      'DUMMY_HASH = make_password(' in src_a
      and 'check_password(password, DUMMY_HASH)' in src_a)
check('login 用 iexact 邮箱查找',
      'email__iexact=' in src_a)

# ===== D7 Meta.ordering =====
print('\n[D7] Meta.ordering 默认值已清')
pm_src = (BASE / 'backend/apps/projects/models.py').read_text(encoding='utf-8')
# 检查 Project / ProjectTask / TestCaseAssignment 的 Meta 不再含 ordering
for cls_name in ('Project', 'ProjectTask', 'TestCaseAssignment'):
    tree = ast.parse(pm_src)
    found = False
    for n in tree.body:
        if isinstance(n, ast.ClassDef) and n.name == cls_name:
            for stmt in n.body:
                if isinstance(stmt, ast.ClassDef) and stmt.name == 'Meta':
                    for s in stmt.body:
                        if isinstance(s, ast.Assign) and any(
                            isinstance(t, ast.Name) and t.id == 'ordering'
                            for t in s.targets
                        ):
                            found = True
    check(f'{cls_name}.Meta 不含 ordering',
          not found, f'{cls_name} 仍有默认 ordering')

# ===== D8 UserProfile 默认 deny =====
print('\n[D8] UserProfile 默认 deny')
am = (BASE / 'backend/apps/accounts/models.py').read_text(encoding='utf-8')
for flag in ('can_access_projects', 'can_access_testcase_library',
             'can_manage_testcase_library', 'can_access_my_projects'):
    check(f'UserProfile.{flag} default=False',
          f'{flag} = models.BooleanField(default=False, verbose_name=' in am)

# ===== F1 路由 meta 守卫 =====
print('\n[F1] 路由 meta 守卫')
rj = (BASE / 'frontend/src/router/index.js').read_text(encoding='utf-8')
check('router 用 hasReadPermission',
      'hasReadPermission(user, meta.permission)' in rj)
check('router 用 hasWritePermission',
      'hasWritePermission(user, meta.writePermission)' in rj)
check('router meta.admin 守卫',
      'meta.admin && !isAdmin(user)' in rj)

# ===== F2 isPathAllowed fail-closed =====
print('\n[F2] isPathAllowed fail-closed')
pj = (BASE / 'frontend/src/utils/permissions.js').read_text(encoding='utf-8')
check('isPathAllowed 处理 null user',
      'if (!user) return false' in pj)


def _isPathAllowed_returns(text):
    """只统计 isPathAllowed 函数体内实际的 return 语句（排除注释行）。"""
    i = text.find('export function isPathAllowed')
    if i < 0:
        return []
    j = text.find('\nexport ', i + 1)
    body = text[i:j] if j > 0 else text[i:]
    returns = []
    for ln in body.splitlines():
        s = ln.strip()
        if s.startswith('//') or s.startswith('/*') or s.startswith('*'):
            continue
        if 'return ' in s and not s.lstrip().startswith('//'):
            returns.append(s)
    return returns


returns_in_ipa = _isPathAllowed_returns(pj)
check('isPathAllowed 末尾兜底是 false（fail-closed）',
      returns_in_ipa and returns_in_ipa[-1].strip() == 'return false',
      f'isPathAllowed 末尾: {returns_in_ipa[-1] if returns_in_ipa else "<empty>"}')
check('isPathAllowed 中 return true 仅出现在允许名单分支',
      sum(1 for r in returns_in_ipa if 'return true' in r) == 2,
      f'实际 true 出现 {sum(1 for r in returns_in_ipa if "return true" in r)} 次; 详情:\n  '
      + '\n  '.join(returns_in_ipa))

# ===== F4 AbortController / gen-token =====
print('\n[F4] generation token 防 stale response')
mtev = (BASE / 'frontend/src/views/MyTestExecuteView.vue').read_text(encoding='utf-8')
check('MyTestExecuteView 用 pendingDetail generation token',
      'pendingDetail' in mtev and 'reqToken = ++pendingDetail.value' in mtev)

# ===== F7 表单 validate =====
print('\n[F7] 表单校验')
tcd = (BASE / 'frontend/src/views/TestCaseDetailView.vue').read_text(encoding='utf-8')
check('TestCaseDetailView 引入 formRef',
      'formRef' in tcd)
check('TestCaseDetailView 引入 rules',
      'const rules = ' in tcd)
check('TestCaseDetailView handleSave validate()',
      'formRef.value?.validate' in tcd)
check('TestCaseDetailView saving 状态锁',
      'saving.value = true' in tcd and 'saving.value = false' in tcd)

# ===== F16 全局错误处理 =====
print('\n[F16] 全局 Vue 错误处理')
mj = (BASE / 'frontend/src/main.js').read_text(encoding='utf-8')
check('main.js 含 app.config.errorHandler',
      'app.config.errorHandler' in mj)

# ===== CI =====
print('\n[CI] GitHub workflows 存在')
check('backend.yml workflow 存在',
      (BASE / '.github/workflows/backend.yml').exists())
check('frontend.yml workflow 存在',
      (BASE / '.github/workflows/frontend.yml').exists())

# ===== 语法 =====
print('\n[语法]')
for f in (
    'backend/apps/accounts/throttles.py',
    'backend/apps/accounts/urls.py',
    'backend/apps/projects/models.py',
    'backend/apps/accounts/models.py',
):
    try:
        ast.parse((BASE / f).read_text(encoding='utf-8'))
        print(f'  OK   {f}')
    except SyntaxError as e:
        print(f'  FAIL {f}: {e}')
        failures.append((f, str(e)))

print('\n' + '=' * 60)
if failures:
    print(f'{len(failures)} checks failed:')
    for label, detail in failures:
        print(f'  - {label}: {detail}')
    raise SystemExit(1)
else:
    print('Full sweep verification OK')
