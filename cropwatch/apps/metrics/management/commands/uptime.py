from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand
from django.utils import timezone

from cropwatch.apps.ioTank.models import ioTank, SensorReading
from cropwatch.apps.metrics.tasks import *


class Command(BaseCommand):
    help = 'Performs uptime validation every 5'

    def handle(self, *args, **options):

        accounts = AccountSettings.objects.filter(notify_iotank_emergency=True)
        email_subject = "ioTank offline."

        for account in accounts:
            bots = ioTank.objects.filter(owner=account.user)
            for bot in bots:
                try:
                    reading = SensorReading.objects.filter(bot=bot).order_by('-timestamp').first()
                    if reading.timestamp < timezone.now() - relativedelta(minutes=15):
                        msg = "ioTank:" + str(bot.name) + " has not communicated with the server in over 15 minutes"
                        print(msg)
                        if account.notify_email is True and account.email_daily > 0:
                            send_email.apply_async((email_subject, msg, account.user.email, account.user.id))
                except:
                    print(bot)
                    print(SensorReading.objects.filter(bot=bot))
