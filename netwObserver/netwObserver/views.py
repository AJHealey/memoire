from django.shortcuts import render


# Create your views here.
def home(request):
	context = {}
	context['app'] = '' 

	# Test
	from gatherer.snmp.getter import getAPIfLoadChannelUtilization,getAPIfLoadRxUtilization,getAPIfLoadTxUtilization,getAPIfLoadNumOfClients,getAPIfPoorSNRClients
	from gatherer.models import AccessPoint
	ap = AccessPoint.objects.get(macAddress='b8:38:61:43:91:50')
	context["test"] = [getAPIfLoadRxUtilization(ip='192.168.251.170', ap=ap.index),getAPIfLoadTxUtilization(ip='192.168.251.170', ap='.184.56.97.60.37.128'),getAPIfLoadChannelUtilization(ip='192.168.251.170', ap='.184.56.97.60.37.128'),getAPIfLoadNumOfClients(ip='192.168.251.170', ap='.184.56.97.60.37.128'),getAPIfPoorSNRClients(ip='192.168.251.170', ap='.184.56.97.60.37.128')]

	return render(request, "common/home.html", context)

	