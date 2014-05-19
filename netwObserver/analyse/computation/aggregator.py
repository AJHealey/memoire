from datetime import datetime,timedelta
from django.utils import timezone

from gatherer.models import WismEvent, DHCPEvent, RadiusEvent, MobileStation, AccessPoint, APSnapshot, APIfSnapshot
from django.core.exceptions import ObjectDoesNotExist


MAX_VALUE_SNMP_COUNTER32 = 4294967295

## Logs Aggregators
def getWismLogsByCategory():
	stats = {}
	## Logs More important than informational (level 5 at least)
	logs = WismEvent.objects.filter(severity__lte=5)
	categories = logs.values_list('category', flat=True).distinct()
	for cat in categories:
		stats[cat] = logs.filter(category=cat).count()

	return stats

def getDhcpLogByType():
	stats = {}
	for t, display in DHCPEvent.DHCP_TYPES:
		tmp = DHCPEvent.objects.filter(dhcpType=t).count()
		if tmp > 0:
			stats[display] = tmp
	return stats

def getRadiusSuccessRate():
	return {
		"Success" : RadiusEvent.objects.filter(radiusType="ok").count(),
		"Failed" : RadiusEvent.objects.filter(radiusType="ko").count(),
	}

## Users Aggregators 
def getUsersByDot11Protocol(timedeltaData=timedelta(weeks=12)):
	stats = {}
	ms = MobileStation.objects.filter(lastTouched__gte=timezone.now() - timedeltaData)
	for proto,display in MobileStation.DOT11_PROTOCOLS:
		tmp =  ms.filter(dot11protocol__exact=proto).count()
		if tmp > 0:
			stats[display] = tmp 
	return stats

def getUsersBySSID():
	stats = {}
	for ssid in MobileStation.objects.values_list('ssid', flat=True).distinct():
		stats[ssid] = MobileStation.objects.isAssociated().filter(ssid=ssid).count()
	return stats

def getNbrOfUsers():
	return MobileStation.objects.isAssociated().count()

## AP aggregators
def getHotAP(number=5):
	ap = sorted([(ap.nbrOfClients(), ap) for ap in AccessPoint.objects.isUp()], reverse=True)
	return ap[:number]

def getNbrOfAP():
	return AccessPoint.objects.isUp().count()

def getAPData(ap, timePerRange=timedelta(hours=1)):
	""" Speed in mbits """
	result = []
	try:
		snapshots = APSnapshot.objects.filter(ap=ap).order_by('date')
		
		datetimeStartRange = snapshots[0].date
		
		ethernetRxTotalBytesStart = snapshots[0].ethernetRxTotalBytes
		ethernetRxTotalBytesEnd = snapshots[0].ethernetRxTotalBytes
		
		ethernetTxTotalBytesStart = snapshots[0].ethernetTxTotalBytes
		ethernetTxTotalBytesEnd = snapshots[0].ethernetTxTotalBytes

		for snap in snapshots:
			if snap.date < (datetimeStartRange + timePerRange):
				ethernetRxTotalBytesEnd = snap.ethernetRxTotalBytes
				ethernetTxTotalBytesEnd = snap.ethernetTxTotalBytes

			else:
				#Counter32 Wrapping
				if ethernetRxTotalBytesStart > ethernetRxTotalBytesEnd:
					total = ((MAX_VALUE_SNMP_COUNTER32 - ethernetRxTotalBytesStart) + ethernetRxTotalBytesEnd)
					rxspeed = ((total/timePerRange.seconds)*8)
				else:
					rxSpeed = (((ethernetRxTotalBytesEnd - ethernetRxTotalBytesStart)/timePerRange.seconds)*8)
				
				if ethernetTxTotalBytesStart > ethernetTxTotalBytesEnd:
					total = ((MAX_VALUE_SNMP_COUNTER32 - ethernetTxTotalBytesStart) + ethernetTxTotalBytesEnd)
					txSpeed = ((total/timePerRange.seconds)*8)
				else:
					txSpeed = (((ethernetTxTotalBytesEnd - ethernetTxTotalBytesStart)/timePerRange.seconds)*8)
				
				result.append({'date':datetimeStartRange+timePerRange/2, 'rx':float(rxSpeed)/1000, 'tx':float(txSpeed)/1000})

				# Start new range
				datetimeStartRange = snap.date
				ethernetRxTotalBytesStart = snap.ethernetRxTotalBytes
				ethernetRxTotalBytesEnd = snap.ethernetRxTotalBytes
				ethernetTxTotalBytesStart = snap.ethernetTxTotalBytes
				ethernetTxTotalBytesEnd = snap.ethernetTxTotalBytes

	except ObjectDoesNotExist:
		pass

	return result

