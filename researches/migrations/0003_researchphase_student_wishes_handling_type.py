from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('researches', '0002_researchphase'),
    ]

    operations = [
        migrations.AddField(
            model_name='researchphase',
            name='student_wishes',
            field=models.BooleanField(
                verbose_name='Studentenwünsche',
                help_text='Können Studenten Betreuerwünsche angeben?',
                default=True,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='researchphase',
            name='handling_type',
            field=models.CharField(
                verbose_name='Handling-Typ',
                max_length=25,
                choices=[
                    ('all-to-selected', 'Alle zu Ausgewählten'),
                    ('selected-to-selected', 'Ausgewählte zu Ausgewählten'),
                ],
                default='all-to-selected',
            ),
            preserve_default=False,
        ),
    ]
