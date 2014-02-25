from django.shortcuts import render
from django.http import HttpResponse

from gatherer.models import UserDevice

def index(request):
	context = {}
	context['users'] = UserDevice.objects.all()
	return render(request, "gatherer/index.html", context)

def logs(request):
	#context = {}
	return render(request, "gatherer/logs.html")

def snmp(request):
	context = {}
	return render(request, "gatherer/snmp.html", context)




