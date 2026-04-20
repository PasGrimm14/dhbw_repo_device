from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.db.models import Q, Count
from accounts.mixins import PermissionMixin
from .models import Person, Student, Personnel, Company, StudyCourse
from sgverwaltung.base_views import ForUserDetailView

# Person Views
class PersonListView(PermissionMixin, ListView):
    """Liste aller Personen"""
    permission_required = 'persons.view_person'
    model = Person
    template_name = 'persons/person_list.html'
    context_object_name = 'persons'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = Person.objects.for_user(self.request.user)
        
        # Filter nach Rolle
        role = self.request.GET.get('role')
        if role:
            queryset = queryset.filter(role_now=role)
        
        # Suche
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                firstname__icontains=search
            ) | queryset.filter(
                lastname__icontains=search
            ) | queryset.filter(
                mail_main__icontains=search
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['role_choices'] = Person.ROLE_CHOICES
        context['current_role'] = self.request.GET.get('role', '')
        context['search_query'] = self.request.GET.get('search', '')
        return context


class PersonDetailView(ForUserDetailView):
    """Detailansicht einer Person"""
    permission_required = 'persons.view_person'
    model = Person
    template_name = 'persons/person_detail.html'
    context_object_name = 'person'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        person = self.get_object()
        
        # Prüfe ob Student
        try:
            context['student'] = person.student_profile
        except Student.DoesNotExist:
            context['student'] = None
        
        # Prüfe ob Personal
        try:
            context['personnel'] = person.personnel_profile
        except Personnel.DoesNotExist:
            context['personnel'] = None
        
        return context


# Student Views
class StudentListView(PermissionMixin, ListView):
    """Liste aller Studenten"""
    permission_required = 'persons.view_student'
    model = Student
    template_name = 'persons/student_list.html'
    context_object_name = 'students'
    paginate_by = 50

    def get_queryset(self):
        queryset = Student.objects.for_user(self.request.user).select_related('person', 'course', 'field', 'company')
        
        # Filter nach Kurs
        course = self.request.GET.get('course')
        if course:
            queryset = queryset.filter(course_id=course)
        
        # Filter nach Studienrichtung
        field = self.request.GET.get('field')
        if field:
            queryset = queryset.filter(field_id=field)
        
        # Suche
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                matri_nr__icontains=search
            ) | queryset.filter(
                person__firstname__icontains=search
            ) | queryset.filter(
                person__lastname__icontains=search
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context


class StudentDetailView(ForUserDetailView):
    """Detailansicht eines Studenten"""
    permission_required = 'persons.view_student'
    model = Student
    template_name = 'persons/student_detail.html'
    context_object_name = 'student'
    
    def get_queryset(self):
        return super().get_queryset().select_related(
            'person', 'course', 'field', 'company', 'company_person'
        )


# Personnel Views
class PersonnelListView(PermissionMixin, ListView):
    """Liste aller Mitarbeiter/Dozenten"""
    permission_required = 'persons.view_personnel'
    model = Personnel
    template_name = 'persons/personnel_list.html'
    context_object_name = 'personnel_list'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = Personnel.objects.for_user(self.request.user).select_related('person')
        
        # Filter nach Aktantentyp
        actant_type = self.request.GET.get('actant_type')
        if actant_type:
            queryset = queryset.filter(actant_type=actant_type)
        
        # Suche
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                personnel_nr__icontains=search
            ) | queryset.filter(
                person__firstname__icontains=search
            ) | queryset.filter(
                person__lastname__icontains=search
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context


class PersonnelDetailView(ForUserDetailView):
    """Detailansicht eines Mitarbeiters"""
    permission_required = 'persons.view_personnel'
    model = Personnel
    template_name = 'persons/personnel_detail.html'
    context_object_name = 'personnel'
    
    def get_queryset(self):
        return super().get_queryset().select_related('person')
    

# Dashboard View
@login_required
def persons_dashboard(request):
    """Dashboard mit Übersicht"""
    
    if request.user.has_role('employee'): 
        # Statistiken
        total_companies = Company.objects.for_user(request.user).count()
        companies_with_students = Company.objects.for_user(request.user).annotate(
            num_students=Count('students', filter=Q(students__in=Student.objects.for_user(request.user)))
        ).filter(num_students__gt=0).count()

        # Top Unternehmen nach Studentenanzahl
        top_companies = Company.objects.for_user(request.user).annotate(
            num_students=Count('students', filter=Q(students__in=Student.objects.for_user(request.user)))
        ).filter(num_students__gt=0).order_by('-num_students')[:10]

        # Neueste Unternehmen
        recent_companies = Company.objects.for_user(request.user).order_by('-id')[:5]

        # Unternehmen nach Bundesland
        companies_by_state = Company.objects.for_user(request.user).values('state').annotate(
            count=Count('id')
        ).order_by('-count')[:5]

        context = {
            #'total_persons': Person.objects.for_user(request.user).count(),
            'total_courses': StudyCourse.objects.for_user(request.user).count(),
            'total_students': Student.objects.for_user(request.user).count(),
            'total_personnel': Personnel.objects.for_user(request.user).count(),
            'recent_persons': Person.objects.for_user(request.user).order_by('-id')[:5],
            'total_companies': total_companies,
            'companies_with_students': companies_with_students,
            'companies_without_students': total_companies - companies_with_students,
            'top_companies': top_companies,
            'recent_companies': recent_companies,
            'companies_by_state': companies_by_state,
        }
    
        return render(request, 'dashboard_employee.html', context)
    elif request.user.has_role('student'): 
        return redirect('researches:dashboard') # Bisher lohnt sich noch kein Dashboard
    else:
        context = {}
        return render(request, 'dashboard.html', context)


class CompanyListView(PermissionMixin, ListView):
    """Liste aller Unternehmen"""
    permission_required = 'persons.view_company'
    model = Company
    template_name = 'persons/company_list.html'
    context_object_name = 'companies'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = Company.objects.for_user(self.request.user).annotate(
            num_students=Count('students', filter=Q(students__in=Student.objects.for_user(self.request.user)))
        )
        
        # Suche
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(city__icontains=search) |
                Q(postal_code__icontains=search) |
                Q(company_nr__icontains=search)
            )
        
        # Filter nach Stadt
        city = self.request.GET.get('city')
        if city:
            queryset = queryset.filter(city__icontains=city)
        
        # Filter nach Bundesland
        state = self.request.GET.get('state')
        if state:
            queryset = queryset.filter(state__icontains=state)
        
        # Filter: Nur mit Studenten
        has_students = self.request.GET.get('has_students')
        if has_students == 'yes':
            queryset = queryset.filter(num_students__gt=0)
        elif has_students == 'no':
            queryset = queryset.filter(num_students=0)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['city_filter'] = self.request.GET.get('city', '')
        context['state_filter'] = self.request.GET.get('state', '')
        context['has_students_filter'] = self.request.GET.get('has_students', '')
        
        # Statistiken
        context['total_companies'] = Company.objects.for_user(self.request.user).count()
        context['companies_with_students'] = Company.objects.for_user(self.request.user).annotate(
            num_students=Count('students')
        ).filter(num_students__gt=0).count()
        
        return context


class CompanyDetailView(ForUserDetailView):
    """Detailansicht eines Unternehmens"""
    permission_required = 'persons.view_company'
    model = Company
    template_name = 'persons/company_detail.html'
    context_object_name = 'company'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.get_object()
        
        # Studenten des Unternehmens
        context['students'] = company.students.select_related('person').all()
        
        return context




