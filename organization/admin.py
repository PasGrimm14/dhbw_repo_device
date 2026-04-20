from django.contrib import admin
from .models import (
    StudyProgram,
    StudyField,
    StudyAcademy,
    StudyOrganisation,
    StudySemester,
    StudyPhase,
    StudyYear,
    StudyCourse
)


@admin.register(StudyProgram)
class StudyProgramAdmin(admin.ModelAdmin):
    list_display = ['study_progr', 'field_count']
    search_fields = ['study_progr']

    def field_count(self, obj):
        return obj.fields.count()
    field_count.short_description = 'Anzahl Studienrichtungen'


@admin.register(StudyField)
class StudyFieldAdmin(admin.ModelAdmin):
    list_display = ['studyfield', 'study', 'course_count']
    list_filter = ['study']
    search_fields = ['studyfield', 'study__study_progr']

    def course_count(self, obj):
        return obj.courses.count()
    course_count.short_description = 'Anzahl Kurse'


@admin.register(StudyAcademy)
class StudyAcademyAdmin(admin.ModelAdmin):
    list_display = ['academy_name', 'course_count']
    search_fields = ['academy_name']

    def course_count(self, obj):
        return obj.courses.count()
    course_count.short_description = 'Anzahl Kurse'


@admin.register(StudyOrganisation)
class StudyOrganisationAdmin(admin.ModelAdmin):
    list_display = ['name', 'course_count']
    search_fields = ['name']

    def course_count(self, obj):
        return obj.courses.count()
    course_count.short_description = 'Anzahl Kurse'


@admin.register(StudySemester)
class StudySemesterAdmin(admin.ModelAdmin):
    list_display = [
        'name_short',
        'name',
        'type',
        'cycle',
        'start_date',
        'end_date',
        'duration_days',
        'is_active',
        'special'
    ]
    list_filter = ['type', 'cycle', 'special']
    search_fields = ['name', 'name_short']
    ordering = ['-start_date']
    date_hierarchy = 'start_date'

    fieldsets = (
        ('Grunddaten', {
            'fields': ('name', 'name_short', 'type', 'cycle', 'special')
        }),
        ('Zeitraum', {
            'fields': ('start_date', 'end_date')
        }),
    )

    def is_active(self, obj):
        return '✓' if obj.is_active else '✗'
    is_active.short_description = 'Aktiv'
    is_active.boolean = True


@admin.register(StudyPhase)
class StudyPhaseAdmin(admin.ModelAdmin):
    list_display = ['name', 'current_semester_display', 'year_count', 'course_count']
    search_fields = ['name']
    ordering = ['name']

    fieldsets = (
        ('Bezeichnung', {
            'fields': ('name',)
        }),
        ('1. Studienjahr', {
            'fields': ('semester_id1t', 'semester_id1p', 'semester_id2t', 'semester_id2p')
        }),
        ('2. Studienjahr', {
            'fields': ('semester_id3t', 'semester_id3p', 'semester_id4t', 'semester_id4p')
        }),
        ('3. Studienjahr', {
            'fields': ('semester_id5t', 'semester_id5p', 'semester_id6t', 'semester_id6p')
        }),
    )

    def current_semester_display(self, obj):
        current = obj.get_current_semester()
        if current:
            return f"{current.name_short} (läuft)"
        return "-"
    current_semester_display.short_description = 'Aktuelles Semester'

    def year_count(self, obj):
        return obj.years.count()
    year_count.short_description = 'Jahrgänge'

    def course_count(self, obj):
        return obj.courses.count()
    course_count.short_description = 'Kurse'


@admin.register(StudyYear)
class StudyYearAdmin(admin.ModelAdmin):
    list_display = ['year_name', 'course_count']
    search_fields = ['year_name']
    ordering = ['-year_name']

    fieldsets = (
        ('Jahrgang', {
            'fields': ('year_name',)
        }),
    )

    def course_count(self, obj):
        return obj.courses.count()
    course_count.short_description = 'Kurse'


@admin.register(StudyCourse)
class StudyCourseAdmin(admin.ModelAdmin):
    list_display = [
        'course_nr',
        'academy',
        'field',
        'academic_year',
        'study_phase',
        'organisation',
        'student_count'
    ]
    list_filter = ['academy', 'organisation', 'academic_year', 'study_phase']
    search_fields = ['course_nr', 'academy__academy_name', 'field__studyfield']
    autocomplete_fields = ['academy', 'field', 'academic_year', 'organisation', 'study_phase']

    fieldsets = (
        ('Kursdaten', {
            'fields': ('course_nr', 'academic_year', 'study_phase')
        }),
        ('Forschungsphasen', {
            'fields': ('pa1_phase', 'pa2_phase', 'ba_phase')
        }),
        ('Zuordnung', {
            'fields': ('academy', 'field', 'organisation')
        }),
    )

    def student_count(self, obj):
        count = obj.student_count
        return f"{count} Student{'en' if count != 1 else ''}"
    student_count.short_description = 'Studenten'
