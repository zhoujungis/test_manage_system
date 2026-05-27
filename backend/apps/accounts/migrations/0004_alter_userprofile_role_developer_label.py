from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_userprofile_permissions'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='role',
            field=models.CharField(
                choices=[
                    ('admin', '管理员'),
                    ('tester', '测试工程师'),
                    ('developer', '测试开发工程师'),
                    ('viewer', '观察者'),
                ],
                default='tester',
                max_length=20,
            ),
        ),
    ]
