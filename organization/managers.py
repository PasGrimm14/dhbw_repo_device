from django.db import models

class StudyCourseManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()

    def for_person (self, person):
        from .models import StudyCourse
        if person.role_now == 'ST':
            return self.get_queryset().filter(
                pk=person.student_profile.course.pk
            )
        if person.role_now == 'MA':
            orga_roles = person.personnel_profile.organisation_roles.all()
            courses = (orga_roles.values_list("organisation__courses", flat=True))
            return self.get_queryset().filter(pk__in=courses).distinct()
        return self.none()

    def for_user(self, user):
        return self.for_person(user.person)
        
    
class StudyRegulationManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()

    def for_user(self, user):
        return self.get_queryset()

class StudyYearManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()

    def for_user(self, user):
        return self.get_queryset()

class StudyPhaseManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()

    def for_user(self, user):
        return self.get_queryset()

class StudySemesterManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()

    def for_user(self, user):
        return self.get_queryset()

class StudyOrganisationManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()

    def for_user(self, user):
        return self.get_queryset()

class StudyFieldManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()

    def for_user(self, user):
        return self.get_queryset() 

class StudyProgramManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()

    def for_user(self, user):
        return self.get_queryset() 

class StudyAcademyManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()

    def for_user(self, user):
        return self.get_queryset() 
