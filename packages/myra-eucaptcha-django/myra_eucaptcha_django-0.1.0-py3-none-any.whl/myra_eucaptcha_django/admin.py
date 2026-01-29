"""
Myra EU Captcha - Django Admin
"""
from django.contrib import admin

from .models import CaptchaConfig


@admin.register(CaptchaConfig)
class CaptchaConfigAdmin(admin.ModelAdmin):
    """Admin interface for Captcha configuration."""

    list_display = [
        "name",
        "sitekey_display",
        "is_default",
        "is_active",
        "updated_at",
    ]

    list_filter = ["is_active", "is_default"]

    search_fields = ["name", "description", "sitekey"]

    readonly_fields = ["created_at", "updated_at"]

    fieldsets = [
        (None, {
            "fields": ["name", "description", "is_default", "is_active"],
        }),
        ("API Credentials", {
            "fields": ["sitekey", "secret"],
            "description": "Get your credentials from the EU Captcha dashboard.",
        }),
        ("URLs", {
            "fields": ["verify_url", "widget_url"],
            "classes": ["collapse"],
        }),
        ("Timeout Settings", {
            "fields": ["connect_timeout", "read_timeout", "write_timeout", "pool_timeout"],
            "classes": ["collapse"],
            "description": "Timeout values in seconds for HTTP operations.",
        }),
        ("Error Handling", {
            "fields": ["default_result_on_error", "suppress_exceptions"],
            "classes": ["collapse"],
            "description": "Control behavior when verification fails due to network errors.",
        }),
        ("Metadata", {
            "fields": ["created_at", "updated_at"],
            "classes": ["collapse"],
        }),
    ]

    actions = ["make_default", "activate", "deactivate"]

    def sitekey_display(self, obj):
        """Display truncated sitekey."""
        if obj.sitekey:
            return f"{obj.sitekey[:20]}..." if len(obj.sitekey) > 20 else obj.sitekey
        return "-"
    sitekey_display.short_description = "Site Key"

    def save_model(self, request, obj, form, change):
        """Clear cache when saving via admin."""
        super().save_model(request, obj, form, change)
        CaptchaConfig.objects.clear_cache()

    @admin.action(description="Set as default configuration")
    def make_default(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, "Please select exactly one configuration.", level="error")
            return
        config = queryset.first()
        config.is_default = True
        config.save()
        self.message_user(request, f"'{config.name}' is now the default configuration.")

    @admin.action(description="Activate selected configurations")
    def activate(self, request, queryset):
        count = queryset.update(is_active=True)
        CaptchaConfig.objects.clear_cache()
        self.message_user(request, f"{count} configuration(s) activated.")

    @admin.action(description="Deactivate selected configurations")
    def deactivate(self, request, queryset):
        count = queryset.update(is_active=False)
        CaptchaConfig.objects.clear_cache()
        self.message_user(request, f"{count} configuration(s) deactivated.")
