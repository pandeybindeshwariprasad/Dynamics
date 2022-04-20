"""
Django settings for Deloitte_Dynamics project.

Generated by 'django-admin startproject' using Django 1.11.7.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import os
import sys
import sql_server


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE_ROOT = os.path.dirname(os.path.realpath(__file__))
sys.path.append(BASE_DIR)


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '#f_xl4(b^*n)^^_-3lp@rax&@fp$m5q+7f&$kc8@!v$edvwc63'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False


ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'main.apps.MainConfig',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.contrib.admindocs.middleware.XViewMiddleware'
]

ROOT_URLCONF = 'Deloitte_Dynamics.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(SITE_ROOT, 'templates')
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages'
            ],
        },
    },
]

WSGI_APPLICATION = 'Deloitte_Dynamics.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    # For Production
    'default': {
        'ENGINE': 'sql_server.pyodbc',
        'NAME': r"UK429_Dynamics",
        'HOST': 'UKVIRCI00210',
        'ATOMIC_REQUESTS': True,
    }

 # # For testing environment
 #    'default': {
 #        'ENGINE': 'sql_server.pyodbc',
 #        'NAME': r"UK429_Dynamics_Test",
 #        'HOST': 'UKVIRCI00210',
 #        'ATOMIC_REQUESTS': True,
 #    }
}


# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

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

# this is the homepage
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login'


LOG_PATH = os.path.join(BASE_DIR, 'Deloitte_Dynamics/dynamics_log.txt')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': LOG_PATH,
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

STATIC_DIR = os.path.join(SITE_ROOT, 'static')

# Dynamics specific static directories

# this is the folder that the pdf files are in
PATH_TO_PDF_FILES = r"\\uk.deloitte.com\ukvfmsecroot\P\Project Dynamics\Engagements\2_Project Data\03 Dev folder\02 PRE CLEANSED"

# this is the folder that the excel files are in
PATH_TO_KEYWORD_FILES = r"\\uk.deloitte.com\ukvfmsecroot\P\Project Dynamics\Engagements\2_Project Data\03 Dev folder\05 RESOURCES\Keywords"

# this is the file containing the searches
PATH_TO_SEARCH_LISTS = r"\\uk.deloitte.com\ukvfmsecroot\P\Project Dynamics\Engagements\2_Project Data\03 Dev folder\05 RESOURCES\Searches"

# this is the file containing
PATH_TO_SAP_FILES = r"\\uk.deloitte.com\ukvfmsecroot\\P\Project Dynamics\Engagements\2_Project Data\03 Dev folder\05 RESOURCES\SAP WBS list"

Y_DRIVE_LOGS = r"\\uk.deloitte.com\ukvfmsecroot\P\Project Dynamics\Engagements\2_Project Data\03 Dev folder\03 LOGS"

STATICFILES_DIRS = (
    STATIC_DIR,
    PATH_TO_PDF_FILES
)

PRINT_STATEMENT = False