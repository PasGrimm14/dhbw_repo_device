from django.urls import path
from . import views

app_name = 'organization'

urlpatterns = [
    # Dashboard
    path('', views.organization_dashboard, name='dashboard'),
    
    # StudyProgram URLs
    path('programs/', views.StudyProgramListView.as_view(), name='program_list'),
    path('programs/<int:pk>/', views.StudyProgramDetailView.as_view(), name='program_detail'),
    
    # StudyField URLs
    path('fields/', views.StudyFieldListView.as_view(), name='field_list'),
    path('fields/<int:pk>/', views.StudyFieldDetailView.as_view(), name='field_detail'),
    
    # StudyAcademy URLs
    path('academies/', views.StudyAcademyListView.as_view(), name='academy_list'),
    path('academies/<int:pk>/', views.StudyAcademyDetailView.as_view(), name='academy_detail'),
    
    # StudySemester URLs
    path('semesters/', views.StudySemesterListView.as_view(), name='semester_list'),
    path('semesters/<int:pk>/', views.StudySemesterDetailView.as_view(), name='semester_detail'),
    
    # StudyYear URLs
    path('years/', views.StudyYearListView.as_view(), name='year_list'),
    path('years/<int:pk>/', views.StudyYearDetailView.as_view(), name='year_detail'),
    
    # StudyCourse URLs
    path('courses/', views.StudyCourseListView.as_view(), name='course_list'),
    path('courses/<int:pk>/', views.StudyCourseDetailView.as_view(), name='course_detail'),
    path('courses/<int:pk>/ical/', views.StudyCourseUpdateICalView.as_view(), name='course_update_ical'),
]