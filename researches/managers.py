from django.db import models
from django.db.models import Q
from organization.models import StudyCourse

class ResearchPhaseManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()   

    def for_user(self, user):
        courses = user.person.get_study_courses()
        phase_ids = set()
        for field in ['pa1_phase_id', 'pa2_phase_id', 'ba_phase_id']:
            ids = courses.values_list(field, flat=True)
            phase_ids.update(ids)
        return self.get_queryset().filter(id__in=phase_ids).distinct()

class ResearchManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()
    
    def for_user(self, user):
        from .models import Research
        qs = super().get_queryset()
        if user.has_role('student'):        
            return qs.filter(student_id=user.person.student_profile)
        elif user.has_role('employee'):
            students = StudyCourse.objects.for_user(user).values_list('students', flat=True)
            return qs.filter(
                Q(student_id__in=students) |
                Q(assessor_scien=user.person.personnel_profile)
            )
        return self.none()
    
class ResearchAssessorWishManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()
    
    def for_user(self, user):
        # TODO SGL can see all -> rest only theirs
        # from .models import Research
        # if user.has_role('employee'):
        #     return self.get_queryset().filter(assessor_scien=user.person.personnel_profile)
        # else:
        return self.none()
    
class ResearchMatchWishManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()
    
    def for_user(self, user):
        # TODO SGL can see all -> rest only theirs
        # from .models import Research
        # if user.has_role('employee'):
        #     return self.get_queryset().filter(assessor_scien=user.person.personnel_profile)
        # else:
        return self.none()