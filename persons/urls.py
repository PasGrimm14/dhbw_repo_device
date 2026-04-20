from django.urls import path
from . import views

app_name = 'persons'

urlpatterns = [
    # Dashboard
    path('', views.persons_dashboard, name='dashboard'),
    
    # Person URLs
    path('persons/', views.PersonListView.as_view(), name='person_list'),
    path('persons/<int:pk>/', views.PersonDetailView.as_view(), name='person_detail'),
    
    # Student URLs
    path('students/', views.StudentListView.as_view(), name='student_list'),
    path('students/<int:pk>/', views.StudentDetailView.as_view(), name='student_detail'),
    
    # Personnel URLs
    path('personnel/', views.PersonnelListView.as_view(), name='personnel_list'),
    path('personnel/<int:pk>/', views.PersonnelDetailView.as_view(), name='personnel_detail'),
    
    # Company URLs
    path('companies/', views.CompanyListView.as_view(), name='company_list'),
    path('companies/<int:pk>/', views.CompanyDetailView.as_view(), name='company_detail'),
]