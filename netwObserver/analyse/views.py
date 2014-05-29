from django.shortcuts import render
from analyse.computation import aggregator
from analyse.observation import monitoring
from gatherer.models import AccessPoint
from django.core.exceptions import ObjectDoesNotExist

from datetime import datetime

# Create your views here.
def general(request):
	context = {}
	context['app'] = 'analysis'
	context['cat'] = 'gen'
	
	context['wronglyPlugged'] = len(monitoring.getDhcpWrongPlugAlerts())
	context['nbrUsers'] = aggregator.getNbrOfUsers()
	context['nbrAP'] = aggregator.getNbrOfAP()

	return render(request, "analyse/general.html", context)

def controller(request):
	context = {}
	context["cat"] = 'controller'
	context['app'] = 'analysis'

	context['byCategory'] = aggregator.getWismLogsByCategory()

	return render(request, "analyse/controller.html", context)


def wifiOverview(request):
	context= {}
	context['app'] = 'analysis'
	context['cat'] = 'wifi'
	context['section'] = 'overview'

	context["apDown"] = AccessPoint.objects.areDown()

	return render(request, "analyse/wifiOverview.html", context)

def wifiAP(request, order='name'):
	context= {}
	context['app'] = 'analysis'
	context['cat'] = 'wifi'
	context['section'] = 'ap'

	context["allAP"] = AccessPoint.objects.all().order_by('name')

	if request.method == 'GET' and 'selectedAP' in request.GET:
		try:
			context["ap"] = AccessPoint.objects.get(id=int(request.GET['selectedAP']))
			context["apData"] = aggregator.getAPData(context["ap"])
			context["interfaceData"] = aggregator.getAllIfData(context["ap"])
		except:
			pass

	return render(request, "analyse/wifiAP.html", context)

def wifiRAP(request):
	context= {}
	context['app'] = 'analysis'
	context['cat'] = 'wifi'
	context['section'] = 'rap'

	return render(request, "analyse/wifiRAP.html", context)

def wifiUsers(request):
	context= {}
	context['app'] = 'analysis'
	context['cat'] = 'wifi'
	context['section'] = 'users'

	context["proto"] = aggregator.getUsersByDot11Protocol()
	context["ssid"] = aggregator.getUsersBySSID()

	return render(request, "analyse/wifiUsers.html", context)

def wifiProbes(request):
	context= {}
	context['app'] = 'analysis'
	context['cat'] = 'wifi'
	context['section'] = 'probes'
	
	context["allProbe"] = aggregator.getAllProbes()
	
	if request.method == 'GET' and 'selectedProbe' in request.GET:
		try:
			context["probe"] = MobileStation.objects.get(id=int(request.GET['selectedProbe']))
			context["lastScan"] = aggregator.getLastScan(context["probe"])
		except:
			pass

	return render(request, "analyse/wifiProbe.html", context)

def dhcpAlerts(request):
	context= {}
	context['app'] = 'analysis'
	context['cat'] = 'dhcp'
	context['section'] = 'alerts'

	context['active'] = monitoring.isDhcpActive()
	context['leaseAlerts'] = monitoring.getDhcpLeaseAlerts()
	context['wronglyPlugged'] = monitoring.getDhcpWrongPlugAlerts()

	return render(request, "analyse/dhcpAlerts.html", context)

def dhcpGraph(request):
	context= {}
	context['app'] = 'analysis'
	context['cat'] = 'dhcp'
	context['section'] = 'graph'
	
	context['byType'] = aggregator.getDhcpLogByType()

	return render(request, "analyse/dhcpGraph.html", context)


def radius(request):
	context= {}
	context['app'] = 'analysis'
	context['cat'] = 'radius'

	context['successRate'] = aggregator.getRadiusSuccessRate()

	return render(request, "analyse/radius.html", context)
