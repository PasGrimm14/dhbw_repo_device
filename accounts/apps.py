from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    verbose_name = 'Benutzerverwaltung'

    def ready(self):
        import accounts.signals  # noqa: F401

        from django.contrib.auth.models import User
        from accounts.utils import has_role as _has_role, get_roles as _get_roles

        User.add_to_class('has_role', lambda self, role: _has_role(self, role))
        User.add_to_class('get_roles', lambda self: _get_roles(self))
