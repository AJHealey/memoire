from django.shortcuts import render
from analyse.computation import aggregator

# Create your views here.
def analyse(request, cat='gen'):
	context = {}
	context["cat"] = cat
	context['app'] = 'analysis'

	# General Indicators
	if cat == 'gen':
		context["gen"] = {'nbrUsers' : aggregator.getNbrOfUsers(), 'nbrAP' : aggregator.getNbrOfAP()}

	# Wifi related issues
	elif cat == 'wifi':
		context["ms"] = {'proto' : aggregator.getUserByDot11Protocol(), 'hotAP': aggregator.getHotAP()}

	# Controller related issues
	elif cat == "wism":
		tmp = aggregator.getWismLogByType()
		context["wism"] = {'logsCount':'test'}

	# DHCP related issues
	elif cat == 'dhcp':
		pass

	# Radius related issues
	elif cat == 'radius':
		pass

	return render(request, "analyse/analyse.html", context)
