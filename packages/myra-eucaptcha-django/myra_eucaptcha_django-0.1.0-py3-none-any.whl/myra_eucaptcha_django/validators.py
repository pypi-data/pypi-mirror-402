"""
Myra EU Captcha - Django Validators
"""
from django.core.exceptions import ValidationError
from myra_eucaptcha import MyraEuCaptchaClient, MyraEuCaptchaClientConfig

from .settings import (
    get_secret,
    get_sitekey,
    get_verify_url,
    get_connect_timeout,
    get_read_timeout,
    get_write_timeout,
    get_pool_timeout,
    get_default_result_on_error,
    get_suppress_exceptions,
)


_clients = {}


def get_client(config_name: str = None) -> MyraEuCaptchaClient:
    """Get or create the EU Captcha client for a configuration."""
    cache_key = config_name or "_default_"
    if cache_key not in _clients:
        config = MyraEuCaptchaClientConfig(
            sitekey=get_sitekey(config_name),
            secret=get_secret(config_name),
            verify_url=get_verify_url(config_name),
            connect_timeout=get_connect_timeout(config_name),
            read_timeout=get_read_timeout(config_name),
            write_timeout=get_write_timeout(config_name),
            pool_timeout=get_pool_timeout(config_name),
            default_result_on_error=get_default_result_on_error(config_name),
            suppress_exceptions=get_suppress_exceptions(config_name),
        )
        _clients[cache_key] = MyraEuCaptchaClient(config)
    return _clients[cache_key]


def clear_client_cache():
    """Clear the client cache (call after config changes)."""
    global _clients
    _clients = {}


def validate_captcha(token: str, remote_addr: str = "", config_name: str = None) -> None:
    """Validate a captcha response token.

    Args:
        token: The captcha response token from the form.
        remote_addr: The client's IP address (optional but recommended).
        config_name: Optional name of specific configuration to use.

    Raises:
        ValidationError: If the captcha validation fails.
    """
    if not token:
        raise ValidationError(
            "Please complete the captcha verification.",
            code="captcha_required",
        )

    client = get_client(config_name)
    result = client.validate(token=token, remote_addr=remote_addr)

    if not result.success:
        raise ValidationError(
            "Captcha verification failed. Please try again.",
            code="captcha_invalid",
        )
