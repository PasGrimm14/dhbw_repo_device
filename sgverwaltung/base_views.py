# core/base_views.py
from django.views.generic import DetailView
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied

class ForUserDetailView(PermissionRequiredMixin, DetailView):
    """
    Basisklasse für DetailViews, die Zugriff über `for_user` prüfen
    und 403 statt 404 werfen.
    """
    permission_required = None

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        if obj not in obj.__class__.objects.for_user(self.request.user):
            raise PermissionDenied("Kein Zugriff auf die Instanz der Klasse " + obj.__class__.__name__)
        return obj