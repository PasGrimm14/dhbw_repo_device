import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView, DetailView, TemplateView
from django.db.models import Case, When, Count, Avg, Q, Sum
from django.utils import timezone
from accounts.mixins import PermissionMixin
from .models import Module, ModuleUnit, Grade, Lesson
from accounts.mixins import TokenOrLoginMixin

# ============= Dashboard =============

@login_required
def lectures_dashboard(request):
    """Dashboard mit Übersicht"""
    context = {
        'total_modules': Module.objects.for_user(request.user).count(),
        'total_units': ModuleUnit.objects.for_user(request.user).count(),
        'total_grades': Grade.objects.for_user(request.user).count(),
        'passed_grades': Grade.objects.for_user(request.user).filter(passed=True).count(),
        'failed_grades': Grade.objects.for_user(request.user).filter(passed=False).count(),
        'average_grade': Grade.objects.for_user(request.user).filter(passed=True).aggregate(
            avg=Avg('grade')
        )['avg'],
        'recent_grades': Grade.objects.for_user(request.user).select_related(
            'student__person', 'module'
        ).order_by('-id')[:10],
    }
    return render(request, 'lectures/dashboard.html', context)


# ============= Module Views =============

class ModuleListView(PermissionMixin, ListView):
    """Liste aller Module"""
    permission_required = 'lectures.view_module'
    model = Module
    template_name = 'lectures/module_list.html'
    context_object_name = 'modules'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = Module.objects.for_user(self.request.user).select_related(
            'study', 'field'
        ).annotate(
            num_units=Count('units'),
            num_grades=Count('grades')
        )
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(module_nr__icontains=search) |
                Q(name__icontains=search)
            )
        
        study = self.request.GET.get('study')
        if study:
            queryset = queryset.filter(study_id=study)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from organization.models import StudyProgram
        context['studies'] = StudyProgram.objects.all()
        return context


class ModuleDetailView(PermissionMixin, DetailView):
    """Detailansicht eines Moduls"""
    permission_required = 'lectures.view_module'
    model = Module
    template_name = 'lectures/module_detail.html'
    context_object_name = 'module'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['units'] = ModuleUnit.objects.for_user(self.request.user).filter(module=self.object)
        context['grades'] = Grade.objects.for_user(self.request.user).filter(module=self.object).select_related(
            'student__person'
        ).order_by('-grade')[:20]
        context['grade_stats'] = Grade.objects.for_user(self.request.user).filter(module=self.object).aggregate(
            avg=Avg('grade'),
            count=Count('id'),
            num_passed=Count('id', filter=Q(passed=True)),
            num_failed=Count('id', filter=Q(passed=False))
        )
        return context


# ============= ModuleUnit Views =============

class ModuleUnitListView(PermissionMixin, ListView):
    """Liste aller Lehrveranstaltungen"""
    permission_required = 'lectures.view_moduleunit'
    model = ModuleUnit
    template_name = 'lectures/moduleunit_list.html'
    context_object_name = 'units'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = ModuleUnit.objects.for_user(self.request.user).select_related('module').annotate(
            num_grades=Count('grades')
        )
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(unit_nr__icontains=search) |
                Q(unit_name__icontains=search) |
                Q(unit_name_short__icontains=search) |
                Q(module__name__icontains=search)
            )
        
        semester = self.request.GET.get('semester')
        if semester:
            queryset = queryset.filter(semester_nr=semester)
        
        return queryset


class ModuleUnitDetailView(PermissionMixin, DetailView):
    """Detailansicht einer Lehrveranstaltung"""
    permission_required = 'lectures.view_moduleunit'
    model = ModuleUnit
    template_name = 'lectures/moduleunit_detail.html'
    context_object_name = 'unit'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grades'] = Grade.objects.for_user(self.request.user).filter(unit=self.object).select_related(
            'student__person'
        ).order_by('-grade')
        context['grade_stats'] = Grade.objects.for_user(self.request.user).filter(unit=self.object).aggregate(
            avg=Avg('grade'),
            count=Count('id'),
            num_passed=Count('id', filter=Q(passed=True)),
            num_failed=Count('id', filter=Q(passed=False))
        )
        return context


# ============= Lesson Schedule View =============

class CourseLessonScheduleView(PermissionMixin, View):
    """Stundenplan-Übersicht aller Lessons eines Kurses für ein Semester"""
    permission_required = 'organization.view_studycourse'
    template_name = 'lectures/course_lesson_schedule.html'

    def get(self, request, course_pk):
        from organization.models import StudyCourse, StudySemester

        course = get_object_or_404(StudyCourse, pk=course_pk)

        # Alle verfügbaren Semester für diesen Kurs
        if course.study_phase:
            semesters = [s for s in course.study_phase.get_all_semesters()]
            current = course.study_phase.get_current_semester()
        else:
            semesters = []
            current = None

        # Gewähltes Semester aus Query-Parameter oder aktuelles
        semester_pk = request.GET.get('semester')
        if semester_pk:
            selected_semester = get_object_or_404(StudySemester, pk=semester_pk)
        else:
            selected_semester = current

        if not course.external_ical_last_sync_at or course.external_ical_last_sync_at > timezone.localtime() - timedelta(days=4):
            # Update Semesterplan
            from lectures import ical_utils
            ical_sync_res = ical_utils.sync_StudyCourse_from_external_ical(
                course=course,
                confirm_overwrite=False,
                selected_semester=selected_semester
            )

        lessons = []
        if selected_semester:
            lessons = (
                Lesson.objects
                .filter(lecture__course=course, lecture__semester=selected_semester)
                .select_related('lecture__unit__module', 'room', 'lecturer__person')
                .order_by('start')
            )

        return render(request, self.template_name, {
            'course': course,
            'semesters': semesters,
            'selected_semester': selected_semester,
            'lessons': lessons,
        })


# ============= Grade Views =============

class GradeListView(PermissionMixin, ListView):
    """Liste aller Noten"""
    permission_required = 'lectures.view_grade'
    model = Grade
    template_name = 'lectures/grade_list.html'
    context_object_name = 'grades'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = Grade.objects.for_user(self.request.user).select_related(
            'student__person', 'module', 'unit'
        )
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(student__matri_nr__icontains=search) |
                Q(student__person__firstname__icontains=search) |
                Q(student__person__lastname__icontains=search) |
                Q(module__module_nr__icontains=search) |
                Q(module__name__icontains=search)
            )
        
        passed = self.request.GET.get('passed')
        if passed == 'yes':
            queryset = queryset.filter(passed=True)
        elif passed == 'no':
            queryset = queryset.filter(passed=False)
        
        student = self.request.GET.get('student')
        if student:
            queryset = queryset.filter(student_id=student)
        
        return queryset


class StudentGradesView(PermissionMixin, DetailView):
    """Notenübersicht eines Studenten"""
    permission_required = 'lectures.view_grade'
    model = 'persons.Student'
    template_name = 'lectures/student_grades.html'
    context_object_name = 'student'
    
    def get_queryset(self):
        from persons.models import Student
        return Student.objects.for_user(self.request.user).select_related('person', 'course', 'field')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.get_object()
        
        context['grades'] = student.grades.select_related(
            'module', 'unit'
        ).order_by('module__module_nr')
        
        context['grade_stats'] = student.grades.aggregate(
            avg=Avg('grade'),
            total_credits=Sum('module__credits', filter=Q(passed=True)),
            total_grades=Count('id'),
            num_passed=Count('id', filter=Q(passed=True)),
            num_failed=Count('id', filter=Q(passed=False))
        )
        
        # Noten nach Versuch gruppieren
        context['attempts'] = {
            1: student.grades.filter(attempt=1).count(),
            2: student.grades.filter(attempt=2).count(),
            3: student.grades.filter(attempt=3).count(),
        }
        
        return context


class DayView(TokenOrLoginMixin, TemplateView):
    """Renders the daily lecture overview page for all courses."""

    permission_required = 'organization.view_studycourse'
    template_name = "lectures/view-day.html"

    def get(self, request, *args, **kwargs):
        if request.GET.get('load'):
            self._sync_all_courses(request)
            # Redirect ohne ?load=1, damit ein Seiten-Reload keinen erneuten Sync auslöst
            params = request.GET.copy()
            params.pop('load')
            base_url = request.path
            redirect_url = f"{base_url}?{params.urlencode()}" if params else base_url
            return redirect(redirect_url)
        return super().get(request, *args, **kwargs)

    def _sync_all_courses(self, request):
        """Synchronisiert iCal-Pläne aller Kurse, auf die der User Zugriff hat."""
        from organization.models import StudyCourse
        from lectures import ical_utils
        courses = (
            StudyCourse.objects
            .for_person(self.get_person(request))
            .filter(study_phase__semester_id6p__end_date__gt=timezone.localdate())
            .filter(external_ical_url__isnull=False)
        )
        for course in courses:
            ical_utils.sync_StudyCourse_from_external_ical(
                course=course,
                confirm_overwrite=False,
            )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Token aus Query-Parameter weitergeben (für Token-basierte Authentifizierung)
        context["token"] = self.request.GET.get('token', '')

        # Optional deep-link date in format DDMMYYYY (e.g., /view-day/01042025)
        date_param = self.kwargs.get("date_param")
        if date_param:
            try:
                parsed_date = datetime.strptime(date_param, "%d%m%Y").date()
                context["initial_date"] = parsed_date.isoformat()
            except ValueError as exc:
                raise Http404("Invalid day-view date format. Use DDMMYYYY.") from exc

        # Get all courses ordered by course_nr
        from organization.models import StudyCourse
        courses = (
            StudyCourse.objects
            .for_person(self.get_person(self.request))
            .filter(study_phase__semester_id6p__end_date__gt=timezone.localdate())
            .filter(external_ical_url__isnull=False)  # korrekt
            .order_by("course_nr")
        )
        course_ids = [course.course_nr for course in courses]

        # Build plan data for each course
        courses_data = {}
        for course in courses:
            courses_data[course.course_nr] = self._get_course_plan_data(course)

        # Pass as JSON for JavaScript and as list for template iteration
        context["courses"] = json.dumps(course_ids)
        context["course_list"] = course_ids
        context["courses_data"] = json.dumps(courses_data)
        return context

    def _get_course_plan_data(self, course):
        """Generate plan data structure for a course with all lessons."""
        display_tz = ZoneInfo(settings.TIME_ZONE)

        # Fetch all lessons for this course
        lessons = (
            Lesson.objects.filter(lecture__course=course)
            .select_related("lecture__unit__module", "room", "lecturer__person")
            .order_by("start")
        )

        # Group lessons by week
        weeks_dict = {}
        for lesson in lessons:
            local_start = lesson.start.astimezone(display_tz)
            local_end = lesson.end.astimezone(display_tz)

            # Get the Monday of the week for this lesson
            lesson_date = local_start.date()
            # Calculate the Monday of this week (0 = Monday, 6 = Sunday)
            days_since_monday = lesson_date.weekday()
            week_start = lesson_date - timedelta(days=days_since_monday)
            week_key = week_start.isoformat()

            if week_key not in weeks_dict:
                weeks_dict[week_key] = {"week_start": week_key, "sessions": []}

            # Add session data
            session = {
                "date": lesson_date.isoformat(),
                "time": f"{local_start.strftime('%H:%M')}-{local_end.strftime('%H:%M')}",
                "module": lesson.lecture.unit.unit_name,
                "module_number": lesson.lecture.unit.unit_nr,
                "is_exam": lesson.is_exam,
                "room": lesson.room.name,
                "lecturer": lesson.lecturer.person.get_full_name()
                if lesson.lecturer
                else "N/A",
                "is_active": lesson.is_active,
            }
            weeks_dict[week_key]["sessions"].append(session)

        # Convert to list sorted by week
        weeks = sorted(weeks_dict.values(), key=lambda w: w["week_start"])

        return {
            "course_id": course.course_nr,
            "course_name": course.course_nr,
            "weeks": weeks,
        }

