from django.conf.urls import patterns, url

from gatherer import views

urlpatterns = patterns('',
	url(r'^$', views.index, name='index'),
	url(r'^logs/$', views.logs, name='logs'),
    url(r'^logs/(?P<cat>\S*)', views.logs, name='logs'),
    url(r'^snmp/', views.snmp, name='snmp'),
)