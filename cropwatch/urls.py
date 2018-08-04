import debug_toolbar
from django.conf.urls import include
from django.conf.urls import url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView

from cropwatch import settings
from cropwatch.apps.metrics import views as metrics_views
from cropwatch.apps.metrics.api import *

js_info_dict = {
    'packages': ('recurrence')
}
urlpatterns = [
                  # breadcrumbs
                  url(r'^$', RedirectView.as_view(url='/metrics/')),
                  url(r'^__debug__/', include(debug_toolbar.urls)),
                  url(r'^login/$', auth_views.login),
                  url(r'^logout/$', auth_views.logout, {'next_page': '/'}),
                  url(r'^register/$', metrics_views.register),
                  url(r'^settings/$', metrics_views.settings),
                  url(r'^admin/', admin.site.urls),
                  url(r'^reset/$', metrics_views.reset, name='reset'),

                  url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
                      metrics_views.reset_confirm, name='password_reset_confirm'),

                  url(r'^success/$', metrics_views.success, name='success'),
                  url(r'^resetsent/$', metrics_views.resetsent, name='resetsent'),

                  # ioTank web
                  url(r'^devices/$', metrics_views.devices, name='devices'),
                  url(r'^device/add/$', metrics_views.bot_add, name='bot_add'),
                  url(r'^device/delete/(?P<uuid>[^/]+)$', metrics_views.bot_delete, name="bot_delete"),
                  url(r'^device/regen/(?P<uuid>[^/]+)$', metrics_views.bot_regen, name="bot_regens"),

                  # ioTank API in/out
                  url(r'^api/v1/post/$', v1_iot, name='v1_iot'),
                  url(r'^api/v1/add/$', v1_ioTank_add, name='v1_ioTank_add'),
                  url(r'^api/v1/delete/$', v1_ioTank_delete, name='v1_ioTank_delete'),
                  url(r'^api/v1/list/$', v1_ioTank_list, name='v1_ioTank_list'),
                  url(r'^api/flot/(?P<start>[^/]+):(?P<end>[^/]+)/(?P<uuid>[^/]+)$', metrics_views.flot_ajax,
                      name='flot_ajax'),

                  # Api Auth
                  url(r'^api/obtain_token/', obtain_auth_token),
                  # user/pass turns into rest token, obtain_auth_token is coming from metrics.api it is an override
                  url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),

                  # Metrics/scheduling/
                  url(r'^metrics/$', metrics_views.base, name="schedule"),
                  url(r'^iotank/(?P<uuid>[^/]+)$', metrics_views.iotank_edit, name="ioTank_edit"),

                  # Notices
                  url(r'^notices/$', metrics_views.notice),
                  url(r'^s/$', metrics_views.status),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL,
                                                                                         document_root=settings.STATIC_ROOT)
