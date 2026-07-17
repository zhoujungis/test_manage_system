import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / '.env')

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY (C11 fix): 未设置 DJANGO_SECRET_KEY 时直接抛出 KeyError，
# 防止生产用默认公开字符串启动。
SECRET_KEY = os.environ['DJANGO_SECRET_KEY']


def _env_bool(name, default='False'):
    """H1 fix: 接受 true/1/yes/on 多种真值；不区分大小写；其他值当 False。"""
    raw = (os.environ.get(name, default) or '').strip().lower()
    return raw in ('1', 'true', 'yes', 'on')


DEBUG = _env_bool('DJANGO_DEBUG')

# C4 fix: 显式部署环境标记。production 模式无论 DEBUG 如何都强制安全基线，
# 防止 .env 残留 DEBUG=True + 占位 secret 启动裸奔。
_ENV = (os.environ.get('DJANGO_ENV', 'development') or 'development').strip().lower()
IS_PRODUCTION = _ENV in ('production', 'prod')

_PLACEHOLDER_SECRETS = (
    'your-secret-key-here',
    'replace-me-with-python-secrets-token-urlsafe-50',
    'replace-with-strong-db-password',
)

if IS_PRODUCTION:
    # 生产模式：DEBUG 必须 False；占位符 secret 必须替换；DB 密码强度最低门槛
    if DEBUG:
        from django.core.exceptions import ImproperlyConfigured
        raise ImproperlyConfigured(
            'DJANGO_ENV=production 时 DJANGO_DEBUG 必须为 False。'
            '禁止用 .env 里的 DEBUG=True 启动生产。'
        )
    if SECRET_KEY in _PLACEHOLDER_SECRETS or SECRET_KEY.startswith('django-insecure-'):
        from django.core.exceptions import ImproperlyConfigured
        raise ImproperlyConfigured(
            'DJANGO_SECRET_KEY 仍为占位符。生产模式要求设置真实随机值，'
            '可用 `python -c "import secrets; print(secrets.token_urlsafe(50))"` 生成。'
        )
    db_pw = os.environ.get('DB_PASSWORD', '')
    if not db_pw or db_pw in _PLACEHOLDER_SECRETS or len(db_pw) < 12:
        from django.core.exceptions import ImproperlyConfigured
        raise ImproperlyConfigured(
            'DB_PASSWORD 必须在生产环境配置为 ≥12 位的强密码，'
            '禁止占位符 / 空值 / 短密码。'
        )

# 二次保险：如果仍然是占位符或 Django 默认 insecure 串，且 DEBUG=False，
# 拒绝启动。开发环境仍可以用默认值跑测试。
if not DEBUG and (SECRET_KEY.startswith('django-insecure-') or SECRET_KEY in _PLACEHOLDER_SECRETS):
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured(
        'DJANGO_SECRET_KEY 必须在生产环境配置为强随机值，'
        '不允许 django-insecure-* / 占位符。'
    )

# H1 fix: strip + 去空；阻止裸的通配符除非 DEBUG=True 且显式开启
ALLOWED_HOSTS = [
    h.strip() for h in os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
    if h.strip()
]
if not DEBUG:
    ALLOWED_HOSTS = [h for h in ALLOWED_HOSTS if h and h != '*']
    if not ALLOWED_HOSTS:
        raise ImproperlyConfigured(
            'DJANGO_ALLOWED_HOSTS 在生产环境不能为空，也不能为通配符 *，'
            '请配置明确的主机名（例如 glazero.com,api.glazero.com）。'
        )

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'apps.accounts',
    'apps.projects',
    'apps.testcases',
    'apps.testplans',
    'apps.testruns',
    'apps.defects',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'testmanager'),
        'USER': os.environ.get('DB_USER', 'testmanager'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {'options': '-c timezone=Asia/Shanghai'},
        'CONN_MAX_AGE': 300,
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# M13 fix: argon2 优先，PBKDF2 兜底（生产没装 argon2-cffi 时自动回退）。
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]

LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = os.environ.get('DJANGO_STATIC_ROOT', BASE_DIR / 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.environ.get('DJANGO_MEDIA_ROOT', BASE_DIR / 'media')

# 执行附件：单文件最大 15MB
ASSIGNMENT_ATTACHMENT_MAX_BYTES = 15 * 1024 * 1024

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Cache
# M12 fix: FileBasedCache 在多 worker / 多 pod 下不可靠（每个进程的 cache 锁独立），
# DRF SimpleRateThrottle 限流就变成"建议性"。生产建议切到 Redis；
# 开发默认继续文件缓存，避免 LocMem 在每次 runserver 之间丢计数。
CACHE_BACKEND = os.environ.get('DJANGO_CACHE_BACKEND', 'file').lower()
if CACHE_BACKEND == 'redis':
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': os.environ.get('DJANGO_REDIS_URL', 'redis://127.0.0.1:6379/1'),
        },
    }
elif CACHE_BACKEND == 'locmem':
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'testmanager-singleton',
        },
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
            'LOCATION': os.environ.get('DJANGO_CACHE_DIR', BASE_DIR / 'cache'),
        },
    }

# CORS
CORS_ALLOW_ALL_ORIGINS = _env_bool('CORS_ALLOW_ALL')
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get('CORS_ALLOWED_ORIGINS', 'http://localhost:3001').split(',')
    if origin.strip()
]
CORS_PREFLIGHT_MAX_AGE = 86400

# H1 fix: 生产环境不允许 CORS_ALLOW_ALL 全开 + 不允许 credentials 全开
if not DEBUG:
    if CORS_ALLOW_ALL_ORIGINS:
        raise ImproperlyConfigured(
            'CORS_ALLOW_ALL=True 在生产环境是危险的，请显式列出 CORS_ALLOWED_ORIGINS。'
        )
CORS_ALLOW_CREDENTIALS = False  # JWT 走 Authorization header，不需要 cookies

# DRF
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    # M14 fix: 增加已认证用户的全局 throttle 兜底，避免登录用户无限刷任意端点。
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'apps.accounts.throttles.UserDefaultRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',          # 已登录用户全局兜底（端点可再缩紧）
        'send_code': '1/min',         # 发送注册验证码：每邮箱每分钟一次
        'send_reset_code': '1/min',   # 发送重置验证码：每邮箱每分钟一次
        'verify_code': '10/min',      # register / reset_password：每 (email, IP) 每分钟 10 次
        'login': '5/min',             # 已用 (ip, email) 双维度
        'refresh': '30/min',          # M4: refresh 端点限速
        'change_password': '10/min',  # 每 (ip, user) 10 次/分钟
    },
}

# M5 fix: 生产环境 SECURE_* / HSTS 块。反向代理场景需要同步 NUM_PROXIES 设置。
if not DEBUG:
    SECURE_SSL_REDIRECT = _env_bool('DJANGO_SECURE_SSL_REDIRECT', 'True')
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_HSTS_SECONDS = int(os.environ.get('DJANGO_SECURE_HSTS_SECONDS', '31536000'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = _env_bool('DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS', 'True')
    SECURE_HSTS_PRELOAD = _env_bool('DJANGO_SECURE_HSTS_PRELOAD', 'False')
    SECURE_REFERRER_POLICY = 'same-origin'
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_SECURE = True
    CSRF_COOKIE_HTTPONLY = True
else:
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

# SimpleJWT
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(hours=8),
    'AUTH_HEADER_TYPES': ('Bearer',),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    # M3 fix: 拒绝已禁用账号的现有 token 进入（即使 access token 还在 1h TTL 内）。
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
}

# Email
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.mxhichina.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '465'))
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'True') == 'True'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)
