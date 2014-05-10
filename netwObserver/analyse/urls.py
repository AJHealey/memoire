from django.conf.urls import patterns, url

from analyse import views

urlpatterns = patterns('',
	url(r'^$', views.analyse, name='analyse'),
	url(r'^(?P<cat>\S+)', views.analyse, name='analyse'),
)