"""
Django settings for netwObserver project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""



# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
from datetime import timedelta

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

import djcelery
djcelery.setup_loader()

TEMPLATE_DIRS = [os.path.join(BASE_DIR, 'templates')]

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '_l35(s7&2goejquw5@wisjiu*t*w28&7-!kee6ajw2s%^addlq'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'djcelery',
    'kombu.transport.django',
    'gatherer',
    'analyse',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'netwObserver.urls'

WSGI_APPLICATION = 'netwObserver.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', 
        'NAME': 'memoire',
        'USER': 'memoire',
        'PASSWORD': 'memoireTest',
        'HOST': 'localhost',   # Or an IP Address that your DB is hosted on
        'PORT': '3306',
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'CET'

USE_I18N = True

USE_L10N = True

USE_TZ = True



## User Settings
SNMPAPLAP = timedelta(minutes=20)
SNMPRAPLAP = timedelta(hours=2)
SNMPMSLAP = timedelta(minutes=30)

DATAVALIDITY = timedelta(days=180)



## Celery
CELERY_RESULT_BACKEND='djcelery.backends.database:DatabaseBackend'
BROKER_URL = 'django://'

CELERYBEAT_SCHEDULE = {
    'snmp-ap-daemon': {
        'task': 'gatherer.tasks.snmpAPDaemon',
        'schedule': SNMPAPLAP,
    },
    'snmp-ms-daemon': {
        'task': 'gatherer.tasks.snmpMSDaemon',
        'schedule': SNMPMSLAP,
    },
    'snmp-rap-daemon': {
        'task': 'gatherer.tasks.snmpRAPDaemon',
        'schedule': SNMPRAPLAP,
    },
    'probeResponder': {
        'task': 'gatherer.tasks.startResponder',
        'schedule': timedelta(minutes=10),
    },
}


## Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/
STATIC_URL = '/static/'
STATIC_ROOT = "/srv/static/"
MEDIA_URL = '/media/'
MEDIA_ROOT = '/srv/media/'
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "static"),
 )







