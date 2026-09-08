from django.db import migrations, models


def set_admin_role_for_staff_and_superusers(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    User.objects.filter(
        models.Q(is_superuser=True) | models.Q(is_staff=True)
    ).update(role='ADMIN')


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(set_admin_role_for_staff_and_superusers, noop),
    ]
