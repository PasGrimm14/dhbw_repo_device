import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0003_studyphase_research_fks_remove_studyyear_phase'),
        ('researches', '0002_researchphase'),
    ]

    operations = [
        # 1. Forschungsphase-FKs aus StudyPhase entfernen
        migrations.RemoveField(
            model_name='studyphase',
            name='pa1_phase',
        ),
        migrations.RemoveField(
            model_name='studyphase',
            name='pa2_phase',
        ),
        migrations.RemoveField(
            model_name='studyphase',
            name='ba_phase',
        ),

        # 2. Forschungsphase-FKs zu StudyCourse hinzufügen
        migrations.AddField(
            model_name='studycourse',
            name='pa1_phase',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='study_courses_pa1',
                to='researches.researchphase',
                verbose_name='PA1-Phase',
            ),
        ),
        migrations.AddField(
            model_name='studycourse',
            name='pa2_phase',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='study_courses_pa2',
                to='researches.researchphase',
                verbose_name='PA2-Phase',
            ),
        ),
        migrations.AddField(
            model_name='studycourse',
            name='ba_phase',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='study_courses_ba',
                to='researches.researchphase',
                verbose_name='BA-Phase',
            ),
        ),
    ]
