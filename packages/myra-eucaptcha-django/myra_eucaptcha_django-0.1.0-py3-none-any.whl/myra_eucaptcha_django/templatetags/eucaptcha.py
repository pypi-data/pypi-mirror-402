"""
Myra EU Captcha - Django Template Tags

Usage in templates:
    {% load eucaptcha %}

    <head>
        {% eucaptcha_script %}
    </head>

    <form method="post">
        {% csrf_token %}
        {{ form.as_p }}
        {% eucaptcha_widget %}
        <button type="submit">Submit</button>
    </form>
"""
from django import template
from django.utils.safestring import mark_safe

from ..settings import get_sitekey, get_widget_url

register = template.Library()


@register.simple_tag
def eucaptcha_script():
    """Render the EU Captcha JavaScript include tag.

    Usage:
        {% eucaptcha_script %}
    """
    url = get_widget_url()
    return mark_safe(f'<script src="{url}" async defer></script>')


@register.simple_tag
def eucaptcha_widget(sitekey=None):
    """Render the EU Captcha widget div.

    Usage:
        {% eucaptcha_widget %}
        {% eucaptcha_widget sitekey="custom-key" %}
    """
    key = sitekey or get_sitekey()
    return mark_safe(f'<div class="eu-captcha" data-sitekey="{key}"></div>')


@register.inclusion_tag("eucaptcha/full_widget.html")
def eucaptcha_full(sitekey=None):
    """Render the complete EU Captcha widget with script.

    Usage:
        {% eucaptcha_full %}
    """
    return {
        "sitekey": sitekey or get_sitekey(),
        "widget_url": get_widget_url(),
    }
