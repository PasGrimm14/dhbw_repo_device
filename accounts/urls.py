from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Custom Login
    path('login/', views.CustomLoginView.as_view(template_name='registration/login.html'), name='login'),

    # Zugriff nicht freigegeben
    path('access-not-granted/', views.access_not_granted, name='access_not_granted'),

    # Benutzerverwaltung
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('users/new/', views.UserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/edit/', views.UserEditView.as_view(), name='user_edit'),

    # Rechteverwaltung
    path('groups/', views.GroupListView.as_view(), name='group_list'),
    path('groups/<int:pk>/permissions/', views.GroupPermissionEditView.as_view(), name='group_permissions'),
]
