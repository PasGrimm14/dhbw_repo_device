from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth.views import LoginView
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView

from .exceptions import AccessNotGrantedError


# ---------------------------------------------------------------------------
# Custom Login
# ---------------------------------------------------------------------------

class CustomLoginView(LoginView):
    pass


# ---------------------------------------------------------------------------
# Zugriff nicht freigegeben
# ---------------------------------------------------------------------------

def access_not_granted(request):
    reason = request.GET.get('grund', AccessNotGrantedError.REASON_NO_PERSON)
    return render(request, 'accounts/access_not_granted.html', {'reason': reason}, status=403)


# ---------------------------------------------------------------------------
# Mixin: nur Staff-User dürfen diese Views aufrufen
# ---------------------------------------------------------------------------

class StaffRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_staff:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


# ---------------------------------------------------------------------------
# Hilfsfunktion: Relevante Permissions der eigenen Apps
# ---------------------------------------------------------------------------

OWN_APPS = ('persons', 'organization', 'lectures', 'researches')


def get_app_permissions():
    content_types = ContentType.objects.filter(app_label__in=OWN_APPS)
    return (
        Permission.objects
        .filter(content_type__in=content_types)
        .select_related('content_type')
        .order_by('content_type__app_label', 'content_type__model', 'codename')
    )


# ---------------------------------------------------------------------------
# Forms
# ---------------------------------------------------------------------------

class UserCreateForm(UserCreationForm):
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Gruppen',
    )
    is_staff = forms.BooleanField(
        required=False,
        label='Admin-Zugang (Staff)',
        help_text='Darf die Benutzerverwaltung und Django Admin nutzen.',
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'is_staff',
                  'password1', 'password2', 'groups')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = self.cleaned_data.get('is_staff', False)
        if commit:
            user.save()
            user.groups.set(self.cleaned_data.get('groups', []))
        return user


class UserGroupForm(forms.ModelForm):
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Gruppen',
    )
    is_staff = forms.BooleanField(
        required=False,
        label='Admin-Zugang (Staff)',
    )
    is_active = forms.BooleanField(
        required=False,
        label='Account aktiv',
    )

    class Meta:
        model = User
        fields = ('is_active', 'is_staff', 'groups')


class GroupPermissionForm(forms.ModelForm):
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Berechtigungen',
    )

    class Meta:
        model = Group
        fields = ('permissions',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['permissions'].queryset = get_app_permissions()


# ---------------------------------------------------------------------------
# Views: User
# ---------------------------------------------------------------------------

class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'accounts/user_detail.html'
    context_object_name = 'users'

    def get_object(self, _queryset=None):
        pk = self.kwargs['pk']
        if not self.request.user.is_staff and self.request.user.pk != pk:
            raise PermissionDenied # Jeder darf nur die eigene Profilseite sehen
        return get_object_or_404(
            User.objects.prefetch_related('groups', 'person'), pk=pk
        )
    
class UserListView(StaffRequiredMixin, ListView):
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'

    def get_queryset(self):
        return (
            User.objects
            .prefetch_related('groups', 'person')
            .order_by('username')
        )


class UserCreateView(StaffRequiredMixin, CreateView):
    model = User
    form_class = UserCreateForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('accounts:user_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Neuen Benutzer anlegen'
        return ctx


class UserEditView(StaffRequiredMixin, UpdateView):
    model = User
    form_class = UserGroupForm
    template_name = 'accounts/user_groups.html'
    success_url = reverse_lazy('accounts:user_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = f'Benutzer bearbeiten: {self.object.username}'
        return ctx


# ---------------------------------------------------------------------------
# Views: Gruppen & Rechte
# ---------------------------------------------------------------------------

class GroupListView(StaffRequiredMixin, ListView):
    model = Group
    template_name = 'accounts/group_list.html'
    context_object_name = 'groups'

    def get_queryset(self):
        return Group.objects.prefetch_related('permissions').order_by('name')


class GroupPermissionEditView(StaffRequiredMixin, UpdateView):
    model = Group
    form_class = GroupPermissionForm
    template_name = 'accounts/group_permissions.html'
    success_url = reverse_lazy('accounts:group_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = f'Rechte für Gruppe: {self.object.name}'
        perms_by_app = {}
        for perm in get_app_permissions():
            app = perm.content_type.app_label
            perms_by_app.setdefault(app, []).append(perm)
        ctx['perms_by_app'] = perms_by_app
        return ctx
