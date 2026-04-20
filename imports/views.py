import csv
import io
import re
from datetime import date, datetime

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render

from organization.models import StudyAcademy, StudyCourse, StudyField, StudyOrganisation, StudyProgram, StudyRegulation, StudyYear
from persons.models import Company, Person, Personnel, PersonnelOrganisation, Student
from .forms import ImportForm, IMPORT_TYPE_DESCRIPTIONS

def open_csv_auto(csv_file):
    raw = csv_file.read()

    # Check for UTF-8 BOM
    if raw.startswith(b'\xef\xbb\xbf'):
        text = raw.decode('utf-8-sig', errors='replace')
        # print("CSV erkannt als UTF-8-BOM")
    else:
        try:
            # UTF-8
            text = raw.decode('utf-8', errors='strict')
            # print("CSV erkannt als UTF-8 (ohne BOM)")
        except UnicodeDecodeError:
            # Fallback Windows-1252
            text = raw.decode('cp1252', errors='replace')
            # print("CSV erkannt als Windows-1252")

    text_file = io.StringIO(text)
    reader = csv.DictReader(text_file, delimiter=';')
    return reader

def _parse_birthday(value):
    if not value or not value.strip():
        return None
    try:
        return datetime.strptime(value.strip(), '%d.%m.%Y').date()
    except ValueError:
        return None


def _coalesce(new_val, existing_val):
    """Gibt new_val zurück wenn nicht leer, sonst existing_val (leere Strings zählen als leer)."""
    return new_val if new_val else existing_val


def _update_or_create_person(lookup_kwargs, update_kwargs, role_now):
    """
    Sucht Person per lookup_kwargs (filter).
    Gefunden (1):    aktualisiert leere Felder per _coalesce, gibt (person, 'updated') zurück.
    Nicht gefunden:  legt neu an mit role_now,              gibt (person, 'created') zurück.
    Mehrere Treffer: gibt (None, 'duplicate') zurück.
    """
    qs = Person.objects.filter(**lookup_kwargs)
    count = qs.count()

    if count > 1:
        return None, 'duplicate'

    if count == 1:
        person = qs.first()
        for field, value in update_kwargs.items():
            setattr(person, field, _coalesce(value, getattr(person, field)))
        person.save()
        return person, 'updated'

    person = Person.objects.create(
        role_now=role_now,
        **{k: (v if v else None) for k, v in {**lookup_kwargs, **update_kwargs}.items()},
    )
    return person, 'created'


def import_dozenten(csv_file, organisation=None):
    results = []
    
    reader = open_csv_auto(csv_file)
    
    if reader.fieldnames is None:
        # Header konnte nicht gelesen werden
        results.append({
            'status': 'error',
            'name': 'Die CSV-Datei konnte nicht gelesen werden oder enthält keine Kopfzeile.'
        })
    
    # Prüfen, ob alle erwarteten Spalten vorhanden sind
    expected_headers = [
        'PERSONALNUMMER', 'ANREDE', 'TITEL', 'VORNAME', 'NACHNAME', 'GEBURTSDATUM', 'BRIEFKOPF', 'MAIL_HAUPTKONTAKT'
    ]
    reader.fieldnames = [h.strip() for h in reader.fieldnames]
    reader.fieldnames = [h.lstrip('\ufeff').lstrip('ï»¿') for h in reader.fieldnames]
    missing_columns = [col for col in expected_headers if col not in reader.fieldnames]
    if missing_columns:
        results.append({
            'status': 'error',
            'name': f'Die CSV-Datei fehlt folgende Spalten: {", ".join(missing_columns)} | folgende header wurden gelesen {", ".join(reader.fieldnames)}'
        })
        return results

    for row in reader:
        personnel_nr_raw = row.get('PERSONALNUMMER', '').strip()
        salutation       = row.get('ANREDE', '').strip()
        title            = row.get('TITEL', '').strip()
        firstname        = row.get('VORNAME', '').strip()
        lastname         = row.get('NACHNAME', '').strip()
        birthday         = _parse_birthday(row.get('GEBURTSDATUM', ''))
        salutation_full  = row.get('BRIEFKOPF', '').strip()
        email            = row.get('MAIL_HAUPTKONTAKT', '').strip()

        if not personnel_nr_raw.isdigit():
            results.append({'status': 'error', 'name': f'Keine Personalnummer gegeben – PERSONALNUMMER_RAW: {personnel_nr_raw}'})
            continue
        personnel_nr = int(personnel_nr_raw)

        if not firstname or not lastname:
            results.append({'status': 'error', 'name': f'(leer) Zeile übersprungen – PERSONALNUMMER: {personnel_nr_raw}'})
            continue
        
        personnel = None
        is_exisiting = False

        doz_update_kwargs = {
            'title': title,
            'birthday': birthday,
            'salutation_short': salutation,
            'salutation_full': salutation_full,
            'mail_main': email,
        }

        # Check Personnel schon vorhanden
        if Personnel.objects.filter(personnel_nr=personnel_nr).exists():
            personnel = Personnel.objects.filter(personnel_nr=personnel_nr).first()
            person = personnel.person
            is_exisiting = True
            for field, value in doz_update_kwargs.items():
                setattr(person, field, _coalesce(value, getattr(person, field)))
            person.save()
        else:
            person, person_status = _update_or_create_person(
                lookup_kwargs={'firstname': firstname, 'lastname': lastname},
                update_kwargs=doz_update_kwargs,
                role_now='DOZ',
            )
            if person is None:
                results.append({'status': 'duplicate', 'name': f'{firstname} {lastname} – mehrere Einträge gefunden, übersprungen'})
                continue
            is_exisiting = (person_status == 'updated')

        if personnel is None:
            check_personnel = Personnel.objects.filter(person_id=person.id)
            if check_personnel.exists(): # Nur noetig fuer Eintragsdupletten (z.B. Bellon)
                personnel = check_personnel.first()
            else:
                personnel = Personnel.objects.create(
                    personnel_nr=personnel_nr,
                    person=person,
                    actant_type=0,
                )

        if organisation:
            if not PersonnelOrganisation.objects.filter(
                personnel=personnel,
                organisation=organisation,
            ).exists():
                PersonnelOrganisation.objects.create(
                    personnel=personnel,
                    organisation=organisation,
                    role='doz',
                )

        if is_exisiting:
            results.append({'status': 'updated', 'name': f'{firstname} {lastname} – Personalnummer {personnel.personnel_nr}'})
        else:
            results.append({'status': 'created', 'name': f'{firstname} {lastname} – Personalnummer {personnel.personnel_nr}'})

        #results.append({'status': 'skipped', 'name': f'{firstname} {lastname} – Personalnummer {personnel_nr} bereits vorhanden'})
    
    return results


def _get_or_update_company(row):
    """Gibt (Company|None) zurück. Legt an wenn nicht vorhanden, aktualisiert wenn vorhanden."""
    firma_id_raw = row.get('FIRMA_ID', '').strip()
    if not firma_id_raw.isdigit():
        return None
    firma_id = int(firma_id_raw)

    firma_name        = row.get('FIRMA_NAME', '').strip()
    firma_adressform  = row.get('FIRMA_ADRESSFORM', '').strip()
    firma_street      = row.get('FIRMA_ANSCHRIFT', '').strip()
    firma_district    = row.get('FIRMA_LANDKREIS', '').strip()
    firma_plz         = row.get('FIRMA_PLZ', '').strip()
    firma_ort         = row.get('FIRMA_ORT', '').strip()
    firma_state       = row.get('FIRMA_BUNDESLAND', '').strip()
    firma_land        = row.get('FIRMA_LAND', '').strip()
    firma_tel         = row.get('FIRMA_TELEFON', '').strip()
    firma_mail_main   = row.get('FIRMA_MAIL_HAUPTKONTAKT', '').strip() or row.get('FIRMA_MAIL_ANSCHRIFT', '').strip()
    firma_mail_person = row.get('FIRMA_MAIL_AKTEUR', '').strip()
    firma_webpage     = row.get('FIRMA_WWW_AKTEUR', '').strip()

    company = Company.objects.filter(company_nr=firma_id).first()
    if company:
        company.adressform  = _coalesce(firma_adressform, company.adressform)
        company.name        = _coalesce(firma_name, company.name)
        company.street      = _coalesce(firma_street, company.street)
        company.district    = _coalesce(firma_district, company.district)
        company.postal_code = _coalesce(firma_plz, company.postal_code)
        company.city        = _coalesce(firma_ort, company.city)
        company.state       = _coalesce(firma_state, company.state)
        company.country     = _coalesce(firma_land, company.country)
        company.tel_main    = _coalesce(firma_tel, company.tel_main)
        company.mail_main   = _coalesce(firma_mail_main, company.mail_main)
        company.mail_person = _coalesce(firma_mail_person, company.mail_person)
        company.webpage     = _coalesce(firma_webpage, company.webpage)
        company.save()
    else:
        if not firma_name:
            return None
        company = Company.objects.create(
            company_nr=firma_id,
            adressform=firma_adressform,
            name=firma_name,
            street=firma_street or None,
            district=firma_district or None,
            postal_code=firma_plz or None,
            city=firma_ort or None,
            state=firma_state or None,
            country=firma_land or None,
            tel_main=firma_tel or None,
            mail_main=firma_mail_main or None,
            mail_person=firma_mail_person or None,
            webpage=firma_webpage or None,
        )
    return company


def _get_or_update_contact_person(row):
    """Gibt (Person|None) zurück. Legt Ansprechpartner an oder aktualisiert ihn."""
    ansp_firstname      = row.get('ANSPRECHPARTNER_VORNAME', '').strip()
    ansp_lastname       = row.get('ANSPRECHPARTNER_NAME', '').strip()
    if not ansp_firstname or not ansp_lastname:
        return None

    ansp_title          = row.get('ANSPRECHPARTNER_TITEL', '').strip()
    ansp_salutation_full = row.get('ANSPRECHPARTNER_ANREDE', '').strip()
    ansp_sal_lower      = ansp_salutation_full.lower()
    ansp_salutation_short = 'Herr' if 'herr' in ansp_sal_lower else ('Frau' if 'frau' in ansp_sal_lower else None)
    ansp_gender         = 'M' if ansp_salutation_short == 'Herr' else ('F' if ansp_salutation_short == 'Frau' else None)
    ansp_tel            = row.get('TELEFON', '').strip()
    ansp_mail           = row.get('ANSPRECHPARTNER_HAUPTKONTAKT', '').strip() or row.get('EMAIL', '').strip() or row.get('EMAIL_AKTEUR', '').strip()

    contact, _ = _update_or_create_person(
        lookup_kwargs={'firstname': ansp_firstname, 'lastname': ansp_lastname},
        update_kwargs={
            'title': ansp_title,
            'salutation_full': ansp_salutation_full,
            'salutation_short': ansp_salutation_short,
            'gender': ansp_gender,
            'tel_main': ansp_tel,
            'mail_main': ansp_mail,
        },
        role_now='COAS',
    )
    return contact  # None bei Duplikat


def import_studenten(csv_file, organisation=None):
    results = []

    reader = open_csv_auto(csv_file)

    gender_map = {'herr': 'M', 'frau': 'F'}

    for row in reader:
        matri_nr_raw    = row.get('MATRIKELNR', '').strip()
        course_nr       = row.get('KURS', '').strip()
        year_raw        = row.get('JAHRGANG', '').strip()
        study_progr_raw = row.get('STUDIENGANG', '').strip()
        studyfield_raw  = row.get('STUDIENRICHTUNG', '').strip()
        firstname       = row.get('VORNAME', '').strip()
        lastname        = row.get('NAME', '').strip()
        birthday        = _parse_birthday(row.get('GEB_DATUM', ''))
        salutation      = row.get('ANREDE_KURZ', '').strip()
        salutation_full = row.get('ANREDE', '').strip()
        gender          = gender_map.get(salutation_full.lower())
        mail            = row.get('AKTEUR_EMAIL_DH', '').strip()

        if not matri_nr_raw.isdigit():
            results.append({'status': 'error', 'name': f'Ungültige Matrikelnummer: {matri_nr_raw}'})
            continue
        matri_nr = int(matri_nr_raw)

        if not firstname or not lastname:
            results.append({'status': 'error', 'name': f'Name leer – Matrikelnummer: {matri_nr}'})
            continue

        if not course_nr:
            results.append({'status': 'error', 'name': f'{firstname} {lastname} – kein Kurs angegeben'})
            continue

        # Kurs suchen – wenn mehrfach vorhanden: Fehler
        courses_qs = StudyCourse.objects.filter(course_nr=course_nr)
        course_count = courses_qs.count()

        if course_count > 1:
            results.append({'status': 'error', 'name': f'{firstname} {lastname} – Kurs „{course_nr}" mehrfach gefunden'})
            continue

        if course_count == 1:
            course = courses_qs.first()
            field = course.field
        else:
            # Kurs existiert nicht → Zwischenstrukturen get_or_create, dann Kurs anlegen
            year_match = re.search(r'\b(\d{4})\b', year_raw)
            if not year_match:
                results.append({'status': 'error', 'name': f'{firstname} {lastname} – kein gültiges Jahr in „{year_raw}"'})
                continue
            year_name = f'Jahrgang {year_match.group(1)}'
            study_year, _ = StudyYear.objects.get_or_create(year_name=year_name)

            if not study_progr_raw:
                results.append({'status': 'error', 'name': f'{firstname} {lastname} – kein Studiengang angegeben'})
                continue
            study_program, _ = StudyProgram.objects.get_or_create(study_progr=study_progr_raw)

            if not studyfield_raw:
                results.append({'status': 'error', 'name': f'{firstname} {lastname} – keine Studienrichtung angegeben'})
                continue
            field, _ = StudyField.objects.get_or_create(study=study_program, studyfield=studyfield_raw)

            if not organisation:
                results.append({'status': 'error', 'name': f'{firstname} {lastname} – Kurs „{course_nr}" nicht vorhanden und keine Organisation ausgewählt'})
                continue

            # Akademie per Abkürzung finden: Präfix von course_nr bis zum ersten '-'
            course_prefix = course_nr.split('-')[0] if '-' in course_nr else course_nr
            academy = StudyAcademy.objects.filter(abbreviation=course_prefix).first()
            if not academy:
                academy = StudyAcademy.objects.create(
                    academy_name=course_prefix,
                    abbreviation=course_prefix,
                )

            course = StudyCourse.objects.create(
                course_nr=course_nr,
                field=field,
                academic_year=study_year,
                organisation=organisation,
                academy=academy,
            )

        # Company + Ansprechpartner aus CSV-Zeile holen/anlegen
        company        = _get_or_update_company(row)
        contact_person = _get_or_update_contact_person(row)

        # Student zuerst per Matrikelnummer suchen
        students_qs = Student.objects.filter(matri_nr=matri_nr)
        student_count = students_qs.count()

        if student_count > 1:
            results.append({'status': 'duplicate', 'name': f'{firstname} {lastname} – Matrikel {matri_nr} mehrfach gefunden'})
            continue

        if student_count == 1:
            # Student bekannt → Person über Student holen und leere Felder befüllen
            student = students_qs.first()
            person = student.person
            person.salutation_short = _coalesce(salutation, person.salutation_short)
            person.salutation_full  = _coalesce(salutation_full, person.salutation_full)
            person.gender           = _coalesce(gender, person.gender)
            person.mail_main        = _coalesce(mail, person.mail_main)
            person.save()
            student.course          = course
            student.field           = field
            student.company         = _coalesce(company, student.company)
            student.company_person  = _coalesce(contact_person, student.company_person)
            student.save()
            results.append({'status': 'updated', 'name': f'{firstname} {lastname} – Matrikel {matri_nr}'})
        else:
            # Student unbekannt → Person suchen oder anlegen
            person, person_status = _update_or_create_person(
                lookup_kwargs={'firstname': firstname, 'lastname': lastname, 'birthday': birthday},
                update_kwargs={
                    'salutation_short': salutation,
                    'salutation_full': salutation_full,
                    'gender': gender,
                    'mail_main': mail,
                },
                role_now='ST',
            )
            if person is None:
                results.append({'status': 'duplicate', 'name': f'{firstname} {lastname} – mehrere Personen gefunden'})
                continue
            is_new_person = (person_status == 'created')

            Student.objects.create(
                matri_nr=matri_nr,
                person=person,
                course=course,
                field=field,
                company=company,
                company_person=contact_person,
            )
            if is_new_person:
                results.append({'status': 'created', 'name': f'{firstname} {lastname} – Matrikel {matri_nr}'})
            else:
                results.append({'status': 'updated', 'name': f'{firstname} {lastname} – Matrikel {matri_nr}'})

    return results


def import_studyregulations(csv_file, organisation=None):
    results = []

    reader = open_csv_auto(csv_file)

    for row in reader:
        po_name         = row.get('PRUEFUNGSORDNUNG', '').strip() # like Wirtschaftsinformatik Heilbronn 2020f
        studiengang_po  = row.get('STUDIENGANG_PO', '').strip() # Wirtschaftsinformatik #HN-W Wirtschaftsinformatik Heilbronn
        studienrichtung = row.get('STUDIENRICHTUNG_PO', '').strip() # Business Engineering

        if not po_name:
            results.append({'status': 'error', 'name': 'PRUEFUNGSORDNUNG leer – Zeile übersprungen'})
            continue
        if not studiengang_po:
            results.append({'status': 'error', 'name': f'{po_name} – STUDIENGANG_PO leer'})
            continue
        if not organisation:
            results.append({'status': 'error', 'name': f'{po_name} – keine Organisation ausgewählt'})
            continue

        # Jahr aus PO-Name extrahieren → start_date
        year_match = re.search(r'(\d{4})', po_name)
        start_year = 2000
        if not year_match:
            year_match = re.search(r'(\d{2})', po_name)
            if not year_match:
                results.append({'status': 'error', 'name': f'{po_name} – keine 4-stellige Jahreszahl gefunden'})
                continue
            else:
                start_year = int('20'+year_match.group(1))
        else:
            start_year = int(year_match.group(1))
        start_date = date(start_year, 1, 1)

        # StudyStudy suchen (nicht anlegen)
        programs_qs = StudyProgram.objects.filter(study_progr=studiengang_po)
        if programs_qs.count() == 0:
            results.append({'status': 'error', 'name': f'{po_name} – Studiengang „{studiengang_po}" nicht gefunden'})
            continue
        if programs_qs.count() > 1:
            results.append({'status': 'error', 'name': f'{po_name} – Studiengang „{studiengang_po}" mehrfach gefunden'})
            continue
        study_program = programs_qs.first()

        # StudyField suchen (optional, nicht anlegen)
        study_field = None
        if studienrichtung:
            fields_qs = StudyField.objects.filter(study=study_program, studyfield=studienrichtung)
            if fields_qs.count() == 0:
                results.append({'status': 'error', 'name': f'{po_name} – Studienrichtung „{studienrichtung}" nicht gefunden'})
                continue
            if fields_qs.count() > 1:
                results.append({'status': 'error', 'name': f'{po_name} – Studienrichtung „{studienrichtung}" mehrfach gefunden'})
                continue
            study_field = fields_qs.first()

        # Prüfungsordnung suchen oder anlegen
        reg_qs = StudyRegulation.objects.filter(name=po_name, study=study_program)
        if reg_qs.exists():
            regulation = reg_qs.first()
            reg_status = 'updated'
        else:
            regulation = StudyRegulation.objects.create(
                name=po_name,
                start_date=start_date,
                study=study_program,
            )
            reg_status = 'created'

        # Kurse filtern: Studiengang + optional Studienrichtung + Organisation + Jahrgang ≥ start_year
        courses_qs = StudyCourse.objects.filter(
            field__study=study_program,
            organisation=organisation,
            study_regulation__isnull=True,  # nur Kurse ohne PO
            academic_year__year_name__gte=f'Jahrgang {start_year}',
        )
        if study_field:
            courses_qs = courses_qs.filter(field=study_field)

        assigned = courses_qs.update(study_regulation=regulation)

        results.append({
            'status': reg_status,
            'name': f'{po_name} ({studiengang_po}{" – " + studienrichtung if studienrichtung else ""}) – {assigned} Kurs(e) zugeordnet',
        })

    return results


def import_module_units(csv_file, study_regulation, pa1_unit_nr='', pa2_unit_nr='', ba_unit_nr=''):
    from decimal import Decimal, InvalidOperation
    from lectures.models import Module, ModuleUnit

    results = []
    units_by_nr = {}  # unit_nr → ModuleUnit, für PA/BA-Zuordnung nach dem Loop
    fields_by_abbreviation = {}  # abbrevation → Study_field, für Modulzuordnung

    reader = open_csv_auto(csv_file)

    study_program = study_regulation.study

    for row in reader:
        # Für 2 Arten von Imports
        module_code = (row.get('MODULCODE') or row.get('MODULNUMMER') or '').strip()
        module_name = (
            row['MODULNAME'].strip().split("_")[0]
            if row.get('MODULNAME')
            else (row.get('MODULBEZEICHNUNG') or '').strip()
        )
        unit_code = (row.get('UNITCODE') or row.get('UNITNUMMER') or '').strip()
        unit_name = (
            row['VERANSTALTUNGSNAME'].strip().split("_")[0]
            if row.get('VERANSTALTUNGSNAME')
            else (row.get('UNITBEZEICHNUNG') or '').strip()
        )
        stunden_raw = (row.get('ANZAHL_STUNDEN') or '').strip()

        if not module_code:
            results.append({'status': 'error', 'name': 'MODULCODE leer – Zeile übersprungen'})
            continue
        if not unit_code:
            results.append({'status': 'error', 'name': f'{module_code} – UNITCODE leer'})
            continue
        if not unit_name:
            results.append({'status': 'error', 'name': f'{module_code}/{unit_code} – VERANSTALTUNGSNAME leer'})
            continue

        try:
            units_val = Decimal(stunden_raw.replace(',', '.')) if stunden_raw else Decimal('0')
        except InvalidOperation:
            units_val = Decimal('0')

        # Studienrichtung aus Modulcode ableiten: Suffix nach letztem '_', führende Buchstaben = Abkürzung
        # z.B. W3WI_BE301 → 'BE' → StudyField mit abbreviation='BE'
        study_field = None
        suffix = module_code.rsplit('_', 1)[-1] if '_' in module_code else ''
        field_abbr_match = re.match(r'^([A-Za-z]+)', suffix)
        if field_abbr_match:
            if field_abbr_match.group(1) not in fields_by_abbreviation:
                fields_by_abbreviation[field_abbr_match.group(1)] = StudyField.objects.filter(
                    study=study_program,
                    abbreviation=field_abbr_match.group(1),
                ).first()
            study_field = fields_by_abbreviation[field_abbr_match.group(1)]

        # Get or create module (no update)
        module, module_created = Module.objects.get_or_create(
            module_nr=module_code,
            defaults={
                'name': module_name or module_code,
                'study': study_program,
                'field': study_field,
                'regulation': study_regulation,
                'credits': 1,
            },
        )

        # Get or create unit (no update)
        unit, unit_created = ModuleUnit.objects.get_or_create(
            module=module,
            unit_nr=unit_code,
            defaults={'unit_name': unit_name, 'units': units_val, 'semester_nr': 1},
        )

        units_by_nr[unit_code] = unit

        status = 'created' if (module_created or unit_created) else 'skipped'
        results.append({'status': status, 'name': f'{module_code} / {unit_code} – {unit_name}'})

    # PA1/PA2/BA-Units der Prüfungsordnung zuordnen (nur wenn das Feld noch leer ist)
    changed = False
    if pa1_unit_nr and pa1_unit_nr in units_by_nr and study_regulation.unit_pa1 is None:
        study_regulation.unit_pa1 = units_by_nr[pa1_unit_nr]
        changed = True
    if pa2_unit_nr and pa2_unit_nr in units_by_nr and study_regulation.unit_pa2 is None:
        study_regulation.unit_pa2 = units_by_nr[pa2_unit_nr]
        changed = True
    if ba_unit_nr and ba_unit_nr in units_by_nr and study_regulation.unit_ba is None:
        study_regulation.unit_ba = units_by_nr[ba_unit_nr]
        changed = True
    if changed:
        study_regulation.save()
        results.append({'status': 'info', 'name': 'PA1/PA2/BA-Units der Prüfungsordnung zugeordnet.'})

    return results


def _get_user_organisations(user):
    try:
        return user.person.personnel_profile.organisations.all()
    except Exception:
        return StudyOrganisation.objects.none()


@login_required
def import_dashboard(request):
    results = None
    user_organisations = _get_user_organisations(request.user)

    if request.method == 'POST':
        form = ImportForm(request.POST, request.FILES)
        form.fields['organisation'].queryset = user_organisations

        if form.is_valid():
            import_type = form.cleaned_data['import_type']
            csv_file = request.FILES['csv_file']
            organisation = form.cleaned_data.get('organisation')

            # Sicherheits-Validierung: gewählte Organisation muss zum User gehören
            if organisation and not user_organisations.filter(pk=organisation.pk).exists():
                form.add_error('organisation', 'Du hast keinen Zugriff auf diese Organisation.')
            else:
                if import_type == 'dozenten':
                    results = import_dozenten(csv_file, organisation=organisation)
                elif import_type == 'studenten':
                    results = import_studenten(csv_file, organisation=organisation)
                elif import_type == 'pruefungsordnungen':
                    results = import_studyregulations(csv_file, organisation=organisation)
                elif import_type == 'module_units':
                    study_regulation = form.cleaned_data.get('study_regulation')
                    if not study_regulation:
                        form.add_error('study_regulation', 'Bitte eine Prüfungsordnung auswählen.')
                    else:
                        pa1_unit_nr = form.cleaned_data.get('pa1_unit_nr', '')
                        pa2_unit_nr = form.cleaned_data.get('pa2_unit_nr', '')
                        ba_unit_nr  = form.cleaned_data.get('ba_unit_nr', '')
                        results = import_module_units(csv_file, study_regulation, pa1_unit_nr, pa2_unit_nr, ba_unit_nr)
                else:
                    results = [{'status': 'info', 'name': 'Dieser Import-Typ ist noch nicht implementiert.'}]
    else:
        form = ImportForm()
        form.fields['organisation'].queryset = user_organisations

    counts = {}
    if results is not None:
        counts = {
            'created_count':   sum(1 for r in results if r['status'] == 'created'),
            'updated_count':   sum(1 for r in results if r['status'] == 'updated'),
            'duplicate_count': sum(1 for r in results if r['status'] == 'duplicate'),
            'skipped_count':   sum(1 for r in results if r['status'] == 'skipped'),
            'error_count':     sum(1 for r in results if r['status'] == 'error'),
        }

    return render(request, 'imports/import_dashboard.html', {
        'form': form,
        'results': results,
        'import_type_descriptions': IMPORT_TYPE_DESCRIPTIONS,
        **counts,
    })
