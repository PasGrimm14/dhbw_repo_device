from django.urls import path
from . import views

app_name = 'lectures'

urlpatterns = [
    # Dashboard
    path('', views.lectures_dashboard, name='dashboard'),
    
    # Module URLs
    path('modules/', views.ModuleListView.as_view(), name='module_list'),
    path('modules/<int:pk>/', views.ModuleDetailView.as_view(), name='module_detail'),
    
    # ModuleUnit URLs
    path('units/', views.ModuleUnitListView.as_view(), name='unit_list'),
    path('units/<int:pk>/', views.ModuleUnitDetailView.as_view(), name='unit_detail'),
    
    # Grade URLs
    path('grades/', views.GradeListView.as_view(), name='grade_list'),
    path('students/<int:pk>/grades/', views.StudentGradesView.as_view(), name='student_grades'),

    # Lesson Schedule
    path('courses/<int:course_pk>/schedule/', views.CourseLessonScheduleView.as_view(), name='course_schedule'),

    # Day View
    path('day/', views.DayView.as_view(), name='day_view'),
    path('day/<str:date_param>/', views.DayView.as_view(), name='day_view_date'),
]
