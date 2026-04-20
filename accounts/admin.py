from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User, Group
from django.utils import timezone

from .models import AccessToken


admin.site.unregister(User)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'first_name', 'last_name', 'email', 'get_groups', 'is_staff', 'is_active']
    list_filter = ['groups', 'is_staff', 'is_active']
    search_fields = ['username', 'first_name', 'last_name', 'email']
    ordering = ['username']
    filter_horizontal = ['groups', 'user_permissions']

    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Persönliche Daten', {
            'fields': ('first_name', 'last_name', 'email')
        }),
        ('Gruppen & Berechtigungen', {
            'fields': ('is_active', 'is_staff', 'groups', 'user_permissions'),
        }),
        ('Wichtige Daten', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',),
        }),
    )

    def get_groups(self, obj):
        return ', '.join(g.name for g in obj.groups.all()) or '-'
    get_groups.short_description = 'Gruppen'


@admin.register(AccessToken)
class AccessTokenAdmin(admin.ModelAdmin):
    list_display = ['person', 'label', 'is_active', 'is_valid_display', 'expires_at', 'last_used_at', 'created_at']
    list_filter = ['is_active']
    search_fields = ['person__firstname', 'person__lastname', 'person__mail_main', 'label']
    readonly_fields = ['token', 'created_at', 'last_used_at']
    autocomplete_fields = ['person']

    fieldsets = (
        (None, {
            'fields': ('person', 'label', 'allowed_url_name', 'is_active'),
        }),
        ('Token', {
            'fields': ('token', 'expires_at'),
        }),
        ('Nutzung', {
            'fields': ('created_at', 'last_used_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(boolean=True, description='Gültig')
    def is_valid_display(self, obj):
        return obj.is_valid
    
    def save_model(self, request, obj, form, change):
        now = timezone.now()
        if not obj.created_at:
            obj.created_at = now
        if not obj.last_used_at:
            obj.last_used_at = now
        super().save_model(request, obj, form, change)
