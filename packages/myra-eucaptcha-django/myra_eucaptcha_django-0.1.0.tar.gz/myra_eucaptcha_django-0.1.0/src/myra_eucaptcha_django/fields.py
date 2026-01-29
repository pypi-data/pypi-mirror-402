"""
Myra EU Captcha - Django Form Field
"""
from django import forms

from .widgets import CaptchaWidget
from .validators import validate_captcha


class CaptchaField(forms.CharField):
    """Form field for EU Captcha validation.

    Usage in a form:
        class ContactForm(forms.Form):
            name = forms.CharField()
            email = forms.EmailField()
            message = forms.CharField(widget=forms.Textarea)

            # Use default configuration
            captcha = CaptchaField()

            # Or use a specific configuration by name
            captcha = CaptchaField("contact-form")

    In your view, pass the request to the form to enable IP validation:
        form = ContactForm(request.POST, request=request)
    """

    def __init__(self, config_name=None, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        self.config_name = config_name

        kwargs.setdefault("label", "")
        kwargs.setdefault("required", True)

        if "widget" not in kwargs:
            kwargs["widget"] = CaptchaWidget(config_name=config_name)

        super().__init__(*args, **kwargs)

    def validate(self, value):
        """Validate the captcha response token."""
        super().validate(value)

        remote_addr = ""
        if self.request:
            remote_addr = self._get_client_ip(self.request)

        validate_captcha(value, remote_addr=remote_addr, config_name=self.config_name)

    def _get_client_ip(self, request) -> str:
        """Extract client IP from request, respecting X-Forwarded-For."""
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "")


class CaptchaFormMixin:
    """Mixin for forms that use EU Captcha.

    This mixin automatically passes the request to the captcha field.

    Usage:
        class ContactForm(CaptchaFormMixin, forms.Form):
            name = forms.CharField()
            captcha = CaptchaField()

        # In your view:
        form = ContactForm(request.POST, request=request)
    """

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            if isinstance(field, CaptchaField):
                field.request = self.request
