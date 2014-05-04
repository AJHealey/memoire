from django.shortcuts import render
from analyse.computation import aggregator

# Create your views here.
def analyse(request, cat='ms'):
	context = {}
	context["cat"] = cat
	context['app'] = 'analysis'

	if cat == 'ms':
		context["ms"] = {'proto' : aggregator.getUserByDot11Protocol(), "Hot Access Point": aggregator.getHotAP()}

	elif cat == "wism":
		context["wism"] = {"pass":'test'}

	return render(request, "analyse/analyse.html", context)
