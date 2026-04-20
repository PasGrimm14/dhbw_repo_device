from django.test import TestCase
from django.urls import reverse
from .models import Person, Student, Personnel, Company


class PersonModelTest(TestCase):
    """Tests für das Person Model"""
    
    def setUp(self):
        """Test-Daten erstellen"""
        self.person = Person.objects.create(
            firstname='Max',
            lastname='Mustermann',
            mail_main='max@example.com',
            role_now='ST'
        )
    
    def test_person_creation(self):
        """Test ob Person korrekt erstellt wird"""
        self.assertEqual(self.person.firstname, 'Max')
        self.assertEqual(self.person.lastname, 'Mustermann')
        self.assertEqual(str(self.person), 'Max Mustermann')
    
    def test_get_full_name(self):
        """Test get_full_name Methode"""
        self.assertEqual(self.person.get_full_name(), 'Max Mustermann')
    
    def test_get_short_name(self):
        """Test get_short_name Methode"""
        self.assertEqual(self.person.get_short_name(), 'Max Mustermann')
    
    def test_person_with_title(self):
        """Test Person mit Titel"""
        person_with_title = Person.objects.create(
            title='Dr.',
            firstname='Anna',
            lastname='Schmidt',
            role_now='DOZ'
        )
        self.assertEqual(str(person_with_title), 'Dr. Anna Schmidt')


class StudentModelTest(TestCase):
    """Tests für das Student Model"""
    
    def setUp(self):
        """Test-Daten erstellen"""
        self.person = Person.objects.create(
            firstname='Lisa',
            lastname='Müller',
            mail_main='lisa@example.com',
            role_now='ST'
        )
        # Note: Diese Tests benötigen weitere Models (Course, Field, Company)
        # die erst erstellt werden müssen
    
    def test_student_str(self):
        """Test String-Repräsentation"""
        # Dieser Test wird erweitert, sobald die abhängigen Models existieren
        pass


class PersonnelModelTest(TestCase):
    """Tests für das Personnel Model"""
    
    def setUp(self):
        """Test-Daten erstellen"""
        self.person = Person.objects.create(
            firstname='Thomas',
            lastname='Weber',
            mail_main='thomas@example.com',
            role_now='DOZ'
        )
        self.personnel = Personnel.objects.create(
            person=self.person,
            personnel_nr=1001,
            actant_type=1
        )
    
    def test_personnel_creation(self):
        """Test ob Personnel korrekt erstellt wird"""
        self.assertEqual(self.personnel.personnel_nr, 1001)
        self.assertEqual(str(self.personnel), '1001 - Thomas Weber')
    
    def test_personnel_properties(self):
        """Test Properties"""
        self.assertEqual(self.personnel.full_name, 'Thomas Weber')
        self.assertEqual(self.personnel.email, 'thomas@example.com')


class PersonViewTest(TestCase):
    """Tests für Views"""
    
    def setUp(self):
        """Test-Daten erstellen"""
        self.person = Person.objects.create(
            firstname='Test',
            lastname='User',
            mail_main='test@example.com',
            role_now='ST'
        )
    
    def test_person_list_view(self):
        """Test Person List View"""
        response = self.client.get(reverse('persons:person_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test User')
    
    def test_person_detail_view(self):
        """Test Person Detail View"""
        response = self.client.get(
            reverse('persons:person_detail', kwargs={'pk': self.person.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test User')
    
    def test_dashboard_view(self):
        """Test Dashboard View"""
        response = self.client.get(reverse('persons:dashboard'))
        self.assertEqual(response.status_code, 200)

class CompanyModelTest(TestCase):
    """Tests für das Company Model"""
    
    def setUp(self):
        """Test-Daten erstellen"""
        self.company = Company.objects.create(
            name='Test GmbH',
            adressform='Firma',
            street='Teststraße 123',
            postal_code='12345',
            city='Teststadt',
            state='Baden-Württemberg',
            country='Deutschland',
            tel_main='+49 123 456789',
            mail_main='info@test.de',
            webpage='https://www.test.de'
        )
    
    def test_company_creation(self):
        """Test ob Company korrekt erstellt wird"""
        self.assertEqual(self.company.name, 'Test GmbH')
        self.assertEqual(str(self.company), 'Test GmbH')
    
    def test_get_full_address(self):
        """Test get_full_address Methode"""
        address = self.company.get_full_address()
        self.assertIn('Teststraße 123', address)
        self.assertIn('12345', address)
        self.assertIn('Teststadt', address)
    
    def test_get_short_address(self):
        """Test get_short_address Methode"""
        short_address = self.company.get_short_address()
        self.assertEqual(short_address, '12345 Teststadt')
    
    def test_has_contact_info(self):
        """Test has_contact_info Property"""
        self.assertTrue(self.company.has_contact_info)
        
        company_no_contact = Company.objects.create(
            name='No Contact GmbH',
            adressform='Firma'
        )
        self.assertFalse(company_no_contact.has_contact_info)
    
    def test_student_count(self):
        """Test student_count Property"""
        # Ohne Students
        self.assertEqual(self.company.student_count, 0)


class CompanyViewTest(TestCase):
    """Tests für Views"""
    
    def setUp(self):
        """Test-Daten erstellen"""
        self.company = Company.objects.create(
            name='View Test GmbH',
            adressform='Firma',
            city='München'
        )
    
    def test_company_list_view(self):
        """Test Company List View"""
        response = self.client.get(reverse('companies:company_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'View Test GmbH')
    
    def test_company_detail_view(self):
        """Test Company Detail View"""
        response = self.client.get(
            reverse('companies:company_detail', kwargs={'pk': self.company.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'View Test GmbH')
    
    def test_dashboard_view(self):
        """Test Dashboard View"""
        response = self.client.get(reverse('companies:dashboard'))
        self.assertEqual(response.status_code, 200)
    
    def test_company_search(self):
        """Test Suchfunktion"""
        response = self.client.get(reverse('companies:company_list'), {'search': 'München'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'View Test GmbH')


class CompanyFilterTest(TestCase):
    """Tests für Filter"""
    
    def setUp(self):
        """Test-Daten erstellen"""
        Company.objects.create(
            name='Stuttgart GmbH',
            adressform='Firma',
            city='Stuttgart',
            state='Baden-Württemberg'
        )
        Company.objects.create(
            name='München GmbH',
            adressform='Firma',
            city='München',
            state='Bayern'
        )
    
    def test_city_filter(self):
        """Test Filter nach Stadt"""
        response = self.client.get(reverse('companies:company_list'), {'city': 'Stuttgart'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Stuttgart GmbH')
        self.assertNotContains(response, 'München GmbH')
    
    def test_state_filter(self):
        """Test Filter nach Bundesland"""
        response = self.client.get(reverse('companies:company_list'), {'state': 'Bayern'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'München GmbH')