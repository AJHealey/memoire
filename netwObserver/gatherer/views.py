from os import listdir
from os.path import isfile,join
from threading import Thread
from datetime import timedelta

from django.core.context_processors import csrf
from django.db import IntegrityError
from django.shortcuts import render
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from gatherer.log.logParser import parser
from gatherer.models import UserDevice, RadiusEvent, DHCPEvent, WismEvent, BadLog

from gatherer.log.events import *

TMPFILE="gatherer/tmp/"
SEVERITYMEANING = ['Emergency: System is unusable','Alert: Action must be taken immediately', 'Critical: Critical conditions', 'Error: Error conditions', 'Warning: Warning conditions', 'Notice: Normal but significant condition', 'Informational: Informational messages', 'Debug: Debug-level messages']

def index(request):
	context = {}
	context['logFiles'] = [ f for f in listdir(TMPFILE) if isfile(join(TMPFILE,f))]
	context.update(csrf(request))

	if 'selectLogFile' in request.POST and request.POST['selectLogFile'] != '':
		selectedLogFile = context['logFiles'][int(float(request.POST['selectLogFile']))-1]
		Thread(target=logParsing, args=(join(TMPFILE,selectedLogFile),)).start()
		#logParsing(join(TMPFILE,selectedLogFile))

	return render(request, "gatherer/index.html", context)

def logs(request, cat='dhcp', page=1, perpage=100):
	context = {}
	context['cat'] = cat

	## DHCP Logs
	if cat == 'dhcp':
		tmpQuery = DHCPEvent.objects.order_by('-date')
		p = Paginator(tmpQuery,perpage)
		try:
			context['dhcpEvent'] = p.page(page)
		except PageNotAnInteger:
			context['dhcpEvent'] = p.page(1)
		except EmptyPage:
			context['dhcpEvent'] = p.page(p.num_pages)


	## Radius Logs
	elif cat == 'radius':
		tmpQuery = RadiusEvent.objects.order_by('-date')
		p = Paginator(tmpQuery,perpage)
		try:
			context['radiusEvent'] = p.page(page)
		except PageNotAnInteger:
			context['radiusEvent'] = p.page(1)
		except EmptyPage:
			context['radiusEvent'] = p.page(p.num_pages)


	## Wism Logs
	elif cat == 'wism':
		context['sevMeaning'] = SEVERITYMEANING
		tmpQuery = WismEvent.objects.order_by('-date')
		p = Paginator(tmpQuery,perpage)
		try:
			context['wismEvent'] = p.page(page)
		except PageNotAnInteger:
			context['wismEvent'] = p.page(1)
		except EmptyPage:
			context['wismEvent'] = p.page(p.num_pages)



	return render(request, "gatherer/logs.html", context)

def snmp(request):
	context = {}
	return render(request, "gatherer/snmp.html", context)


######################

def logParsing(path):
	
	for event in parser(path):
		try:
			if isinstance(event,NotAnEvent):
				pass

			## Radius Events
			if isinstance(event,RadiusOk):
				RadiusEvent.objects.create(date=event.date, login=event.login, radiusType='OK')

			elif isinstance(event,RadiusIncorrect):
				RadiusEvent.objects.create(date=event.date, login=event.login, radiusType='KO')

			elif isinstance(event,RadiusError):
				RadiusEvent.objects.create(date=event.date, message=event.message, radiusType='error')

			elif isinstance(event,RadiusNotice):
				RadiusEvent.objects.create(date=event.date, message=event.message, radiusType='notice')

			elif isinstance(event,RadiusInfo):
				RadiusEvent.objects.create(date=event.date, message=event.message, radiusType='info')


			## DHCP Events
			elif isinstance(event,DHCPDiscover):
				DHCPEvent.objects.create(date=event.date, server=event.dhcpServer, device=event.device, dhcpType='Discover')

			elif isinstance(event,DHCPRequest):
				DHCPEvent.objects.create(date=event.date, server=event.dhcpServer, device=event.device, dhcpType='Request', ip=event.ipRequested)

			elif isinstance(event,DHCPOffer):
				DHCPEvent.objects.create(date=event.date, server=event.dhcpServer, device=event.device, dhcpType='Offer',  ip=event.ipOffered)

			elif isinstance(event,DHCPAck):
				DHCPEvent.objects.create(date=event.date, server=event.dhcpServer, device=event.device, dhcpType='Ack',  ip=event.ipAcked)

			## Wism Event
			elif isinstance(event,WismLog):
				WismEvent.objects.create(date=event.date, ip=event.ip, category=event.category, severity=event.severity, mnemo=event.mnemo, message=event.message)

			#####
			elif isinstance(event,UnparsedLog):
				BadLog.objects.create(log=event.log, cause=event.cause)

		except IntegrityError:
			pass





