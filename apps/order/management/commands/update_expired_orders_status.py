from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, datetime
from ...models import Order


class Command(BaseCommand):
    help = "Update status of expired orders to 'expired'"

    def handle(self, *args, **options):
        # 尋找過去最近的UTC 16:00，然後將 created_at < 2天前的UTC 16:00的訂單標記為過期
        time = timezone.now()
        utc_dt = timezone.now() - timedelta(hours=8)
        utc_today_end = utc_dt.replace(hour=16, minute=0, second=0, microsecond=0)

        if utc_dt >= utc_today_end:
            utc_expired_dt = utc_today_end - timedelta(days=2)
        else:
            utc_expired_dt = utc_today_end - timedelta(days=3)

        Order.objects.filter(created_at__lte=utc_expired_dt).update(status=Order.FAIL)
        self.stdout.write("UTC now is %s" % time)
        self.stdout.write("Update status of orders before UTC %s to expired. " % utc_expired_dt)