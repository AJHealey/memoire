import collections
import codecs
from datetime import datetime,timedelta
from django.utils import timezone
from django.db.models import Max, Min
from gatherer.models import *
from django.core.exceptions import ObjectDoesNotExist

import json
from django.conf import settings


MAX_VALUE_SNMP_COUNTER32 = 4294967295

## Logs Aggregators
def getWismLogsByCategory():
	""" Aggregate the controller log by category """
	stats = {}
	## Logs More important than informational (level 5 at least)
	logs = WismEvent.objects.filter(severity__lte=5)
	categories = set(logs.values_list('category', flat=True))
	for cat in categories:
		stats[cat] = logs.filter(category=cat).count()

	return stats

def getWismLogsBySeverity(cat='', severity=5):
	""" Aggregate the controller log by severity """
	result = {}
	logs = WismEvent.objects.filter(severity__lte=severity).filter(category=cat)
	for severity in set(logs.values_list('severity', flat=True)):
		result[severity] = logs.filter(severity=severity)

def getDhcpLogByType():
	""" Aggregate the DHCP log by type """
	stats = []
	order=[("dis","Discover"), ("off","Offer"), ("req","Request"), ("ack","Ack"), ("nak","Nak"), ("inf", "Inform")]
	for t, display in order:
		tmp = DHCPEvent.objects.filter(dhcpType=t).count()
		if tmp > 0:
			stats.append((display, tmp))
	return stats

def getRadiusSuccessRate():
	 """ Compute the success rate of the authentications """
	return {
		"Success" : RadiusEvent.objects.filter(radiusType="ok").count(),
		"Failed" : RadiusEvent.objects.filter(radiusType="ko").count(),
	}

## Users Aggregators 
def getUsersByDot11Protocol(timedeltaData=timedelta(weeks=12)):
	""" Compute the rate of utilization of the 802.11 standards """
	stats = {}
	ms = MobileStation.objects.areAssociated()
	for proto,display in MobileStation.DOT11_PROTOCOLS:
		tmp =  ms.filter(dot11protocol__exact=proto).count()
		if tmp > 0:
			stats[display] = tmp 
	return stats

def getUsersBySSID():
	""" Compute the rate of utilization of the SSID """
	stats = {}
	ms =  MobileStation.objects.filter(ssid__isnull=False)
	for ssid in set(MobileStation.objects.values_list('ssid', flat=True)):
		stats[ssid] = MobileStation.objects.areAssociated().filter(ssid=ssid).count()
	return stats

def getNbrOfUsers():
	return MobileStation.objects.areAssociated().count()

def getNbrOfAP():
	return AccessPoint.objects.areUp().count()

def getAPData(ap, timePerRange=3*settings.SNMPAPLAP, 
	startTime=None,
	endTime=None):
	""" Aggregate all the data gathered about the access point 

		arguments:
		ap - access point to analyse
		timePerRange - period of aggregation
		startTime - minimum date of the data
		endTime - maximum date of the data
	"""

	COUNTERTOSPEED = ['ethernetRxTotalBytes','ethernetTxTotalBytes']
	GETMAX = []
	
	result = []
	try:

		if startTime == None:
			startTime = APSnapshot.objects.aggregate(Min("date"))["date__min"]
		if endTime == None:
			endTime = APSnapshot.objects.aggregate(Max("date"))["date__max"]


		snapshots = APSnapshot.objects.filter(ap=ap, date__gte=startTime, date__lte=endTime).order_by('date')
		startAt = snapshots[0].date
		
		values = {}
		for data in snapshots[0].apsnapshotdata_set.all():
			values[data.name] = [data.value]

		for snap in snapshots[1:]:
			# Get the data of the period
			if snap.date < (startAt + timePerRange):
				for data in snap.apsnapshotdata_set.all():
					if data.name in values:
						values[data.name].append(data.value)

			# Aggregate and reset the period
			else:
				data = {}
				for attr, value in values.items():
					if attr in COUNTERTOSPEED:
						data[attr] = getSpeed(value[0], value[-1], timePerRange)
					elif attr in GETMAX:
						data[attr] = max(value)
					else:
						data[attr] = sum(value)/float(len(value))

				result.append({'date':timezone.localtime(startAt + timePerRange), 'data': data})

				# Start new period
				startAt = snap.date
				values = {}
				for data in snap.apsnapshotdata_set.all():
					values[data.name] = [data.value]

	except Exception as e:
		OperationalError(source="getAPData", error=str(e)).save()
		raise e

	return result


def getIfData(interface, timePerRange=3*settings.SNMPAPLAP, startTime=None, endTime=None):
	""" Aggregate all the data gathered about the interface of the access points

		arguments:
		interface - interface to analyse
		timePerRange - period of aggregation
		startTime - minimum date of the data
		endTime - maximum date of the data
	"""
	result = []
	try:
		if startTime == None:
			startTime = APSnapshot.objects.aggregate(Min("date"))["date__min"]
		if endTime == None:
			endTime = APSnapshot.objects.aggregate(Max("date"))["date__max"]

		snapshots = APIfSnapshot.objects.filter(apinterface=interface, date__gte=startTime, date__lte=endTime).order_by('date')
		startAt = snapshots[0].date
		
		values = {}
		for data in snapshots[0].apifsnapshotdata_set.all():
			values[data.name] = [data.value]

		for snap in snapshots[1:]:
			# Get the data of the period
			if snap.date < (startAt + timePerRange):
				for data in snap.apifsnapshotdata_set.all():
					if data.name in values:
						values[data.name].append(data.value)
			# Aggregate and reset the period
			else:
				data = {}
				for attr, value in values.items():
					data[attr] = max(value)

				result.append({'date':timezone.localtime(startAt + timePerRange), 'data': data})

				# Start new period
				startAt = snap.date
				values = {}
				for data in snap.apifsnapshotdata_set.all():
					values[data.name] = [data.value]

	except ObjectDoesNotExist:
		pass

	except Exception as e:
		OperationalError(source="getIfData", error=str(e)).save()
		return []

	return {'interface':interface, 'data':result}

def getAllIfData(ap, timePerRange=3*settings.SNMPAPLAP, startTime=None, endTime=None):
	result = []
	interfaces = ap.apinterface_set.all()
	for i in interfaces:
		result.append(getIfData(i,timePerRange,startTime,endTime))
	return result
	


def getSpeed(start, end, time):
	""" Compute the speed based on byte counter 

		arguments:
		start - counter at start
		end - counter at end
		time - elapsed time between 'start' and 'end'
	"""
	# Warning wrap up counter
	if start > (MAX_VALUE_SNMP_COUNTER32/2) and end < (MAX_VALUE_SNMP_COUNTER32/2):
		total = (MAX_VALUE_SNMP_COUNTER32 - start) + end
		speed = float(total)/time.total_seconds()
	else:
		speed = float(end - start)/time.total_seconds()

	# In Mbites
	return (speed/1048576)*8

############################
### Rogue Access Point #####
############################

def getRapPerZone():
	""" Aggregate the Rogue Access Point by zone """
	dicoZone = {}
	try:
		dicoZone = json.load(codecs.open(settings.APDICOZONE,'r',encoding='utf-8'))
	except Exception as e:
		OperationalError(source="Rap Per Zone - dico loading", error=str(e)).save()
		return {}

	result = {}

	# prefetch to avoid n+1 queries
	for rap in RogueAccessPoint.objects.filter(closestAp__isnull=False).prefetch_related('closestAp'):
		if rap.closestAp != None:
			closestApName = rap.closestAp.name
			for tag,zone in dicoZone.items():
				if tag in closestApName:
					if zone not in result:
						result[zone] = []
					result[zone].append(rap)
					break


	return result



################
### Probes #####
################
def getAllProbes():
	""" Detect the Mobile Station that are probe """
	probes = set()
	for log in ProbeLog.objects.all():
		probes.add(log.probe)
	return probes

def getLastScan(probe):
	""" Get the last scan information of the probe """
	try:
		result = {}
		lastLog = ProbeLog.objects.filter(probe=probe).latest(field_name='date')

		for test in lastLog.probetest_set.all().order_by('-id'):
			if test.probescanresult_set.all().exists():
				for scan in test.probescanresult_set.all():
					if scan.ap.macAddress not in result:
						result[scan.ap.macAddress] = {"ap": scan.ap, "ssid":set(), "frequency":set(), "signalStrength":[]}
					
					result[scan.ap.macAddress]["ssid"].add(scan.ssid)
					result[scan.ap.macAddress]["frequency"].add(int(scan.frequency))
					result[scan.ap.macAddress]["signalStrength"].append(int(scan.signalStrength))

				for r, v in result.items():
					tmp = sum(v["signalStrength"])/float(len(v["signalStrength"]))
					v["signalStrength"] = tmp

				return {"date": timezone.localtime(lastLog.date),"results":result}


	except ObjectDoesNotExist:
		return {}


def getConnectionTime(probe,since=None):
	"""  Aggregate the time record by the probe """
	try:
		result = {}
				
		connectionResults = ProbeConnectionResult.objects.filter(test__log__probe = probe).prefetch_related('timecheck_set')
		if since != None:
			connectionResults = connectionResults.filter(date__gte=since)

		ssids = set(connectionResults.values_list('ssid', flat=True))
		for ssid in ssids:
			tmp = ssid.replace(".","").replace("-","")
			result[tmp] = []
			ssidResults = connectionResults.filter(ssid=ssid).order_by("date")
			for con in ssidResults:
				if con.timecheck_set.all().exists():
					result[tmp].append({"date": timezone.localtime(con.date), "connection":con, "times":con.timecheck_set.all().order_by('step')})


		return result

	except:
		return {}



def getAvailabilityByService(since=None):
	""" Aggregate the overall availability of all the service

		Note: The information of ALL the probe are aggregated
	"""
	try:
		result = []
		connectionResults = ProbeConnectionResult.objects.all().prefetch_related('servicecheck_set')
		
		if since != None:
			connectionResults = connectionResults.filter(date__gte=since)

		# !Keep same ordering
		services = sorted(list(set(connectionResults.filter(servicecheck__service__isnull=False).values_list('servicecheck__service', flat=True))))
		ssids = sorted(list(set(connectionResults.filter(ssid__isnull=False).values_list('ssid', flat=True))))

		for service in services:
			data = {"service":service, "data":[]}
			for ssid in ssids:
				total = connectionResults.filter(ssid=ssid,servicecheck__service=service).count()
				if total > 0:
					success = connectionResults.filter(ssid=ssid,servicecheck__service=service,servicecheck__state=True).count()
					data['data'].append(float(success)*100/total)
			result.append(data)
			
		return {"ssids":ssids, "data":result}
	except:
		return {}






