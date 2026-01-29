from __future__ import annotations

from pathlib import Path
import os

# Load .env file if exists (for local development)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent

# Environment detection
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = ENVIRONMENT == "development"

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-secret-key-change-me")

ALLOWED_HOSTS: list[str] = [
    "localhost",
    "127.0.0.1",
    ".railway.app",      # Railway domains
    ".cdcstream.io",     # Custom domain
    "*" if DEBUG else "", # Allow all in development
]
ALLOWED_HOSTS = [h for h in ALLOWED_HOSTS if h]  # Remove empty strings

INSTALLED_APPS = [
	"django.contrib.admin",
	"django.contrib.auth",
	"django.contrib.contenttypes",
	"django.contrib.sessions",
	"django.contrib.messages",
	"django.contrib.staticfiles",
	"corsheaders",
	"rest_framework",
	"api",
]

MIDDLEWARE = [
	"corsheaders.middleware.CorsMiddleware",
	"django.middleware.security.SecurityMiddleware",
	"whitenoise.middleware.WhiteNoiseMiddleware",  # Serve static files in production
	"cdcserver.middleware.NoCacheMiddleware",  # Prevent browser caching of HTML/API
	"django.contrib.sessions.middleware.SessionMiddleware",
	"django.middleware.common.CommonMiddleware",
	# "django.middleware.csrf.CsrfViewMiddleware",  # Disabled for API-only server
	"django.contrib.auth.middleware.AuthenticationMiddleware",
	"django.contrib.messages.middleware.MessageMiddleware",
	"django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "cdcserver.urls"

TEMPLATES = [
	{
		"BACKEND": "django.template.backends.django.DjangoTemplates",
		"DIRS": [BASE_DIR / "templates"],
		"APP_DIRS": True,
		"OPTIONS": {
			"context_processors": [
				"django.template.context_processors.debug",
				"django.template.context_processors.request",
				"django.contrib.auth.context_processors.auth",
				"django.contrib.messages.context_processors.messages",
			],
		},
	},
]

WSGI_APPLICATION = "cdcserver.wsgi.application"

# Database configuration
# Priority: DATABASE_URL env var > SQLite (local development)
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # PostgreSQL (Railway, Heroku, etc.)
    import dj_database_url
    DATABASES = {
        "default": dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    # SQLite for local development
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR.parent / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "tr-tr"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR.parent / "static"

# Frontend static files location
# Priority: 1) cdcserver/staticfiles (PyPI package), 2) server/staticfiles (local), 3) web/out (dev)
_pkg_staticfiles = Path(__file__).parent / "staticfiles"
_local_staticfiles = BASE_DIR / "staticfiles"
_web_out_dir = BASE_DIR.parent / "web" / "out"

if _pkg_staticfiles.exists():
    FRONTEND_OUT_DIR = _pkg_staticfiles
elif _local_staticfiles.exists():
    FRONTEND_OUT_DIR = _local_staticfiles
else:
    FRONTEND_OUT_DIR = _web_out_dir

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
	"DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
	"PAGE_SIZE": 20,
	# Allow both with and without trailing slash in DRF routers
	"DEFAULT_ROUTER_TRAILING_SLASH": "/?",
	# Disable authentication for API (no login required)
	"DEFAULT_AUTHENTICATION_CLASSES": [],
	"DEFAULT_PERMISSION_CLASSES": [
		"rest_framework.permissions.AllowAny",
	],
}

# CORS Settings
CORS_ALLOW_ALL_ORIGINS = DEBUG  # Only allow all in development
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = [
	"DELETE",
	"GET",
	"OPTIONS",
	"PATCH",
	"POST",
	"PUT",
]
CORS_ALLOW_HEADERS = [
	"accept",
	"accept-encoding",
	"authorization",
	"content-type",
	"dnt",
	"origin",
	"user-agent",
	"x-csrftoken",
	"x-requested-with",
]

# Production CORS origins
if not DEBUG:
    CORS_ALLOWED_ORIGINS = [
        "https://cdcstream.io",
        "https://www.cdcstream.io",
        "https://app.cdcstream.io",
    ]

# Security settings for production
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
