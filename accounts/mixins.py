from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.conf import settings
from django.shortcuts import redirect


class PermissionMixin(LoginRequiredMixin, PermissionRequiredMixin):
    """
    Kombinierter Mixin: Prüft zuerst Login, dann Permissions.
    - Nicht eingeloggt → Redirect zu LOGIN_URL
    - Eingeloggt, aber kein Recht → 403 (rendert templates/403.html)
    """

    def has_permission(self):
        if self.request.user.is_staff:
            return True
        return super().has_permission()

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            missing = [
                perm for perm in self.get_permission_required()
                if not self.request.user.has_perm(perm)
            ]
            msg = 'Fehlende Rechte: ' + ', '.join(missing) if missing else 'Kein Zugriff.'
            raise PermissionDenied(msg)
        return super(PermissionRequiredMixin, self).handle_no_permission()


class TokenOrLoginMixin:
    """
    Erlaubt Zugriff mit gültigem AccessToken ODER normaler Session-Authentifizierung.

    In Views, die diesen Mixin nutzen, ist die zugehörige Person über
    request.token_person (Token-Zugang) oder request.user.person (Login) erreichbar.
    Hilfsmethode: self.get_person(request) gibt die richtige Person zurück.

    Verwendung in Class-Based Views:
        class MeineView(TokenOrLoginMixin, DetailView):
            ...
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated and not getattr(request, 'token_person', None):
            return redirect(f"{settings.LOGIN_URL}?next={request.path}")
        return super().dispatch(request, *args, **kwargs)

    def get_person(self, request):
        """Gibt die Person zurück – egal ob Token- oder Login-Zugang."""
        if getattr(request, 'token_person', None):
            return request.token_person
        if request.user.is_authenticated and hasattr(request.user, 'person'):
            return request.user.person
        return None
