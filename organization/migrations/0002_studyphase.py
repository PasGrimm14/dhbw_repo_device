import django.db.models.deletion
from django.db import migrations, models


def create_study_phases(apps, schema_editor):
    """
    Für jeden bestehenden StudyYear wird eine StudyPhase erstellt,
    die die bisherigen Semester-FKs übernimmt. StudyYear und StudyCourse
    werden dann auf die neue StudyPhase verwiesen.
    """
    StudyYear = apps.get_model('organization', 'StudyYear')
    StudyPhase = apps.get_model('organization', 'StudyPhase')
    StudyCourse = apps.get_model('organization', 'StudyCourse')

    for year in StudyYear.objects.all():
        phase = StudyPhase.objects.create(
            name=year.year_name,
            semester_id1t_id=year.semester_id1t_id,
            semester_id1p_id=year.semester_id1p_id,
            semester_id2t_id=year.semester_id2t_id,
            semester_id2p_id=year.semester_id2p_id,
            semester_id3t_id=year.semester_id3t_id,
            semester_id3p_id=year.semester_id3p_id,
            semester_id4t_id=year.semester_id4t_id,
            semester_id4p_id=year.semester_id4p_id,
            semester_id5t_id=year.semester_id5t_id,
            semester_id5p_id=year.semester_id5p_id,
            semester_id6t_id=year.semester_id6t_id,
            semester_id6p_id=year.semester_id6p_id,
        )
        year.study_phase = phase
        year.save()

        # Kurse dieses Jahrgangs der gleichen StudyPhase zuordnen
        StudyCourse.objects.filter(academic_year=year).update(study_phase=phase)


def reverse_create_study_phases(apps, schema_editor):
    StudyPhase = apps.get_model('organization', 'StudyPhase')
    StudyPhase.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0001_initial'),
    ]

    operations = [
        # 1. StudyPhase-Tabelle erstellen (mit denselben Semester-FKs wie StudyYear)
        migrations.CreateModel(
            name='StudyPhase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='Bezeichnung')),
                ('semester_id1t', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='phase_1t', to='organization.studysemester', verbose_name='1. Semester Theorie')),
                ('semester_id1p', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='phase_1p', to='organization.studysemester', verbose_name='1. Semester Praxis')),
                ('semester_id2t', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='phase_2t', to='organization.studysemester', verbose_name='2. Semester Theorie')),
                ('semester_id2p', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='phase_2p', to='organization.studysemester', verbose_name='2. Semester Praxis')),
                ('semester_id3t', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='phase_3t', to='organization.studysemester', verbose_name='3. Semester Theorie')),
                ('semester_id3p', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='phase_3p', to='organization.studysemester', verbose_name='3. Semester Praxis')),
                ('semester_id4t', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='phase_4t', to='organization.studysemester', verbose_name='4. Semester Theorie')),
                ('semester_id4p', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='phase_4p', to='organization.studysemester', verbose_name='4. Semester Praxis')),
                ('semester_id5t', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='phase_5t', to='organization.studysemester', verbose_name='5. Semester Theorie')),
                ('semester_id5p', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='phase_5p', to='organization.studysemester', verbose_name='5. Semester Praxis')),
                ('semester_id6t', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='phase_6t', to='organization.studysemester', verbose_name='6. Semester Theorie')),
                ('semester_id6p', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='phase_6p', to='organization.studysemester', verbose_name='6. Semester Praxis')),
            ],
            options={
                'verbose_name': 'Studienphase',
                'verbose_name_plural': 'Studienphasen',
                'db_table': 'study_phase',
                'ordering': ['name'],
            },
        ),

        # 2. study_phase (nullable) zu StudyYear hinzufügen
        migrations.AddField(
            model_name='studyyear',
            name='study_phase',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='years',
                to='organization.studyphase',
                verbose_name='Studienphase',
            ),
        ),

        # 3. study_phase (nullable) zu StudyCourse hinzufügen
        migrations.AddField(
            model_name='studycourse',
            name='study_phase',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='courses',
                to='organization.studyphase',
                verbose_name='Studienphase',
            ),
        ),

        # 4. Datenmigration: StudyPhase-Einträge aus StudyYear erzeugen
        migrations.RunPython(create_study_phases, reverse_create_study_phases),

        # 5. study_phase auf StudyYear non-nullable setzen
        migrations.AlterField(
            model_name='studyyear',
            name='study_phase',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='years',
                to='organization.studyphase',
                verbose_name='Studienphase',
            ),
        ),

        # 6. Alte Semester-FK-Spalten aus StudyYear entfernen
        migrations.RemoveField(model_name='studyyear', name='semester_id1t'),
        migrations.RemoveField(model_name='studyyear', name='semester_id1p'),
        migrations.RemoveField(model_name='studyyear', name='semester_id2t'),
        migrations.RemoveField(model_name='studyyear', name='semester_id2p'),
        migrations.RemoveField(model_name='studyyear', name='semester_id3t'),
        migrations.RemoveField(model_name='studyyear', name='semester_id3p'),
        migrations.RemoveField(model_name='studyyear', name='semester_id4t'),
        migrations.RemoveField(model_name='studyyear', name='semester_id4p'),
        migrations.RemoveField(model_name='studyyear', name='semester_id5t'),
        migrations.RemoveField(model_name='studyyear', name='semester_id5p'),
        migrations.RemoveField(model_name='studyyear', name='semester_id6t'),
        migrations.RemoveField(model_name='studyyear', name='semester_id6p'),
    ]
