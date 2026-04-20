from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator
from django.core.validators import EmailValidator
from organization.models import StudyCourse
from .managers import PersonnelManager, StudentManager, PersonManager, CompanyManager

class Person(models.Model):
    """
    Basis-Modell für alle Personen im System
    """
    GENDER_CHOICES = [
        ('M', 'Männlich'),
        ('F', 'Weiblich'),
        ('D', 'Divers'),
    ]
    
    ROLE_CHOICES = [
        ('ST', 'Student'),
        ('MA', 'Mitarbeiter'),
        ('DOZ', 'Dozent'),
        ('CO', 'Company'),
        ('COAS', 'Company Assessor'),
        ('TEST', 'Test'),
    ]
    
    title = models.CharField('Titel', max_length=30, blank=True, null=True)
    firstname = models.CharField('Vorname', max_length=50)
    lastname = models.CharField('Nachname', max_length=50)
    birthday = models.DateField('Geburtstag', blank=True, null=True)
    gender = models.CharField('Geschlecht', max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    salutation_short = models.CharField('Anrede (kurz)', max_length=50, blank=True, null=True)
    salutation_full = models.CharField('Anrede (voll)', max_length=150, blank=True, null=True)
    mail_main = models.EmailField('Haupt-E-Mail', max_length=200, blank=True, null=True)
    tel_main = models.CharField('Haupt-Telefon', max_length=30, blank=True, null=True)
    role_now = models.CharField('Aktuelle Rolle', max_length=10, choices=ROLE_CHOICES)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='person',
        verbose_name='Benutzer-Account',
    )

    class Meta:
        db_table = 'persons'
        verbose_name = 'Person'
        verbose_name_plural = 'Personen'
        ordering = ['lastname', 'firstname']
    
    def __str__(self):
        if self.title:
            return f"{self.title} {self.firstname} {self.lastname}"
        return f"{self.firstname} {self.lastname}"
    
    def get_full_name(self):
        """Gibt den vollständigen Namen zurück"""
        parts = [self.title, self.firstname, self.lastname]
        return ' '.join(filter(None, parts))
    
    def get_short_name(self):
        """Gibt Vorname und Nachname zurück"""
        return f"{self.firstname} {self.lastname}"
    
    def get_study_courses(self, role=None):
        # Student
        if self.role_now == 'ST':
            if role and role != 'student':
                return StudyCourse.objects.none()
            return StudyCourse.objects.filter(
                pk=self.student_profile.course.pk
            )

        # Mitarbeiter
        if self.role_now == 'MA':
            orga_roles = self.personnel_profile.organisation_roles.all()
            if role:
                orga_roles = orga_roles.filter(role=role)
            courses = (orga_roles.values_list("organisation__courses", flat=True))
            return StudyCourse.objects.filter(pk__in=courses).distinct()

        return StudyCourse.objects.none()
    
    def get_study_courses_with_roles(self):
        result = []

        # Student
        if self.role_now == 'ST':
            result.append({
                "course": self.student_profile.course,
                "role": "student"
            })
            return result

        # Mitarbeiter (SGL, SGS, SGM ...)
        if self.role_now == 'MA':
            for orga in self.personnel_profile.organisation_roles.all():
                for course in orga.organisation.courses.all():
                    result.append({
                        "course": course,
                        "role": orga.role
                    })

        return result
    
    objects = PersonManager()


class Company(models.Model):
    """
    Unternehmen/Partnerunternehmen
    """
    company_nr = models.IntegerField(
        'Unternehmensnummer',
        unique=True,
        null=True,
        blank=True
    )
    adressform = models.CharField(
        'Adressform',
        max_length=300,
        help_text='z.B. Herrn, Frau, Firma'
    )
    name = models.CharField('Unternehmensname', max_length=300)
    street = models.CharField('Straße', max_length=400, blank=True, null=True)
    district = models.CharField('Bezirk/Ortsteil', max_length=300, blank=True, null=True)
    postal_code = models.CharField('PLZ', max_length=10, blank=True, null=True)
    city = models.CharField('Stadt', max_length=200, blank=True, null=True)
    state = models.CharField('Bundesland', max_length=200, blank=True, null=True)
    country = models.CharField('Land', max_length=200, blank=True, null=True)
    tel_main = models.CharField('Haupt-Telefon', max_length=200, blank=True, null=True)
    mail_main = models.EmailField(
        'Haupt-E-Mail',
        max_length=200,
        blank=True,
        null=True,
        validators=[EmailValidator()]
    )
    mail_person = models.EmailField(
        'Ansprechpartner-E-Mail',
        max_length=200,
        blank=True,
        null=True,
        validators=[EmailValidator()]
    )
    webpage = models.URLField('Webseite', max_length=300, blank=True, null=True)
    
    class Meta:
        db_table = 'companies'
        verbose_name = 'Unternehmen'
        verbose_name_plural = 'Unternehmen'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_full_address(self):
        """Gibt die vollständige Adresse zurück"""
        parts = [
            self.street,
            self.district,
            f"{self.postal_code} {self.city}" if self.postal_code and self.city else self.city,
            self.state,
            self.country
        ]
        return ', '.join(filter(None, parts))
    
    def get_short_address(self):
        """Gibt PLZ und Stadt zurück"""
        if self.postal_code and self.city:
            return f"{self.postal_code} {self.city}"
        return self.city or "-"
    
    @property
    def student_count_all(self):
        """Anzahl der Studenten bei diesem Unternehmen"""
        return self.students.count()
    
    @property
    def student_count(self, user):
        """Anzahl der Studenten bei diesem Unternehmen"""
        return self.students.for_user(user).count()
    
    @property
    def has_contact_info(self):
        """Prüft ob Kontaktdaten vorhanden sind"""
        return bool(self.tel_main or self.mail_main or self.mail_person)
    
    objects = CompanyManager()
    

class Student(models.Model):
    """
    Studierenden-Daten
    """
    person = models.OneToOneField(
        Person, 
        on_delete=models.CASCADE, 
        related_name='student_profile',
        verbose_name='Person'
    )
    matri_nr = models.IntegerField(
        'Matrikelnummer', 
        unique=True,
        validators=[MinValueValidator(1)]
    )    
    #course_id = models.IntegerField('Kurs ID', null=True, blank=True)
    #field_id = models.IntegerField('Feld ID', null=True, blank=True)
    course = models.ForeignKey(
        'organization.StudyCourse',  # Forward reference
        on_delete=models.PROTECT,
        related_name='students', # Reverse-Lookup
        verbose_name='Kurs'
    )
    field = models.ForeignKey(
        'organization.StudyField',  # Forward reference
        on_delete=models.PROTECT,
        related_name='students',
        verbose_name='Studienrichtung'
    )
    company = models.ForeignKey(
        'persons.Company',  # Forward reference
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='students',
        verbose_name='Unternehmen'
    )
    company_person = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='supervised_students',
        verbose_name='Ansprechpartner im Unternehmen'
    )
    
    class Meta:
        db_table = 'students'
        verbose_name = 'Student'
        verbose_name_plural = 'Studenten'
        ordering = ['matri_nr']
    
    def __str__(self):
        return f"{self.matri_nr} - {self.person.get_short_name()}"
    
    @property
    def full_name(self):
        return self.person.get_full_name()
    
    @property
    def email(self):
        return self.person.mail_main
    
    objects = StudentManager()


class Personnel(models.Model):
    """
    Personal/Mitarbeiter/Dozenten
    """
    personnel_nr = models.IntegerField(
        'Personalnummer',
        unique=True,
        null=True,
        blank=True,
        validators=[MinValueValidator(1)]
    )
    person = models.OneToOneField(
        Person,
        on_delete=models.CASCADE,
        related_name='personnel_profile',
        verbose_name='Person'
    )
    actant_type = models.IntegerField(
        'Aktantentyp',
        help_text='Typ des Aktanten (z.B. Dozent, Verwaltung, etc.)'
    )
    organisations = models.ManyToManyField(
        'organization.StudyOrganisation',
        through='PersonnelOrganisation',
        blank=True,
        related_name='personnel',
        verbose_name='Studiengangsorganisationen',
    )

    class Meta:
        db_table = 'personnel'
        verbose_name = 'Personal'
        verbose_name_plural = 'Personal'
        ordering = ['personnel_nr']

    def __str__(self):
        if self.personnel_nr:
            return f"{self.personnel_nr} - {self.person.get_short_name()}"
        return self.person.get_short_name()

    @property
    def full_name(self):
        return self.person.get_full_name()

    @property
    def email(self):
        return self.person.mail_main
    
    objects = PersonnelManager()


class PersonnelOrganisation(models.Model):
    """
    Zuordnung Personal ↔ Organisation mit Rolle (personnel_organisations)
    """
    ROLE_CHOICES = [
        ('sgl', 'Studiengangsleitung'),
        ('sgs', 'Studiengangssekretariat'),
        ('sgm', 'Studiengangsmanagement'),
        ('acc', 'Wiss. MA'),
        ('hilfs', 'Hilfskraft'),
        ('lab', 'Labor'),
        ('doz', 'Dozent'),
    ]

    personnel = models.ForeignKey(
        Personnel,
        on_delete=models.CASCADE,
        related_name='organisation_roles',
        verbose_name='Personal'
    )
    organisation = models.ForeignKey(
        'organization.StudyOrganisation',
        on_delete=models.CASCADE,
        related_name='personnel_roles',
        verbose_name='Organisation',
        db_column='studyorganisation_id'
    )
    role = models.CharField(
        'Rolle',
        max_length=10,
        choices=ROLE_CHOICES,
        blank=True,
        null=True,
    )

    class Meta:
        db_table = 'personnel_organisations'
        verbose_name = 'Personal-Organisation'
        verbose_name_plural = 'Personal-Organisationen'
        ordering = ['organisation', 'role', 'personnel']
        unique_together = [['personnel', 'organisation', 'role']]

    def __str__(self):
        role_display = self.get_role_display() if self.role else '–'
        return f"{self.personnel} @ {self.organisation} ({role_display})"
    

