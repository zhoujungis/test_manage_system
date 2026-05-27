from django.db import migrations


def fix_tester_permissions(apps, schema_editor):
    UserProfile = apps.get_model('accounts', 'UserProfile')
    UserProfile.objects.filter(role='tester').update(
        can_manage_testcase_library=False,
    )


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_fix_viewer_permissions'),
    ]

    operations = [
        migrations.RunPython(fix_tester_permissions, migrations.RunPython.noop),
    ]
