"""
Django settings for Doctor project.
"""

from pathlib import Path
import os

# ================= BASE DIR =================
BASE_DIR = Path(__file__).resolve().parent.parent

# ================= SECURITY =================
SECRET_KEY = 'django-insecure-cu#-nm1*oeeev$ypmk&j#g*sunpl#&f^ph@#!68_6$7qy@rs)h'
DEBUG = True

ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
]

# ================= CUSTOM USER =================
AUTH_USER_MODEL = 'accounts.User'

# ================= INSTALLED APPS =================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',

    'accounts',
    'appointments',
    'Doctor',
]

# ================= MIDDLEWARE =================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',

    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',  # 🔥 MUST

    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ================= URL CONFIG =================
ROOT_URLCONF = 'Doctor.urls'

# ================= TEMPLATES =================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'Doctor.wsgi.application'

# ================= DATABASE (SQLite for Auth/Admin) =================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ================= PASSWORD VALIDATION =================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ================= INTERNATIONALIZATION =================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ================= STATIC FILES =================
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'Doctor/static')]

# ================= MEDIA FILES =================
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ================= DEFAULT PK =================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ======================================================
# 🔐 CSRF & SESSION FIX (THIS FIXES 403 ERROR)
# ======================================================

CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:8000',
    'http://localhost:8000',
]

CSRF_COOKIE_SECURE = False
CSRF_COOKIE_HTTPONLY = False
CSRF_USE_SESSIONS = False

SESSION_COOKIE_SECURE = False
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

# ======================================================
# 📧 EMAIL CONFIG (REAL OTP EMAIL)
# ======================================================

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST_USER = 'medisyncind@gmail.com'
EMAIL_HOST_PASSWORD = 'lyckxlehhysmzhab'  # Gmail App Password

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER


LOGIN_URL = '/doctor-login/'
LOGIN_REDIRECT_URL = '/doctor/dashboard/'
LOGOUT_REDIRECT_URL = '/'

