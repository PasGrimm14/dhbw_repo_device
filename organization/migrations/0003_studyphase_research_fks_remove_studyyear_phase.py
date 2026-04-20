import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0002_studyphase'),
        ('researches', '0002_researchphase'),
    ]

    operations = [
        # 1. Forschungsphase-FKs zu StudyPhase hinzufügen
        migrations.AddField(
            model_name='studyphase',
            name='pa1_phase',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='study_phases_pa1',
                to='researches.researchphase',
                verbose_name='PA1-Phase',
            ),
        ),
        migrations.AddField(
            model_name='studyphase',
            name='pa2_phase',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='study_phases_pa2',
                to='researches.researchphase',
                verbose_name='PA2-Phase',
            ),
        ),
        migrations.AddField(
            model_name='studyphase',
            name='ba_phase',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='study_phases_ba',
                to='researches.researchphase',
                verbose_name='BA-Phase',
            ),
        ),

        # 2. study_phase FK aus StudyYear entfernen
        migrations.RemoveField(
            model_name='studyyear',
            name='study_phase',
        ),
    ]
