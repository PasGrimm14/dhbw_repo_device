from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0006_studyregulation_abbreviations'),
    ]

    operations = [
        migrations.AddField(
            model_name='studycourse',
            name='external_ical_url',
            field=models.URLField(
                blank=True,
                null=True,
                help_text='Optional URL for an external iCal source used to sync this study courses schedule.',
            ),
        ),
        migrations.AddField(
            model_name='studycourse',
            name='external_ical_last_sync_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
