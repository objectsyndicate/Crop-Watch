from __future__ import absolute_import

from celery import shared_task
from django.contrib.auth.models import User
from django.core.mail import send_mail

from cropwatch.apps.metrics.models import AccountSettings, Notice
from cropwatch.settings import DEFAULT_FROM_EMAIL

@shared_task(bind=True)
def send_email(self, subject, body, to, user):
    settings = AccountSettings.objects.get(user=user)
    settings.email_daily = settings.email_daily - 1
    settings.save()
    notice = Notice()
    notice.taskid = self.request.id
    notice.owner = User.objects.get(id=user)
    notice.type = "E"
    notice.save()
    mail = send_mail(
        subject,
        body + " if you would like to unsubscribe from notifications modify your Crop🌱Watch settings ID:" + str(
            notice.id),
        DEFAULT_FROM_EMAIL,
        [to],
        fail_silently=False,
    )
    return mail
