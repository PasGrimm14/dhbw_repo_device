from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save
from django.dispatch import receiver

ROLE_TO_GROUPS = {
    'ST':   ['student'],
    'MA':   ['employee'],
    'DOZ':  ['lecturer'],
    'COAS': ['mentor'],
    'CO':   ['supervisor'],
}


def assign_groups(user, role):
    group_names = ROLE_TO_GROUPS.get(role, [])
    if group_names:
        groups = Group.objects.filter(name__in=group_names)
        user.groups.set(groups)


def _try_link_user_to_person(user):
    """Verknüpft einen User mit dem passenden Person-Datensatz anhand der E-Mail."""
    if hasattr(user, 'person'):
        return
    if not user.email:
        return

    from persons.models import Person

    email = user.email
    if email.endswith('@heilbronn.dhbw.de'):
        alt_email = email.replace('@heilbronn.dhbw.de', '@dhbw.de')
    elif email.endswith('@dhbw.de'):
        alt_email = email.replace('@dhbw.de', '@heilbronn.dhbw.de')
    else:
        alt_email = None

    emails_to_try = [email] + ([alt_email] if alt_email else [])

    for mail in emails_to_try:
        try:
            person = Person.objects.get(mail_main=mail)
            person.user = user
            person.save(update_fields=['user'])
            assign_groups(user, person.role_now)
            return
        except Person.DoesNotExist:
            continue
        except Person.MultipleObjectsReturned:
            return  # Mehrere Treffer → kein automatisches Linking


@receiver(user_logged_in)
def link_user_to_person_on_login(sender, user, **kwargs):
    _try_link_user_to_person(user)


@receiver(post_save, sender=get_user_model())
def link_user_to_person_on_create(sender, instance, created, **kwargs):
    if created:
        _try_link_user_to_person(instance)
