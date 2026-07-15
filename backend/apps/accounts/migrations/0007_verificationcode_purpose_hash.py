# Generated for code review C3 fix:
#   - 重写 VerificationCode：去掉明文 code、is_used；加 purpose、attempts、consumed_at、code_hash
#   - 新增 (email, purpose, consumed_at) 复合索引；email / created_at 显式索引
#   - 通过 RunPython 把所有遗留 5-min-TTL 行清掉（都是新近的、不可哈希）。

import django.utils.timezone
from django.db import migrations, models


def clear_legacy_codes(apps, schema_editor):
    """清空 VerificationCode；它们都是短 TTL 的、不应当跨代码改动存在。
    新逻辑下，code 列已经被移除，所以遗留明文 code 行根本无处可放。"""
    VerificationCode = apps.get_model('accounts', 'VerificationCode')
    VerificationCode.objects.all().delete()


def reverse_noop(apps, schema_editor):
    """无意义——一旦降级到旧代码，原本写入的哈希也不再能匹配明文验证路径。
    不实现下行迁移，避免误操作。"""
    return


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_fix_tester_permissions'),
    ]

    operations = [
        # 1. 新增 purpose（带 default 让已有行满足 NOT NULL）
        migrations.AddField(
            model_name='verificationcode',
            name='purpose',
            field=models.CharField(
                choices=[('register', '注册'), ('reset', '重置')],
                default='register',
                max_length=16,
            ),
            preserve_default=False,
        ),
        # 2. 新增 code_hash（placeholder 默认；后续 AlterField 收紧）
        migrations.AddField(
            model_name='verificationcode',
            name='code_hash',
            field=models.CharField(default='', max_length=128),
            preserve_default=False,
        ),
        # 3. 新增 attempts 计数器
        migrations.AddField(
            model_name='verificationcode',
            name='attempts',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        # 4. 新增 consumed_at（nullable）
        migrations.AddField(
            model_name='verificationcode',
            name='consumed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        # 5. email 单列索引（已经有 db_index=True 的描述）
        migrations.AlterField(
            model_name='verificationcode',
            name='email',
            field=models.EmailField(db_index=True, max_length=254),
        ),
        # 6. created_at 单列索引
        migrations.AlterField(
            model_name='verificationcode',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        # 7. 清空已有的明文 code 行（这些行无法平滑迁到新结构）
        migrations.RunPython(clear_legacy_codes, reverse_noop),
        # 8. 收紧 code_hash：去掉 default，改为强制必填
        migrations.AlterField(
            model_name='verificationcode',
            name='code_hash',
            field=models.CharField(max_length=128),
        ),
        # 9. 删除 legacy 明文 code
        migrations.RemoveField(
            model_name='verificationcode',
            name='code',
        ),
        # 10. 删除 legacy is_used
        migrations.RemoveField(
            model_name='verificationcode',
            name='is_used',
        ),
        # 11. 复合 (email, purpose, consumed_at) 索引
        migrations.AddIndex(
            model_name='verificationcode',
            index=models.Index(
                fields=['email', 'purpose', 'consumed_at'],
                name='verification_email_purpose__idx',
            ),
        ),
    ]
