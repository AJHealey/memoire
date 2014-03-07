from django.shortcuts import render

# Create your views here.
def home(request):
	context = {}
	context['app'] = '' 
	return render(request, "common/home.html", context)