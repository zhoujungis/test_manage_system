from django.db import migrations, models


def apply_tester_defaults(apps, schema_editor):
    UserProfile = apps.get_model('accounts', 'UserProfile')
    UserProfile.objects.filter(role='tester').update(can_access_projects=False)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_verificationcode'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='can_access_projects',
            field=models.BooleanField(default=True, verbose_name='项目管理'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='can_access_testcase_library',
            field=models.BooleanField(default=True, verbose_name='测试用例库'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='can_manage_testcase_library',
            field=models.BooleanField(default=True, verbose_name='管理用例库'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='can_access_my_projects',
            field=models.BooleanField(default=True, verbose_name='我的项目'),
        ),
        migrations.RunPython(apply_tester_defaults, migrations.RunPython.noop),
    ]
