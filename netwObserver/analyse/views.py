from django.shortcuts import render

# Create your views here.
def index(request):
	context = {}
	context['app'] = 'analysis' 
	return render(request, "analyse/index.html", context)