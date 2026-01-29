"""
Myra EU Captcha - Django Models
"""
from django.db import models
from django.core.cache import cache

CACHE_KEY_DEFAULT = "captcha_config_default"
CACHE_KEY_PREFIX = "captcha_config_"


class CaptchaConfigManager(models.Manager):
    """Manager for CaptchaConfig with caching."""

    def get_default(self):
        """Get the default configuration, with caching."""
        config = cache.get(CACHE_KEY_DEFAULT)
        if config is None:
            config = self.filter(is_default=True, is_active=True).first()
            if config is None:
                config = self.filter(is_active=True).first()
            if config:
                cache.set(CACHE_KEY_DEFAULT, config, timeout=300)
        return config

    def get_by_name(self, name: str):
        """Get a configuration by name, with caching."""
        cache_key = f"{CACHE_KEY_PREFIX}{name}"
        config = cache.get(cache_key)
        if config is None:
            config = self.filter(name=name, is_active=True).first()
            if config:
                cache.set(cache_key, config, timeout=300)
        return config

    def get_config(self, name: str = None):
        """Get a configuration by name, or the default if not specified."""
        if name:
            return self.get_by_name(name)
        return self.get_default()

    def clear_cache(self):
        """Clear all configuration caches."""
        cache.delete(CACHE_KEY_DEFAULT)
        for config in self.all():
            cache.delete(f"{CACHE_KEY_PREFIX}{config.name}")


class CaptchaConfig(models.Model):
    """Configuration model for EU Captcha settings.

    Allows administrators to configure multiple captcha configurations
    via Django admin. One can be marked as default.

    Usage in forms:
        # Use default configuration
        captcha = CaptchaField()

        # Use specific configuration by name
        captcha = CaptchaField("contact-form")
    """

    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique configuration name (used to reference this config in code)",
    )

    description = models.TextField(
        blank=True,
        help_text="Optional description of where this configuration is used",
    )

    sitekey = models.CharField(
        max_length=255,
        help_text="Public site key for client-side integration",
    )

    secret = models.CharField(
        max_length=255,
        help_text="Secret key for server-side verification",
    )

    verify_url = models.URLField(
        default="https://api.eu-captcha.eu/v1/verify/",
        help_text="Verification API endpoint URL",
    )

    widget_url = models.URLField(
        default="https://cdn.eu-captcha.eu/verify.js",
        help_text="JavaScript widget URL",
    )

    connect_timeout = models.PositiveIntegerField(
        default=3,
        help_text="Connection timeout in seconds",
    )

    read_timeout = models.PositiveIntegerField(
        default=10,
        help_text="Read timeout in seconds",
    )

    write_timeout = models.PositiveIntegerField(
        default=10,
        help_text="Write timeout in seconds",
    )

    pool_timeout = models.PositiveIntegerField(
        default=3,
        help_text="Connection pool timeout in seconds",
    )

    default_result_on_error = models.BooleanField(
        default=True,
        help_text="If True, return success on network errors (fail-open). If False, return failure (fail-closed).",
    )

    suppress_exceptions = models.BooleanField(
        default=True,
        help_text="If True, suppress exceptions and return result. If False, raise exceptions on errors.",
    )

    is_default = models.BooleanField(
        default=False,
        help_text="Use this configuration when no specific config is specified",
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Inactive configurations cannot be used",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CaptchaConfigManager()

    class Meta:
        verbose_name = "Captcha Configuration"
        verbose_name_plural = "Captcha Configurations"
        ordering = ["-is_default", "name"]

    def __str__(self):
        parts = [self.name]
        if self.is_default:
            parts.append("(default)")
        if not self.is_active:
            parts.append("[inactive]")
        return " ".join(parts)

    def save(self, *args, **kwargs):
        if self.is_default:
            CaptchaConfig.objects.exclude(pk=self.pk).update(is_default=False)
        CaptchaConfig.objects.clear_cache()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        CaptchaConfig.objects.clear_cache()
        super().delete(*args, **kwargs)
