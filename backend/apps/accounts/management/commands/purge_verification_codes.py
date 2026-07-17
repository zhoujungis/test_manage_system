"""M12 fix: 定期清理过期 / 已消费的验证码，避免表无限膨胀。

默认保留窗口：
  - consumed_at != NULL → 删除（已经用过，无意义）
  - 已消费且保留超 7 天 → 删除（防审计需要）
  - 未消费但 created_at 早于 30 天 → 删除（早过期）

参数：
  --dry-run    只打印数量，不真删
  --keep-consumed-days 7
  --keep-unconsumed-days 30
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import models
from django.utils import timezone

from apps.accounts.models import VerificationCode


class Command(BaseCommand):
    help = '清理 VerificationCode 中已消费 / 已过期的记录'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='只统计，不删除')
        parser.add_argument('--keep-consumed-days', type=int, default=7)
        parser.add_argument('--keep-unconsumed-days', type=int, default=30)

    def handle(self, *args, **opts):
        now = timezone.now()
        keep_consumed = opts['keep_consumed_days']
        keep_unconsumed = opts['keep_unconsumed_days']

        consumed_qs = VerificationCode.objects.filter(consumed_at__isnull=False)
        old_consumed = consumed_qs.filter(consumed_at__lt=now - timedelta(days=keep_consumed))
        old_unconsumed = VerificationCode.objects.filter(
            consumed_at__isnull=True,
            created_at__lt=now - timedelta(days=keep_unconsumed),
        )

        consumed_count = old_consumed.count()
        unconsumed_count = old_unconsumed.count()
        self.stdout.write(
            f'将删除：consumed>{keep_consumed}d 共 {consumed_count} 条；'
            f'unconsumed>{keep_unconsumed}d 共 {unconsumed_count} 条'
        )

        if opts['dry_run']:
            self.stdout.write(self.style.WARNING('--dry-run: 不执行删除'))
            return

        old_consumed.delete()
        old_unconsumed.delete()
        self.stdout.write(self.style.SUCCESS(
            f'已删除 {consumed_count + unconsumed_count} 条 VerificationCode'
        ))