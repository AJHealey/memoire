import operator

from django.conf import settings
from datetime import timedelta

from django.utils import timezone
from gatherer.models import *


def getOverloadedAP(since=settings.AP_OVERLOADED_PERIOD):
	""" Get the Access Point which have been detected as overloadedSnaps

		arguments:
		since - period of the analysis

		return: 
		[{'ap': <AccessPoint>, 'overload': <int>}, ... ]
		A list of dictionnary reverse order by the number of overload.
	"""
	result = {}
	overloadedSnaps = APIfSnapshot.objects.filter(apifsnapshotdata__name="channelUtilization",apifsnapshotdata__value__gt=settings.CHANNEL_UTILIZATION_TRESHOLD,date__gte=timezone.now()-since)

	for snap in overloadedSnaps:
		if snap.apinterface.ap.name not in result:
			result[snap.apinterface.ap.name] = {'ap': snap.apinterface.ap, "overload":0}

		result[snap.apinterface.ap.name]["overload"] += 1

	return sorted(result.values(), key=operator.itemgetter('overload'),reverse=True)


def getDhcpLeaseAlerts(fromDate=(timezone.now() - settings.DHCP_LEASE_ALERT_TRESHOLD)):
	""" Compute the concentration of the lease alert among device

		A low value means that the alerts a shattered among a high
		number of devices.

		argument:
		fromDate - period of analysis
	"""
	logs = DHCPEvent.objects.filter(dhcpType= "dis", date__gte=fromDate, message__icontains="free leases")
	nbrAlert = logs.count()
	devices = len(set(logs.values_list('device', flat=True)))
	if devices > 0:
		return {"alerts": logs , "devices": devices, "ratio": nbrAlert/devices}
	else:
		return {}

def getDhcpWrongPlugAlerts(fromDate=(timezone.now() - timedelta(hours=1))):
	""" Look for a pattern that recognize the wrongly plugged device 

		The pattern is a 'peer holds all free leases' alert on
		all the dhcp server at the same time.

		argument:
		fromDate - period of analyse
	"""
	result = {}

	logs = DHCPEvent.objects.filter(dhcpType= "dis", date__gte=fromDate, message__icontains="peer holds all free leases").order_by('date','microsecond')
	lastTime = None
	lastDevice = None
	lastServer = None
	lastVia = None
	for log in logs:
		time = log.date
		device = log.device
		server = log.server
		via = log.via
		if  lastTime == None:
			lastTime = time
			lastDevice = device
			lastServer = server
			lastVia = via

		elif (time - lastTime) < timedelta(seconds=2) and device == lastDevice and via == lastVia and server != lastServer:
			result[device] = {"date": timezone.localtime(time), "via": via}
		

		lastTime = time
		lastDevice = device
		lastServer = server
		lastVia = via


	return result

def isDhcpActive(lastAck=settings.DHCP_ACTIVITY_ALERT):
	""" Check if a DHCP Ack have been recorded recently

		argument:
		lastAck - period of verification (define recently)
	"""
	return DHCPEvent.objects.filter(dhcpType= "ack", date__gte=(timezone.now() - lastAck)).exists()

