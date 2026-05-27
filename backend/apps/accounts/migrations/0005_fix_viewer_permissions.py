from django.db import migrations


def apply_viewer_defaults(apps, schema_editor):
    UserProfile = apps.get_model('accounts', 'UserProfile')
    UserProfile.objects.filter(role='viewer').update(
        can_access_projects=True,
        can_access_testcase_library=True,
        can_manage_testcase_library=False,
        can_access_my_projects=True,
    )


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_alter_userprofile_role_developer_label'),
    ]

    operations = [
        migrations.RunPython(apply_viewer_defaults, migrations.RunPython.noop),
    ]
