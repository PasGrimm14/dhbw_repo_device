from django.contrib import admin
from .models import Module, ModuleUnit, Grade


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ['module_nr', 'name', 'credits', 'study', 'field', 'unit_count']
    list_filter = ['study', 'field', 'credits']
    search_fields = ['module_nr', 'name']
    raw_id_fields = ['study', 'field']
    ordering = ['module_nr']
    
    fieldsets = (
        ('Modul', {
            'fields': ('module_nr', 'name', 'credits')
        }),
        ('Zuordnung', {
            'fields': ('study', 'field')
        }),
    )
    
    def unit_count(self, obj):
        return obj.unit_count
    unit_count.short_description = 'Anzahl Veranstaltungen'


@admin.register(ModuleUnit)
class ModuleUnitAdmin(admin.ModelAdmin):
    list_display = [
        'unit_nr',
        'unit_name_short',
        'unit_name',
        'module',
        'units',
        'semester_nr',
        'grade_count'
    ]
    list_filter = ['semester_nr', 'module']
    search_fields = ['unit_nr', 'unit_name', 'unit_name_short', 'module__name']
    raw_id_fields = ['module']
    ordering = ['module', 'semester_nr', 'unit_nr']
    
    fieldsets = (
        ('Veranstaltung', {
            'fields': ('module', 'unit_nr', 'unit_name', 'unit_name_short')
        }),
        ('Details', {
            'fields': ('units', 'semester_nr')
        }),
    )
    
    def grade_count(self, obj):
        return obj.grades.count()
    grade_count.short_description = 'Anzahl Noten'


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = [
        'get_student_name',
        'get_matri_nr',
        'module',
        'unit',
        'grade',
        'passed',
        'attempt',
        'grade_text'
    ]
    list_filter = ['passed', 'attempt', 'grade', 'module']
    search_fields = [
        'student__matri_nr',
        'student__person__firstname',
        'student__person__lastname',
        'module__module_nr',
        'module__name'
    ]
    raw_id_fields = ['student', 'module', 'unit']
    ordering = ['student', 'module']
    
    fieldsets = (
        ('Student', {
            'fields': ('student',)
        }),
        ('Prüfung', {
            'fields': ('module', 'unit', 'attempt')
        }),
        ('Ergebnis', {
            'fields': ('grade', 'passed')
        }),
    )
    
    def get_student_name(self, obj):
        return obj.student.person.get_short_name()
    get_student_name.short_description = 'Student'
    
    def get_matri_nr(self, obj):
        return obj.student.matri_nr
    get_matri_nr.short_description = 'Matrikel-Nr.'
    
    def grade_text(self, obj):
        return obj.grade_text
    grade_text.short_description = 'Note (Text)'
    
    # Farbe für bestandene/nicht bestandene Noten
    def get_list_display_links(self, request, list_display):
        return ['get_student_name']
    
    def passed(self, obj):
        if obj.passed:
            return '✓ Bestanden'
        return '✗ Nicht bestanden'
    passed.short_description = 'Status'
