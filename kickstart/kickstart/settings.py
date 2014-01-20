import os
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
SECRET_KEY = 'z1kt)jnwx#*x6^&f@g6n$=(e3tmaq@)la6e@#wze5e+a9ii)&-'
DEBUG = True
TEMPLATE_DEBUG = True
ALLOWED_HOSTS = []

try:
    from settings_local import DB_SETTINGS
    DATABASES = {
        'default': {
            'ENGINE': "django.db.backends.mysql",
            'NAME': DB_SETTINGS['database'],
            'USER': DB_SETTINGS['user'],
            'PASSWORD': DB_SETTINGS['password'],
        }
    }
except ImportError:
    from django.db import DatabaseError
    raise DatabaseError(u"Set database settings")

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'registration',
    'loginza',
    'south',
    'parsley',
    'django_select2',
    'kickstart',
    "easy_thumbnails",
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.request",
    "django.core.context_processors.tz",
    "django.contrib.messages.context_processors.messages",
)

TEMPLATE_DIRS = (
    os.path.join(PROJECT_ROOT, 'kickstart', 'templates'),
)

SITE_ID = 1
ROOT_URLCONF = 'kickstart.urls'
WSGI_APPLICATION = 'kickstart.wsgi.application'
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True
STATIC_URL = '/static/'
MEDIA_URL = '/media/'
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static')
MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'media')

THUMBNAIL_ALIASES = {
    '': {
        'avatar': {'size': (64, 64), 'crop': True, 'upscale': True},
    },
}

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'loginza.authentication.LoginzaBackend',
)

LOGINZA_AMNESIA_PATHS = ('/accounts/complete_registration/',)

ACCOUNT_ACTIVATION_DAYS = 3
REGISTRATION_OPEN = True
LOGIN_URL = '/accounts/login'
LOGIN_REDIRECT_URL = '/'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend' # to users
EMAIL_HOST = 'localhost'
DEFAULT_FROM_EMAIL = 'webmaster@localhost'

try:
    from settings_local import DEBUG_TOOLBAR
except:
    DEBUG_TOOLBAR = False

if DEBUG and DEBUG_TOOLBAR:
    INSTALLED_APPS = INSTALLED_APPS + ('debug_toolbar', )
    INTERNAL_IPS = ('127.0.0.1', )

    try:
        from settings_local import DEBUG_TOOLBAR_PANELS 
    except:
        DEBUG_TOOLBAR_PANELS_LOCAL = (
            'debug_toolbar.panels.version.VersionDebugPanel',
            'debug_toolbar.panels.timer.TimerDebugPanel',
            'debug_toolbar.panels.settings_vars.SettingsVarsDebugPanel',
            'debug_toolbar.panels.headers.HeaderDebugPanel',
            'debug_toolbar.panels.request_vars.RequestVarsDebugPanel',
            'debug_toolbar.panels.template.TemplateDebugPanel',
            'debug_toolbar.panels.sql.SQLDebugPanel',
            'debug_toolbar.panels.signals.SignalDebugPanel',
            'debug_toolbar.panels.logger.LoggingPanel',
        )

    try:
        from settings_local import DEBUG_TOOLBAR_CONFIG
    except:
        pass
