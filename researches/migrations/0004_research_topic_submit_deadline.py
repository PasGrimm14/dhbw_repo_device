import datetime
from django.db import migrations, models


def set_topic_submit_deadline(apps, schema_editor):
    Research = apps.get_model('researches', 'Research')
    for research in Research.objects.all():
        if research.research_phase_id and research.research_phase.submission_date:
            research.topic_submit_deadline = research.research_phase.submission_date
        else:
            research.topic_submit_deadline = datetime.date.today()
        research.save(update_fields=['topic_submit_deadline'])


class Migration(migrations.Migration):

    dependencies = [
        ('researches', '0003_researchphase_student_wishes_handling_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='research',
            name='topic_submit_deadline',
            field=models.DateField(
                verbose_name='Thema einreichen bis',
                db_column='topic_submit_deadline',
                null=True,
            ),
        ),
        migrations.RunPython(
            set_topic_submit_deadline,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name='research',
            name='topic_submit_deadline',
            field=models.DateField(
                verbose_name='Thema einreichen bis',
                db_column='topic_submit_deadline',
            ),
        ),
    ]
