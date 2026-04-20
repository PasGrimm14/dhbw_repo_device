from django import forms

from organization.models import StudyOrganisation, StudyRegulation
from django.core.validators import FileExtensionValidator


IMPORT_TYPE_DESCRIPTIONS = {
    'dozenten': (
        'Importiert Dozenten aus einer CSV-Datei (Trennzeichen: Semikolon, Kodierung: Windows-1252). '
        '<br>Pflichtspalten: PERSONALNUMMER, VORNAME, NACHNAME. '
        '<br>Optionale Spalten: ANREDE, TITEL, GEBURTSDATUM, MAIL_HAUPTKONTAKT.'
        '<br>DDV: Reporting > Datenquellen > Lehrbeauftragte > Lehrbeauftragte nach Kategorie > alle Kategorien einmal'
    ),
    'studenten': (
        'Importiert Studenten aus einer CSV-Datei (Trennzeichen: Semikolon, Kodierung: Windows-1252). '
        '<br>Pflichtspalten: MATRIKELNR, KURS, VORNAME, NAME. '
        '<br>Optionale Spalten: GEB_DATUM, ANREDE_KURZ, ANREDE, AKTEUR_EMAIL_DH. '
        '<br>Kurse müssen bereits im System vorhanden sein. '
        '<br>DDV: Reporting > Datenquellen > Studenten > Immatrikulierte Studenten und Ausbildungsunternehmen sowie Träger'
    ),
    'pruefungsordnungen': (
        'Importiert Prüfungsordnungen und ordnet sie passenden Kursen zu. '
        '<br>Pflichtspalten: PRUEFUNGSORDNUNG, STUDIENGANG_PO, STUDIENRICHTUNG_PO. '
        '<br>Studiengang und Studienrichtung müssen bereits im System vorhanden sein. '
        '<br>Organisation muss ausgewählt sein. '
        '<br>Kurse die bereits eine PO haben werden nicht verändert.'
        '<br>DDV: Reporting > Datenquellen > Moddelierung (neu) > Prüfungsordnung (mit Übersetzungen) ab 2017'
    ),
    'module_units': (
        'Importiert Module und Lehreinheiten aus einer CSV-Datei (Trennzeichen: Semikolon, Kodierung: Windows-1252). '
        '<br>Pflichtspalten: MODULCODE, MODULNAME, UNITCODE, VERANSTALTUNGSNAME. '
        '<br>Optionale Spalten: DAUER, ANZAHL_STUNDEN. Wenn Abkürzungen definiert sind für Studiengang und Studienrichtung so werden dise zugeordnet.'
        '<br>Prüfungsordnung muss ausgewählt sein. '
        '<br>PA1-, PA2- und BA-Unit-Nr werden der Prüfungsordnung zugeordnet, wenn die Felder noch leer sind.'
        '<br>DDV: Reporting > Datenquellen > Lehrveranstaltungen > Übersicht Vorlesungsangebote'
        '<br>ODER bei noch nicht gehaltenen: DDV: Reporting > Datenquellen > Modellierung (neu) > Modul und Unitübersicht (mit Übersetzung) > Moduldaten: aus Prüfungsordnung'
    ),
}


class ImportForm(forms.Form):
    IMPORT_TYPES = [
        ('dozenten', 'Dozenten importieren'),
        ('studenten', 'Studenten importieren'),
        ('pruefungsordnungen', 'Prüfungsordnungen importieren'),
        ('module_units', 'Module & Lehrveranstaltungen importieren'),
    ]

    import_type = forms.ChoiceField(
        choices=IMPORT_TYPES,
        label='Import-Typ',
    )
    organisation = forms.ModelChoiceField(
        queryset=StudyOrganisation.objects.all(),
        label='Organisation',
        required=False,
        empty_label='– keine Organisationszuordnung –',
        help_text='Optional: Die importierten Personen werden dieser Organisation als Dozent zugeordnet.',
    )
    study_regulation = forms.ModelChoiceField(
        queryset=StudyRegulation.objects.select_related('study').all(),
        label='Prüfungsordnung',
        required=False,
        empty_label='– Prüfungsordnung auswählen –',
        help_text='Nur für Import: Module & Lehrveranstaltungen.',
    )
    pa1_unit_nr = forms.CharField(
        label='PA1 Unit-Nr',
        required=False,
        max_length=15,
        help_text='Unit-Nr der PA1-Lehrveranstaltung (wird der PO zugeordnet wenn noch leer).',
    )
    pa2_unit_nr = forms.CharField(
        label='PA2 Unit-Nr',
        required=False,
        max_length=15,
        help_text='Unit-Nr der PA2-Lehrveranstaltung.',
    )
    ba_unit_nr = forms.CharField(
        label='BA Unit-Nr',
        required=False,
        max_length=15,
        help_text='Unit-Nr der BA-Lehrveranstaltung.',
    )
    csv_file = forms.FileField(
        label='CSV-Datei',
        validators=[FileExtensionValidator(allowed_extensions=['csv'])]
    )
