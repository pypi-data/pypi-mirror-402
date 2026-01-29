from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="CaptchaConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, unique=True, help_text="Unique configuration name (used to reference this config in code)")),
                ("description", models.TextField(blank=True, help_text="Optional description of where this configuration is used")),
                ("sitekey", models.CharField(max_length=255, help_text="Public site key for client-side integration")),
                ("secret", models.CharField(max_length=255, help_text="Secret key for server-side verification")),
                ("verify_url", models.URLField(default="https://api.eu-captcha.eu/v1/verify/", help_text="Verification API endpoint URL")),
                ("widget_url", models.URLField(default="https://cdn.eu-captcha.eu/verify.js", help_text="JavaScript widget URL")),
                ("connect_timeout", models.PositiveIntegerField(default=3, help_text="Connection timeout in seconds")),
                ("read_timeout", models.PositiveIntegerField(default=10, help_text="Read timeout in seconds")),
                ("write_timeout", models.PositiveIntegerField(default=10, help_text="Write timeout in seconds")),
                ("pool_timeout", models.PositiveIntegerField(default=3, help_text="Connection pool timeout in seconds")),
                ("default_result_on_error", models.BooleanField(default=True, help_text="If True, return success on network errors (fail-open). If False, return failure (fail-closed).")),
                ("suppress_exceptions", models.BooleanField(default=True, help_text="If True, suppress exceptions and return result. If False, raise exceptions on errors.")),
                ("is_default", models.BooleanField(default=False, help_text="Use this configuration when no specific config is specified")),
                ("is_active", models.BooleanField(default=True, help_text="Inactive configurations cannot be used")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Captcha Configuration",
                "verbose_name_plural": "Captcha Configurations",
                "ordering": ["-is_default", "name"],
            },
        ),
    ]
