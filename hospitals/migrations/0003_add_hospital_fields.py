# hospitals/migrations/0003_add_hospital_fields.py
from django.db import migrations, models
import django.utils.timezone

class Migration(migrations.Migration):

    dependencies = [
        ('hospitals', '0002_alter_hospital_table'),
    ]

    operations = [
        # add city (varchar, blank allowed)
        migrations.AddField(
            model_name='hospital',
            name='city',
            field=models.CharField(max_length=100, blank=True, default=''),
            preserve_default=False,
        ),
        # add contact_phone (varchar, blank allowed)
        migrations.AddField(
            model_name='hospital',
            name='contact_phone',
            field=models.CharField(max_length=20, blank=True, default=''),
            preserve_default=False,
        ),
        # add timezone (has default)
        migrations.AddField(
            model_name='hospital',
            name='timezone',
            field=models.CharField(max_length=64, default='UTC'),
            preserve_default=False,
        ),
        # add updated_at - make it nullable to avoid filling existing rows;
        # apps/model still uses auto_now=True — but a nullable column here avoids requiring a default.
        migrations.AddField(
            model_name='hospital',
            name='updated_at',
            field=models.DateTimeField(null=True, blank=True),
            preserve_default=False,
        ),
    ]
