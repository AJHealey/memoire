from os import listdir
from os.path import isfile,join, splitext
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
		#Thread(target=logParsing, args=(join(TMPFILE,selectedLogFile),)).start()
		logParsing(join(TMPFILE,selectedLogFile))

	return render(request, "gatherer/index.html", context)

def logs(request, cat='dhcp', page=1, perpage=100, filters={}):
	context = {}
	context['cat'] = cat
	context['perpage'] = perpage
	context['page'] = page
	context['filters'] = filters

	## DHCP Logs
	if cat == 'dhcp':
		tmpQuery = DHCPEvent.objects.order_by('-date')
		
		if 'filterIP' in filters:
			tmpQuery = tmpQuery.filter(ip=filters['filterIP'])
		if 'filterType' in filters:
			tmpQuery = tmpQuery.filter(ip=filters['filterType'])
		if 'filterDevice' in filters:
			tmpQuery = tmpQuery.filter(ip=filters['filterDevice'])
		
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


####### Auxiliary Methods ######
def logParsing(path):

	# keeps the entries not put in the DB
	entries = []

	for i, event in enumerate(parser(path)):

		## Unuseful log
		if isinstance(event,NotAnEvent):
			pass

		## Radius Events
		if isinstance(event,RadiusOk):
			entries.append(RadiusEvent(date=event.date, login=event.login, radiusType='OK'))

		elif isinstance(event,RadiusIncorrect):
			entries.append(RadiusEvent(date=event.date, login=event.login, radiusType='KO'))

		elif isinstance(event,RadiusError):
			entries.append(RadiusEvent(date=event.date, message=event.message, radiusType='error'))

		elif isinstance(event,RadiusNotice):
			entries.append(RadiusEvent(date=event.date, message=event.message, radiusType='notice'))

		elif isinstance(event,RadiusInfo):
			entries.append(RadiusEvent(date=event.date, message=event.message, radiusType='info'))

		## DHCP Events
		elif isinstance(event,DHCPDiscover):
			entries.append(DHCPEvent(date=event.date, server=event.dhcpServer, device=event.device, dhcpType='Discover', message=event.message))

		elif isinstance(event,DHCPRequest):
			entries.append(DHCPEvent(date=event.date, server=event.dhcpServer, device=event.device, dhcpType='Request', ip=event.ipRequested))

		elif isinstance(event,DHCPOffer):
			entries.append(DHCPEvent(date=event.date, server=event.dhcpServer, device=event.device, dhcpType='Offer',  ip=event.ipOffered))

		elif isinstance(event,DHCPAck):
			entries.append(DHCPEvent(date=event.date, server=event.dhcpServer, device=event.device, dhcpType='Ack',  ip=event.ipAcked))

		elif isinstance(event,DHCPNak):
			entries.append(DHCPEvent(date=event.date, server=event.dhcpServer, device=event.device, dhcpType='Nak',  ip=event.ipNak))


		elif isinstance(event,DHCPLog):
			entries.append(DHCPEvent(date=event.date, server=event.dhcpServer, dhcpType='Log', message=event.message, ip=event.ip))

		elif isinstance(event,DHCPWarning):
			entries.append(DHCPEvent(date=event.date, server=event.dhcpServer, dhcpType='Warning', message=event.message, ip=event.ip))

		## Wism Event
		elif isinstance(event,WismLog):
			entries.append(WismEvent(date=event.date, ip=event.ip, category=event.category, severity=event.severity, mnemo=event.mnemo, message=event.message))
		
		##### Bad logs
		elif isinstance(event,UnparsedLog):
			entries.append(BadLog(log=event.log, cause=event.cause))

		# groups the access to the database
		if (i+1) % 500 == 0:
			addBatch(entries)
			entries = []

	addBatch(entries)

	# Save the wrong logs and delete them from the DB
	name,ext = splitext(path)
	saveBadLogs(name + '.badLogs')


def addBatch(entrieslist):
	""" Add all the entries in lists to the DB

	Argument:
	list -- list of entries
	"""
	for element in entrieslist:
		try:
			element.save()
		except IntegrityError:
			pass

def saveBadLogs(path):
	""" Save the unparsed log in path and remove them from the DB

	Argument:
	path -- the path where the bad logs are saved
	"""
	
	badLogs = BadLog.objects.all()
	if len(badLogs) > 0:
		with open(path, 'w') as f:
			for element in badLogs:
				f.write(str(element) + '\n')

		badLogs.delete()

