from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    )
urlpatterns += patterns('es-graphite-shim.views',
    url(r'^$', 'homepage', name='home'),
    url(r'^mapping/?$', 'view_mapping', name='mapping'),
    url(r'^render/?$', 'metrics_render', name='render'),
    url(r'^metrics/find/?$', 'metrics_find', name='find'),
    url(r'^dashboard/find/?$', 'dashboard_find', name='dash_find'),
    )
