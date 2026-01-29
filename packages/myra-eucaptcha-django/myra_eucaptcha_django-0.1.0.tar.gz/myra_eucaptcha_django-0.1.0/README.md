# Myra EU Captcha - Django Integration

Django integration for the Myra EU Captcha service. Provides form fields, widgets, and an admin interface for managing captcha configurations.

## Installation

```bash
pip install myra-eucaptcha-django
```

Or with uv:

```bash
uv add myra-eucaptcha-django
```

## Quick Start

### 1. Add to INSTALLED_APPS

```python
# settings.py
INSTALLED_APPS = [
    ...
    'myra_eucaptcha_django',
]
```

### 2. Run Migrations

```bash
python manage.py migrate
```

### 3. Configure via Admin

1. Go to Django Admin → **Captcha Configurations**
2. Add a new configuration with your sitekey and secret
3. Mark it as **Default** if you want it used automatically

### 4. Add to Your Form

```python
from django import forms
from myra_eucaptcha_django import CaptchaField, CaptchaFormMixin

class ContactForm(CaptchaFormMixin, forms.Form):
    name = forms.CharField()
    email = forms.EmailField()
    message = forms.CharField(widget=forms.Textarea)

    # Uses the default configuration
    captcha = CaptchaField()
```

### 5. Use in Your View

```python
from django.shortcuts import render, redirect
from .forms import ContactForm

def contact_view(request):
    if request.method == "POST":
        # Pass request= to enable IP validation
        form = ContactForm(request.POST, request=request)
        if form.is_valid():
            # Process the form
            return redirect("success")
    else:
        form = ContactForm()

    return render(request, "contact.html", {"form": form})
```

### 6. Render in Template

```html
<form method="post">
    {% csrf_token %}
    {{ form.as_p }}
    <button type="submit">Send</button>
</form>
```

The captcha widget automatically includes the required JavaScript.

## Multiple Configurations

You can define multiple captcha configurations for different forms or purposes.

### In Admin

Create multiple configurations with unique names:
- `default` (marked as default)
- `contact-form`
- `registration`

### In Forms

Reference configurations by name:

```python
class ContactForm(CaptchaFormMixin, forms.Form):
    name = forms.CharField()
    captcha = CaptchaField("contact-form")

class RegistrationForm(CaptchaFormMixin, forms.Form):
    username = forms.CharField()
    captcha = CaptchaField("registration")

class CommentForm(CaptchaFormMixin, forms.Form):
    comment = forms.CharField()
    captcha = CaptchaField()  # Uses default configuration
```

## Configuration Options

Each configuration in the admin supports:

| Field | Description | Default |
|-------|-------------|---------|
| `name` | Unique identifier for this config | Required |
| `description` | Optional notes about usage | - |
| `sitekey` | Public site key for client-side | Required |
| `secret` | Secret key for server-side verification | Required |
| `is_default` | Use when no config name specified | `False` |
| `is_active` | Allow this config to be used | `True` |

### URLs (Advanced)

| Field | Description | Default |
|-------|-------------|---------|
| `verify_url` | Verification API endpoint | `https://api.eu-captcha.eu/v1/verify/` |
| `widget_url` | JavaScript widget URL | `https://cdn.eu-captcha.eu/verify.js` |

### Timeouts (Advanced)

| Field | Description | Default |
|-------|-------------|---------|
| `connect_timeout` | Connection timeout (seconds) | `3` |
| `read_timeout` | Read timeout (seconds) | `10` |
| `write_timeout` | Write timeout (seconds) | `10` |
| `pool_timeout` | Connection pool timeout (seconds) | `3` |

### Error Handling (Advanced)

| Field | Description | Default |
|-------|-------------|---------|
| `default_result_on_error` | Return success on network errors (fail-open) | `True` |
| `suppress_exceptions` | Suppress exceptions, return result instead | `True` |

## Fallback Configuration via Settings

If you prefer not to use the database, configure via `settings.py`:

```python
# settings.py
EUCAPTCHA_SITEKEY = "your-site-key"
EUCAPTCHA_SECRET = "your-secret-key"

# Optional
EUCAPTCHA_VERIFY_URL = "https://api.eu-captcha.eu/v1/verify/"
EUCAPTCHA_WIDGET_URL = "https://cdn.eu-captcha.eu/verify.js"
EUCAPTCHA_CONNECT_TIMEOUT = 3
EUCAPTCHA_READ_TIMEOUT = 10
EUCAPTCHA_WRITE_TIMEOUT = 10
EUCAPTCHA_POOL_TIMEOUT = 3
EUCAPTCHA_DEFAULT_RESULT_ON_ERROR = True
EUCAPTCHA_SUPPRESS_EXCEPTIONS = True
```

Database configurations take precedence over settings.

## API Reference

### CaptchaField

```python
CaptchaField(config_name=None, **kwargs)
```

Form field that renders the captcha widget and validates the response.

- `config_name`: Optional name of the configuration to use. If not specified, uses the default configuration.

### CaptchaFormMixin

Mixin that automatically passes the request to captcha fields for IP validation.

```python
class MyForm(CaptchaFormMixin, forms.Form):
    captcha = CaptchaField()

# In view:
form = MyForm(request.POST, request=request)
```

### CaptchaWidget

The widget that renders the captcha challenge. Usually not used directly.

### validate_captcha

Low-level validation function for custom use cases:

```python
from myra_eucaptcha_django import validate_captcha

validate_captcha(
    token="captcha-response-token",
    remote_addr="client-ip",  # Optional
    config_name="my-config",  # Optional
)
```

Raises `django.core.exceptions.ValidationError` on failure.

## License

Proprietary - Myra Security GmbH
