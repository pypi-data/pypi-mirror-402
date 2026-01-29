"""
Myra EU Captcha - Django App Configuration
"""
from django.apps import AppConfig


class MyraCaptchaAppConfig(AppConfig):
    name = "myra_eucaptcha_django"
    verbose_name = "Myra EU Captcha"
    default_auto_field = "django.db.models.BigAutoField"
