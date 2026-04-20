from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('lectures', '0002_alter_grade_passed'),
        ('organization', '0006_studyregulation_abbreviations'),
    ]

    operations = [
        migrations.AddField(
            model_name='module',
            name='regulation',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='modules',
                to='organization.studyregulation',
                verbose_name='Prüfungsordnung',
                default=1,
            ),
            preserve_default=False,
        ),
    ]
