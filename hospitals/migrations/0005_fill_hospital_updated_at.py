# hospitals/migrations/0005_fill_hospital_updated_at.py
from django.db import migrations
from django.utils import timezone

def set_updated_at(apps, schema_editor):
    Hospital = apps.get_model('hospitals', 'Hospital')
    now = timezone.now()
    qs = Hospital.objects.filter(updated_at__isnull=True)
    # update in batches to avoid loading everything into memory if table is large
    for h in qs:
        h.updated_at = now
        h.save()

class Migration(migrations.Migration):

    dependencies = [
        # point to the latest hospitals migration you have
        ('hospitals', '0004_alter_hospital_timezone_alter_hospital_updated_at'),
    ]

    operations = [
        migrations.RunPython(set_updated_at, reverse_code=migrations.RunPython.noop),
    ]
