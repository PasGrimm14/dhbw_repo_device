from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('lectures', '0001_initial'),
        ('organization', '0005_studyacademy_abbreviation'),
    ]

    operations = [
        # abbreviation für StudyProgram (study_study)
        migrations.AddField(
            model_name='studyprogram',
            name='abbreviation',
            field=models.CharField(
                blank=True,
                max_length=20,
                null=True,
                unique=True,
                verbose_name='Abkürzung',
            ),
        ),
        # abbreviation für StudyField (study_field)
        migrations.AddField(
            model_name='studyfield',
            name='abbreviation',
            field=models.CharField(
                blank=True,
                max_length=20,
                null=True,
                verbose_name='Abkürzung',
            ),
        ),
        # Neue Tabelle study_regulations
        migrations.CreateModel(
            name='StudyRegulation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Bezeichnung')),
                ('start_date', models.DateField(verbose_name='Gültig ab')),
                ('study', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='regulations',
                    to='organization.studyprogram',
                    verbose_name='Studiengang',
                )),
                ('unit_pa1', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='regulations_pa1',
                    to='lectures.moduleunit',
                    verbose_name='PA1-Einheit',
                )),
                ('unit_pa2', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='regulations_pa2',
                    to='lectures.moduleunit',
                    verbose_name='PA2-Einheit',
                )),
                ('unit_ba', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='regulations_ba',
                    to='lectures.moduleunit',
                    verbose_name='BA-Einheit',
                )),
            ],
            options={
                'verbose_name': 'Prüfungsordnung',
                'verbose_name_plural': 'Prüfungsordnungen',
                'db_table': 'study_regulations',
                'ordering': ['study', 'start_date'],
            },
        ),
        # study_regulation FK in StudyCourse
        migrations.AddField(
            model_name='studycourse',
            name='study_regulation',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='courses',
                to='organization.studyregulation',
                verbose_name='Prüfungsordnung',
            ),
        ),
    ]
