from django.shortcuts import render
from analyse.computation import aggregator

# Create your views here.
def analyse(request, cat='gen'):
	context = {}
	context["cat"] = cat
	context['app'] = 'analysis'

	if cat == 'gen':
		context["gen"] = {'nbrUsers' : }

	elif cat == 'wifi':
		context["ms"] = {'proto' : aggregator.getUserByDot11Protocol(), "Hot Access Point": aggregator.getHotAP()}

	elif cat == "wism":
		tmp = aggregator.getWismLogByType()
		context["wism"] = {'logsCount':'test'}

	return render(request, "analyse/analyse.html", context)
