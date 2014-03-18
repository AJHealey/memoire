from django.shortcuts import render
from analyse.computation import aggregator

# Create your views here.
def analyse(request, cat='ms'):
	context = {}
	context["cat"] = cat
	context['app'] = 'analysis'

	if cat == 'ms':
		context["ms"] = {'802.11 Statistics' : "3" + str(aggregator.getUserByDot11Protocol())}

	elif cat == "wism":
		context["wism"] = {}

	return render(request, "analyse/analyse.html", context)
