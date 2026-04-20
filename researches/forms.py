from django import forms
from .models import ResearchPhase


class ResearchPhaseForm(forms.ModelForm):
    class Meta:
        model = ResearchPhase
        fields = ['name', 'submission_date', 'offer_date', 'start_date', 'end_date', 'feedback_date', 'student_wishes', 'handling_type']
        widgets = {
            'submission_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'offer_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'start_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'end_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'feedback_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }
        help_texts = {
            'offer_date': 'Leer lassen → wird automatisch 2 Wochen vor Startdatum gesetzt',
        }
