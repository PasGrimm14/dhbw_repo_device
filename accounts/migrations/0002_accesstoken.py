import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('persons', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AccessToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('person', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='access_tokens',
                    to='persons.person',
                    verbose_name='Person',
                )),
                ('label', models.CharField(
                    blank=True,
                    help_text='Z.B. "Betreuer BA Schmidt 2025"',
                    max_length=200,
                    verbose_name='Bezeichnung',
                )),
                ('allowed_url_name', models.CharField(
                    blank=True,
                    help_text='Z.B. "researches:research_detail". Leer lassen = alle Token-Views erlaubt.',
                    max_length=200,
                    verbose_name='Erlaubte Seite (URL-Name)',
                )),
                ('expires_at', models.DateTimeField(
                    blank=True,
                    help_text='Leer lassen = unbegrenzt gültig',
                    null=True,
                    verbose_name='Gültig bis',
                )),
                ('is_active', models.BooleanField(default=True, verbose_name='Aktiv')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Erstellt am')),
                ('last_used_at', models.DateTimeField(blank=True, null=True, verbose_name='Zuletzt verwendet')),
            ],
            options={
                'verbose_name': 'Zugriffstoken',
                'verbose_name_plural': 'Zugriffstoken',
                'ordering': ['-created_at'],
            },
        ),
    ]
