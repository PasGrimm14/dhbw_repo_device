from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .models import (
    StudyProgram,
    StudyField,
    StudyAcademy,
    StudyOrganisation,
    StudySemester,
    StudyYear,
    StudyCourse
)


class StudyProgramModelTest(TestCase):
    """Tests für StudyProgram Model"""
    
    def setUp(self):
        self.program = StudyProgram.objects.create(
            study_progr='Wirtschaftsinformatik'
        )
    
    def test_program_creation(self):
        self.assertEqual(self.program.study_progr, 'Wirtschaftsinformatik')
        self.assertEqual(str(self.program), 'Wirtschaftsinformatik')


class StudyFieldModelTest(TestCase):
    """Tests für StudyField Model"""
    
    def setUp(self):
        self.program = StudyProgram.objects.create(study_progr='Informatik')
        self.field = StudyField.objects.create(
            study=self.program,
            studyfield='Software Engineering'
        )
    
    def test_field_creation(self):
        self.assertEqual(self.field.studyfield, 'Software Engineering')
        self.assertEqual(str(self.field), 'Informatik - Software Engineering')


class StudySemesterModelTest(TestCase):
    """Tests für StudySemester Model"""
    
    def setUp(self):
        today = timezone.localdate()
        self.semester = StudySemester.objects.create(
            name='Wintersemester 2024/25 - Theorie',
            name_short='WS24/25-T',
            start_date=today - timedelta(days=30),
            end_date=today + timedelta(days=60),
            type='Theorie',
            cycle='A'
        )
    
    def test_semester_creation(self):
        self.assertEqual(self.semester.name_short, 'WS24/25-T')
        self.assertEqual(self.semester.type, 'Theorie')
    
    def test_is_active(self):
        """Test ob Semester als aktiv erkannt wird"""
        self.assertTrue(self.semester.is_active)
    
    def test_duration_days(self):
        """Test Dauer-Berechnung"""
        self.assertEqual(self.semester.duration_days, 90)


class StudyCourseModelTest(TestCase):
    """Tests für StudyCourse Model"""
    
    def setUp(self):
        # Setup dependencies
        self.academy = StudyAcademy.objects.create(academy_name='DHBW Stuttgart')
        self.program = StudyProgram.objects.create(study_progr='Informatik')
        self.field = StudyField.objects.create(
            study=self.program,
            studyfield='Software Engineering'
        )
        self.organisation = StudyOrganisation.objects.create(name='DHBW')
        
        # Create semesters for StudyYear
        today = timezone.localdate()
        semesters = []
        for i in range(12):
            sem = StudySemester.objects.create(
                name=f'Semester {i+1}',
                name_short=f'S{i+1}',
                start_date=today + timedelta(days=i*90),
                end_date=today + timedelta(days=(i+1)*90-1),
                type='Theorie' if i % 2 == 0 else 'Praxis',
                cycle='A'
            )
            semesters.append(sem)
        
        self.year = StudyYear.objects.create(
            year_name='2024',
            semester_id1t=semesters[0],
            semester_id1p=semesters[1],
            semester_id2t=semesters[2],
            semester_id2p=semesters[3],
            semester_id3t=semesters[4],
            semester_id3p=semesters[5],
            semester_id4t=semesters[6],
            semester_id4p=semesters[7],
            semester_id5t=semesters[8],
            semester_id5p=semesters[9],
            semester_id6t=semesters[10],
            semester_id6p=semesters[11],
        )
        
        self.course = StudyCourse.objects.create(
            academy=self.academy,
            field=self.field,
            course_nr='TINF2024A',
            academic_year=self.year,
            organisation=self.organisation
        )
    
    def test_course_creation(self):
        self.assertEqual(self.course.course_nr, 'TINF2024A')
        self.assertEqual(str(self.course), 'TINF2024A')
    
    def test_full_name(self):
        self.assertEqual(self.course.full_name, 'TINF2024A - DHBW Stuttgart')


class StudyProgramViewTest(TestCase):
    """Tests für Views"""
    
    def setUp(self):
        self.program = StudyProgram.objects.create(
            study_progr='BWL'
        )
    
    def test_program_list_view(self):
        response = self.client.get(reverse('organization:program_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'BWL')
    
    def test_program_detail_view(self):
        response = self.client.get(
            reverse('organization:program_detail', kwargs={'pk': self.program.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'BWL')
    
    def test_dashboard_view(self):
        response = self.client.get(reverse('organization:dashboard'))
        self.assertEqual(response.status_code, 200)