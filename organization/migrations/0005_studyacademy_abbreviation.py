from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0004_move_research_phases_to_studycourse'),
    ]

    operations = [
        migrations.AddField(
            model_name='studyacademy',
            name='abbreviation',
            field=models.CharField(
                blank=True,
                max_length=20,
                null=True,
                unique=True,
                verbose_name='Abkürzung',
            ),
        ),
    ]
