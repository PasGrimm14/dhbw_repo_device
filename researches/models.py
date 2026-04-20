from datetime import timedelta

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from .managers import *
from enum import StrEnum

class ResearchStatus(StrEnum):
        NOT_STARTED = "Themeneinreichung"
        CHOOSE_SUPERVISOR = "Wahl der Betreuung"
        ASSIGN_SUPERVISOR = "Zuordnung der Betreuung"
        WRITING = "Schreiben"
        RATE_SUPERVISOR = "Bewertung"
        COMPLETED = "Abgeschlossen"

class ResearchPhase(models.Model):
    """
    Forschungsphase (research_phase)
    Definiert eine Abschlussarbeitsphase, z.B. PA1, PA2, BA.
    Jede Research wird einer ResearchPhase zugeordnet.
    """

    class HandlingType(models.TextChoices):
        ALL_TO_SELECTED = 'all-to-selected', 'Potenzielle Betreuungen bekommen alle Arbeiten'
        SELECTED_TO_SELECTED = 'selected-to-selected', 'Arbeiten werden nur bestimmten Betreuungen vorgeschlagen'

    name = models.CharField('Bezeichnung', max_length=20)
    submission_date = models.DateField('Datum Einreichung des Themas', blank=False, null=False)
    offer_date = models.DateField(
        'Rückmeldedatum der potenziellen wiss. Betreuungen',
        blank=True,
        null=True,
        help_text='Standard: start_date minus 2 Wochen'
    )
    start_date = models.DateField('Startdatum der Bearbeitungszeit', blank=False, null=False)
    end_date = models.DateField('Abgabedatum der Arbeiten', blank=False, null=False)
    feedback_date = models.DateField('Abgabedatum der Bewertungen', blank=True, null=True)
    student_wishes = models.BooleanField(
        'Studentenwünsche',
        help_text='Können Studenten Betreuerwünsche angeben?'
    )
    handling_type = models.CharField(
        'Handling-Typ',
        max_length=25,
        choices=HandlingType.choices,
    )

    class Meta:
        db_table = 'research_phase'
        verbose_name = 'Forschungsphase'
        verbose_name_plural = 'Forschungsphasen'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.start_date and not self.offer_date:
            self.offer_date = self.start_date - timedelta(weeks=2)
        super().save(*args, **kwargs)

    def clean(self):
        if self.start_date and self.end_date and self.end_date <= self.start_date:
            raise ValidationError('Enddatum muss nach dem Startdatum liegen')
    
    @property
    def status_display(self):
        """Status als Text"""
        today = timezone.localdate()
        if today < self.submission_date:
            return ResearchStatus.NOT_STARTED
        if self.offer_date and today < self.offer_date:
            return ResearchStatus.CHOOSE_SUPERVISOR
        if today < self.start_date:
            return ResearchStatus.ASSIGN_SUPERVISOR
        if today < self.end_date:
            return ResearchStatus.WRITING
        if self.feedback_date and today < self.feedback_date:
            return ResearchStatus.RATE_SUPERVISOR
        return ResearchStatus.COMPLETED
    
    def get_dates(self):
        dates = [
            ("Einreichungsdatum", self.submission_date, "Ab diesem Datum können Arbeiten eingereicht werden."),
            ("Angebotsdatum", self.offer_date, "Ab diesem Datum können Betreuerangebote eingesehen bzw. ausgewählt werden."),
            ("Startdatum", self.start_date, "Ab diesem Datum beginnt die offizielle Bearbeitungszeit."),
            ("Enddatum", self.end_date, "Bis zu diesem Datum muss die Arbeit abgegeben werden."),
            ("Feedbackdatum", self.feedback_date, "Ab diesem Datum können Bewertungen eingesehen oder abgegeben werden."),
        ]    
        return [
            {"label": label, "date": date, "description": desc}
            for label, date, desc in dates
            if date
        ]
    
    objects = ResearchPhaseManager()


class Research(models.Model):
    """
    Forschungsarbeit/Abschlussarbeit (researches)
    Bachelor-/Projektarbeiten der Studenten
    """
    unit = models.ForeignKey(
        'lectures.ModuleUnit',
        on_delete=models.PROTECT,
        related_name='researches',
        verbose_name='Lehrveranstaltung'
    )
    student = models.ForeignKey(
        'persons.Student',
        on_delete=models.CASCADE,
        related_name='researches',
        verbose_name='Student'
    )
    assessor_scien = models.ForeignKey(
        'persons.Personnel',
        on_delete=models.SET_NULL,
        related_name='researches_acad',
        blank=True,
        null=True,
        verbose_name='Betreuung (wissenschaftlich)',
        db_column='assessor_scien_id'
    )
    assessor_oper = models.ForeignKey(
        'persons.Person',
        on_delete=models.SET_NULL,
        related_name='researches_oper',
        blank=True,
        null=True,
        verbose_name='Betreuung (betrieblich)',
        db_column='assessor_oper_id'
    )
    
    # Arbeitsinhalte
    title = models.TextField('Titel', blank=True, null=True)
    problem = models.TextField('Problemstellung', blank=True, null=True)
    goal = models.TextField('Zielsetzung', blank=True, null=True)
    methodology = models.TextField('Methodik', blank=True, null=True)
    
    # Status und Termine
    approved_oper = models.BooleanField(
        'Vom Betrieb genehmigt',
        default=False,
        db_column='approved_oper'
    )
    approved_scien = models.BooleanField(
        'Von wiss. Betreuung genehmigt',
        default=False,
        db_column='approved_scien'
    )
    approved_orga = models.BooleanField(
        'Von Studiengangsleitung genehmigt',
        default=False,
        db_column='approved_orga'
    )
    topic_submitted_date = models.DateField(
        'Thema eingereicht am',
        blank=True,
        null=True,
        db_column='topic_submitted_date'
    )
    topic_submit_deadline = models.DateField(
        'Thema einreichen bis',
        db_column='topic_submit_deadline'
    )
    start_date = models.DateField('Startdatum', db_column='start_date')
    end_date = models.DateField('Abgabefrist', db_column='end_date')
    
    # Unternehmens-Betreuer Info
    company_context = models.CharField(
        'Firma des Unternehmensbetreuers',
        max_length=200,
        blank=True,
        null=True,
        db_column='company_context'
    )
    comment = models.CharField(
        'Kommentar (z.B. Betreuerwunsch)',
        max_length=200,
        blank=True,
        null=True,
        db_column='comment'
    )
    research_phase = models.ForeignKey(
        ResearchPhase,
        on_delete=models.SET_NULL,
        related_name='researches',
        blank=True,
        null=True,
        verbose_name='Forschungsphase'
    )

    class Meta:
        db_table = 'researches'
        verbose_name = 'Forschungsarbeit'
        verbose_name_plural = 'Forschungsarbeiten'
        ordering = ['-start_date']
        unique_together = [['student', 'unit', 'start_date']]
    
    def __str__(self):
        if self.title:
            return f"{self.student.person.get_short_name()} - {self.title[:50]}"
        return f"{self.student.person.get_short_name()} - {self.unit}"
    
    def clean(self):
        """Validierung"""
        if self.end_date and self.start_date:
            if self.end_date <= self.start_date:
                raise ValidationError('Abgabefrist muss nach dem Startdatum liegen')
    
    @property
    def days_remaining(self):
        """Verbleibende Tage bis zur Abgabe"""
        if self.end_date:
            delta = self.end_date - timezone.localdate()
            return delta.days
        return None
    
    @property
    def approved_all(self):
        """Status als Text"""
        if not self.approved_oper or not self.approved_scien or not self.approved_orga:
            return False
        return True

    @property
    def status_display(self):
        today = timezone.localdate()
        """Status als Text"""
        if not self.topic_submitted_date and today < self.start_date:
            return "Thema noch in Einreichung"
        if self.topic_submitted_date and today < self.start_date and not self.approved_all:
            return "Thema eingereicht & In Genehmigung"
        if self.topic_submitted_date and today < self.start_date and self.approved_all:
            return "Thema eingereicht & Genehmigt"
        if self.topic_submitted_date and self.approved_all and today > self.start_date and today < self.end_date and self.days_remaining and self.days_remaining <= 7:
            return "Deadline naht"
        if self.topic_submitted_date and self.approved_all and today > self.start_date and today < self.end_date:
            return "In progress"
        if today > self.end_date:
            return "Beendet"
        # Abgegeben
        # Bewertet
        return "XX"
    
    @property
    def duration_days(self):
        """Dauer der Arbeit in Tagen"""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days
        return None
    
    objects = ResearchManager()

    def check_submittable(self):
        """
        Prüft ob alle Pflichtfelder für die Themeneinreichung ausgefüllt sind.
        Gibt eine Liste der fehlenden Felder zurück. Leere Liste = bereit zur Einreichung.
        """
        missing = []

        if self.topic_submit_deadline < timezone.localdate():
            missing.append("Frist vergangen")
            return missing
    
        # Betriebliche Betreuung
        if not self.company_context:
            missing.append("Unternehmen der Betreuung")
    
        if not self.assessor_oper:
            missing.append("Betriebliche Betreuung: Ansprache")
            missing.append("Betriebliche Betreuung: Vorname")
            missing.append("Betriebliche Betreuung: Nachname")
            missing.append("Betriebliche Betreuung: E-Mail")
        else:
            if not self.assessor_oper.gender:
                missing.append("Betriebliche Betreuung: Ansprache")
            if not self.assessor_oper.firstname:
                missing.append("Betriebliche Betreuung: Vorname")
            if not self.assessor_oper.lastname:
                missing.append("Betriebliche Betreuung: Nachname")
            if not self.assessor_oper.mail_main:
                missing.append("Betriebliche Betreuung: E-Mail")
    
        if not self.approved_oper:
            missing.append("Thema vom Betrieb genehmigt")
    
        # Wissenschaftliche Arbeit
        if not self.title:
            missing.append("Titel der Arbeit")
        if not self.problem:
            missing.append("Problemstellung")
        if not self.goal:
            missing.append("Zielsetzung")
        if not self.methodology:
            missing.append("Methodik und Vorgehensweise")
        if not self.title or len(self.title) < 10:
            missing.append("Titel der Arbeit: kürzer als 10 Zeichen")
        if not self.problem or len(self.problem) < 10:
            missing.append("Problemstellung: kürzer als 10 Zeichen")
        if not self.goal or len(self.goal) < 10:
            missing.append("Zielsetzung: kürzer als 10 Zeichen")
        if not self.methodology or len(self.methodology) < 10:
            missing.append("Methodik und Vorgehensweise: kürzer als 10 Zeichen")
    
        return missing


class ResearchAssessorWish(models.Model):
    """
    Betreuerwunsch (research_assessorwish)
    Präferenzen der Betreuer für Anzahl der zu betreuenden Arbeiten
    """
    personnel = models.ForeignKey(
        'persons.Personnel',
        on_delete=models.CASCADE,
        related_name='assessor_wishes',
        verbose_name='Betreuer'
    )
    unit = models.ForeignKey(
        'lectures.ModuleUnit',
        on_delete=models.CASCADE,
        related_name='assessor_wishes',
        verbose_name='Lehrveranstaltung'
    )
    academic_year = models.ForeignKey(
        'organization.StudyYear',
        on_delete=models.CASCADE,
        related_name='assessor_wishes',
        verbose_name='Jahrgang'
    )
    max_count = models.IntegerField(
        'Maximum Anzahl möglicher Betreuungen',
        validators=[MinValueValidator(0)]
    )
    max_count_orga = models.IntegerField(
        'Maximum Anzahl Vergabe laut Orga',
        validators=[MinValueValidator(0)]
    )
    random_sel = models.BooleanField(
        'Zufällige Auswahl',
        default=False,
        help_text='Sollen Studenten zufällig zugewiesen werden?'
    )
    comment = models.TextField('Kommentar')
    submitted_date = models.DateField(
        'Eingereicht am'
    )
    
    class Meta:
        db_table = 'research_assessorwish'
        verbose_name = 'Betreuerwunsch'
        verbose_name_plural = 'Betreuerwünsche'
        ordering = ['academic_year', 'personnel']
        unique_together = [['personnel', 'unit', 'academic_year']]
    
    def __str__(self):
        return f"{self.personnel.person.get_short_name()} - {self.unit.unit_name_short} ({self.max_count})"
    
    def clean(self):
        """Validierung"""
        if self.max_count_orga < self.max_count:
            raise ValidationError('Maximum laut Organisation muss kleiner sein als das Maximum der Betreuung')
    
    @property
    def current_count(self):
        """Aktuelle Anzahl zugewiesener Arbeiten"""
        return Research.objects.filter(
            personnel=self.personnel,
            unit=self.unit
        ).count()
    
    @property
    def is_full(self):
        """Prüft ob Maximum erreicht"""
        return self.current_count >= self.max_count_orga
    
    @property
    def remaining_capacity(self):
        """Verbleibende Kapazität"""
        return max(0, self.max_count_orga - self.current_count)
    
    objects = ResearchAssessorWishManager()


class ResearchMatchWish(models.Model):
    """
    Matching-Wunsch (research_matchwish)
    Präferenzen für die Zuordnung von Betreuern zu Forschungsarbeiten
    """
    research = models.ForeignKey(
        Research,
        on_delete=models.CASCADE,
        related_name='match_wishes',
        verbose_name='Forschungsarbeit'
    )
    person_from = models.ForeignKey(
        'persons.Person',
        on_delete=models.CASCADE,
        related_name='match_wishes_made',
        verbose_name='Von (Person)',
        db_column='person_from_id'
    )
    personnel_who = models.ForeignKey(
        'persons.Personnel',
        on_delete=models.CASCADE,
        related_name='match_wishes_received',
        verbose_name='Gewünschter Betreuer',
        db_column='personnel_who_id'
    )
    priority = models.IntegerField(
        'Priorität',
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(6)],
        help_text='5 = höchste Priorität'
    )
    
    class Meta:
        db_table = 'research_matchwish'
        verbose_name = 'Matching-Wunsch'
        verbose_name_plural = 'Matching-Wünsche'
        ordering = ['research', 'priority']
        unique_together = [['research', 'person_from', 'personnel_who']]
    
    def __str__(self):
        priority_text = f"Prio {self.priority}" if self.priority else "Keine Prio"
        return f"{self.research.student.person.get_short_name()} → {self.personnel_who.person.get_short_name()} ({priority_text})"

    objects = ResearchMatchWishManager()