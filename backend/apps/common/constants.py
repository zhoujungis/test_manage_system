"""M10 fix: 集中产品 / 业务常量。

之前 @glazero.com、15MB、6/8 位密码、分页 20/100/500/2000 散落在 serializer、
view、settings.py 三处。修改时容易漏；这里给唯一来源。
"""
from django.conf import settings

# === 认证 / 注册 ===
GLAZERO_EMAIL_SUFFIX = '@glazero.com'
MIN_PASSWORD_LENGTH = 6

# === 文件上传 ===
ASSIGNMENT_ATTACHMENT_MAX_BYTES = 15 * 1024 * 1024  # 15 MB

# === 分页 ===
DEFAULT_PAGE_SIZE = 20
LARGE_PAGE_SIZE = 100      # 项目详情等列表
MAX_PAGE_SIZE = 200        # 自定义 action 上限

# === 用例库 ===
TESTCASE_TREE_DEFAULT_LIMIT = 500
TESTCASE_TREE_HARD_MAX = 2000

# === 验证码 ===
VERIFICATION_CODE_LENGTH = 6
VERIFICATION_CODE_MAX_ATTEMPTS = 5
VERIFICATION_CODE_TTL_SECONDS = 5 * 60

# === 产品线 ===
PRODUCT_LINE_CAMERA = 'camera'
PRODUCT_LINE_DOORBELL = 'doorbell'
PRODUCT_LINE_CHOICES = [
    (PRODUCT_LINE_CAMERA, '摄像头'),
    (PRODUCT_LINE_DOORBELL, '门铃'),
]

# === 角色 ===
ROLE_ADMIN = 'admin'
ROLE_TESTER = 'tester'
ROLE_DEVELOPER = 'developer'
ROLE_VIEWER = 'viewer'