from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from .managers import ModuleManager, ModuleUnitManager, GradeManager
from organization.models import StudyCourse, StudySemester
from persons.models import Personnel

class Module(models.Model):
    """
    Modul (modules)
    Ein Studienmodul wie "Programmierung 1", "Mathematik", etc.
    """
    module_nr = models.CharField('Modulnummer', max_length=30, unique=True)
    name = models.CharField('Modulname', max_length=200)
    credits = models.IntegerField(
        'ECTS Credits',
        validators=[MinValueValidator(1)]
    )
    study = models.ForeignKey(
        'organization.StudyProgram',
        on_delete=models.PROTECT,
        related_name='modules',
        verbose_name='Studiengang'
    )
    field = models.ForeignKey(
        'organization.StudyField',
        on_delete=models.PROTECT,
        related_name='modules',
        blank=True,
        null=True,
        verbose_name='Studienrichtung'
    )
    regulation = models.ForeignKey(
        'organization.StudyRegulation',
        on_delete=models.PROTECT,
        related_name='modules',
        verbose_name='Prüfungsordnung'
    )

    class Meta:
        db_table = 'modules'
        verbose_name = 'Modul'
        verbose_name_plural = 'Module'
        ordering = ['module_nr']
    
    def __str__(self):
        return f"{self.module_nr} - {self.name}"
    
    @property
    def total_units(self):
        """Gesamtanzahl Units (Summe aller Units des Moduls)"""
        return self.units.aggregate(
            total=models.Sum('units')
        )['total'] or 0
    
    @property
    def unit_count(self):
        """Anzahl der Lehrveranstaltungen"""
        return self.units.count()
    
    objects = ModuleManager()


class ModuleUnit(models.Model):
    """
    Lehrveranstaltung/Teilmodul (module_units)
    Eine konkrete Lehrveranstaltung innerhalb eines Moduls
    """
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name='units',
        verbose_name='Modul',
        to_field='module_nr',
        db_column='ModuleNr'
    )
    unit_nr = models.CharField('Veranstaltungsnummer', max_length=15)
    unit_name = models.CharField('Veranstaltungsname', max_length=200)
    unit_name_short = models.CharField(
        'Kurzname',
        max_length=10,
        blank=True,
        null=True
    )
    units = models.DecimalField(
        'Lehreinheiten',
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    semester_nr = models.IntegerField(
        'Semester-Nr',
        validators=[MinValueValidator(1), MaxValueValidator(6)],
        help_text='Semester in dem die Veranstaltung stattfindet (1-6)'
    )
    
    class Meta:
        db_table = 'module_units'
        verbose_name = 'Lehrveranstaltung'
        verbose_name_plural = 'Lehrveranstaltungen'
        ordering = ['module', 'semester_nr', 'unit_nr']
        unique_together = [['module', 'unit_nr']]
    
    def __str__(self):
        if self.unit_name_short:
            return f"{self.module.module_nr} - {self.unit_name_short}"
        return f"{self.module.module_nr} - {self.unit_name}"
    
    @property
    def full_name(self):
        """Vollständiger Name mit Modulnummer"""
        return f"{self.module.module_nr} {self.unit_nr}: {self.unit_name}"
    
    objects = ModuleUnitManager()


class Grade(models.Model):
    """
    Note (grades)
    Eine Note eines Studenten für ein Modul/eine Lehrveranstaltung
    """
    student = models.ForeignKey(
        'persons.Student',
        on_delete=models.CASCADE,
        related_name='grades',
        verbose_name='Student'
    )
    module = models.ForeignKey(
        Module,
        on_delete=models.PROTECT,
        related_name='grades',
        verbose_name='Modul',
        to_field='module_nr',
        db_column='ModuleNr'
    )
    unit = models.ForeignKey(
        ModuleUnit,
        on_delete=models.PROTECT,
        related_name='grades',
        blank=True,
        null=True,
        verbose_name='Lehrveranstaltung'
    )
    attempt = models.IntegerField(
        'Versuch',
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(3)],
        help_text='Prüfungsversuch (1-3)'
    )
    passed = models.BooleanField('Bestanden', default=True, db_column='Passed')
    grade = models.DecimalField(
        'Note',
        max_digits=2,
        decimal_places=1,
        validators=[MinValueValidator(1.0), MaxValueValidator(5.0)],
        help_text='Note von 1.0 bis 5.0'
    )
    
    class Meta:
        db_table = 'grades'
        verbose_name = 'Note'
        verbose_name_plural = 'Noten'
        ordering = ['student', 'module']
        unique_together = [['student', 'module', 'attempt']]
        indexes = [
            models.Index(fields=['student', 'module']),
        ]
    
    def __str__(self):
        return f"{self.student.person.get_short_name()} - {self.module.module_nr}: {self.grade}"
    
    def clean(self):
        """Validierung"""
        # Wenn nicht bestanden, muss Note >= 4.0 sein
        if not self.passed and self.grade < 4.0:
            raise ValidationError('Wenn nicht bestanden, muss Note >= 4.0 sein')
        
        # Wenn bestanden, muss Note < 4.0 sein (in Deutschland)
        if self.passed and self.grade >= 4.0:
            raise ValidationError('Wenn bestanden, muss Note < 4.0 sein')
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    @property
    def grade_text(self):
        """Note als Text"""
        grade_map = {
            1.0: 'Sehr gut',
            1.3: 'Sehr gut',
            1.7: 'Gut',
            2.0: 'Gut',
            2.3: 'Gut',
            2.7: 'Befriedigend',
            3.0: 'Befriedigend',
            3.3: 'Befriedigend',
            3.7: 'Ausreichend',
            4.0: 'Ausreichend',
            5.0: 'Nicht bestanden',
        }
        return grade_map.get(float(self.grade), str(self.grade))
    
    @property
    def is_final_attempt(self):
        """Prüft ob es der letzte Versuch war"""
        return self.attempt >= 3
    
    @property
    def status_text(self):
        """Status als Text"""
        if self.passed:
            return f"Bestanden ({self.grade})"
        elif self.is_final_attempt:
            return f"Endgültig nicht bestanden ({self.grade})"
        else:
            return f"Nicht bestanden ({self.grade}) - Versuch {self.attempt}"

    objects = GradeManager()

class Room(models.Model):
    name = models.CharField(max_length=100, primary_key=True)
    is_double_bookable = models.BooleanField(
        default=False,
        help_text="Indicates whether this room can be double-booked (e.g., Online, Field Trip)",
    )

    def __str__(self):
        return self.name
    
class Lecture(models.Model):
    unit = models.ForeignKey(ModuleUnit, on_delete=models.PROTECT)
    semester = models.ForeignKey(StudySemester, on_delete=models.CASCADE)
    course = models.ForeignKey(StudyCourse, on_delete=models.CASCADE)
    lecturers = models.ManyToManyField(
        Personnel,
        through='LectureAssignment',
        related_name='lectures',
        blank=True,
    )

    class Meta:
        unique_together = [["unit", "course"]]

    def __str__(self):
        return (
            f"{self.unit.unit_name} - {self.course.course_nr} ({self.semester.name_short})"
        )


class LectureAssignment(models.Model):
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE, related_name='assignments')
    lecturer = models.ForeignKey(Personnel, on_delete=models.PROTECT, related_name='lecture_assignments')
    lectureunits = models.DecimalField(
        'Unterrichtseinheiten (UE)',
        max_digits=3,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    class Meta:
        unique_together = [['lecture', 'lecturer']]

    def __str__(self):
        return f"{self.lecturer} – {self.lecture} ({self.units} UE)"

class Lesson(models.Model):
    room = models.ForeignKey(Room, on_delete=models.PROTECT)
    is_exam = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    lecture = models.ForeignKey(Lecture, on_delete=models.PROTECT)
    lecturer = models.ForeignKey(Personnel, on_delete=models.CASCADE, blank=True, null=True)
    start = models.DateTimeField()
    end = models.DateTimeField()

    def __str__(self):
        from django.utils import timezone
        formatted_start = timezone.localtime(self.start)
        exam_suffix = " [Klausur]" if self.is_exam else ""
        return (
            f"{self.course} - {self.room.name} "
            f"({formatted_start.strftime('%Y-%m-%d %H:%M')}){exam_suffix}"
        )


