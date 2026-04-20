from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView, DetailView
from django.db.models import Count, Q
from django.utils import timezone
from accounts.mixins import PermissionMixin
from .models import (
    StudyProgram,
    StudyField,
    StudyAcademy,
    StudyOrganisation,
    StudySemester,
    StudyYear,
    StudyCourse
)
from sgverwaltung.base_views import ForUserDetailView
from django.db.models.functions import Substr, Length


# ============= Dashboard =============

@login_required
def organization_dashboard(request):
    """Dashboard mit Übersicht"""
    today = timezone.localdate()
    
    context = {
        'total_programs': StudyProgram.objects.for_user(request.user).count(),
        'total_fields': StudyField.objects.for_user(request.user).count(),
        'total_academies': StudyAcademy.objects.for_user(request.user).count(),
        'total_courses': StudyCourse.objects.for_user(request.user).count(),
        'total_semesters': StudySemester.objects.for_user(request.user).count(),
        'active_semesters': StudySemester.objects.for_user(request.user).filter(
            start_date__lte=today,
            end_date__gte=today
        ).count(),
        'recent_courses': StudyCourse.objects.for_user(request.user).select_related(
            'academy', 'field', 'academic_year'
        ).order_by('-id')[:5],
    }
    return render(request, 'organization/dashboard.html', context)


# ============= StudyProgram Views =============

class StudyProgramListView(PermissionMixin, ListView):
    """Liste aller Studiengänge"""
    permission_required = 'organization.view_studyprogram'
    model = StudyProgram
    template_name = 'organization/studyprogram_list.html'
    context_object_name = 'programs'
    
    def get_queryset(self):
        queryset = StudyProgram.objects.for_user(self.request.user).annotate(
            field_count=Count('fields')
        )
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(study_progr__icontains=search)
        
        return queryset


class StudyProgramDetailView(PermissionMixin, DetailView):
    """Detailansicht eines Studiengangs"""
    permission_required = 'organization.view_studyprogram'
    model = StudyProgram
    template_name = 'organization/studyprogram_detail.html'
    context_object_name = 'program'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['fields'] = self.object.fields.all()
        return context


# ============= StudyField Views =============

class StudyFieldListView(PermissionMixin, ListView):
    """Liste aller Studienrichtungen"""
    permission_required = 'organization.view_studyfield'
    model = StudyField
    template_name = 'organization/studyfield_list.html'
    context_object_name = 'fields'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = StudyField.objects.for_user(self.request.user).select_related('study').annotate(
            course_count=Count('courses')
        )
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(studyfield__icontains=search) |
                Q(study__study_progr__icontains=search)
            )
        
        program = self.request.GET.get('program')
        if program:
            queryset = queryset.filter(study_id=program)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['programs'] = StudyProgram.objects.all()
        return context


class StudyFieldDetailView(PermissionMixin, DetailView):
    """Detailansicht einer Studienrichtung"""
    permission_required = 'organization.view_studyfield'
    model = StudyField
    template_name = 'organization/studyfield_detail.html'
    context_object_name = 'field'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['courses'] = self.object.courses.select_related(
            'academy', 'academic_year'
        ).all()
        return context


# ============= StudyAcademy Views =============

class StudyAcademyListView(PermissionMixin, ListView):
    """Liste aller Akademien"""
    permission_required = 'organization.view_studyacademy'
    model = StudyAcademy
    template_name = 'organization/studyacademy_list.html'
    context_object_name = 'academies'
    
    def get_queryset(self):
        queryset = StudyAcademy.objects.for_user(self.request.user).annotate(
            course_count=Count('courses')
        )
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(academy_name__icontains=search)
        
        return queryset


class StudyAcademyDetailView(PermissionMixin, DetailView):
    """Detailansicht einer Akademie"""
    permission_required = 'organization.view_studyacademy'
    model = StudyAcademy
    template_name = 'organization/studyacademy_detail.html'
    context_object_name = 'academy'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['courses'] = self.object.courses.select_related(
            'field', 'academic_year'
        ).all()
        return context


# ============= StudySemester Views =============

class StudySemesterListView(PermissionMixin, ListView):
    """Liste aller Semester"""
    permission_required = 'organization.view_studysemester'
    model = StudySemester
    template_name = 'organization/studysemester_list.html'
    context_object_name = 'semesters'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(name_short__icontains=search)
            )
        
        semester_type = self.request.GET.get('type')
        if semester_type:
            queryset = queryset.filter(type=semester_type)
        
        cycle = self.request.GET.get('cycle')
        if cycle:
            queryset = queryset.filter(cycle=cycle)
        
        # Filter: Nur aktive Semester
        active = self.request.GET.get('active')
        if active == 'yes':
            from django.utils import timezone
            today = timezone.localdate()
            queryset = queryset.filter(start_date__lte=today, end_date__gte=today)
        
        return queryset.order_by('-start_date')


class StudySemesterDetailView(PermissionMixin, DetailView):
    """Detailansicht eines Semesters"""
    permission_required = 'organization.view_studysemester'
    model = StudySemester
    template_name = 'organization/studysemester_detail.html'
    context_object_name = 'semester'


# ============= StudyYear Views =============

class StudyYearListView(PermissionMixin, ListView):
    """Liste aller Studienjahre"""
    permission_required = 'organization.view_studyyear'
    model = StudyYear
    template_name = 'organization/studyyear_list.html'
    context_object_name = 'years'
    
    def get_queryset(self):
        queryset = StudyYear.objects.for_user(self.request.user).prefetch_related(
            'semester_id1t', 'semester_id1p',
            'semester_id2t', 'semester_id2p',
            'semester_id3t', 'semester_id3p',
            'semester_id4t', 'semester_id4p',
            'semester_id5t', 'semester_id5p',
            'semester_id6t', 'semester_id6p'
        )
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(year_name__icontains=search)
        
        return queryset


class StudyYearDetailView(PermissionMixin, DetailView):
    """Detailansicht eines Studienjahres"""
    permission_required = 'organization.view_studyyear'
    model = StudyYear
    template_name = 'organization/studyyear_detail.html'
    context_object_name = 'year'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['courses'] = self.object.courses.select_related('academy', 'field').all()
        return context


# ============= StudyCourse Views =============

class StudyCourseListView(PermissionMixin, ListView):
    """Liste aller Kurse"""
    permission_required = 'organization.view_studycourse'
    model = StudyCourse
    template_name = 'organization/studycourse_list.html'
    context_object_name = 'courses'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = StudyCourse.objects.for_user(self.request.user).select_related(
            'academy', 'field', 'academic_year', 'organisation'
        ).annotate(
            num_students=Count('students')
        )
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(course_nr__icontains=search) |
                Q(academy__academy_name__icontains=search)
            )
        
        academy = self.request.GET.get('academy')
        if academy:
            queryset = queryset.filter(academy_id=academy)
        
        field = self.request.GET.get('field')
        if field:
            queryset = queryset.filter(field_id=field)
        
        year = self.request.GET.get('year')
        if year:
            queryset = queryset.filter(academic_year_id=year)

        queryset = queryset.annotate(
            course_nr_last4=Substr('course_nr', Length('course_nr') - 3, 4)   
        ).order_by('-course_nr_last4')

        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['academies'] = StudyAcademy.objects.all()
        context['fields'] = StudyField.objects.all()
        context['years'] = StudyYear.objects.all()
        return context


class StudyCourseDetailView(ForUserDetailView):
    """Detailansicht eines Kurses"""
    permission_required = 'organization.view_studycourse'
    model = StudyCourse
    template_name = 'organization/studycourse_detail.html'
    context_object_name = 'course'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['students'] = self.object.students.select_related('person').all()
        context['can_edit'] = self.request.user.has_perm('organization.change_studycourse')
        if(self.object.study_phase):
            context['semesters'] = self.object.study_phase.get_all_semesters()
            context['current_semester'] = self.object.study_phase.get_current_semester()
        return context


class StudyCourseUpdateICalView(PermissionMixin, View):
    """Inline-Update für external_ical_url eines Kurses"""
    permission_required = 'organization.change_studycourse'

    def post(self, request, pk):
        course = get_object_or_404(StudyCourse, pk=pk)
        url = request.POST.get('external_ical_url', '').strip()
        course.external_ical_url = url or None
        course.save(update_fields=['external_ical_url'])
        from lectures import ical_utils
        ical_utils.sync_StudyCourse_from_external_ical(
            course=course,
            confirm_overwrite=False,
        )
        return redirect('organization:course_detail', pk=pk)