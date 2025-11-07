from pathlib import Path
import environ, os

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env(DEBUG=(bool, False))
if os.path.exists(BASE_DIR / ".env"):
    environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY", default="change-me")
DEBUG = env("DEBUG", default=True)
ALLOWED_HOSTS = env("ALLOWED_HOSTS", default="*").split(",")

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'shop',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'auntie_jummys.urls'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'templates'],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.debug',
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
        'shop.context_processors.cart',
    ]},
}]

WSGI_APPLICATION = 'auntie_jummys.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/Indiana/Indianapolis'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Square
SQUARE_PUBLIC_KEY = env("SQUARE_PUBLIC_KEY", default="")
SQUARE_ACCESS_TOKEN = env("SQUARE_ACCESS_TOKEN", default="")
SQUARE_ENV = env("SQUARE_ENV", default="sandbox")
SQUARE_LOCATION_ID = env("SQUARE_LOCATION_ID", default="")
SQUARE_WEBHOOK_SIGNATURE_KEY = env("SQUARE_WEBHOOK_SIGNATURE_KEY", default="")

# Email (SMTP)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = int(env('EMAIL_PORT', default='587'))
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_USE_SSL = env.bool('EMAIL_USE_SSL', default=False)
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default=EMAIL_HOST_USER or 'no-reply@auntiejummys.com')
ORDER_NOTIFY_EMAIL = env('ORDER_NOTIFY_EMAIL', default='orders@auntiejummys.com')


# Store info
STORE_ADDRESS = env("STORE_ADDRESS", default="Auntie Jummy’s Candy & Snacks, Brownsburg, IN")
STORE_ZIP = env("STORE_ZIP", default="46112")
STORE_PHONE = env("STORE_PHONE", default="+1-317-000-0000")

# Tiered delivery fee config: e.g. "5:3,10:5,999:8" (miles:fee)
DELIVERY_FEE_TIERS = env("DELIVERY_FEE_TIERS", default="5:3,10:5,999:8")


# Free delivery threshold (cart total after discount); set empty or 0 to disable
FREE_DELIVERY_THRESHOLD = env.decimal('FREE_DELIVERY_THRESHOLD', default=0)
