"""
Myra EU Captcha - Django Settings

Configuration can be done in two ways:

1. Via Django Admin (recommended):
   - Add 'myra_eucaptcha_django' to INSTALLED_APPS
   - Run migrations
   - Configure via Admin > Captcha Configuration

2. Via Django settings.py (fallback):
    EUCAPTCHA_SITEKEY = "your-site-key"
    EUCAPTCHA_SECRET = "your-secret-key"

Optional settings.py options:
    EUCAPTCHA_VERIFY_URL = "https://api.eu-captcha.eu/v1/verify/"
    EUCAPTCHA_WIDGET_URL = "https://cdn.eu-captcha.eu/verify.js"
    EUCAPTCHA_CONNECT_TIMEOUT = 3
    EUCAPTCHA_READ_TIMEOUT = 10
    EUCAPTCHA_WRITE_TIMEOUT = 10
    EUCAPTCHA_POOL_TIMEOUT = 3
    EUCAPTCHA_DEFAULT_RESULT_ON_ERROR = True
    EUCAPTCHA_SUPPRESS_EXCEPTIONS = True
"""
from django.conf import settings


def get_setting(name: str, default=None):
    """Get an EU Captcha setting from Django settings."""
    return getattr(settings, name, default)


def get_db_config(config_name: str = None):
    """Get configuration from database if available."""
    try:
        from .models import CaptchaConfig
        return CaptchaConfig.objects.get_config(config_name)
    except Exception:
        return None


def get_sitekey(config_name: str = None) -> str:
    """Get the site key (from DB or settings)."""
    config = get_db_config(config_name)
    if config and config.sitekey:
        return config.sitekey

    if not config_name:
        sitekey = get_setting("EUCAPTCHA_SITEKEY")
        if sitekey:
            return sitekey

    raise ValueError(
        f"Captcha configuration '{config_name or 'default'}' not found. "
        "Configure via Django Admin or add EUCAPTCHA_SITEKEY to settings."
    )


def get_secret(config_name: str = None) -> str:
    """Get the secret key (from DB or settings)."""
    config = get_db_config(config_name)
    if config and config.secret:
        return config.secret

    if not config_name:
        secret = get_setting("EUCAPTCHA_SECRET")
        if secret:
            return secret

    raise ValueError(
        f"Captcha configuration '{config_name or 'default'}' not found. "
        "Configure via Django Admin or add EUCAPTCHA_SECRET to settings."
    )


def get_verify_url(config_name: str = None) -> str:
    """Get the verification URL (from DB or settings)."""
    config = get_db_config(config_name)
    if config and config.verify_url:
        return config.verify_url
    return get_setting("EUCAPTCHA_VERIFY_URL", "https://api.eu-captcha.eu/v1/verify/")


def get_widget_url(config_name: str = None) -> str:
    """Get the widget JavaScript URL (from DB or settings)."""
    config = get_db_config(config_name)
    if config and config.widget_url:
        return config.widget_url
    return get_setting("EUCAPTCHA_WIDGET_URL", "https://cdn.eu-captcha.eu/verify.js")


def get_connect_timeout(config_name: str = None) -> int:
    """Get the connection timeout (from DB or settings)."""
    config = get_db_config(config_name)
    if config and config.connect_timeout:
        return config.connect_timeout
    return get_setting("EUCAPTCHA_CONNECT_TIMEOUT", 3)


def get_read_timeout(config_name: str = None) -> int:
    """Get the read timeout (from DB or settings)."""
    config = get_db_config(config_name)
    if config and config.read_timeout:
        return config.read_timeout
    return get_setting("EUCAPTCHA_READ_TIMEOUT", 10)


def get_write_timeout(config_name: str = None) -> int:
    """Get the write timeout (from DB or settings)."""
    config = get_db_config(config_name)
    if config and config.write_timeout:
        return config.write_timeout
    return get_setting("EUCAPTCHA_WRITE_TIMEOUT", 10)


def get_pool_timeout(config_name: str = None) -> int:
    """Get the connection pool timeout (from DB or settings)."""
    config = get_db_config(config_name)
    if config and config.pool_timeout:
        return config.pool_timeout
    return get_setting("EUCAPTCHA_POOL_TIMEOUT", 3)


def get_default_result_on_error(config_name: str = None) -> bool:
    """Get the default result on error setting (from DB or settings)."""
    config = get_db_config(config_name)
    if config is not None:
        return config.default_result_on_error
    return get_setting("EUCAPTCHA_DEFAULT_RESULT_ON_ERROR", True)


def get_suppress_exceptions(config_name: str = None) -> bool:
    """Get the suppress exceptions setting (from DB or settings)."""
    config = get_db_config(config_name)
    if config is not None:
        return config.suppress_exceptions
    return get_setting("EUCAPTCHA_SUPPRESS_EXCEPTIONS", True)
