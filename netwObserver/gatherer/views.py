from os import listdir
from os.path import isfile,join

from django.shortcuts import render
from django.http import HttpResponse

from gatherer.log.logParser import parser
from gatherer.models import UserDevice,DHCPEvent, BadLog

from gatherer.log.events import *

TMPFILE="gatherer/tmp/"

def index(request):
	context = {}
	context['logFiles'] = [ f for f in listdir(TMPFILE) if isfile(join(TMPFILE,f))]

	if 'selectLogFile' in request.POST:
		selectedLogFile = context['logFiles'][int(float(request.POST['selectLogFile']))-1]
		logParsing(join(TMPFILE,selectedLogFile))

	return render(request, "gatherer/index.html", context)

def logs(request, cat='dhcp'):
	context = {}
	context['dhcpEvent'] = DHCPEvent.objects.order_by('date')
	context["cat"] = cat
	return render(request, "gatherer/logs.html", context)

def snmp(request):
	context = {}
	return render(request, "gatherer/snmp.html", context)


######################

def logParsing(path):
	
	for event in parser(path):
		## DHCP Events
		if isinstance(event,DHCPDiscover):
			DHCPEvent.objects.create(date=event.date, milisec=event.date.microsecond, server=event.dhcpServer, device=event.device, dhcpType='Discover')

		elif isinstance(event,DHCPRequest):
			DHCPEvent.objects.create(date=event.date, milisec=event.date.microsecond, server=event.dhcpServer, device=event.device, dhcpType='Request', ip=event.ipRequested)

		elif isinstance(event,DHCPOffer):
			DHCPEvent.objects.create(date=event.date, milisec=event.date.microsecond, server=event.dhcpServer, device=event.device, dhcpType='Offer',  ip=event.ipOffered)

		elif isinstance(event,DHCPAck):
			DHCPEvent.objects.create(date=event.date, milisec=event.date.microsecond, server=event.dhcpServer, device=event.device, dhcpType='Ack',  ip=event.ipAcked)


		#####
		elif isinstance(event,UnparsedLog):
			BadLog.objects.create(log=event.log)




