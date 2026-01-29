SECRET_KEY = 'django-insecure'
ALLOWED_HOSTS = ['*']
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
            ]
        },
    }
]
MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'saas_base.middleware.HeaderTenantIdMiddleware',
    'saas_base.middleware.TenantMiddleware',
]
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        },
    },
]
INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'drf_spectacular',
    'saas_base',
    'saas_base.drf',
    'saas_domain',
    'tests',
]
REST_FRAMEWORK = {
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    'DEFAULT_SCHEMA_CLASS': 'saas_base.drf.spectacular.AutoSchema',
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
    'DEFAULT_PARSER_CLASSES': ['rest_framework.parsers.JSONParser'],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
}
SAAS_DOMAIN = {
    'PROVIDERS': {
        'null': {
            'backend': 'saas_domain.providers.NullProvider',
            'options': {},
        },
        'cloudflare': {
            'backend': 'saas_domain.providers.CloudflareProvider',
            'options': {'zone_id': '123', 'auth_key': 'auth-key', 'ignore_hostnames': ['localtest.me']},
        },
    },
}
USE_TZ = True
TIME_ZONE = 'UTC'
ROOT_URLCONF = 'tests.urls'
