import uuid
from django.shortcuts import redirect
from django.urls import resolve, reverse, Resolver404
from django.utils import timezone

from .exceptions import AccessNotGrantedError

# Pfade, bei denen die Prüfung übersprungen wird
_EXEMPT_URL_NAMES = {
    'accounts:access_not_granted',
    'accounts:login',
}
_EXEMPT_PATH_PREFIXES = (
    '/admin/',
    '/saml2/',
    '/accounts/login/',
    '/accounts/logout/',
    '/accounts/access-not-granted/',
)


def _resolve_token(request):
    """
    Versucht ein AccessToken aus dem Query-Parameter ?token= .
    Setzt request.token_person auf die zugehörige Person, oder None.
    Wenn das Token ein allowed_url_name hat, wird geprüft ob die aktuelle
    Seite übereinstimmt – sonst bleibt token_person None.
    """
    request.token_person = None

    token_str = request.GET.get('token')
    if not token_str:
        return

    token_obj = _lookup_token(token_str)
    if not token_obj:
        import logging
        logging.getLogger('sgverwaltung.auth').warning('AccessToken: no valid token for "%s"', token_str)
        return

    # URL-Einschränkung prüfen
    if token_obj.allowed_url_name:
        try:
            current_url_name = resolve(request.path).view_name
        except Resolver404:
            current_url_name = None
        if current_url_name != token_obj.allowed_url_name:
            import logging
            logging.getLogger('sgverwaltung.auth').warning(
                'AccessToken: Token %s only valid for "%s", but now "%s"',
                token_str[:8], token_obj.allowed_url_name, current_url_name,
            )
            return

    request.token_person = token_obj.person
    token_obj.last_used_at = timezone.now()
    token_obj.save(update_fields=['last_used_at'])
    import logging
    logging.getLogger('sgverwaltung.auth').debug(
        'AccessToken in use for %s on view %s', request.token_person, token_obj.allowed_url_name
    )


def _lookup_token(token_str):
    """Gibt ein gültiges AccessToken zurück, oder None."""
    try:
        token_uuid = uuid.UUID(token_str)
    except ValueError:
        return None
    from .models import AccessToken
    token = (
        AccessToken.objects
        .select_related('person')
        .filter(token=token_uuid, is_active=True)
        .first()
    )
    if token and token.is_valid:
        return token
    return None


class AccessCheckMiddleware:
    """
    Prüft nach jedem Request ob ein eingeloggter User einen validen Zustand hat:
    - User muss einer Person zugeordnet sein
    - Person mit Rolle MA muss ein Personnel-Profil haben
    - Person mit Rolle ST muss ein Student-Profil haben

    Ist das nicht der Fall, wird der User auf die "Zugriff nicht freigegeben"-Seite
    weitergeleitet, anstatt einen Fehler zu werfen.

    Zusätzlich: Wenn ein gültiger ?token=<uuid> Query-Parameter vorhanden ist, wird request.token_person gesetzt und die normale
    Auth-Prüfung übersprungen.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _resolve_token(request)

        if not request.token_person and request.user.is_authenticated:
            reason = self._check_access(request)
            if reason:
                url = reverse('accounts:access_not_granted') + f'?grund={reason}'
                if not request.path.startswith('/accounts/access-not-granted/'):
                    return redirect(url)

        return self.get_response(request)

    def _check_access(self, request):
        if any(request.path.startswith(p) for p in _EXEMPT_PATH_PREFIXES):
            return None

        user = request.user

        # Prüfen ob User einer Person zugeordnet ist
        if not hasattr(user, 'person'):
            return AccessNotGrantedError.REASON_NO_PERSON

        person = user.person

        # Mitarbeiter ohne Personnel-Profil
        if person.role_now == 'MA':
            try:
                _ = person.personnel_profile
            except Exception:
                return AccessNotGrantedError.REASON_NO_PERSONNEL

        # Student ohne Student-Profil
        elif person.role_now == 'ST':
            try:
                _ = person.student_profile
            except Exception:
                return AccessNotGrantedError.REASON_NO_STUDENT

        return None
