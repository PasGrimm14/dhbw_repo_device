from django.contrib import admin
from django.utils.html import format_html
from .models import Research, ResearchAssessorWish, ResearchMatchWish, ResearchPhase


@admin.register(ResearchPhase)
class ResearchPhaseAdmin(admin.ModelAdmin):
    list_display = ['name', 'submission_date', 'offer_date', 'start_date', 'end_date', 'feedback_date']
    search_fields = ['name']
    ordering = ['name']

    fieldsets = (
        ('Bezeichnung', {
            'fields': ('name',)
        }),
        ('Termine', {
            'fields': ('submission_date', 'offer_date', 'start_date', 'end_date', 'feedback_date'),
            'description': 'offer_date wird automatisch auf start_date - 2 Wochen gesetzt, wenn leer gelassen.'
        }),
    )


@admin.register(Research)
class ResearchAdmin(admin.ModelAdmin):
    list_display = [
        'get_student_name',
        'get_title_short',
        'unit',
        'research_phase',
        'assessor_scien',
        'assessor_oper',
        'start_date',
        'end_date',
        'status_display',
        'approved_oper',
        'approved_scien',
        'approved_orga',
        'approved_all'
    ]
    list_filter = ['unit', 'research_phase', 'start_date', 'end_date']
    search_fields = [
        'title',
        'student__matri_nr',
        'student__person__firstname',
        'student__person__lastname',
        'personnel__person__firstname',
        'personnel__person__lastname'
    ]
    raw_id_fields = ['unit', 'student', 'assessor_scien', 'assessor_oper']
    date_hierarchy = 'start_date'
    ordering = ['-start_date']

    fieldsets = (
        ('Student & Veranstaltung', {
            'fields': ('student', 'unit', 'research_phase')
        }),
        ('Betreuer', {
            'fields': ('assessor_scien', 'assessor_oper', 'company_context')
        }),
        ('Arbeit', {
            'fields': ('title', 'problem', 'goal', 'methodology')
        }),
        ('Termine & Status', {
            'fields': ('start_date', 'end_date', 'topic_submitted_date', 'approved_oper', 'approved_scien', 'approved_orga')
        }),
    )

    def get_student_name(self, obj):
        return obj.student.person.get_short_name()
    get_student_name.short_description = 'Student'

    def get_title_short(self, obj):
        if obj.title:
            return obj.title[:50] + ('...' if len(obj.title) > 50 else '')
        return '-'
    get_title_short.short_description = 'Titel'

    def approved_status(self, obj):
        if obj.approved_all:
            return format_html('<span style="color: green;">✓ Genehmigt</span>')
        return format_html('<span style="color: orange;">⚠ Nicht genehmigt</span>')
    approved_status.short_description = 'Genehmigung'

    def status_display(self, obj):
        status = obj.status_display
        colors = {
            'Eingereicht': 'green',
            'Warten auf Start': 'lightgreen',
            'In Bearbeitung': 'blue',
            'Überfällig': 'red',
            'Deadline naht': 'orange',
            'Nicht genehmigt': 'gray'
        }
        color = colors.get(status, 'black')
        return format_html(f'<span style="color: {color}; font-weight: bold;">{status}</span>')
    status_display.short_description = 'Status'


@admin.register(ResearchAssessorWish)
class ResearchAssessorWishAdmin(admin.ModelAdmin):
    list_display = [
        'get_personnel_name',
        'unit',
        'academic_year',
        'current_count',
        'remaining_capacity',
        'random_sel',
        'is_full_display',
        'submitted_date'
    ]
    list_filter = ['academic_year', 'unit', 'random_sel']
    search_fields = [
        'personnel__person__firstname',
        'personnel__person__lastname',
        'unit__unit_name',
        'comment'
    ]
    raw_id_fields = ['personnel', 'unit', 'academic_year']
    ordering = ['academic_year', 'personnel']

    fieldsets = (
        ('Betreuer & Veranstaltung', {
            'fields': ('personnel', 'unit', 'academic_year')
        }),
        ('Kapazität', {
            'fields': ('max_count_orga', 'max_count', 'random_sel')
        })
    )

    def get_personnel_name(self, obj):
        return obj.personnel.person.get_short_name()
    get_personnel_name.short_description = 'Betreuer'

    def current_count(self, obj):
        count = obj.current_count
        return format_html(f'<strong>{count}</strong>')
    current_count.short_description = 'Aktuell'

    def remaining_capacity(self, obj):
        remaining = obj.remaining_capacity
        color = 'green' if remaining > 0 else 'red'
        return format_html(f'<span style="color: {color};">{remaining}</span>')
    remaining_capacity.short_description = 'Frei'

    def is_full_display(self, obj):
        if obj.is_full:
            return format_html('<span style="color: red;">✗ Voll</span>')
        return format_html('<span style="color: green;">✓ Verfügbar</span>')
    is_full_display.short_description = 'Status'


@admin.register(ResearchMatchWish)
class ResearchMatchWishAdmin(admin.ModelAdmin):
    list_display = [
        'get_student_name',
        'get_research_title',
        'get_personnel_name',
        'priority'
    ]
    list_filter = ['personnel_who', 'priority']
    search_fields = [
        'research__student__person__firstname',
        'research__student__person__lastname',
        'personnel_who__person__firstname',
        'personnel_who__person__lastname',
        'research__title'
    ]
    raw_id_fields = ['research', 'person_from', 'personnel_who']
    ordering = ['research', 'priority']

    def get_student_name(self, obj):
        return obj.research.student.person.get_short_name()
    get_student_name.short_description = 'Student'

    def get_research_title(self, obj):
        if obj.research.title:
            return obj.research.title[:30] + ('...' if len(obj.research.title) > 30 else '')
        return '-'
    get_research_title.short_description = 'Arbeit'

    def get_personnel_name(self, obj):
        return obj.personnel_who.person.get_short_name()
    get_personnel_name.short_description = 'Gewünschter Betreuer'
