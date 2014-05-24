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

def getWismLogsBySeverity(cat='', severity=5):
	result = {}
	logs = WismEvent.objects.filter(severity__lte=severity).filter(category=cat)
	for severity in logs.values_list('severity', flat=True).distinct():
		result[severity] = logs.filter(severity=severity)

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
	ms = MobileStation.objects.areAssociated()
	for proto,display in MobileStation.DOT11_PROTOCOLS:
		tmp =  ms.filter(dot11protocol__exact=proto).count()
		if tmp > 0:
			stats[display] = tmp 
	return stats

def getUsersBySSID():
	stats = {}
	for ssid in MobileStation.objects.values_list('ssid', flat=True).distinct():
		stats[ssid] = MobileStation.objects.areAssociated().filter(ssid=ssid).count()
	return stats

def getNbrOfUsers():
	return MobileStation.objects.areAssociated().count()

## AP aggregators
def getHotAP(number=5):
	ap = sorted([(ap.nbrOfClients(), ap) for ap in AccessPoint.objects.areUp()], reverse=True)
	return ap[:number]

def getNbrOfAP():
	return AccessPoint.objects.areUp().count()

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
				result.append({'date':timezone.localtime(datetimeStartRange+timePerRange), 
					'rx':getSpeed(ethernetRxTotalBytesStart,ethernetRxTotalBytesEnd,timePerRange), 
					'tx':getSpeed(ethernetTxTotalBytesStart,ethernetTxTotalBytesEnd,timePerRange)})

				# Start new range
				datetimeStartRange = snap.date
				ethernetRxTotalBytesStart = snap.ethernetRxTotalBytes
				ethernetRxTotalBytesEnd = snap.ethernetRxTotalBytes
				ethernetTxTotalBytesStart = snap.ethernetTxTotalBytes
				ethernetTxTotalBytesEnd = snap.ethernetTxTotalBytes

	except ObjectDoesNotExist:
		pass

	return result


def getIfData(ap, timePerRange=timedelta(hours=1)):
	result = {}
	types = {}
	try:
		snapshots = APSnapshot.objects.filter(ap=ap).order_by('date')

		datetimeStartRange = snapshots[0].date

		for snap in snapshots[0].apifsnapshot_set.all():
			types[snap.apinterface.index[1:]] = snap.apinterface.get_ifType_display()

		nbrIf = snapshots[0].apifsnapshot_set.all().count()

		for i in range(nbrIf):
			result[str(i)] = []

		client = [0] * nbrIf
		poorSNR = [0] * nbrIf
		channelUtilization = [0] * nbrIf
		count = 0

		for snap in snapshots:
			
			if snap.date > (datetimeStartRange + timePerRange):
				for i in range(nbrIf):
					result[str(i)].append({"date":timezone.localtime(datetimeStartRange+timePerRange),
						"clients":int(client[i]) ,
						"poorSNR":int(poorSNR[i]),
						"channel":float(channelUtilization[i]/count)/100
						})

				datetimeStartRange = snap.date
				client = [0] * nbrIf
				poorSNR = [0] * nbrIf
				channelUtilization = [0] * nbrIf
				count = 0


			for ifData in snap.apifsnapshot_set.all():
				ifIndex = int(ifData.apinterface.index[1:])
				client[ifIndex] = max(client[ifIndex],ifData.numOfClients)
				poorSNR[ifIndex] = max(poorSNR[ifIndex],ifData.numOfPoorSNRClients)
				channelUtilization[ifIndex] += ifData.channelUtilization
				count += 1

	except ObjectDoesNotExist:
		pass

	return {"types":types , "result":result}



def getSpeed(start, end, time):
	# Warning wrap up counter
	if start > (MAX_VALUE_SNMP_COUNTER32/2) and end < (MAX_VALUE_SNMP_COUNTER32/2):
		total = (MAX_VALUE_SNMP_COUNTER32 - start) + end
		speed = float(total)/time.total_seconds()
	else:
		speed = float(end - start)/time.total_seconds()

	# In Mbites
	return (speed/1048576)*8


