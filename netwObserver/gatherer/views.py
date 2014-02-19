from django.shortcuts import render
from django.http import HttpResponse

from gatherer.models import UserDevice

def index(request):
	context = {}
	context['users'] = UserDevice.objects.all()
	return render(request, "gatherer/index.html", context)



