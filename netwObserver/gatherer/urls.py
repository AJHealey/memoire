from django.conf.urls import patterns, url

from gatherer import views

urlpatterns = patterns('',
	url(r'^$', views.index, name='index'),
	url(r'^logs/$', views.dhcplogs, name='logs'),

	url(r'^logs/wism/(?P<page>\d+)', views.wismlogs, name='wismlogs'),
	url(r'^logs/wism/', views.wismlogs, name='wismlogs'),

	url(r'^logs/dhcp/(?P<page>\d+)', views.dhcplogs, name='dhcplogs'),
	url(r'^logs/dhcp/', views.dhcplogs, name='dhcplogs'),
	
	url(r'^logs/radius/(?P<page>\d+)', views.radiuslogs, name='radiuslogs'),
	url(r'^logs/radius/', views.radiuslogs, name='radiuslogs'),
	
	url(r'^snmp/$', views.apsnmp, name='snmp'),

	url(r'^snmp/ap/(?P<page>\d+)', views.apsnmp, name='apsnmp'),
	url(r'^snmp/ap', views.apsnmp, name='apsnmp'),

	url(r'^snmp/ms/(?P<page>\d+)', views.mssnmp, name='mssnmp'),
	url(r'^snmp/ms', views.mssnmp, name='mssnmp'),

	url(r'^snmp/rap/(?P<page>\d+)', views.rapsnmp, name='rapsnmp'),
	url(r'^snmp/rap', views.rapsnmp, name='rapsnmp'),

)