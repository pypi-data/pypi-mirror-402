"""
Myra EU Captcha - Django Widget
"""
from django import forms

from .settings import get_sitekey, get_widget_url


class CaptchaWidget(forms.Widget):
    """Widget that renders the EU Captcha challenge."""

    template_name = "eucaptcha/widget.html"

    def __init__(self, attrs=None, sitekey=None, config_name=None):
        super().__init__(attrs)
        self._sitekey = sitekey
        self._config_name = config_name

    @property
    def sitekey(self):
        """Get the sitekey, from init or config."""
        return self._sitekey or get_sitekey(self._config_name)

    @property
    def widget_url(self):
        """Get the widget URL from config."""
        return get_widget_url(self._config_name)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"].update({
            "sitekey": self.sitekey,
            "widget_url": self.widget_url,
        })
        return context

    def value_from_datadict(self, data, files, name):
        """Extract the captcha response from form data."""
        return data.get("eu-captcha-response", "")
