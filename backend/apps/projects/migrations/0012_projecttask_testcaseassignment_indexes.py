# Generated for code review D2 + D3:
#   - ProjectTask.status / priority 加索引（views / dashboard 频繁按这两列过滤）
#   - TestCaseAssignment.status / approval_status 加索引（projects/views batch_approve 用到）

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0011_projecttask_round_testcaseassignment_task_and_more'),
    ]

    operations = [
        # D2: ProjectTask
        migrations.AlterField(
            model_name='projecttask',
            name='status',
            field=models.CharField(
                choices=[('todo', '待开始'), ('in_progress', '进行中'), ('done', '已完成')],
                db_index=True,
                default='todo',
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='projecttask',
            name='priority',
            field=models.CharField(
                choices=[
                    ('P0', 'P0-紧急'),
                    ('P1', 'P1-高'),
                    ('P2', 'P2-中'),
                    ('P3', 'P3-低'),
                ],
                db_index=True,
                default='P2',
                max_length=10,
            ),
        ),
        # D3: TestCaseAssignment
        migrations.AlterField(
            model_name='testcaseassignment',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending', '待测试'),
                    ('passed', 'Pass'),
                    ('failed', 'Fail'),
                    ('not_applicable', 'N/A'),
                    ('not_tested', 'N/T'),
                ],
                db_index=True,
                default='pending',
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='testcaseassignment',
            name='approval_status',
            field=models.CharField(
                choices=[
                    ('pending', '未审核'),
                    ('approved', '审核通过'),
                    ('rejected', '审核不通过'),
                ],
                db_index=True,
                default='pending',
                max_length=20,
            ),
        ),
    ]
