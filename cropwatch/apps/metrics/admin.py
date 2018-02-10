from django.contrib import admin

from cropwatch.apps.metrics.models import AccountSettings, Notice, ioTank, SensorReading


class AccountSettingsAdmin(admin.ModelAdmin):
    pass

admin.site.register(AccountSettings, AccountSettingsAdmin)

class NoticeAdmin(admin.ModelAdmin):
    pass

admin.site.register(Notice, NoticeAdmin)

# Register your models here.
class ioTankAdmin(admin.ModelAdmin):
    readonly_fields = ['bot_user']
    list_filter = ('bot_user', 'owner')
    list_display = ('bot_user', 'owner')

    def get_readonly_fields(self, request, obj=None):
        if obj:  # This is the case when obj is already created i.e. it's an edit
            return ['bot_user']
        else:
            return []


admin.site.register(ioTank, ioTankAdmin)


class SensorReadingAdmin(admin.ModelAdmin):
    list_filter = ('bot', 'timestamp')
    list_display = ('bot', 'timestamp')
    readonly_fields = ['timestamp']


admin.site.register(SensorReading, SensorReadingAdmin)
