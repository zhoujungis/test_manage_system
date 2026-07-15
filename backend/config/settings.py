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

# 二次保险：如果仍然是占位符或 Django 默认 insecure 串，且 DEBUG=False，
# 拒绝启动。开发环境仍可以用默认值跑测试。
if not DEBUG and (SECRET_KEY.startswith('django-insecure-') or SECRET_KEY == 'your-secret-key-here'):
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured(
        'DJANGO_SECRET_KEY 必须在生产环境配置为强随机值，'
        '不允许 django-insecure-* / your-secret-key-here 等占位符。'
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
    if 'CORS_ALLOW_CREDENTIALS' in os.environ:
        # 仅当运营方明确需要时开 credentials；这里干脆 production 一律不开
        pass
CORS_ALLOW_CREDENTIALS = False  # JWT 走 Authorization header，不需要 cookies

# DRF
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'send_code': '1/min',          # 发送注册验证码：每邮箱每分钟一次
        'send_reset_code': '1/min',    # 发送重置验证码：每邮箱每分钟一次（与注册分开，防止相互挤兑）
        'verify_code': '10/min',       # register / reset_password：每 (email, IP) 每分钟 10 次
        'login': '5/min',
        'change_password': '10/min',
    },
}

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
