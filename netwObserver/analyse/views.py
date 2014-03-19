from django.shortcuts import render
from analyse.computation import aggregator

# Create your views here.
def analyse(request, cat='ms'):
	context = {}
	context["cat"] = cat
	context['app'] = 'analysis'

	if cat == 'ms':
		context["ms"] = {'802.11 Protocol' : aggregator.getUserByDot11Protocol()}

	elif cat == "wism":
		context["wism"] = {"pass":'test'}

	return render(request, "analyse/analyse.html", context)
