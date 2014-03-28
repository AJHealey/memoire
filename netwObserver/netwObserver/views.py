from django.shortcuts import render


# Create your views here.
def home(request):
	context = {}
	context['app'] = '' 

	# Test
	from gatherer.snmp.getter import getAPIfLoadChannelUtilization,getAPIfLoadRxUtilization,getAPIfLoadTxUtilization,getAPIfLoadNumOfClients,getAPIfPoorSNRClients
	context["test"] = [getAPIfLoadRxUtilization(ip='192.168.251.170', ap='.184.56.97.60.37.128'),getAPIfLoadTxUtilization(ip='192.168.251.170', ap='.184.56.97.60.37.128'),getAPIfLoadChannelUtilization(ip='192.168.251.170', ap='.184.56.97.60.37.128'),getAPIfLoadNumOfClients(ip='192.168.251.170', ap='.184.56.97.60.37.128'),getAPIfPoorSNRClients(ip='192.168.251.170', ap='.184.56.97.60.37.128')]

	return render(request, "common/home.html", context)

	