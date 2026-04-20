from django.db import models
from researches.models import Research

class PersonnelManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()

    def for_user(self, user):
        user_org_ids = (
            user.person
                .personnel_profile
                .organisation_roles
                .values_list('organisation_id', flat=True)
        )
        return self.get_queryset().filter(
            organisation_roles__organisation_id__in=user_org_ids
        ).distinct()

class StudentManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()

    def for_user(self, user):
        courses = user.person.get_study_courses()
        return self.get_queryset().filter(
            course__in=courses
        ).distinct()
    
class PersonManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()

    def for_user(self, user):
        from .models import Student, Personnel
        if user.has_role('employee'):
            student_person_ids = Student.objects.for_user(user).values_list('person_id', flat=True)
            company_person_ids = Student.objects.for_user(user).values_list('company_person_id', flat=True)
            personnel_person_ids = Personnel.objects.for_user(user).values_list('person_id', flat=True)
            researches_person_oper_ids = Research.objects.for_user(user).values_list('assessor_oper_id', flat=True)
            ids = student_person_ids.union(personnel_person_ids).union(company_person_ids).union(researches_person_oper_ids)
            return self.get_queryset().filter(id__in=ids).distinct()
        else:
            return self.get_queryset().filter(id__in=user.person).distinct()

class CompanyManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()

    def for_user(self, user):
        from .models import Student
        companies = Student.objects.for_user(user).values_list('company_id', flat=True)
        return self.get_queryset().filter(id__in=companies).distinct()
