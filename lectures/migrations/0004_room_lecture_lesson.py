import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lectures', '0003_module_regulation'),
        ('organization', '0006_studyregulation_abbreviations'),
        ('persons', '0005_alter_student_course_alter_student_field'),
    ]

    operations = [
        migrations.CreateModel(
            name='Room',
            fields=[
                ('name', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('is_double_bookable', models.BooleanField(
                    default=False,
                    help_text='Indicates whether this room can be double-booked (e.g., Online, Field Trip)',
                )),
            ],
        ),
        migrations.CreateModel(
            name='Lecture',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('unit', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to='lectures.moduleunit',
                )),
                ('semester', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to='organization.studysemester',
                )),
                ('course', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to='organization.studycourse',
                )),
            ],
            options={
                'unique_together': {('unit', 'course')},
            },
        ),
        migrations.CreateModel(
            name='LectureAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('units', models.DecimalField(
                    decimal_places=2,
                    max_digits=5,
                    validators=[django.core.validators.MinValueValidator(0)],
                    verbose_name='Lehreinheiten',
                )),
                ('lecture', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='assignments',
                    to='lectures.lecture',
                )),
                ('lecturer', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='lecture_assignments',
                    to='persons.personnel',
                )),
            ],
            options={
                'unique_together': {('lecture', 'lecturer')},
            },
        ),
        migrations.CreateModel(
            name='Lesson',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_exam', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),                
                ('lecturer', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to='persons.personnel', blank=True, null=True, 
                )),
                ('start', models.DateTimeField()),
                ('end', models.DateTimeField()),
                ('room', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to='lectures.room',
                )),
                ('lecture', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to='lectures.lecture'                    
                )),
            ],
        ),
    ]
