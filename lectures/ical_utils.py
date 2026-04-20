from datetime import datetime, time, timezone as dt_timezone
from zoneinfo import ZoneInfo

import icalendar
import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
import logging

from .models import StudyCourse, Lecture, Lesson, ModuleUnit, Room, StudySemester

logger = logging.getLogger(__name__)


class ICalImportError(Exception):
    def __init__(self, detail, status_code=400):
        super().__init__(str(detail))
        self.detail = detail
        self.status_code = status_code


def _directly_modified_Lesson_ids(Lesson_queryset):
    Lesson_ids = list(Lesson_queryset.values_list("pk", flat=True))
    if not Lesson_ids:
        return set()

    historical_Lesson_model = Lesson.history.model
    return set(
        historical_Lesson_model.objects.filter(
            id__in=Lesson_ids,
            history_type="~",
        )
        .values_list("id", flat=True)
        .distinct()
    )


def _normalize_event_datetime(event_dt_value, tzid_param=None):
    # RFC5545 allows DATE and DATE-TIME values; normalize both to aware datetimes.
    if not isinstance(event_dt_value, datetime):
        event_dt_value = datetime.combine(event_dt_value, time.min)

    if timezone.is_naive(event_dt_value):
        tz_name = tzid_param if tzid_param else settings.TIME_ZONE
        event_dt_value = event_dt_value.replace(tzinfo=ZoneInfo(tz_name))
    elif event_dt_value.tzinfo != dt_timezone.utc:
        event_dt_value = event_dt_value.astimezone(dt_timezone.utc)

    return event_dt_value

def import_ical_bytes_for_StudyCourse(
    *, course: StudyCourse, body: bytes, replace_existing=False, selected_semester:StudySemester=None
):
    if not body:
        raise ICalImportError("Empty ical body.")
    
    try:
        calendar = icalendar.Calendar.from_ical(body)
    except Exception as exc:
        raise ICalImportError(f"Could not parse iCal payload: {exc}") from exc

    # Fast pre-flight check: fail early if any event falls outside known semester.
    for event in calendar.walk("VEVENT"):
        event_start = event.get("DTSTART")
        if not event_start:
            continue

        tzid = (
            event_start.params.get("TZID") if hasattr(event_start, "params") else None
        )
        event_dt = _normalize_event_datetime(event_start.dt, tzid)

        if selected_semester:
            # Ignore events outside the selected StudySemester window.
            if not (
                selected_semester.start_date
                <= event_dt.date()
                <= selected_semester.end_date
            ):
                continue

        semester_exists = StudySemester.objects.filter(
            start_date__lte=event_dt.date(),
            end_date__gte=event_dt.date(),
        ).exists()
        if not selected_semester and not semester_exists:
            logger.info("Skipping iCal event with no matching StudySemester window")
            raise ICalImportError("StudySemester not found.", status_code=404)

    events_in_selected_semester = 0
    for event in calendar.walk("VEVENT"):
        event_start = event.get("DTSTART")
        if not event_start:
            continue

        if not selected_semester:
            events_in_selected_semester += 1
            continue

        tzid = (
            event_start.params.get("TZID") if hasattr(event_start, "params") else None
        )
        event_dt = _normalize_event_datetime(event_start.dt, tzid)
        if (
            selected_semester.start_date
            <= event_dt.date()
            <= selected_semester.end_date
        ):
            events_in_selected_semester += 1

    if selected_semester and events_in_selected_semester == 0:
        raise ICalImportError(
            f"Keine Termine im gewählten StudySemester '{selected_semester.name}' gefunden.",
            status_code=400,
        )

    created_Lessons = 0
    skipped_modules = []
    skipped_entries = []
    missing_room_entries = []
    event_timezone_info = {}

    with transaction.atomic():
        if replace_existing:
            # Replace mode: only clear the selected StudySemester window when one is chosen.
            lessons_to_replace = Lesson.objects.filter(lecture__course=course)
            if selected_semester:
                lessons_to_replace = lessons_to_replace.filter(
                    lecture__semester=selected_semester
                )
            lessons_to_replace.delete()

        for event in calendar.walk("VEVENT"):
            module_name = event.get("SUMMARY")
            if not module_name:
                continue
            module_name_text = str(module_name).strip()
            if not ModuleUnit.objects.filter(unit_name=module_name_text).exists():
                if module_name_text not in skipped_modules:
                    skipped_modules.append(module_name_text)
                continue

            event_start = event.get("DTSTART")
            event_end = event.get("DTEND")
            if not event_start or not event_end:
                skipped_entries.append(
                    {
                        "summary": module_name_text,
                        "reason": "Missing DTSTART or DTEND.",
                    }
                )
                continue

            unit = ModuleUnit.objects.filter(unit_name=module_name_text).first()
            if not unit:
                continue

            tzid_start = (
                event_start.params.get("TZID")
                if hasattr(event_start, "params")
                else None
            )
            tzid_end = (
                event_end.params.get("TZID") if hasattr(event_end, "params") else None
            )

            if tzid_start:
                event_timezone_info[tzid_start] = (
                    event_timezone_info.get(tzid_start, 0) + 1
                )

            event_start_dt = _normalize_event_datetime(event_start.dt, tzid_start)
            event_end_dt = _normalize_event_datetime(event_end.dt, tzid_end)

            if selected_semester and not (
                selected_semester.start_date
                <= event_start_dt.date()
                <= selected_semester.end_date
            ):
                continue

            raw_room_value = str(event.get("LOCATION", "")).strip()
            if not raw_room_value:
                missing_room_entries.append(
                    {
                        "summary": module_name_text,
                        "start": event_start_dt.isoformat(),
                        "end": event_end_dt.isoformat(),
                        "assigned_room": "TBD",
                    }
                )

            semester = (
                selected_semester
                or StudySemester.objects.filter(
                    start_date__lte=event_start_dt.date(),
                    end_date__gte=event_start_dt.date(),
                ).first()
            )
            if not semester:
                continue

            lecture, _ = Lecture.objects.get_or_create(
                unit=unit,
                semester=semester,
                course=course,
            )

            location_str = str(event.get("LOCATION", "TBD")).replace("\\,", ",")
            # Support comma-separated multi-room events by creating one Lesson per room.
            room_names = [
                room.strip() for room in location_str.split(",") if room.strip()
            ]
            if not room_names:
                room_names = ["TBD"]

            for room_name in room_names:
                is_double_bookable = room_name == "HN Online-Veranstaltung"
                room, _ = Room.objects.get_or_create(
                    name=room_name,
                    defaults={"is_double_bookable": is_double_bookable},
                )

                Lesson.objects.create(
                    room=room,
                    lecture=lecture,
                    start=event_start_dt,
                    end=event_end_dt,
                )
                created_Lessons += 1

        if selected_semester and created_Lessons == 0:
            raise ICalImportError(
                (
                    f"Im gewählten StudySemester '{selected_semester.name}' wurden keine "
                    "importierbaren Termine gefunden. "
                    "Bitte prüfen Sie Modulnamen und iCal-Daten."
                ),
                status_code=400,
            )

    return {
        "created_Lessons": created_Lessons,
        "skipped_modules": skipped_modules,
        "skipped_entries": skipped_entries,
        "missing_room_entries": missing_room_entries,
        "debug_timezone_info": event_timezone_info
        or "No explicit TZID found (naive datetimes)",
    }


def get_StudyCourse_overwrite_risk(*, course: StudyCourse):
    # Separate metrics help the UI communicate plain overwrite vs. overwrite of edited data.
    Lesson_queryset = Lesson.objects.filter(lecture__course=course)
    Lesson_count = Lesson_queryset.count()

    # Detect explicit modification requests and direct Lesson edits.
    modified_by_request_ids = set(
        Lesson.objects.filter(
            lecture__course=course,
            modifications__isnull=False,
        )
        .distinct()
        .values_list("pk", flat=True)
    )
    modified_by_history_ids = _directly_modified_Lesson_ids(Lesson_queryset)
    modified_Lesson_count = len(modified_by_request_ids | modified_by_history_ids)

    if Lesson_count == 0 and modified_Lesson_count == 0:
        return None

    return {
        "Lesson_count": Lesson_count,
        "modified_Lesson_count": modified_Lesson_count,
    }


def get_StudyCourse_overwrite_risk_for_StudySemester(*, StudyCourse: StudyCourse, StudySemester: StudySemester):
    Lesson_queryset = Lesson.objects.filter(
        Lecture__StudyCourse=StudyCourse,
        Lecture__StudySemester=StudySemester,
    )
    Lesson_count = Lesson_queryset.count()

    # Detect explicit modification requests and direct Lesson edits.
    modified_by_request_ids = set(
        Lesson.objects.filter(
            Lecture__StudyCourse=StudyCourse,
            Lecture__StudySemester=StudySemester,
            modifications__isnull=False,
        )
        .distinct()
        .values_list("pk", flat=True)
    )
    modified_by_history_ids = _directly_modified_Lesson_ids(Lesson_queryset)
    modified_Lesson_count = len(modified_by_request_ids | modified_by_history_ids)

    if Lesson_count == 0 and modified_Lesson_count == 0:
        return None

    return {
        "Lesson_count": Lesson_count,
        "modified_Lesson_count": modified_Lesson_count,
    }


def sync_StudyCourse_from_external_ical(
    *, course: StudyCourse, confirm_overwrite=False, selected_semester=None
):
    if not course.external_ical_url:
        return {"synced": False, "reason": "no_external_url"}

    now = timezone.now()

    # TODO
    #overwrite_risk = get_StudyCourse_overwrite_risk(course=course)
    #if overwrite_risk and not confirm_overwrite:
    #    # Require explicit confirmation before replacing potentially curated schedules.
    #    warning = (
    #        "Synchronisation würde bestehende Planungsdaten überschreiben "
    #        f"({overwrite_risk['Lesson_count']} Vorlesungen, "
    #        f"{overwrite_risk['modified_Lesson_count']} mit Änderungen)."
    #    )
    #    return {
    #        "synced": False,
    #        "reason": "requires_confirmation",
    #        "warning": warning,
    #        "overwrite_risk": overwrite_risk,
    #    }

    try:
        response = requests.get(course.external_ical_url, timeout=15)
        response.raise_for_status()
        payload = response.content

        result = import_ical_bytes_for_StudyCourse(
            course=course,
            body=payload,
            replace_existing=True,
            selected_semester=selected_semester,
        )

        course.external_ical_last_sync_at = now
        course.save(
            update_fields=[
                "external_ical_last_sync_at",
            ]
        )

        return {"synced": True, "reason": "ok", "result": result}

    except requests.RequestException as exc:
        error = f"Could not fetch external iCal URL: {exc}"
        logger.info(error)
    except (ICalImportError, ValidationError) as exc:
        detail = exc.detail if isinstance(exc, ICalImportError) else str(exc)
        error = f"Could not import external iCal data: {detail}"
        logger.info(error)
    except Exception as exc:
        error = f"Unexpected external iCal sync error: {exc}"
        logger.exception(error)

    return {"synced": False, "reason": "error", "error": error}
