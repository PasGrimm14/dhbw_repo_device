from django.db import models
from django.core.exceptions import ValidationError
from .managers import *


class StudyAcademy(models.Model):
    """
    Akademie/Standort (study_academies)
    z.B. DHBW Stuttgart, DHBW Karlsruhe
    """
    academy_name = models.CharField('Akademiename', max_length=30)
    abbreviation = models.CharField('Abkürzung', max_length=20, blank=True, null=True, unique=True)

    class Meta:
        db_table = 'study_academies'
        verbose_name = 'Akademie'
        verbose_name_plural = 'Akademien'
        ordering = ['academy_name']

    def __str__(self):
        return self.academy_name
    
    objects = StudyAcademyManager()


class StudyProgram(models.Model):
    """
    Studiengang (study_study)
    z.B. Wirtschaftsinformatik, Informatik, BWL
    """
    study_progr = models.CharField('Studiengang', max_length=50)
    abbreviation = models.CharField('Abkürzung', max_length=20, blank=True, null=True, unique=True)

    class Meta:
        db_table = 'study_study'
        verbose_name = 'Studiengang'
        verbose_name_plural = 'Studiengänge'
        ordering = ['study_progr']

    def __str__(self):
        return self.study_progr
    
    objects = StudyProgramManager()


class StudyField(models.Model):
    """
    Studienrichtung (study_field)
    z.B. Application Management, Software Engineering
    """
    study = models.ForeignKey(
        StudyProgram,
        on_delete=models.CASCADE,
        related_name='fields',
        verbose_name='Studiengang'
    )
    studyfield = models.CharField('Studienrichtung', max_length=30)
    abbreviation = models.CharField('Abkürzung', max_length=20, blank=True, null=True)

    class Meta:
        db_table = 'study_field'
        verbose_name = 'Studienrichtung'
        verbose_name_plural = 'Studienrichtungen'
        ordering = ['study', 'studyfield']

    def __str__(self):
        return f"{self.study.study_progr} - {self.studyfield}"
    
    objects = StudyFieldManager()


class StudyOrganisation(models.Model):
    """
    Organisation (study_organisation)
    z.B. DHBW, Berufsakademie
    """
    name = models.CharField('Organisationsname', max_length=100)

    class Meta:
        db_table = 'study_organisation'
        verbose_name = 'Organisation'
        verbose_name_plural = 'Organisationen'
        ordering = ['name']

    def __str__(self):
        return self.name
    
    objects = StudyOrganisationManager()


class StudySemester(models.Model):
    """
    Semester (study_semester)
    Ein konkretes Semester mit Start- und Enddatum
    """
    TYPE_CHOICES = [
        ('Praxis', 'Praxisphase'),
        ('Theorie', 'Theoriephase'),
    ]

    CYCLE_CHOICES = [
        ('A', 'A-Zyklus'),
        ('B', 'B-Zyklus'),
        ('X', 'Unabhängig'),
    ]

    SPECIAL_CHOICES = [
        ('First', 'Erstes Semester'),
        ('Last', 'Letztes Semester'),
    ]

    name = models.CharField('Name', max_length=100)
    name_short = models.CharField('Kurzname', max_length=20)
    start_date = models.DateField('Startdatum')
    end_date = models.DateField('Enddatum')
    type = models.CharField('Typ', max_length=10, choices=TYPE_CHOICES)
    cycle = models.CharField('Zyklus', max_length=1, choices=CYCLE_CHOICES)
    special = models.CharField(
        'Besonderheit',
        max_length=5,
        choices=SPECIAL_CHOICES,
        blank=True,
        null=True
    )

    class Meta:
        db_table = 'study_semester'
        verbose_name = 'Semester'
        verbose_name_plural = 'Semester'
        ordering = ['start_date']

    def __str__(self):
        return f"{self.name_short} ({self.get_type_display()})"

    def clean(self):
        """Validierung: Enddatum muss nach Startdatum liegen"""
        if self.start_date and self.end_date:
            if self.end_date <= self.start_date:
                raise ValidationError('Enddatum muss nach dem Startdatum liegen')

    @property
    def is_active(self):
        """Prüft ob das Semester aktuell läuft"""
        from django.utils import timezone
        today = timezone.localdate()
        return self.start_date <= today <= self.end_date

    @property
    def duration_days(self):
        """Dauer des Semesters in Tagen"""
        return (self.end_date - self.start_date).days
    
    objects = StudySemesterManager()


class StudyPhase(models.Model):
    """
    Studienphase (study_phase)
    Enthält den Semesterplan eines Jahrgangs (ausgelagert aus StudyYear).
    Jeder StudyCourse wird einer StudyPhase zugeordnet.
    """
    name = models.CharField('Bezeichnung', max_length=50)

    # Semester 1
    semester_id1t = models.ForeignKey(
        StudySemester,
        on_delete=models.PROTECT,
        related_name='phase_1t',
        verbose_name='1. Semester Theorie'
    )
    semester_id1p = models.ForeignKey(
        StudySemester,
        on_delete=models.PROTECT,
        related_name='phase_1p',
        verbose_name='1. Semester Praxis'
    )

    # Semester 2
    semester_id2t = models.ForeignKey(
        StudySemester,
        on_delete=models.PROTECT,
        related_name='phase_2t',
        verbose_name='2. Semester Theorie'
    )
    semester_id2p = models.ForeignKey(
        StudySemester,
        on_delete=models.PROTECT,
        related_name='phase_2p',
        verbose_name='2. Semester Praxis'
    )

    # Semester 3
    semester_id3t = models.ForeignKey(
        StudySemester,
        on_delete=models.PROTECT,
        related_name='phase_3t',
        verbose_name='3. Semester Theorie'
    )
    semester_id3p = models.ForeignKey(
        StudySemester,
        on_delete=models.PROTECT,
        related_name='phase_3p',
        verbose_name='3. Semester Praxis'
    )

    # Semester 4
    semester_id4t = models.ForeignKey(
        StudySemester,
        on_delete=models.PROTECT,
        related_name='phase_4t',
        verbose_name='4. Semester Theorie'
    )
    semester_id4p = models.ForeignKey(
        StudySemester,
        on_delete=models.PROTECT,
        related_name='phase_4p',
        verbose_name='4. Semester Praxis'
    )

    # Semester 5
    semester_id5t = models.ForeignKey(
        StudySemester,
        on_delete=models.PROTECT,
        related_name='phase_5t',
        verbose_name='5. Semester Theorie'
    )
    semester_id5p = models.ForeignKey(
        StudySemester,
        on_delete=models.PROTECT,
        related_name='phase_5p',
        verbose_name='5. Semester Praxis'
    )

    # Semester 6
    semester_id6t = models.ForeignKey(
        StudySemester,
        on_delete=models.PROTECT,
        related_name='phase_6t',
        verbose_name='6. Semester Theorie'
    )
    semester_id6p = models.ForeignKey(
        StudySemester,
        on_delete=models.PROTECT,
        related_name='phase_6p',
        verbose_name='6. Semester Praxis'
    )

    class Meta:
        db_table = 'study_phase'
        verbose_name = 'Studienphase'
        verbose_name_plural = 'Studienphasen'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_all_semesters(self):
        """Gibt alle Semester der Phase zurück"""
        return [
            self.semester_id1t, self.semester_id1p,
            self.semester_id2t, self.semester_id2p,
            self.semester_id3t, self.semester_id3p,
            self.semester_id4t, self.semester_id4p,
            self.semester_id5t, self.semester_id5p,
            self.semester_id6t, self.semester_id6p,
        ]

    def get_current_semester(self):
        """Gibt das aktuell laufende Semester zurück (falls vorhanden)"""
        for semester in self.get_all_semesters():
            if semester.is_active:
                return semester
        return None
    
    objects = StudyPhaseManager()


class StudyYear(models.Model):
    """
    Studienjahr (study_year)
    Ein Jahrgang, z.B. 2021. Kurse werden über study_phase mit dem Semesterplan verknüpft.
    """
    year_name = models.CharField('Jahrgangsbezeichnung', max_length=20)

    class Meta:
        db_table = 'study_year'
        verbose_name = 'Studienjahr'
        verbose_name_plural = 'Studienjahre'
        ordering = ['-year_name']

    def __str__(self):
        return self.year_name
    
    objects = StudyYearManager()


class StudyRegulation(models.Model):
    """
    Prüfungsordnung (study_regulations)
    Definiert die gültige Prüfungsordnung eines Studiengangs ab einem bestimmten Datum.
    """
    name = models.CharField('Bezeichnung', max_length=100)
    start_date = models.DateField('Gültig ab')
    study = models.ForeignKey(
        StudyProgram,
        on_delete=models.PROTECT,
        related_name='regulations',
        verbose_name='Studiengang'
    )
    unit_pa1 = models.ForeignKey(
        'lectures.ModuleUnit',
        on_delete=models.SET_NULL,
        related_name='regulations_pa1',
        blank=True,
        null=True,
        verbose_name='PA1-Einheit'
    )
    unit_pa2 = models.ForeignKey(
        'lectures.ModuleUnit',
        on_delete=models.SET_NULL,
        related_name='regulations_pa2',
        blank=True,
        null=True,
        verbose_name='PA2-Einheit'
    )
    unit_ba = models.ForeignKey(
        'lectures.ModuleUnit',
        on_delete=models.SET_NULL,
        related_name='regulations_ba',
        blank=True,
        null=True,
        verbose_name='BA-Einheit'
    )

    class Meta:
        db_table = 'study_regulations'
        verbose_name = 'Prüfungsordnung'
        verbose_name_plural = 'Prüfungsordnungen'
        ordering = ['study', 'start_date']

    def __str__(self):
        return f"{self.name} ({self.study.study_progr})"
    
    objects = StudyRegulationManager()


class StudyCourse(models.Model):
    """
    Kurs (study_courses)
    Ein konkreter Kurs, z.B. TINF2021A
    """
    academy = models.ForeignKey(
        StudyAcademy,
        on_delete=models.PROTECT,
        related_name='courses',
        verbose_name='Akademie'
    )
    field = models.ForeignKey(
        StudyField,
        on_delete=models.PROTECT,
        related_name='courses',
        blank=True,
        null=True,
        verbose_name='Studienrichtung'
    )
    course_nr = models.CharField('Kursnummer', max_length=20)
    academic_year = models.ForeignKey(
        StudyYear,
        on_delete=models.PROTECT,
        related_name='courses',
        verbose_name='Jahrgang'
    )
    organisation = models.ForeignKey(
        StudyOrganisation,
        on_delete=models.PROTECT,
        related_name='courses',
        verbose_name='Organisation'
    )
    study_phase = models.ForeignKey(
        StudyPhase,
        on_delete=models.PROTECT,
        related_name='courses',
        blank=True,
        null=True,
        verbose_name='Studienphase'
    )

    # Forschungsphasen dieses Kurses
    pa1_phase = models.ForeignKey(
        'researches.ResearchPhase',
        on_delete=models.SET_NULL,
        related_name='study_courses_pa1',
        blank=True,
        null=True,
        verbose_name='PA1-Phase'
    )
    pa2_phase = models.ForeignKey(
        'researches.ResearchPhase',
        on_delete=models.SET_NULL,
        related_name='study_courses_pa2',
        blank=True,
        null=True,
        verbose_name='PA2-Phase'
    )
    ba_phase = models.ForeignKey(
        'researches.ResearchPhase',
        on_delete=models.SET_NULL,
        related_name='study_courses_ba',
        blank=True,
        null=True,
        verbose_name='BA-Phase'
    )
    study_regulation = models.ForeignKey(
        StudyRegulation,
        on_delete=models.SET_NULL,
        related_name='courses',
        blank=True,
        null=True,
        verbose_name='Prüfungsordnung'
    )
    external_ical_url = models.URLField(
        blank=True,
        null=True,
        help_text="Optional URL for an external iCal source used to sync this study courses schedule.",
    )
    external_ical_last_sync_at = models.DateTimeField(null=True, blank=True)


    class Meta:
        db_table = 'study_courses'
        verbose_name = 'Kurs'
        verbose_name_plural = 'Kurse'
        ordering = ['course_nr']

    def __str__(self):
        return self.course_nr

    @property
    def full_name(self):
        """Vollständiger Kursname mit Akademie"""
        return f"{self.course_nr} - {self.academy.academy_name}"

    @property
    def student_count(self):
        """Anzahl der Studenten in diesem Kurs"""
        return self.students.count()
    
    objects = StudyCourseManager()
