from django.urls import path
from . import views

app_name = 'researches'

urlpatterns = [
    # Dashboard
    path('', views.researches_dashboard, name='dashboard'),

    # Research URLs
    path('list/', views.ResearchListView.as_view(), name='research_list'),
    path('research/<int:pk>/', views.ResearchDetailView.as_view(), name='research_detail'),
    path('research/<int:pk>/edit/', views.research_edit, name='research_edit'),

    # Themeneinreichung
    path('research/topic/phase/<int:phase_pk>/', views.research_form_start, name='research_form_start'),
    path('research/<int:pk>/topic/', views.research_form, name='research_form'),
    path('research/<int:pk>/topic/preview/', views.research_form_preview, name='research_form_preview'),

    # ResearchPhase URLs
    path('phases/', views.ResearchPhaseListView.as_view(), name='researchphase_list'),
    path('phases/new/', views.ResearchPhaseCreateView.as_view(), name='researchphase_create'),
    path('phases/<int:pk>/', views.ResearchPhaseDetailView.as_view(), name='researchphase_detail'),
    path('phases/<int:pk>/edit/', views.ResearchPhaseUpdateView.as_view(), name='researchphase_update'),
    path('phases/<int:pk>/delete/', views.ResearchPhaseDeleteView.as_view(), name='researchphase_delete'),
    path('phases/<int:pk>/csv/', views.researchphase_csv_export, name='researchphase_csv_export'),
    # path('students/<int:pk>/researches/', views.StudentResearchesView.as_view(), name='student_researches'),

    # AssessorWish URLs
    # path('assessorwishes/', views.AssessorWishListView.as_view(), name='assessorwish_list'),
    # path('assessorwish/<int:pk>/', views.AssessorWishDetailView.as_view(), name='assessorwish_detail'),

    # MatchWish URLs
    # path('matchwishes/', views.MatchWishListView.as_view(), name='matchwish_list'),
    # path('matchwish/<int:pk>/', views.MatchWishDetailView.as_view(), name='matchwish_detail'),
]
