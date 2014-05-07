import time

from datetime import timedelta

from django.utils import timezone
from django.conf import settings
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist

from pysnmp.entity.rfc3413.oneliner import cmdgen
from gatherer.models import AccessPoint, APInterface, MobileStation, RogueAccessPoint, OperationalError, CurrentTask

wism = ['192.168.251.170']

"""
	This module offers an abstraction to perform the SNMP requests

"""

def walker(ip, oib, port=161, community='snmpstudentINGI'):
	cmdGen = cmdgen.CommandGenerator()

	errorIndication, errorStatus, errorIndex, varBindTable = cmdGen.nextCmd(
	cmdgen.CommunityData(community),
	cmdgen.UdpTransportTarget((ip, port)),
	oib, lookupValues=True)

	if errorIndication:
		raise Exception(str(errorIndication))

	else:
		if errorStatus:
			raise Exception('%s at %s' % (
			errorStatus.prettyPrint(),
			errorIndex and varBindTable[int(errorIndex)-1] or '?'
			))
		else:
			result = {}
			for varBindTableRow in varBindTable:
				for name, val in varBindTableRow:
					result[name.prettyPrint()[len(oib)+1:]] = val.prettyPrint()
			return result


## Access Points Requests
def getApNames(ip, port=161, community='snmpstudentINGI'):
	""" Name of each Access Point """
	return walker(ip,'1.3.6.1.4.1.14179.2.2.1.1.3', port=port, community=community)

def getApMacAddresses(ip, port=161, community='snmpstudentINGI'):
	""" MAC address of Access Point """
	return walker(ip,'1.3.6.1.4.1.14179.2.2.1.1.1', port=port, community=community)

def getApIPs(ip, port=161, community='snmpstudentINGI'):
	""" IP address of Access Point """
	return walker(ip,'1.3.6.1.4.1.14179.2.2.1.1.19', port=port, community=community)

def getApLocation(ip, port=161, community='snmpstudentINGI'):
	""" Location of the access point (if configured) """
	return walker(ip,'1.3.6.1.4.1.14179.2.2.1.1.4', port=port, community=community)

## AP Interfaces
def getAPIfTypeface(ip, port=161, community='snmpstudentINGI'):
	""" Interface Type 

		return - a dictionary where each index is the index of the APs
				 each entries is also a dictionary where each 
				 entries are an interface type
	"""

	result = {}
	for index, ifType in walker(ip,'1.3.6.1.4.1.14179.2.2.13.1.3', port=port, community=community).items():
		tmp = index.rfind('.')
		if index[:tmp] not in result:
			result[index[:tmp]] = {}
		result[index[:tmp]][tmp:] = int(ifType)
	return result

def getAPIfLoadChannelUtilization(ip, port=161, community='snmpstudentINGI'):
	""" Channel Utilization 

		return - a dictionary where each index is the index of the APs
				 each entries is also a dictionary where each 
				 entries are an interface
	"""

	result = {}
	for index, load in walker(ip,'1.3.6.1.4.1.14179.2.2.13.1.3', port=port, community=community).items():
		tmp = index.rfind('.')
		if index[:tmp] not in result:
			result[index[:tmp]] = {}
		result[index[:tmp]][tmp:] = int(load)
	return result


def getAPIfLoadNumOfClients(ip, port=161, community='snmpstudentINGI', ap=''):
	""" This is the number of clients attached to this Airespace
		AP at the last measurement interval(This comes from 
		APF)
	"""
	result = {}
	for index, noUsers in walker(ip,'1.3.6.1.4.1.14179.2.2.13.1.4', port=port, community=community).items():
		tmp = index.rfind('.')
		if index[:tmp] not in result:
			result[index[:tmp]] = {}
		result[index[:tmp]][tmp:] = int(noUsers)
	return result


def getAPIfPoorSNRClients(ip, port=161, community='snmpstudentINGI', ap=''):
	""" This is the number of clients attached to this Airespace
		AP at the last measurement interval(This comes from 
		APF)
	"""
	result = {}
	for index, noUsers in walker(ip,'1.3.6.1.4.1.14179.2.2.13.1.24', port=port, community=community).items():
		tmp = index.rfind('.')
		if index[:tmp] not in result:
			result[index[:tmp]] = {}
		result[index[:tmp]][tmp:] = int(noUsers)
	return result

def getAPIfLoadRxUtilization(ip, port=161, community='snmpstudentINGI', ap=''):
	""" This is the percentage of time the Airespace AP
		receiver is busy operating on packets. It is a number 
		from 0-100 representing a load from 0 to 1.) 
	"""
	result = {}
	for index, rx in walker(ip,'1.3.6.1.4.1.14179.2.2.13.1.1', port=port, community=community).items():
		tmp = index.rfind('.')
		if index[:tmp] not in result:
			result[index[:tmp]] = {}
		result[index[:tmp]][tmp:] = int(rx)
	return result


def getAPIfLoadTxUtilization(ip, port=161, community='snmpstudentINGI', ap=''):
	""" This is the percentage of time the Airespace AP
		transmitter is busy operating on packets. It is a number 
		from 0-100 representing a load from 0 to 1.) 
	"""
	result = {}
	for index, tx in walker(ip,'1.3.6.1.4.1.14179.2.2.13.1.2' + ap, port=port, community=community).items():
		tmp = index.rfind('.')
		if index[:tmp] not in result:
			result[index[:tmp]] = {}
		result[index[:tmp]][tmp:] = int(tx)
	return result

def getAPEthernetRxTotalBytes(ip, port=161, community='snmpstudentINGI', ap=''):
	""" This is the total number of bytes in the
		error-free packets received on the ethernet
		interface of the AP
	"""
	result = {}
	for index, tx in walker(ip,'1.3.6.1.4.1.9.9.513.1.2.2.1.13' + ap, port=port, community=community).items():
		tmp = index.rfind('.')
		if index[:tmp] not in result:
			result[index[:tmp]] = 0
		result[index[:tmp]] = int(tx)
	return result 

def getAPEthernetTxTotalBytes(ip, port=161, community='snmpstudentINGI', ap=''):
	""" This is the total number of bytes in the
		error-free packets received on the ethernet
		interface of the AP
	"""
	result = {}
	for index, tx in walker(ip,'1.3.6.1.4.1.9.9.513.1.2.2.1.14' + ap, port=port, community=community).items():
		tmp = index.rfind('.')
		if index[:tmp] not in result:
			result[index[:tmp]] = 0
		result[index[:tmp]] = int(tx)
	return result

def getAPEthernetLinkSpeed(ip, port=161, community='snmpstudentINGI', ap=''):
	""" Speed of the interface """
	result = {}
	for index, speed in walker(ip,'1.3.6.1.4.1.9.9.513.1.2.2.1.11' + ap, port=port, community=community).items():
		tmp = index.rfind('.')
		if index[:tmp] not in result:
			result[index[:tmp]] = 0
		result[index[:tmp]] = int(speed)
	return result

## Mobile Stations Requests
def getMobileStationMacAddresses(ip, port=161, community='snmpstudentINGI'):
	""" Mac Address of each station connected to an AP """
	return walker(ip,'1.3.6.1.4.1.14179.2.1.4.1.1', port=port, community=community)

def getMobileStationIPs(ip, port=161, community='snmpstudentINGI'):
	""" IP address of each station connected to an AP """
	return walker(ip,'1.3.6.1.4.1.14179.2.1.4.1.2', port=port, community=community)

def getMobileStationProtocol(ip, port=161, community='snmpstudentINGI'):
	""" Protocol used by the station (e.g 802.11a, b, g, n) """
	return walker(ip,'1.3.6.1.4.1.14179.2.1.4.1.25', port=port, community=community)

def getMobileStationSSID(ip, port=161, community='snmpstudentINGI'):
	""" SSID advertised by the mobile station """
	return walker(ip,'1.3.6.1.4.1.14179.2.1.4.1.7', port=port, community=community)

def getMobileStationAPMacAddress(ip, port=161, community='snmpstudentINGI'):
	""" SSID advertised by the mobile station """
	return walker(ip,'1.3.6.1.4.1.14179.2.1.4.1.4', port=port, community=community)


## Rogue Access Point
def getRAPMacAddresses(ip, port=161, community='snmpstudentINGI'):
	""" Mac Address of each station connected to an AP """
	return walker(ip,'1.3.6.1.4.1.14179.2.1.7.1.1', port=port, community=community)

def getRAPDetectingAP(ip, port=161, community='snmpstudentINGI'):
	""" Get the number of AP detecting the Rogue Access Point """
	return walker(ip,'1.3.6.1.4.1.14179.2.1.7.1.2', port=port, community=community)

def getRAPNbrOfClients(ip, port=161, community='snmpstudentINGI'):
	""" Get the number of client associated with the Rogue Access Point """
	return walker(ip,'1.3.6.1.4.1.14179.2.1.7.1.8', port=port, community=community)

def getRAPSSID(ip, port=161, community='snmpstudentINGI'):
	""" Get the SSID of the Rogue Access Point """
	return walker(ip,'1.3.6.1.4.1.14179.2.1.7.1.11', port=port, community=community)

def getRAPClosestAP(ip, port=161, community='snmpstudentINGI'):
	""" Get the AP with the strongest RSSI with the Rogue Access Point """
	return walker(ip,'1.3.6.1.4.1.14179.2.1.7.1.13', port=port, community=community)


############################################################################################################################
### Aggregator #############################################################################################################
############################################################################################################################

def getAllAP():
	''' Cross reference all the information on the Access Points and update the database '''

	result = {}
	# Get All Access Points (Mac Address)
	try:       
		tmp = getApMacAddresses(ip=wism[0])
		for index, mac in tmp.items():
			mac = parseMacAdresse(mac)
			if not mac == '':
				try:
					result[index], created = AccessPoint.objects.get_or_create(macAddress=mac)
				except IntegrityError:
					# get_or_create is not thread safe
					result[index] = AccessPoint.objects.get(macAddress=mac)
				finally:
					result[index].index = "." + index
	except Exception as e:
		OperationalError(date=timezone.localtime(timezone.now()), source='snmpAPDaemon - Ap Mac Address', error=str(e)).save()
	
	# Add names    
	try:
		tmp = getApNames(ip=wism[0])
		for index, name in tmp.items():
			if index in result:
				if "b\'" in name:
					result[index].name = name[2:-1]
				else:
					result[index].name = name
	except Exception as e:
		OperationalError(date=timezone.localtime(timezone.now()), source='snmpAPDaemon - Ap Names', error=str(e)).save()

	# Add IP
	try:
		tmp = getApIPs(ip=wism[0])
		for index, ip in tmp.items():
			if index in result:
				result[index].ip = ip
	except Exception as e:
		OperationalError(date=timezone.localtime(timezone.now()), source='snmpAPDaemon - Ap IP', error=str(e)).save()
	
	# Add Link Speed
	try:
		tmp = getAPEthernetLinkSpeed(ip=wism[0])
		for index, speed in tmp.items():
			if index in result:
				if speed  == 100:
					result[index].etherneLinkSpeed = 'm'
				elif speed == 1000:
					result[index].etherneLinkSpeed = 'G'
	except Exception as e:
		OperationalError(date=timezone.localtime(timezone.now()), source='snmpAPDaemon - Ap Ethernet Link Speed', error=str(e)).save()

	# Add AP Tx bytes counter
	try:
		tmp = getAPEthernetTxTotalBytes(ip=wism[0])
		for index, b in tmp.items():
			if index in result:
				result[index].ethernetTxTotalBytes = b
	except Exception as e:
		OperationalError(date=timezone.localtime(timezone.now()), source='snmpAPDaemon - Ap Tx Total Bytes', error=str(e)).save()

	# Add AP Rx bytes counter
	try:
		tmp = getAPEthernetRxTotalBytes(ip=wism[0])
		for index, b in tmp.items():
			if index in result:
				result[index].ethernetRxTotalBytes = b
	except Exception as e:
		OperationalError(date=timezone.localtime(timezone.now()), source='snmpAPDaemon - Ap Rx Total Bytes', error=str(e)).save()

	# Add Interface Types and create the interface if required
	try:
		tmp = getAPIfTypeface(ip=wism[0])
		for apIndex, interfaces in tmp.items():
			for ifIndex, ifType in interfaces.items():
				try:
					interface, created = APInterface.objects.get_or_create(index=ifIndex, ap=result[apIndex])

				except IntegrityError:
					# get_or_create is not thread safe
					interface = APInterface.objects.get(index=ifIndex, ap=result[apIndex])

				interface.ifType = ifType
				interface.save() 
	except Exception as e:
		OperationalError(date=timezone.localtime(timezone.now()), source='snmpAPDaemon - AP Interface Types', error=str(e)).save()


	# Add Channel Utilization
	try:
		tmp = getAPIfLoadChannelUtilization(ip=wism[0])
		for apIndex, interfaces in tmp.items():
			for ifIndex, load in interfaces.items():
				if apIndex in result:
					interface = APInterface.objects.get(index=ifIndex, ap=result[apIndex])
					interface.channelUtilization = load
					interface.save()
	except Exception as e:
		OperationalError(date=timezone.localtime(timezone.now()), source='snmpAPDaemon - AP Channel Utilization', error=str(e)).save()


	# Add numOfClients
	try:
		tmp = getAPIfLoadNumOfClients(ip=wism[0])
		for apIndex, interfaces in tmp.items():
			for ifIndex, num in interfaces.items():
				if apIndex in result:
					interface = APInterface.objects.get(index=ifIndex, ap=result[apIndex])
					interface.numOfClients = num
					interface.save()
	except Exception as e:
		OperationalError(date=timezone.localtime(timezone.now()), source='snmpAPDaemon - Ap Nbr Of Clients', error=str(e)).save()
	
	# Add number Of poor SNR Clients
	try:
		tmp = getAPIfPoorSNRClients(ip=wism[0])
		for apIndex, interfaces in tmp.items():
			for ifIndex, num in interfaces.items():
				if apIndex in result:
					interface = APInterface.objects.get(index=ifIndex, ap=result[apIndex])
					interface.numOfPoorSNRClients = num
					interface.save()
	except Exception as e:
		OperationalError(date=timezone.localtime(timezone.now()), source='snmpAPDaemon - AP Poor SNR Clients', error=str(e)).save()

	# Add Transmission Utilization
	try:
		tmp = getAPIfLoadTxUtilization(ip=wism[0])
		for apIndex, interfaces in tmp.items():
			for ifIndex, load in interfaces.items():
				if apIndex in result:
					interface = APInterface.objects.get(index=ifIndex, ap=result[apIndex])
					interface.txUtilization = load
					interface.save()
	except Exception as e:
		OperationalError(date=timezone.localtime(timezone.now()), source='snmpAPDaemon - AP Transmission Utilization', error=str(e)).save()

	# Add Reception Utilization
	try:
		tmp = getAPIfLoadRxUtilization(ip=wism[0])
		for apIndex, interfaces in tmp.items():
			for ifIndex, load in interfaces.items():
				if apIndex in result:
					interface = APInterface.objects.get(index=ifIndex, ap=result[apIndex])
					interface.rxUtilization = load
					interface.save()
	except Exception as e:
		OperationalError(date=timezone.localtime(timezone.now()), source='snmpAPDaemon - AP Reception Utilization', error=str(e)).save()


	# Update all the APs
	for ap in result.values():
		ap.touch()
		ap.save()


def getAllMS():
	''' Cross reference all the information on the Mobile Station and update the database '''
	
	result = {}
	# Get All Mobile Stations (Mac Address)	
	try:
		tmp = getMobileStationMacAddresses(ip=wism[0])
		for index, mac in tmp.items():
			mac = parseMacAdresse(mac)
			if not mac == '':
				# Handle possible race condition (get_or_create not thread safe)
				try: 
					result[index], created = MobileStation.objects.get_or_create(macAddress=mac)
				except IntegrityError:
					result[index] = MobileStation.objects.get(macAddress=mac)
				finally:
					result[index].index = "." + index
	except Exception as e:
		OperationalError(date=timezone.localtime(timezone.now()), source='snmpMSDaemon - MS Mac Address', error=str(e)).save()

	# Add names   
	try: 
		tmp = getMobileStationSSID(ip=wism[0])
		for index, ssid in tmp.items():
			if index in result:
				if 'b\'' in ssid:
					result[index].ssid = ssid[2:-1]
				else:
					result[index].ssid = ssid
	except Exception as e:
		OperationalError(date=timezone.localtime(timezone.now()), source='snmpMSDaemon - MS Names', error=str(e)).save()

	# Add IP
	try:
		tmp = getMobileStationIPs(ip=wism[0])
		for index, ip in tmp.items():
			if index in result:
				result[index].ip = ip
	except Exception as e:
		OperationalError(date=timezone.localtime(timezone.now()), source='snmpMSDaemon - MS IP', error=str(e)).save()

	# Add Protocol
	try:
		tmp = getMobileStationProtocol(ip=wism[0])
		for index, proto in tmp.items():
			if index in result:
				result[index].dot11protocol = proto
	except Exception as e:
		OperationalError(date=timezone.localtime(timezone.now()), source='snmpMSDaemon - MS Proto', error=str(e)).save()
	
	# Link to AP
	try:
		tmp = getMobileStationAPMacAddress(ip=wism[0])
		for index, apMac in tmp.items():
			if index in result:
				apMac = parseMacAdresse(apMac)
				if not apMac == '': 
					result[index].ap, created = AccessPoint.objects.get_or_create(macAddress=apMac)
	except Exception as e:
		OperationalError(date=timezone.localtime(timezone.now()), source='snmpMSDaemon - MS Associated AP', error=str(e)).save()

	# Update all the MS
	for ms in result.values():
		ms.touch()
		ms.save()


def getAllRAP():
	''' Cross reference all the information on the Rogue Access Points and update the database '''
	result = {}
	# Get All Rogue Access Points (Mac Address)
	try:       
		tmp = getRAPMacAddresses(ip=wism[0])
		for index, mac in tmp.items():
			try:
				result[index], created = RogueAccessPoint.objects.get_or_create(macAddress=parseMacAdresse(mac))
			except IntegrityError:
				# get_or_create is not thread safe
				result[index] = RogueAccessPoint.objects.get(macAddress=mac)
			finally:
				result[index].index = "." + index
	except Exception as e:
		OperationalError(date=timezone.localtime(timezone.now()), source='snmpRAPDaemon - Rogue Ap Mac Address', error=str(e)).save()
	
	# Add RAP SSID   
	try: 
		tmp = getRAPSSID(ip=wism[0])
		for index, ssid in tmp.items():
			if index in result:
				if 'b\'' in ssid:
					result[index].ssid = ssid[2:-1]
				else:
					result[index].ssid = ssid
	except Exception as e:
		OperationalError(date=timezone.localtime(timezone.now()), source='snmpRAPDaemon - Rogue Ap SSID', error=str(e)).save()

	# Add RAP Number of Clients   
	try: 
		tmp = getRAPNbrOfClients(ip=wism[0])
		for index, num in tmp.items():
			if index in result:
				result[index].nbrOfClients = num
	except Exception as e:
		OperationalError(date=timezone.localtime(timezone.now()), source='snmpRAPDaemon - Rogue Ap SSID', error=str(e)).save()
	
	# Add RAP Closest AP   
	try: 
		tmp = getRAPClosestAP(ip=wism[0])
		for index, apMac in tmp.items():
			apMac = parseMacAdresse(apMac)
			if index in result:
				try:
					result[index].closestAp = AccessPoint.objects.get(macAddress=apMac)
				except ObjectDoesNotExist:
					pass
	except Exception as e:
		OperationalError(date=timezone.localtime(timezone.now()), source='snmpRAPDaemon - Rogue Ap SSID', error=str(e)).save()


	# Update all the RAP
	for rap in result.values():
		rap.touch()
		rap.save()

############################################################################################################################
### Daemon Methods ###
############################################################################################################################

def snmpAPDaemon(laps=timedelta(minutes=15)):
	''' Background task gathering information on Access Point '''
	task, _ = CurrentTask.objects.get_or_create(name="apdaemon")
	task.touch()
	while True:
		try:
			getAllAP()
			task.touch()
			time.sleep(laps.total_seconds())
		except:
			OperationalError(date=timezone.localtime(timezone.now()), source='snmpAPDaemon', error='Laps failed').save()
			time.sleep(10*laps.total_seconds())


def snmpMSDaemon(laps=timedelta(minutes=30)):
	''' Background task gathering information on Mobile Station 

		Argument:
		laps -- duration between update. Instance of timedelta
	'''
	task, _ = CurrentTask.objects.get_or_create(name="msdaemon")
	task.touch()
	time.sleep(30)
	while True:
		try:
			getAllMS()
			task.touch()
			time.sleep(laps.total_seconds())
		except:
			OperationalError(date=timezone.localtime(timezone.now()), source='snmpMSDaemon', error='Loop failed').save()
			time.sleep(10*laps.total_seconds())



###### Auxiliary Methods #######
def parseMacAdresse(macString):
	''' Parse a mac address in hexadecimal into canonical form '''
	result = macString

	if result.startswith('0x'):
		result = result[2:]

	if len(result) == 12:
		return result[0:2] + ":" + result[2:4] + ":" + result[4:6] + ":" + result[6:8] + ":" + result[8:10] + ":" +result[10:]
	else:
		OperationalError(date=timezone.localtime(timezone.now()), source='snmp macAddress parsing', error=macString).save()
		raise Exception()



#####
if __name__ == '__main__':
	import sys

	for ap in getAPIfLoadNumOfClients(wism[0]):
		print(str(ap))
