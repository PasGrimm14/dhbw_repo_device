import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Wandelt die automatische M2M-Tabelle 'personnel_organisations' in ein
    explizites Through-Model mit Role-Feld um.

    Die Tabelle existiert bereits (erstellt durch 0006) mit den Spalten
    (id, personnel_id, studyorganisation_id). Wir fügen nur 'role' hinzu
    und registrieren das Through-Model im Django-State via SeparateDatabaseAndState.
    """

    dependencies = [
        ('organization', '0001_initial'),
        ('persons', '0007_create_permission_groups'),
    ]

    operations = [
        # Tabelle existiert bereits – State mit Through-Model befüllen
        # und in der DB nur die fehlende 'role'-Spalte ergänzen.
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='PersonnelOrganisation',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('role', models.CharField(
                            blank=True,
                            choices=[
                                ('sgl', 'Studiengangsleitung'),
                                ('sgs', 'Studiengangssekretariat'),
                                ('sgm', 'Studiengangsmanagement'),
                                ('acc', 'Wiss. MA'),
                                ('hilfs', 'Hilfskraft'),
                                ('lab', 'Labor'),
                            ],
                            max_length=10,
                            null=True,
                            verbose_name='Rolle',
                        )),
                        ('organisation', models.ForeignKey(
                            db_column='studyorganisation_id',
                            on_delete=django.db.models.deletion.CASCADE,
                            related_name='personnel_roles',
                            to='organization.studyorganisation',
                            verbose_name='Organisation',
                        )),
                        ('personnel', models.ForeignKey(
                            on_delete=django.db.models.deletion.CASCADE,
                            related_name='organisation_roles',
                            to='persons.personnel',
                            verbose_name='Personal',
                        )),
                    ],
                    options={
                        'verbose_name': 'Personal-Organisation',
                        'verbose_name_plural': 'Personal-Organisationen',
                        'db_table': 'personnel_organisations',
                        'ordering': ['organisation', 'role', 'personnel'],
                    },
                ),
            ],
            database_operations=[
                # Nur 'role'-Spalte hinzufügen – Tabelle + restliche Spalten existieren bereits
                migrations.RunSQL(
                    sql="ALTER TABLE `personnel_organisations` ADD COLUMN `role` VARCHAR(10) NULL",
                    reverse_sql="ALTER TABLE `personnel_organisations` DROP COLUMN `role`",
                ),
            ],
        ),

        # Unique-Together im State registrieren
        migrations.AlterUniqueTogether(
            name='personnelorganisation',
            unique_together={('personnel', 'organisation', 'role')},
        ),

        # M2M-Feld auf Through-Model umstellen (nur State-Änderung,
        # kein Tabellen-Drop/Create in der DB)
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name='personnel',
                    name='organisations',
                    field=models.ManyToManyField(
                        blank=True,
                        related_name='personnel',
                        through='persons.PersonnelOrganisation',
                        to='organization.studyorganisation',
                        verbose_name='Studiengangsorganisationen',
                    ),
                ),
            ],
            database_operations=[],
        ),
    ]
