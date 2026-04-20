import django.db.models.deletion
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('researches', '0001_initial'),
    ]

    operations = [
        # 1. ResearchPhase-Tabelle erstellen
        migrations.CreateModel(
            name='ResearchPhase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20, verbose_name='Bezeichnung')),
                ('submission_date', models.DateField(blank=False, null=True, verbose_name='Einreichungsdatum')),
                ('offer_date', models.DateField(blank=True, help_text='Standard: start_date minus 2 Wochen', null=True, verbose_name='Angebotsdatum')),
                ('start_date', models.DateField(blank=True, null=False, verbose_name='Startdatum')),
                ('end_date', models.DateField(blank=True, null=False, verbose_name='Enddatum')),
                ('feedback_date', models.DateField(blank=True, null=True, verbose_name='Feedbackdatum')),
            ],
            options={
                'verbose_name': 'Forschungsphase',
                'verbose_name_plural': 'Forschungsphasen',
                'db_table': 'research_phase',
                'ordering': ['name'],
            },
        ),
        
        # 2. research_phase-FK zu Research hinzufügen
        migrations.AddField(
            model_name='research',
            name='research_phase',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='researches',
                to='researches.researchphase',
                verbose_name='Forschungsphase',
            ),
        ),
    ]
