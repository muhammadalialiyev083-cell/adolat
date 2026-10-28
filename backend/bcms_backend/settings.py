import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR.parent / ".env")
load_dotenv(BASE_DIR / ".env")

# ==============================
# SECURITY
# ==============================

SECRET_KEY = os.environ.get("SECRET_KEY", "")

DEBUG = os.environ.get("DEBUG", "False").lower() == "true"
if not SECRET_KEY:
    if not DEBUG:
        from django.core.exceptions import ImproperlyConfigured

        raise ImproperlyConfigured("Production requires SECRET_KEY from the environment.")
    # Development key is ephemeral, never a shared default credential.
    from secrets import token_urlsafe

    SECRET_KEY = token_urlsafe(48)
SECURE_SSL_REDIRECT = not DEBUG
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 28800
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]
if DEBUG:
    CSRF_TRUSTED_ORIGINS += ["http://localhost:5173", "http://127.0.0.1:5173"]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
# Browsers reject SameSite=None cookies without Secure on local HTTP.
SESSION_COOKIE_SAMESITE = "Lax" if DEBUG else os.environ.get("COOKIE_SAMESITE", "Lax")
CSRF_COOKIE_SAMESITE = SESSION_COOKIE_SAMESITE

# ==============================
# APPLICATIONS
# ==============================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    "apps.core",
    "apps.organizations",
    "apps.authentication",
    "apps.processes",
    "apps.bia",
    "apps.risks",
    "apps.engine",
    "apps.plans",
    "apps.simulation",
    "apps.reports",
    "apps.imports",
    "apps.management",
    "apps.incidents",
    "apps.monitoring",
]

# ==============================
# MIDDLEWARE
# ==============================

MIDDLEWARE = [
    "apps.core.middleware.PrivateAPICacheMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.authentication.oidc.EnterpriseSessionMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "bcms_backend.urls"

# ==============================
# TEMPLATES
# ==============================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "bcms_backend.wsgi.application"

# ==============================
# DATABASE
# ==============================


DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        ssl_require=os.environ.get("DATABASE_SSL_REQUIRE", "true").lower() == "true"
        and os.environ.get("DATABASE_URL", "").startswith(("postgres://", "postgresql://")),
    )
}
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True


AUTH_USER_MODEL = "authentication.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ==============================
# LOCALIZATION
# ==============================

LANGUAGE_CODE = "uz"
TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_TZ = True

# ==============================
# STATIC FILES
# ==============================

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ==============================
# DJANGO REST FRAMEWORK
# ==============================

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.TenantPagination",
    "PAGE_SIZE": 50,
    "EXCEPTION_HANDLER": "apps.core.exceptions.api_exception_handler",
}

# ==============================
# CORS
# ==============================

CORS_ALLOW_ALL_ORIGINS = False

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]

CORS_ALLOW_CREDENTIALS = True

if DEBUG:
    CORS_ALLOWED_ORIGINS += ["http://localhost:5173", "http://127.0.0.1:5173"]
TEMPLATES[0]["DIRS"] = [BASE_DIR.parent / "frontend" / "dist"]
STATICFILES_DIRS = (
    [("assets", BASE_DIR.parent / "frontend" / "dist" / "assets")]
    if (BASE_DIR.parent / "frontend" / "dist" / "assets").exists()
    else []
)
MEDIA_ROOT = Path(os.environ.get("MEDIA_ROOT", str(BASE_DIR / "media")))
MEDIA_URL = "/media/"
DATA_UPLOAD_MAX_MEMORY_SIZE = 3 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024
DATA_UPLOAD_MAX_NUMBER_FILES = 1

WHITENOISE_ROOT = BASE_DIR.parent / "frontend" / "dist"

if not DEBUG and not os.environ.get("DATABASE_URL", "").startswith(
    ("postgres://", "postgresql://")
):
    from django.core.exceptions import ImproperlyConfigured

    raise ImproperlyConfigured("Production requires a PostgreSQL DATABASE_URL.")

if not DEBUG:
    from django.core.exceptions import ImproperlyConfigured
    from urllib.parse import urlsplit

    if (
        len(SECRET_KEY) < 50
        or not os.environ.get("ALLOWED_HOSTS")
        or not ALLOWED_HOSTS
        or any("*" in host or "://" in host or host.startswith(".") for host in ALLOWED_HOSTS)
    ):
        raise ImproperlyConfigured("Production requires a strong key and explicit exact hosts.")
    for origin in CSRF_TRUSTED_ORIGINS + CORS_ALLOWED_ORIGINS:
        parsed = urlsplit(origin)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or "*" in origin
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
            or parsed.path not in {"", "/"}
        ):
            raise ImproperlyConfigured("Production origins must be exact HTTPS origins.")
    if SESSION_COOKIE_SAMESITE not in {"Lax", "Strict", "None"}:
        raise ImproperlyConfigured("Invalid COOKIE_SAMESITE.")

if not DEBUG:
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"safe_json": {"()": "apps.core.logging.SecurityJSONFormatter"}},
        "handlers": {"safe_console": {"class": "logging.StreamHandler", "formatter": "safe_json"}},
        "root": {"handlers": ["safe_console"], "level": "INFO"},
        "loggers": {
            "django": {"handlers": ["safe_console"], "level": "INFO", "propagate": False},
            "requests": {"handlers": ["safe_console"], "level": "WARNING", "propagate": False},
            "authlib": {"handlers": ["safe_console"], "level": "WARNING", "propagate": False},
        },
    }
