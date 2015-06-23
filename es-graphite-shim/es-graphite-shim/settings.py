#!/usr/bin/env python
"""
Django settings for es-graphite-shim project
For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/
import os

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

try:
    from local_settings import *
except Exception as e:
    raise

import socket
hostname = socket.gethostname()
del socket

# SECURITY WARNING: don't run with debug turned on in production!
if hostname == HOSTNAME:
    DEBUG = False
    PRODUCTION = True
else:
    # All other environments are assumed to be non-production
    # environments. You can override this settings here to test out production
    # like behaviors.
    DEBUG = True
    PRODUCTION = False

TEMPLATE_DEBUG = True

# FIXME: If you want to test development mode with ./manage.py runserver as if
# it would be production, you need to add 'localhost' or '*' to the
# ALLOWED_HOSTS list, set DEBUG above to False, and you need to use the
# --insecure switch on runserver (e.g. $ python3 ./manage.py runserver
# --insecure).

if DEBUG:
    ALLOWED_HOSTS = ['']
elif PRODUCTION:
    # ALLOWED_HOSTS = [HOSTNAME,]
    ALLOWED_HOSTS = ['*']
else:
    ALLOWED_HOSTS = ['localhost',]

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'es-graphite-shim.urls'
WSGI_APPLICATION = 'es-graphite-shim.wsgi.application'
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {}
# DATABASES = {
#     'default': {
#         'NAME': os.path.join(BASE_DIR, 'storage/%s.sqlite3' % (DB_NAME)),
#         'ENGINE': 'django.db.backends.sqlite3',
#         'USER': 'apache',
#         'PASSWORD': DB_PASS,
#         'HOST': '',
#         'PORT': ''
#     }
# }


# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

# FIXME: either remove, or configure based on local settings

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_ROOT = '/mnt/static'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)

STATIC_URL = '/static/'

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    # 'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    # 'django.template.loaders.eggs.Loader',
)

TEMPLATE_DIRS = (os.path.join(BASE_DIR, 'templates/'),)

# Initiate ElasticSearch connection
from elasticsearch import Elasticsearch #, client
from urllib3 import Timeout
timeoutobj = Timeout(total=1200, connect=10, read=600)

from time import ctime
print("[%s] - Initiating ES connection" % (ctime()))
ES = Elasticsearch(host=ES_HOST, port=ES_PORT,
                   timeout=timeoutobj, max_retries=0)
print("[%s] - Established ES connection" % (ctime()))
# get the data to be displayed in drop down list in grafana
from lib.get_es_metadata import get_fieldnames as _get_fieldnames
from lib.get_es_metadata import get_open_indices_list as _get_open_indices_list
# query list of indices in state:open

import json as _js
_indices_path = os.path.join(BASE_DIR, 'lib/mappings/open_indices.json')

try:
    if not os.path.exists(_indices_path):
        _OPEN_INDICES = _get_open_indices_list(ES, INDEX_PREFIX, DOC_TYPE)
        # dict with index name as key and fieldnames as values
        f = open(_indices_path, 'wb')
        f.write(bytes(_js.dumps(_OPEN_INDICES), 'UTF-8'))
        f.close()
    else:
        f = open(_indices_path, 'rb')
        _OPEN_INDICES = _js.loads(f.read().decode('UTF-8'))
        f.close()
except Exception as e:
    quit("[%s] - ERROR: %s" % (ctime(), e))
    
print("[%s] - # of Open Indices: %d" % (ctime(), len(_OPEN_INDICES)))

_FIELDS = _get_fieldnames(ES, FIELD, _OPEN_INDICES, doc_type=DOC_TYPE)
# remove methods which won't be used any longer
del _get_fieldnames
del _get_open_indices_list


# build an aggregate dict of mappings to be referred 
# for field validation each time a query is issued
from lib.get_es_metadata import get_mappings as _get_mappings
_MAPPINGS = _get_mappings(ES, DOC_TYPE, _fresh=FRESH)
del _get_mappings
del _js
