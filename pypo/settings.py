import os
import sys
from os import path

PROJECT_ROOT = path.abspath(path.join(path.dirname(__file__), '..'))

# Django settings for pypo project.

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'pypo',                      # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': 'postgres',
        'PASSWORD': '',
        'HOST': '',                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '',                      # Set to empty string for default.
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake'
    }
}

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'Europe/Berlin'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = path.join(PROJECT_ROOT, '../static')

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

BOWER = path.join(PROJECT_ROOT, 'bower_components')


# Additional locations of static files
STATICFILES_DIRS = (
    BOWER,
)

PIPELINE_JS = {
    'components': {
        'source_filenames': (
            'jquery/dist/jquery.js',
            'jquery-ui/ui/jquery-ui.js',
            'bootstrap/dist/js/bootstrap.js',
            'PopConfirm/jquery.popconfirm.js',
            'select2/select2.js',
            'x-editable/dist/bootstrap3-editable/js/bootstrap-editable.js',
            'js/readme.js',
            # you can choose to be specific to reduce your payload
        ),
        'output_filename': 'js/components.js',
    },
    'testing': {
        'source_filenames': (
            'qunit/qunit/qunit.js',
            'sinon/lib/sinon.js',
        ),
        'output_filename': 'js/testing.js',
    },
}

# Disable yuglify until it works with jquery again
# https://github.com/yui/yuglify/issues/19
PIPELINE_JS_COMPRESSOR = None

PIPELINE_CSS = {
    'all': {
        'source_filenames': (
            'select2/select2.css',
            'bootstrap-tokenfield/dist/css/bootstrap-tokenfield.css',
            'jquery-ui/themes/base/jquery-ui.css',
            'fontawesome/css/font-awesome.css',
            'select2-bootstrap-css/select2-bootstrap.css',
            'css/readme.css',
        ),
        'output_filename': 'css/all.css',
    },
    'testing': {
        'source_filenames': (
            'qunit/qunit/qunit.css',
        ),
        'output_filename': 'js/testing.js',
        },
}

STATICFILES_STORAGE = 'pipeline.storage.PipelineStorage'

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'pipeline.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

STATICFILES_STORAGE = 'pipeline.storage.PipelineCachedStorage'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '42'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    ('django.template.loaders.cached.Loader', (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )),
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
    "django.contrib.messages.context_processors.messages",
    "settings_context_processor.context_processors.settings",
    "django.core.context_processors.request",
)


MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

SESSION_COOKIE_NAME = 'sessionid'
AUTHENTICATION_BACKENDS = ('django.contrib.auth.backends.ModelBackend',)

ROOT_URLCONF = 'pypo.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'pypo.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

LOGIN_REDIRECT_URL = '/'

SOUTH_MIGRATION_MODULES = {
    'taggit': 'taggit.south_migrations',
}


INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'pipeline',
    'south',
    # Uncomment the next line to enable admin documentation:
    'django.contrib.admindocs',
    'readme',
    'crispy_forms',
    'haystack',
    'taggit',
    'rest_framework',
    'django_admin_bootstrapped.bootstrap3',
    'django_admin_bootstrapped',
    'django.contrib.admin',
    'settings_context_processor',
    'sitegate',
    'functional_tests',
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'readme.request': {
            'handlers': ['mail_admins'],
            'level': 'INFO',
            'propagate': True,
        },
    }
}

CRISPY_FAIL_SILENTLY = not DEBUG
CRISPY_TEMPLATE_PACK = 'bootstrap3'

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
        'PATH': os.path.join(os.path.dirname(__file__), 'whoosh_index'),
    },
}

HAYSTACK_SIGNAL_PROCESSOR = 'readme.signals.ItemOnlySignalProcessor'

REST_FRAMEWORK = {
    # Use hyperlinked styles by default.
    # Only used if the `serializer_class` attribute is not set on a view.
    'DEFAULT_MODEL_SERIALIZER_CLASS':
        'rest_framework.serializers.HyperlinkedModelSerializer',

    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    )
}

TEMPLATE_VISIBLE_SETTINGS = ('PYPO_DEFAULT_THEME',)

# 10MB
PYPO_MAX_CONTENT_LENGTH = int(1.049e+7)

PYPO_ITEMS_ON_PAGE = 51

PYPO_DEFAULT_THEME = 'slate'

PYPO_THEMES = (
    ('amelia', 'Amelia'),
    ('cerulean', 'Cerulean'),
    ('cosmo', 'Cosmo'),
    ('cyborg', 'Cyborg'),
    ('flatly', 'Flatly'),
    ('journal', 'Journal'),
    ('readable', 'Readable'),
    ('simplex', 'Simplex'),
    ('slate', 'Slate'),
    ('spacelab', 'SpaceLab'),
    ('united', 'United'),
    ('superhero', 'Superhero'),
    ('lumen', 'Lumen'),
)

try:
    from .settings_local import *
except ImportError:
    pass
