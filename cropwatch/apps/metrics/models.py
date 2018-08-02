import uuid

from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _
from timezone_field import TimeZoneField

NOTICE_TYPE = (
    ('I', 'ioTank Emergency'),
)


class Notice(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    taskid = models.CharField(_('Task ID'), max_length=36)
    type = models.CharField(max_length=1, choices=NOTICE_TYPE)
    timestamp = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        verbose_name = _('Notice')
        verbose_name_plural = _('Notices')
        ordering = ('owner',)

    def __str__(self):
        return str(self.taskid)

    def __unicode__(self):
        return str(self.taskid)


class Notices(models.Model):
    sentdt = models.DateTimeField(auto_now_add=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=1, choices=NOTICE_TYPE)
    value = models.CharField(max_length=50)


class AccountSettings(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timezone = TimeZoneField()

    notify_iotank_emergency = models.BooleanField(default=True)
    notify_email = models.BooleanField(default=True)

    email_daily = models.PositiveSmallIntegerField(default=1)

    def __str__(self):
        return str(self.user)

    def __unicode__(self):
        return str(self.user)

    class Meta:
        verbose_name = 'Account Setting'
        verbose_name_plural = 'Account Settings'



from django.utils import timezone


UNIT = (
    ('C', 'Celsius'),
    ('F', 'Fahrenheit'),
)


# Create your models here.
class ioTank(models.Model):
    bot_user = models.ForeignKey(User, related_name="bot_owner", on_delete=models.CASCADE)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    qrcode = models.ImageField(upload_to='qrcode', blank=True, null=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    m = models.DecimalField(_('Minimum Temperature 1'), max_digits=6, decimal_places=2, default=0)
    x = models.DecimalField(_('Maximum Temperature 1'), max_digits=6, decimal_places=2, default=100)

    m2 = models.DecimalField(_('Minimum Temperature 2'), max_digits=6, decimal_places=2, default=0)
    x2 = models.DecimalField(_('Maximum Temperature 2'), max_digits=6, decimal_places=2, default=100)

    mh = models.DecimalField(_('Minimum Humidity'), max_digits=6, decimal_places=2, default=0)
    xh = models.DecimalField(_('Maximum Humidity'), max_digits=6, decimal_places=2, default=100)

    night_start = models.TimeField(_('Nighttime Start'), default='19:00')
    night_end = models.TimeField(_('Nighttime End'), default='07:00')
    night_max_light = models.DecimalField(_('Night Maximum Light'), max_digits=6, decimal_places=2, default=0.50)
    day_min_light = models.DecimalField(_('Day Minimum Light'), max_digits=6, decimal_places=2, default=5000)

    u = models.CharField(_('Temperature Unit'), max_length=1, default='F', choices=UNIT)

    name = models.CharField(max_length=100, blank=True, null=True, )


    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = 'ioTank'
        verbose_name_plural = 'ioTanks'


class SensorReading(models.Model):
    bot = models.ForeignKey(ioTank, editable=False, on_delete=models.CASCADE)
    t1 = models.DecimalField(_('Waterproof Temp'), max_digits=6, decimal_places=2)
    t2 = models.PositiveSmallIntegerField(_('Box Temperature'))
    h = models.PositiveSmallIntegerField(_('Humidity'))

    uv = models.DecimalField(_('UV Index'), max_digits=6, decimal_places=2)
    l = models.DecimalField(_('UV Index'), max_digits=12, decimal_places=2)

    timestamp = models.DateTimeField(editable=False)

    def save(self, *args, **kwargs):
        if not self.timestamp:
            self.timestamp = (timezone.now())
        super(SensorReading, self).save(*args, **kwargs)

    def __str__(self):
        return str(self.timestamp)

    class Meta:
        verbose_name = 'Sensor Reading'
        verbose_name_plural = 'Sensor Readings'
