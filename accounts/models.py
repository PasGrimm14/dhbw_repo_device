import uuid
from django.db import models
from django.utils import timezone


class AccessToken(models.Model):
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    person = models.ForeignKey(
        'persons.Person',
        on_delete=models.CASCADE,
        related_name='access_tokens',
        verbose_name='Person',
    )
    label = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Bezeichnung',
        help_text='Z.B. "Betreuer BA Schmidt 2025"',
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Gültig bis',
        help_text='Leer lassen = unbegrenzt gültig',
    )
    allowed_url_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Erlaubte Seite (URL-Name)',
        help_text='Z.B. "researches:research_detail". Leer lassen = alle Token-Views erlaubt.',
    )
    is_active = models.BooleanField(default=True, verbose_name='Aktiv')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Erstellt am')
    last_used_at = models.DateTimeField(null=True, blank=True, verbose_name='Zuletzt verwendet')

    class Meta:
        verbose_name = 'Zugriffstoken'
        verbose_name_plural = 'Zugriffstoken'
        ordering = ['-created_at']

    def __str__(self):
        label = self.label or str(self.token)[:8] + '...'
        return f'{self.person} – {label}'

    @property
    def is_valid(self):
        if not self.is_active:
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        return True
