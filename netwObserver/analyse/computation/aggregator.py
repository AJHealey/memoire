from datetime import datetime,timedelta

from gatherer.models import WismEvent, MobileStation, AccessPoint, APSnapshot, APIfSnapshot
from django.core.exceptions import ObjectDoesNotExist


MAX_VALUE_SNMP_COUNTER32 = 4294967295

def getWismLogByType():
	stats = {}
	logs = WismEvent.objects
	categories = logs.distinct('category').values_list('category',flat=True).order_by('category')
	for cat in categories:
		stats[cat] = {}

		for element in logs.filter(category__exact=cat).distinct('severity','mnemo').values('severity','mnemo'):
			severity = element['severity']
			mnemo = element['mnemo']
			if not severity in stats[cat]:
				stats[cat][severity] = {}
			
			stats[cat][severity][mnemo] = logs.filter(category__exact=cat, severity__exact=severity, mnemo__exact=mnemo).count()

	return stats

## Users Aggregators 
def getUsersByDot11Protocol():
	stats = {}
	for proto,display in MobileStation.DOT11_PROTOCOLS:
		tmp =  MobileStation.objects.filter(dot11protocol__exact=proto).count()
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

