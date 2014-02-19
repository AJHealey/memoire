from django.conf.urls import patterns, url

from gatherer import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
)