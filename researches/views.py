from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Count, Q, Case, When, Sum
from django.http import Http404, HttpResponse
import csv
from django.utils import timezone
from accounts.mixins import PermissionMixin
from .models import Research, ResearchAssessorWish, ResearchMatchWish, ResearchPhase
from .forms import ResearchPhaseForm
from persons.models import Person, Personnel
from organization.models import StudyCourse
from sgverwaltung.base_views import ForUserDetailView
from sgverwaltung.email_utils import send_email



# ============= Dashboard =============

@login_required
def researches_dashboard(request):
    """Dashboard mit Übersicht"""
    today = timezone.localdate()
    
    my_researches = Research.objects.for_user(request.user)
    context = {
        'my_researches': my_researches,
    }
    if request.user.has_role('student'):
        course = request.user.person.student_profile.course

        context.update({
            "phases": [
                {
                    "label": "PA1",
                    "phase": course.pa1_phase or None,
                    "research": my_researches.filter(research_phase=course.pa1_phase).first() if course.pa1_phase else None,
                },
                {
                    "label": "PA2",
                    "phase": course.pa2_phase or None,
                    "research": my_researches.filter(research_phase=course.pa2_phase).first() if course.pa2_phase else None,
                },
                {
                    "label": "BA",
                    "phase": course.ba_phase or None,
                    "research": my_researches.filter(research_phase=course.ba_phase).first() if course.ba_phase else None,
                },
            ],
        })
        return render(request, 'researches/dashboard_student.html', context)

    if request.user.has_role('employee'):        
        my_researches = Research.objects.for_user(request.user)
        context.update({
            'my_researches': my_researches,
            'total_researches_pa1': my_researches.filter(unit_id=2).filter(Q(assessor_scien=request.user.person.personnel_profile)).count(),
            'total_researches_pa2': my_researches.filter(unit_id=5).filter(Q(assessor_scien=request.user.person.personnel_profile)).count(),
            'total_researches_ba': my_researches.filter(unit_id=8).filter(Q(assessor_scien=request.user.person.personnel_profile)).count(),
            'total_researches_finished': my_researches.filter(end_date__lte=today).count(),
            'total_researches_running': my_researches.filter(start_date__lte=today).filter(end_date__gte=today).count(),
            'total_researches_waiting': my_researches.filter(start_date__gte=today).count(),
            'sgl_courses': request.user.person.get_study_courses(),
            'upcoming_deadlines': Research.objects.for_user(request.user).filter(
                end_date__gte=today,
                end_date__lte=today + timezone.timedelta(days=14),
                topic_submitted_date__isnull=True
            ).select_related('student__person', 'unit')[:10],
            'recent_researches': Research.objects.for_user(request.user).select_related(
                'student__person', 'unit', 'assessor_scien__person'
            ).order_by('-id')[:10],
        })
        return render(request, 'researches/dashboard_employee.html', context)

    


# ============= Research Views =============

class ResearchListView(PermissionMixin, ListView):
    """Liste aller Forschungsarbeiten"""
    permission_required = 'researches.view_research'
    model = Research
    template_name = 'researches/research_list.html'
    context_object_name = 'researches'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = Research.objects.for_user(self.request.user).select_related(
            'student__person', 'unit', 'assessor_scien__person'
        )

        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(student__matri_nr__icontains=search) |
                Q(student__person__firstname__icontains=search) |
                Q(student__person__lastname__icontains=search)
            )

        status = self.request.GET.get('status')
        if status == 'approved':
            queryset = queryset.filter(approved_oper=True, approved_scien=True, approved_orga=True)
        elif status == 'not_approved':
            queryset = queryset.filter(
                Q(approved_oper=False) | Q(approved_scien=False) | Q(approved_orga=False)
            )
        elif status == 'submitted':
            queryset = queryset.filter(topic_submitted_date__isnull=False)
        elif status == 'overdue':
            queryset = queryset.filter(
                end_date__lt=timezone.localdate(),
                topic_submitted_date__isnull=True
            )
        elif status == 'in_progress':
            today = timezone.localdate()
            queryset = queryset.filter(
                start_date__lte=today,
                end_date__gte=today,
                topic_submitted_date__isnull=True
            )
        
        return queryset


class ResearchDetailView(ForUserDetailView):
    """Detailansicht einer Forschungsarbeit"""
    permission_required = 'researches.view_research'
    model = Research
    template_name = 'researches/research_detail.html'
    context_object_name = 'research'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['match_wishes'] = self.object.match_wishes.select_related(
            'person_from', 'personnel_who__person'
        ).all()
        return context


# ============= Themeneinreichung (Studierende) =============

def _get_student_research_or_404(request, pk):
    """Hilfsfunktion: Gibt Research zurück, wenn der eingeloggte User der Student ist."""
    research = get_object_or_404(
        Research.objects.for_user(request.user).select_related(
            'student__person', 'student__course', 'student__company',
            'student__company_person', 'assessor_oper', 'unit'
        ),
        pk=pk
    )
    if (research is None 
        or not request.user.is_authenticated
        or not hasattr(request.user, 'person')
        or not hasattr(request.user.person, 'student_profile')
        or research.student != request.user.person.student_profile
    ):
        raise Http404
    return research


@login_required
def research_form_start(request, phase_pk):
    """Einstiegspunkt für Themeneinreichung – erstellt Research falls noch keine existiert."""
    if (not request.user.is_authenticated
            or not hasattr(request.user, 'person')
            or not hasattr(request.user.person, 'student_profile')):
        raise Http404

    student = request.user.person.student_profile
    phase = get_object_or_404(ResearchPhase, pk=phase_pk)

    course = student.course
    if phase == course.pa1_phase:
        unit = getattr(course.study_regulation, 'unit_pa1', None)
    elif phase == course.pa2_phase:
        unit = getattr(course.study_regulation, 'unit_pa2', None)
    elif phase == course.ba_phase:
        unit = getattr(course.study_regulation, 'unit_ba', None)
    else:
        raise Http404

    if not unit:
        raise Http404

    research = Research.objects.filter(student=student, research_phase=phase).first()
    if not research:
        research = Research.objects.create(
            student=student,
            unit=unit,
            research_phase=phase,
            topic_submit_deadline=phase.submission_date,
            start_date=phase.start_date,
            end_date=phase.end_date,
        )

    return redirect('researches:research_form', pk=research.pk)


@login_required
def research_form(request, pk):
    """Themeneinreichung – Formular (Zwischenspeichern & Vorschau)"""
    research = _get_student_research_or_404(request, pk)
    today = timezone.localdate()

    if research.topic_submitted_date or research.topic_submit_deadline < today:
        return redirect('researches:research_form_preview', pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action in ('save', 'preview'):
            bet_gender = request.POST.get('bet_salutation_short') or None
            bet_title = request.POST.get('bet_title', '').strip() or None
            bet_firstname = request.POST.get('bet_firstname', '').strip()
            bet_lastname = request.POST.get('bet_lastname', '').strip()
            bet_email = request.POST.get('bet_email', '').strip() or None
            bet_tel = request.POST.get('bet_tel', '').strip() or None
            bet_approved = bool(request.POST.get('bet_approved'))

            salutation_map = {'M': 'Herr', 'F': 'Frau', 'D': ''}
            greeting_map = {'M': 'Sehr geehrter Herr ', 'F': 'Sehr geehrte Frau ', 'D': ''}
            salutation_short = salutation_map.get(bet_gender, '')
            salutation_full = greeting_map.get(bet_gender, '') + bet_lastname

            if research.assessor_oper_id:
                existing = research.assessor_oper
                if existing.firstname == bet_firstname and existing.lastname == bet_lastname:
                    # Gleiche Person – Daten aktualisieren
                    Person.objects.filter(pk=existing.pk).update(
                        title=bet_title,
                        gender=bet_gender,
                        salutation_short=salutation_short,
                        salutation_full=salutation_full,
                        mail_main=bet_email,
                        tel_main=bet_tel,
                    )
                else:
                    # Name hat sich geändert – andere Person, suchen oder neu anlegen
                    assessor = None
                    if bet_firstname and bet_lastname and bet_email:
                        assessor = Person.objects.filter(
                            firstname=bet_firstname,
                            lastname=bet_lastname,
                            mail_main=bet_email,
                        ).first()
                    if not assessor:
                        assessor = Person.objects.create(
                            title=bet_title,
                            gender=bet_gender,
                            salutation_short=salutation_short,
                            salutation_full=salutation_full,
                            firstname=bet_firstname,
                            lastname=bet_lastname,
                            mail_main=bet_email,
                            tel_main=bet_tel,
                            role_now='COAS',
                        )
                    research.assessor_oper = assessor
            else:
                # Noch kein betrieblicher Betreuer – existierende Person suchen oder neu anlegen
                assessor = None
                if bet_firstname and bet_lastname and bet_email:
                    assessor = Person.objects.filter(
                        firstname=bet_firstname,
                        lastname=bet_lastname,
                        mail_main=bet_email,
                    ).first()
                if not assessor:
                    assessor = Person.objects.create(
                        title=bet_title,
                        gender=bet_gender,
                        salutation_short=salutation_short,
                        salutation_full=salutation_full,
                        firstname=bet_firstname,
                        lastname=bet_lastname,
                        mail_main=bet_email,
                        tel_main=bet_tel,
                        role_now='COAS',
                    )
                research.assessor_oper = assessor

            research.title = request.POST.get('res_title', '').strip() or None
            research.problem = request.POST.get('res_problem', '').strip() or None
            research.goal = request.POST.get('res_goal', '').strip() or None
            research.methodology = request.POST.get('res_method', '').strip() or None
            research.approved_oper = bet_approved
            research.comment = request.POST.get('wunschbetreuung', '').strip() or None
            research.company_context = request.POST.get('bet_dual_partner', '').strip() or None
            research.save()     

            if action == 'preview':
                return redirect('researches:research_form_preview', pk=pk)
            return redirect('researches:research_form', pk=pk)
       

    # company_context fällt auf Firmenname des Studenten zurück
    company_context = research.company_context
    if not company_context and research.student.company:
        company_context = research.student.company.name

    context = {
        'research': research,
        'student': research.student,
        'company_context': company_context,
        'today': today
    }

    return render(request, 'researches/research_form.html', context)


@login_required
def research_form_preview(request, pk):
    """Themeneinreichung – Vorschau & finale Einreichung"""
    research = _get_student_research_or_404(request, pk)

    if request.method == 'POST' and request.POST.get('action') == 'submit':
        if not research.topic_submitted_date:
            research.topic_submitted_date = timezone.localdate()
            research.save()
            send_email(
                to=['tessa.steinigke@heilbronn.dhbw.de'],
                subject='Neue Themeneinreichung',
                body='Es ist eine neue Themeneinreichung eingegangen. ',
            )
        return redirect('researches:research_form_preview', pk=pk)

    context = {
        'research': research,
        'student': research.student,
        'today': timezone.localdate(),
        'time': timezone.localtime(timezone.now()),
    }
    return render(request, 'researches/research_form_preview.html', context)


@login_required
def research_edit(request, pk):
    """Forschungsarbeit bearbeiten – für Mitarbeiter"""
    if not request.user.has_role('employee'):
        raise Http404

    research = get_object_or_404(
        Research.objects.select_related(
            'student__person', 'student__course', 'student__company',
            'assessor_oper', 'assessor_scien__person', 'unit', 'research_phase'
        ),
        pk=pk
    )

    if request.method == 'POST':
        research.title = request.POST.get('title', '').strip() or None
        research.problem = request.POST.get('problem', '').strip() or None
        research.goal = request.POST.get('goal', '').strip() or None
        research.methodology = request.POST.get('methodology', '').strip() or None
        research.company_context = request.POST.get('company_context', '').strip() or None
        research.comment = request.POST.get('comment', '').strip() or None
        research.approved_oper = bool(request.POST.get('approved_oper'))
        research.approved_scien = bool(request.POST.get('approved_scien'))
        research.approved_orga = bool(request.POST.get('approved_orga'))
        research.assessor_scien_id = request.POST.get('assessor_scien') or None
        research.assessor_oper_id = request.POST.get('assessor_oper') or None

        for field in ('start_date', 'end_date', 'topic_submit_deadline'):
            val = request.POST.get(field, '').strip()
            if val:
                try:
                    setattr(research, field, timezone.datetime.fromisoformat(val).date())
                except ValueError:
                    pass

        val = request.POST.get('topic_submitted_date', '').strip()
        try:
            research.topic_submitted_date = timezone.datetime.fromisoformat(val).date() if val else None
        except ValueError:
            pass

        research.save()
        return redirect('researches:research_detail', pk=pk)

    coas_persons = Person.objects.for_user(request.user).filter(role_now='COAS').order_by('lastname', 'firstname')
    course_personnel = Personnel.objects.for_user(request.user).filter(
        organisations__courses=research.student.course
    ).distinct().select_related('person').order_by('person__lastname', 'person__firstname')

    context = {
        'research': research,
        'coas_persons': coas_persons,
        'course_personnel': course_personnel,
    }
    return render(request, 'researches/research_edit.html', context)


# ============= ResearchPhase Views =============

class ResearchPhaseListView(PermissionMixin, ListView):
    """Liste aller Forschungsphasen"""
    permission_required = 'researches.view_researchphase'
    model = ResearchPhase
    template_name = 'researches/researchphase_list.html'
    context_object_name = 'phases'

    def get_queryset(self):
        return ResearchPhase.objects.for_user(self.request.user)


class ResearchPhaseDetailView(PermissionMixin, DetailView):
    """Detailansicht einer Forschungsphase inkl. zugehöriger Arbeiten"""
    permission_required = 'researches.view_researchphase'
    model = ResearchPhase
    template_name = 'researches/researchphase_detail.html'
    context_object_name = 'phase'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        courses = _build_course_assignments(self.request.user, self.object)
        researches = self.object.researches.select_related(
            'student__person', 'unit', 'assessor_scien__person'
        ).all()
        total_students = sum(
            entry['course'].total_students 
            for entry in courses 
            if entry['current_type'] is not None
        )
        total_students_topic_submitted = researches.filter(
            topic_submitted_date__isnull=False
        ).count()

        total_students_assessor_scien = researches.filter(
            assessor_scien_id__isnull=False
        ).count()

        context['researches'] = researches
        context['courses'] = courses
        context['total_students'] = total_students
        context['total_students_topic_submitted'] = total_students_topic_submitted
        context['total_students_assessor_scien'] = total_students_assessor_scien
        return context
    

def _build_course_assignments(user, phase=None):
    """Gibt alle Kurse zurück, mit dem aktuell zugewiesenen Typ (PA1/PA2/BA/None) für diese Phase."""
    courses = StudyCourse.objects.for_user(user).select_related(
        'field__study', 'academic_year'
    ).annotate(
        total_students=Count('students')
    ).all()

    # Kurse mit Arbeiten in dieser Phase vorab ermitteln (eine DB-Abfrage)
    locked_course_pks = set()
    if phase:
        locked_course_pks = set(
            Research.objects.filter(research_phase=phase)
            .values_list('student__course_id', flat=True)
            .distinct()
        )

    result = []
    phase_pk = phase.pk if phase else None
    for course in courses:
        current_type = None
        if phase_pk:
            if course.pa1_phase_id == phase_pk:
                current_type = 'PA1'
            elif course.pa2_phase_id == phase_pk:
                current_type = 'PA2'
            elif course.ba_phase_id == phase_pk:
                current_type = 'BA'
        # Typen sperren, die bereits einer anderen Phase zugewiesen sind
        blocked = set()
        if course.pa1_phase_id and course.pa1_phase_id != phase_pk:
            blocked.add('PA1')
        if course.pa2_phase_id and course.pa2_phase_id != phase_pk:
            blocked.add('PA2')
        if course.ba_phase_id and course.ba_phase_id != phase_pk:
            blocked.add('BA')
        # Gesamte Zeile sperren, wenn der Kurs bereits Arbeiten in dieser Phase hat
        locked = course.pk in locked_course_pks
        result.append({'course': course, 'current_type': current_type, 'blocked_types': blocked, 'locked': locked})
    return result


def _save_course_assignments(post_data, phase):
    """Liest die Kurs-Zuweisungen aus POST und aktualisiert die StudyCourse-Objekte."""
    locked_course_pks = set(
        Research.objects.filter(research_phase=phase)
        .values_list('student__course_id', flat=True)
        .distinct()
    )
    courses = StudyCourse.objects.all()
    for course in courses:
        if course.pk in locked_course_pks:
            continue
        selected = post_data.get(f'course_{course.pk}_type', '')
        changed = False
        if course.pa1_phase_id == phase.pk and selected != 'PA1':
            course.pa1_phase = None
            changed = True
        if course.pa2_phase_id == phase.pk and selected != 'PA2':
            course.pa2_phase = None
            changed = True
        if course.ba_phase_id == phase.pk and selected != 'BA':
            course.ba_phase = None
            changed = True
        if selected == 'PA1' and course.pa1_phase_id != phase.pk:
            course.pa1_phase = phase
            changed = True
        elif selected == 'PA2' and course.pa2_phase_id != phase.pk:
            course.pa2_phase = phase
            changed = True
        elif selected == 'BA' and course.ba_phase_id != phase.pk:
            course.ba_phase = phase
            changed = True
        if changed:
            course.save()


class ResearchPhaseCreateView(PermissionMixin, CreateView):
    """Neue Forschungsphase anlegen"""
    permission_required = 'researches.add_researchphase'
    model = ResearchPhase
    form_class = ResearchPhaseForm
    template_name = 'researches/researchphase_form.html'
    success_url = reverse_lazy('researches:researchphase_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course_assignments'] = _build_course_assignments(self.request.user)
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        _save_course_assignments(self.request.POST, self.object)
        return response


class ResearchPhaseUpdateView(PermissionMixin, UpdateView):
    """Forschungsphase bearbeiten"""
    permission_required = 'researches.change_researchphase'
    model = ResearchPhase
    form_class = ResearchPhaseForm
    template_name = 'researches/researchphase_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course_assignments'] = _build_course_assignments(self.request.user, self.object)
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        _save_course_assignments(self.request.POST, self.object)
        return response

    def get_success_url(self):
        return reverse_lazy('researches:researchphase_detail', kwargs={'pk': self.object.pk})


class ResearchPhaseDeleteView(PermissionMixin, DeleteView):
    """Forschungsphase löschen"""
    permission_required = 'researches.delete_researchphase'
    model = ResearchPhase
    template_name = 'researches/researchphase_confirm_delete.html'
    context_object_name = 'phase'
    success_url = reverse_lazy('researches:researchphase_list')


@login_required
def researchphase_csv_export(request, pk):
    """CSV-Export aller Forschungsarbeiten einer Phase"""
    if not request.user.has_perm('researches.view_researchphase'):
        raise Http404

    phase = get_object_or_404(ResearchPhase, pk=pk)
    researches = phase.researches.select_related(
        'student__person', 'unit', 'assessor_scien__person', 'assessor_oper', 'research_phase'
    ).all()

    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="phase_{phase.pk}_{phase.name}_forschungsarbeiten.csv"'
    response.write('\ufeff')  # BOM für Excel

    writer = csv.writer(response, delimiter=';')
    writer.writerow([
        'Research-ID', 'Matrikelnummer', 'Student-ID', 'Student',
        'Veranstaltung-ID', 'Veranstaltung', 'Phase-ID', 'Phase',
        'Titel', 'Problemstellung', 'Zielsetzung', 'Methodik',
        'Wiss. Betreuer-ID', 'Wiss. Betreuer',
        'Betr. Betreuer-ID', 'Betr. Betreuer',
        'Firma Betreuung', 'Kommentar',
        'Thema einreichen bis', 'Thema eingereicht am',
        'Startdatum', 'Abgabefrist',
        'Genehmigt (Betrieb)', 'Genehmigt (Wiss.)', 'Genehmigt (Orga)',
        'Status',
    ])

    def fmt_date(d):
        return d.strftime('%d.%m.%Y') if d else '–'

    def ja_nein(b):
        return 'Ja' if b else 'Nein'

    for r in researches:
        writer.writerow([
            r.pk,
            r.student.matri_nr,
            r.student_id,
            r.student.person.get_full_name(),
            r.unit_id,
            r.unit.unit_name_short or r.unit.unit_name,
            r.research_phase_id,
            r.research_phase.name if r.research_phase else '–',
            r.title or '',
            r.problem or '',
            r.goal or '',
            r.methodology or '',
            r.assessor_scien_id or '',
            r.assessor_scien.person.get_full_name() if r.assessor_scien else '–',
            r.assessor_oper_id or '',
            r.assessor_oper.get_full_name() if r.assessor_oper else '–',
            r.company_context or '',
            r.comment or '',
            fmt_date(r.topic_submit_deadline),
            fmt_date(r.topic_submitted_date),
            fmt_date(r.start_date),
            fmt_date(r.end_date),
            ja_nein(r.approved_oper),
            ja_nein(r.approved_scien),
            ja_nein(r.approved_orga),
            r.status_display,
        ])

    return response
