from django.db import models
from django.db.models import Q

class ModuleManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()

    def for_user(self, user):
        courses = user.person.get_study_courses()
        field_ids = courses.values_list('field_id', flat=True)
        regulation_ids = courses.values_list('study_regulation_id', flat=True)
        return self.get_queryset().filter(
            Q(regulation_id__in=regulation_ids),
            Q(field_id__in=field_ids) | Q(field_id__isnull=True)
        ).distinct()
    
class ModuleUnitManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()

    def for_user(self, user):
        from .models import Module
        module_ids = Module.objects.for_user(user).values_list('module_nr', flat=True)
        return self.get_queryset().filter(module_id__in=module_ids).distinct()

class GradeManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()

    def for_user(self, user):
        from persons.models import Student
        student_ids = Student.objects.for_user(user).values_list('id', flat=True)
        return self.get_queryset().filter(student_id__in=student_ids).distinct()

 