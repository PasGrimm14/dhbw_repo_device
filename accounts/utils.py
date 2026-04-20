"""
Hilfsfunktionen für Rollen- und Rechteprüfung.

Verwendung in Python (kein Import nötig):
    request.user.has_role('student')    # → True / False
    request.user.get_roles()            # → {'employee', 'mentor'}

Standalone-Funktionen (intern, z.B. für AnonymousUser):
    from accounts.utils import has_role, get_roles
    has_role(user, 'student')
    get_roles(user)

Verwendung in Templates (via Context Processor, kein {% load %} nötig):
    {% if user_roles.student %}...{% endif %}
    {% if user_roles.employee %}...{% endif %}
"""


# ============= Rollen =============

def _get_groups(user) -> set:
    """Gruppennamen des Users als Set — wird einmal pro Request gecacht."""
    if not hasattr(user, '_groups_cache'):
        user._groups_cache = set(user.groups.values_list('name', flat=True))
    return user._groups_cache


def has_role(user, role: str) -> bool:
    """
    Gibt True zurück wenn der User der Gruppe `role` angehört.
    Staff-User erhalten immer True.
    Ergebnis wird auf dem User-Objekt gecacht (einmal pro Request).
    """
    if not user or not user.is_authenticated:
        return False
    # if user.is_staff:
    #    return True
    return role in _get_groups(user)


def get_roles(user) -> set:
    """Gibt alle Rollennamen des Users als Set zurück."""
    if not user or not user.is_authenticated:
        return set()
    return _get_groups(user)


class _UserRolesProxy:
    """
    Proxy-Objekt für Templates: erlaubt {{ user_roles.student }}.
    Jeder Attributzugriff ruft has_role() auf.
    """

    def __init__(self, user):
        self._user = user

    def __getattr__(self, role: str) -> bool:
        return has_role(self._user, role)

    def __contains__(self, role: str) -> bool:
        return has_role(self._user, role)

    def __bool__(self) -> bool:
        return self._user.is_authenticated


def utils_context_processor(request):
    """Context Processor: stellt Hilfsvariablen in jedem Template bereit."""
    return {
        'user_roles': _UserRolesProxy(request.user),
    }
