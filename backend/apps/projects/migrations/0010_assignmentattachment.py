import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import apps.projects.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('projects', '0009_project_product_line'),
    ]

    operations = [
        migrations.CreateModel(
            name='AssignmentAttachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to=apps.projects.models.assignment_attachment_upload_to)),
                ('original_name', models.CharField(max_length=255)),
                ('file_size', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('assignment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='projects.testcaseassignment')),
                ('uploaded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='uploaded_assignment_files', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'assignment_attachment',
                'ordering': ['-created_at'],
            },
        ),
    ]
