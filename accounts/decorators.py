from functools import wraps
from django.conf import settings
from django.shortcuts import redirect


def token_or_login_required(view_func):
    """
    Decorator für Function-Based Views: Erlaubt Zugriff mit gültigem AccessToken
    ODER normaler Session-Authentifizierung.

    Verwendung:
        @token_or_login_required
        def meine_view(request, pk):
            person = request.token_person or request.user.person
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated and not getattr(request, 'token_person', None):
            return redirect(f"{settings.LOGIN_URL}?next={request.path}")
        return view_func(request, *args, **kwargs)
    return wrapper
