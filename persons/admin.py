from django.contrib import admin
from .models import Person, Student, Personnel, Company, PersonnelOrganisation


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'mail_main', 'tel_main', 'role_now', 'gender','user']
    list_filter = ['role_now', 'gender']
    search_fields = ['firstname', 'lastname', 'mail_main']
    ordering = ['lastname', 'firstname']
    
    fieldsets = (
        ('Persönliche Daten', {
            'fields': ('title', 'firstname', 'lastname', 'birthday', 'gender')
        }),
        ('Kontaktdaten', {
            'fields': ('mail_main', 'tel_main')
        }),
        ('Anrede', {
            'fields': ('salutation_short', 'salutation_full'),
            'classes': ('collapse',)
        }),
        ('System', {
            'fields': ('role_now', 'user')
        }),
    )
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Name'


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['matri_nr', 'get_person_name', 'get_email', 'course', 'field', 'company']
    list_filter = ['course', 'field']
    search_fields = ['matri_nr', 'person__firstname', 'person__lastname', 'person__mail_main']
    raw_id_fields = ['person', 'company_person']
    autocomplete_fields = ['course', 'field', 'company']
    ordering = ['matri_nr']
    
    fieldsets = (
        ('Student', {
            'fields': ('matri_nr', 'person')
        }),
        ('Studium', {
            'fields': ('course', 'field')
        }),
        ('Unternehmen', {
            'fields': ('company', 'company_person')
        }),
    )
    
    def get_person_name(self, obj):
        return obj.person.get_short_name()
    get_person_name.short_description = 'Name'
    
    def get_email(self, obj):
        return obj.person.mail_main
    get_email.short_description = 'E-Mail'


class PersonnelOrganisationInline(admin.TabularInline):
    model = PersonnelOrganisation
    extra = 1
    autocomplete_fields = ['organisation']
    verbose_name = 'Organisation & Rolle'
    verbose_name_plural = 'Organisationen & Rollen'


@admin.register(Personnel)
class PersonnelAdmin(admin.ModelAdmin):
    list_display = ['personnel_nr', 'get_person_name', 'get_email', 'actant_type', 'get_role']
    list_filter = ['actant_type', 'person__role_now']
    search_fields = ['personnel_nr', 'person__firstname', 'person__lastname', 'person__mail_main']
    raw_id_fields = ['person']
    ordering = ['personnel_nr']
    inlines = [PersonnelOrganisationInline]

    fieldsets = (
        ('Personal', {
            'fields': ('personnel_nr', 'person', 'actant_type')
        }),
    )

    def get_person_name(self, obj):
        return obj.person.get_short_name()
    get_person_name.short_description = 'Name'

    def get_email(self, obj):
        return obj.person.mail_main
    get_email.short_description = 'E-Mail'

    def get_role(self, obj):
        return obj.person.get_role_now_display()
    get_role.short_description = 'Rolle'


@admin.register(PersonnelOrganisation)
class PersonnelOrganisationAdmin(admin.ModelAdmin):
    list_display = ['personnel', 'organisation', 'role']
    list_filter = ['role', 'organisation']
    search_fields = [
        'personnel__person__firstname',
        'personnel__person__lastname',
        'organisation__name',
    ]
    autocomplete_fields = ['organisation']
    ordering = ['organisation', 'role']


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = [
        'name', 
        'get_short_address', 
        'tel_main', 
        'mail_main',
        'webpage_link',
        'student_count'
    ]
    list_filter = ['country', 'state', 'city']
    search_fields = ['name', 'city', 'postal_code', 'company_nr']
    ordering = ['name']
    
    fieldsets = (
        ('Unternehmensdaten', {
            'fields': ('company_nr', 'adressform', 'name')
        }),
        ('Adresse', {
            'fields': ('street', 'district', 'postal_code', 'city', 'state', 'country')
        }),
        ('Kontaktdaten', {
            'fields': ('tel_main', 'mail_main', 'mail_person', 'webpage')
        }),
    )
    
    def get_short_address(self, obj):
        return obj.get_short_address()
    get_short_address.short_description = 'Ort'
    
    def webpage_link(self, obj):
        if obj.webpage:
            return f'<a href="{obj.webpage}" target="_blank">🔗 Webseite</a>'
        return '-'
    webpage_link.short_description = 'Webseite'
    webpage_link.allow_tags = True
    
    def student_count(self, obj):
        count = obj.student_count
        return f"{count} Student{'en' if count != 1 else ''}"
    student_count.short_description = 'Studenten'