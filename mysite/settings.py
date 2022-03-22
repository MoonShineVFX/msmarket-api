"""
Django settings for mysite project.

Generated by 'django-admin startproject' using Django 3.2.7.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""
import sys
import os
import pymysql
from datetime import timedelta
pymysql.install_as_MySQLdb()


# Set the project base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', False)
PRODUCTION = os.environ.get('PRODUCTION', False)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'secret_key')


ALLOWED_HOSTS = os.environ.get('API_HOST', '127.0.0.1').split(' ')

# Application definition

INSTALLED_APPS = [
    "corsheaders",
    'rest_framework',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',  # required for allauth
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'apps.user',
    'apps.category',
    'apps.product',
    'apps.order',
    'apps.index',

    # allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    #'dj_rest_auth',
    #'dj_rest_auth.registration',

    'modeltranslation',
]

SITE_ID = 1

AUTH_USER_MODEL = 'user.User'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    "corsheaders.middleware.CorsMiddleware",
    'django.middleware.common.ComonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware'
]

AUTHENTICATION_BACKENDS = [

    # Needed to login by username in Django admin, regardless of `allauth`
    'django.contrib.auth.backends.ModelBackend',

    # `allauth` specific authentication methods, such as login by e-mail
    'allauth.account.auth_backends.AuthenticationBackend',

]

ROOT_URLCONF = 'mysite.urls'

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
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'mysite.wsgi.application'


# REST_FRAMEWORK
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'apps.renderers.ApiRenderer',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_THROTTLE_RATES': {
        'anon': '10/minute',
    }
}

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases


SQL_HOST = os.environ.get('SQL_HOST')

DATABASES = {
    'dev': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'msmarket',
        'USER': 'root',
        'PASSWORD': os.environ.get('SQL_PASSWORD', None),
        'HOST': 'localhost',
        'PORT': os.environ.get('SQL_PORT', '3306'),
    },
    'test': {
        'ENGINE': 'mysql.connector.django',
        'NAME': 'msmarket',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '3306',
        'TEST': {
            'CHARSET': "utf8",
            'COLLATION': "utf8_general_ci",
        }
    },
    # Equivalent URL:
    # mysql+pymysql://<db_user>:<db_pass>@/<db_name>?unix_socket=<socket_path>/<cloud_sql_instance_name>
    'production': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'msmarket'),
        'USER':  os.environ.get('DB_USER', 'root'),
        'PASSWORD': os.environ.get('DB_PASS', ''),
        # 在上文提到的 Connection Name
        # 的前面加入 /cloudsql/

        'HOST': f'{SQL_HOST}',
    },

}


if PRODUCTION:
    DATABASES['default'] = DATABASES['production']
elif 'test' in sys.argv:
    DATABASES['default'] = DATABASES['test']
else:
    DATABASES['default'] = DATABASES['dev']


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "static"),
    '/static/',
)

MEDIA_ROOT = '/docker_api/media/'
if 'test' in sys.argv:
    MEDIA_ROOT = os.path.join(BASE_DIR, 'test')

MEDIA_URL = '/media/'


# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Google Cloud Storage
DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
STATICFILES_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
GS_BUCKET_NAME = 'ms-image-storage'
GS_INTERNAL_BUCKET_NAME = '3dmodel-storage'
GS_FILE_OVERWRITE = False
MEDIA_SERVICE_ACCOUNT_SECRET = os.environ.get('MEDIA_SERVICE_ACCOUNT_SECRET', None)

if 'test' in sys.argv:
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# url path for image on gcp
IMAGE_ROOT = 'https://market-dev.moonshine.tw'

# django-cors-headers
CORS_ORIGIN_ALLOW_ALL = True


# newebpay 金流
NEWEBPAY_ID = os.environ.get('NEWEBPAY_ID', 'ID')
NEWEBPAY_HASHKEY = os.environ.get('NEWEBPAY_HASHKEY', "12345678912345678912345678912345")
NEWEBPAY_HASHIV = os.environ.get('NEWEBPAY_HASHIV', "1234567891234567")

# ezpay
EZPAY_ID = os.environ.get('EZPAY_ID', 'ID')
EZPAY_HASHKEY = os.environ.get('EZPAY_HASHKEY', "12345678912345678912345678912345")
EZPAY_HASHIV = os.environ.get('EZPAY_HASHIV', "1234567891234567")

# JWT Token
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': False,
}

# allauth and dj-rest-auth
REST_USE_JWT = True
REST_AUTH_TOKEN_MODEL = None
JWT_AUTH_COOKIE = "token"
ACCOUNT_USER_MODEL_USERNAME_FIELD = "email"


# SMTP
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')

EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_HOST_USER = 'apikey' # this is exactly the value 'apikey'
EMAIL_HOST_PASSWORD = SENDGRID_API_KEY
EMAIL_PORT = 587
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL')


API_HOST = os.environ.get('API_HOST', 'localhost')
PASSWORD_RESET_TIMEOUT = 1800 # 30 min in seconds


# django-modeltranslation
gettext = lambda s: s
LANGUAGES = (
    ('zh', gettext('Chinese')), # The first language is treated as the default language.
    ('en', gettext('English')),
)

# Query logger
LOGGING = {
    'version': 1,
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
        }
    },
    'loggers': {
        'django.db.backends': {
            'level': 'DEBUG',
            'handlers': ['console'],
        }
    }
}
