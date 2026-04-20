from django.test import TestCase
from django.core.exceptions import ValidationError
from decimal import Decimal
from .models import Module, ModuleUnit, Grade


class ModuleModelTest(TestCase):
    """Tests für Module Model"""
    
    def setUp(self):
        from organization.models import StudyProgram
        self.study = StudyProgram.objects.create(study_progr='Informatik')
        
        self.module = Module.objects.create(
            module_nr='INF101',
            name='Programmierung 1',
            credits=5,
            study=self.study
        )
    
    def test_module_creation(self):
        self.assertEqual(self.module.module_nr, 'INF101')
        self.assertEqual(self.module.name, 'Programmierung 1')
        self.assertEqual(str(self.module), 'INF101 - Programmierung 1')


class ModuleUnitModelTest(TestCase):
    """Tests für ModuleUnit Model"""
    
    def setUp(self):
        from organization.models import StudyProgram
        study = StudyProgram.objects.create(study_progr='Informatik')
        
        self.module = Module.objects.create(
            module_nr='INF101',
            name='Programmierung 1',
            credits=5,
            study=study
        )
        
        self.unit = ModuleUnit.objects.create(
            module=self.module,
            unit_nr='INF101-V',
            unit_name='Vorlesung Programmierung 1',
            unit_name_short='Prog1-V',
            units=Decimal('2.00'),
            semester_nr=1
        )
    
    def test_unit_creation(self):
        self.assertEqual(self.unit.unit_nr, 'INF101-V')
        self.assertEqual(self.unit.semester_nr, 1)


class GradeModelTest(TestCase):
    """Tests für Grade Model"""
    
    def setUp(self):
        # Setup minimal data
        from organization.models import StudyProgram, StudyField, StudyAcademy, StudyOrganisation, StudySemester, StudyYear, StudyCourse
        from persons.models import Person, Student
        from companies.models import Company
        from django.utils import timezone
        
        # Create person
        person = Person.objects.create(
            firstname='Max',
            lastname='Mustermann',
            role_now='ST'
        )
        
        # Create company
        company = Company.objects.create(
            name='Test GmbH',
            adressform='Firma'
        )
        
        # Create study program and field
        study = StudyProgram.objects.create(study_progr='Informatik')
        field = StudyField.objects.create(study=study, studyfield='Software Engineering')
        
        # Create academy and organisation
        academy = StudyAcademy.objects.create(academy_name='DHBW Test')
        organisation = StudyOrganisation.objects.create(name='DHBW')
        
        # Create semesters for year (simplified - just create 12 dummy semesters)
        today = timezone.localdate()
        semesters = []
        for i in range(12):
            sem = StudySemester.objects.create(
                name=f'Semester {i+1}',
                name_short=f'S{i+1}',
                start_date=today,
                end_date=today,
                type='Theorie' if i % 2 == 0 else 'Praxis',
                cycle='A'
            )
            semesters.append(sem)
        
        # Create year
        year = StudyYear.objects.create(
            year_name='2024',
            semester_id1t=semesters[0], semester_id1p=semesters[1],
            semester_id2t=semesters[2], semester_id2p=semesters[3],
            semester_id3t=semesters[4], semester_id3p=semesters[5],
            semester_id4t=semesters[6], semester_id4p=semesters[7],
            semester_id5t=semesters[8], semester_id5p=semesters[9],
            semester_id6t=semesters[10], semester_id6p=semesters[11],
        )
        
        # Create course
        course = StudyCourse.objects.create(
            academy=academy,
            field=field,
            course_nr='TINF2024A',
            academic_year=year,
            organisation=organisation
        )
        
        # Create student
        self.student = Student.objects.create(
            person=person,
            matri_nr=12345,
            course=course,
            field=field,
            company=company
        )
        
        # Create module
        self.module = Module.objects.create(
            module_nr='INF101',
            name='Programmierung 1',
            credits=5,
            study=study
        )
    
    def test_grade_creation_passed(self):
        """Test erfolgreiche Note"""
        grade = Grade.objects.create(
            student=self.student,
            module=self.module,
            attempt=1,
            passed=True,
            grade=Decimal('2.0')
        )
        
        self.assertEqual(grade.grade, Decimal('2.0'))
        self.assertTrue(grade.passed)
        self.assertEqual(grade.grade_text, 'Gut')
    
    def test_grade_creation_failed(self):
        """Test nicht bestandene Note"""
        grade = Grade.objects.create(
            student=self.student,
            module=self.module,
            attempt=1,
            passed=False,
            grade=Decimal('5.0')
        )
        
        self.assertEqual(grade.grade, Decimal('5.0'))
        self.assertFalse(grade.passed)
    
    def test_grade_validation_failed(self):
        """Test Validierung: Nicht bestanden mit guter Note sollte Fehler werfen"""
        with self.assertRaises(ValidationError):
            grade = Grade(
                student=self.student,
                module=self.module,
                attempt=1,
                passed=False,  # Nicht bestanden
                grade=Decimal('2.0')  # Aber gute Note!
            )
            grade.clean()  # Sollte ValidationError werfen
    
    def test_is_final_attempt(self):
        """Test ob letzter Versuch erkannt wird"""
        grade = Grade.objects.create(
            student=self.student,
            module=self.module,
            attempt=3,
            passed=False,
            grade=Decimal('5.0')
        )
        
        self.assertTrue(grade.is_final_attempt)
