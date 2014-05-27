import time

from datetime import timedelta

from django.utils import timezone
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist

from pysnmp.entity.rfc3413.oneliner import cmdgen
from gatherer.models import APSnapshot, APIfSnapshot, APIfSnapshotData, APSnapshotData, AccessPoint, APInterface, MobileStation, RogueAccessPoint, OperationalError, CurrentTask

wism = ['192.168.251.170']
SNMPPORT =161
SNMPCOMMUNITY='snmpstudentINGI'

"""
	This module offers an abstraction to perform the SNMP requests
"""

## Helper Functions
def walker(ip, oib, port=SNMPPORT, community=SNMPCOMMUNITY):
	"""Perform a SNMP Walk Command"""
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

def walkByInterface(ip, oib, port=SNMPPORT, community=SNMPCOMMUNITY):
	"""
	return - a dictionary where each index is the index of the APs
			each entries is also a dictionary where each 
			entries are an interface of the AP
	"""
	result = {}
	for index, value in walker(ip=ip, oib=oib, port=port, community=community).items():
		tmp = index.rfind('.')
		if index[:tmp] not in result:
			result[index[:tmp]] = {}
		result[index[:tmp]][index[tmp:]] = int(value)
	return result

def walkByInterfaceWithAggregation(ip, oib, port=SNMPPORT, community=SNMPCOMMUNITY):
	"""
	return - a dictionary where each index is the index of the APs
			each entries is the aggregated value of all the interfaces
	"""
	result = {}
	for index, value in walker(ip=ip, oib=oib, port=port, community=community).items():
		tmp = index.rfind('.')
		if index[:tmp] not in result:
			result[index[:tmp]] = 0
		result[index[:tmp]] += int(value)
	return result

## Access Points Requests
def getApNames(ip, port=SNMPPORT, community=SNMPCOMMUNITY):
	""" Name of each Access Point """
	return walker(ip,'1.3.6.1.4.1.14179.2.2.1.1.3', port=port, community=community)

def getApMacAddresses(ip, port=SNMPPORT, community=SNMPCOMMUNITY):
	""" MAC address of Access Point """
	return walker(ip,'1.3.6.1.4.1.14179.2.2.1.1.1', port=port, community=community)

def getApIPs(ip, port=SNMPPORT, community=SNMPCOMMUNITY):
	""" IP address of Access Point """
	return walker(ip,'1.3.6.1.4.1.14179.2.2.1.1.19', port=port, community=community)

def getApLocation(ip, port=SNMPPORT, community=SNMPCOMMUNITY):
	""" Location of the access point (if configured) """
	return walker(ip,'1.3.6.1.4.1.14179.2.2.1.1.4', port=port, community=community)

## AP Interfaces
def getAPIfTypeface(ip, port=SNMPPORT, community=SNMPCOMMUNITY):
	""" Interface Type """
	return walkByInterface(ip=ip, oib='1.3.6.1.4.1.14179.2.2.2.1.2', port=port, community=community)

def getAPIfLoadChannelUtilization(ip, port=SNMPPORT, community=SNMPCOMMUNITY):
	""" Channel Utilization """
	return walkByInterface(ip=ip, oib='1.3.6.1.4.1.14179.2.2.13.1.3', port=port, community=community)

def getAPIfLoadNumOfClients(ip, port=SNMPPORT, community=SNMPCOMMUNITY, ap=''):
	""" This is the number of clients attached to this Airespace
		AP at the last measurement interval(This comes from 
		APF)
	"""
	return walkByInterface(ip=ip, oib='1.3.6.1.4.1.14179.2.2.13.1.4', port=port, community=community)

def getAPIfPoorSNRClients(ip, port=SNMPPORT, community=SNMPCOMMUNITY, ap=''):
	""" This is the number of clients attached to this Airespace
		AP at the last measurement interval(This comes from 
		APF)
	"""
	return walkByInterface(ip=ip, oib='1.3.6.1.4.1.14179.2.2.13.1.24', port=port, community=community)

def getAPIfLoadRxUtilization(ip, port=SNMPPORT, community=SNMPCOMMUNITY, ap=''):
	""" This is the percentage of time the Airespace AP
		receiver is busy operating on packets. It is a number 
		from 0-100 representing a load from 0 to 1.) 
	"""
	return walkByInterface(ip=ip, oib='1.3.6.1.4.1.14179.2.2.13.1.1', port=port, community=community)

def getAPIfLoadTxUtilization(ip, port=SNMPPORT, community=SNMPCOMMUNITY, ap=''):
	""" This is the percentage of time the Airespace AP
		transmitter is busy operating on packets. It is a number 
		from 0-100 representing a load from 0 to 1.) 
	"""
	return walkByInterface(ip=ip, oib='1.3.6.1.4.1.14179.2.2.13.1.2' + ap, port=port, community=community)

def getAPEthernetRxTotalBytes(ip, port=SNMPPORT, community=SNMPCOMMUNITY, ap=''):
	""" This is the total number of bytes in the
		error-free packets received on the ethernet
		interface of the AP
	"""
	return walkByInterfaceWithAggregation(ip=ip, oib='1.3.6.1.4.1.9.9.513.1.2.2.1.13', port=port, community=community)


def getAPEthernetTxTotalBytes(ip, port=SNMPPORT, community=SNMPCOMMUNITY, ap=''):
	""" This is the total number of bytes in the
		error-free packets received on the ethernet
		interface of the AP
	"""
	return walkByInterfaceWithAggregation(ip=ip, oib='1.3.6.1.4.1.9.9.513.1.2.2.1.14', port=port, community=community)


def getAPEthernetLinkSpeed(ip, port=SNMPPORT, community=SNMPCOMMUNITY, ap=''):
	""" Speed of the interface """
	return walkByInterfaceWithAggregation(ip=ip, oib='1.3.6.1.4.1.9.9.513.1.2.2.1.11', port=port, community=community)

## Mobile Stations Requests
def getMobileStationMacAddresses(ip, port=SNMPPORT, community=SNMPCOMMUNITY):
	""" Mac Address of each station connected to an AP """
	return walker(ip,'1.3.6.1.4.1.14179.2.1.4.1.1', port=port, community=community)

def getMobileStationIPs(ip, port=SNMPPORT, community=SNMPCOMMUNITY):
	""" IP address of each station connected to an AP """
	return walker(ip,'1.3.6.1.4.1.14179.2.1.4.1.2', port=port, community=community)

def getMobileStationProtocol(ip, port=SNMPPORT, community=SNMPCOMMUNITY):
	""" Protocol used by the station (e.g 802.11a, b, g, n) """
	return walker(ip,'1.3.6.1.4.1.14179.2.1.4.1.25', port=port, community=community)

def getMobileStationSSID(ip, port=SNMPPORT, community=SNMPCOMMUNITY):
	""" SSID advertised by the mobile station """
	return walker(ip,'1.3.6.1.4.1.14179.2.1.4.1.7', port=port, community=community)

def getMobileStationAPMacAddress(ip, port=SNMPPORT, community=SNMPCOMMUNITY):
	""" SSID advertised by the mobile station """
	return walker(ip,'1.3.6.1.4.1.14179.2.1.4.1.4', port=port, community=community)


## Rogue Access Point
def getRAPMacAddresses(ip, port=SNMPPORT, community=SNMPCOMMUNITY):
	""" Mac Address of each station connected to an AP """
	return walker(ip,'1.3.6.1.4.1.14179.2.1.7.1.1', port=port, community=community)

def getRAPDetectingAP(ip, port=SNMPPORT, community=SNMPCOMMUNITY):
	""" Get the number of AP detecting the Rogue Access Point """
	return walker(ip,'1.3.6.1.4.1.14179.2.1.7.1.2', port=port, community=community)

def getRAPNbrOfClients(ip, port=SNMPPORT, community=SNMPCOMMUNITY):
	""" Get the number of client associated with the Rogue Access Point """
	return walker(ip,'1.3.6.1.4.1.14179.2.1.7.1.8', port=port, community=community)

def getRAPSSID(ip, port=SNMPPORT, community=SNMPCOMMUNITY):
	""" Get the SSID of the Rogue Access Point """
	return walker(ip,'1.3.6.1.4.1.14179.2.1.7.1.11', port=port, community=community)

def getRAPClosestAP(ip, port=SNMPPORT, community=SNMPCOMMUNITY):
	""" Get the AP with the strongest RSSI with the Rogue Access Point """
	return walker(ip,'1.3.6.1.4.1.14179.2.1.7.1.13', port=port, community=community)


############################################################################################################################
### Aggregator #############################################################################################################
############################################################################################################################

def getData(elements, attr, getter, ip, port=SNMPPORT, community=SNMPCOMMUNITY, valueInBinaryString=False, source='snmpAPDaemon'):
	""" Update the information about the Access Points

		arguments:
		elements - Dictionnary of AccessPoints indexed by their controller index
		attr - gathered information
		getter - SNMP request handler
		ip, port, community - SNMP request parameters
		valueInBinaryString - is the return value a binary string
	"""
	try:
		for index, value in getter(ip=ip, port=port, community=community).items():

			if index in elements and attr in elements[index].__dict__:
				
				if valueInBinaryString and (value.startswith("b'") or value.startswith('b"')):
					elements[index].__dict__[attr] = value[2:-1]
				else:
					elements[index].__dict__[attr] = value
				elements[index].save(update_fields=[attr])
	
	except Exception as e:
		OperationalError(source='%s - %s' % (source,attr), error=str(e)).save()


def getApSnapshotData(elements, attr, getter, ip, port=SNMPPORT, community=SNMPCOMMUNITY):
	""" Get the information about the Access Points Snapshots

		arguments:
		elements - Dictionnary of APSnapshot indexed by their controller index
		attr - gathered information
		getter - SNMP request handler
		ip, port, community - SNMP request parameters
	"""
	try:
		for apIndex, value in getter(ip=ip, port=port, community=community).items():
			if apIndex in elements:
				APSnapshotData(apSnapshot=elements[apIndex], name=attr, value=value).save()
	
	except Exception as e:
		OperationalError(source='snmpAPDaemon - %s' % attr, error=str(e)).save()


def getIfSnapshotData(elements, attr, getter, ip, port=SNMPPORT, community=SNMPCOMMUNITY):
	""" Get the information about the Access Points Interface Snapshots

		arguments:
		elements - Dictionnary of APSnapshot indexed by their controller index
		attr - gathered information
		getter - SNMP request handler
		ip, port, community - SNMP request parameters
	"""
	try:
		for apIndex, interfaces in getter(ip=ip, port=port, community=community).items():
			for ifIndex, value in interfaces.items():
				if apIndex in elements and ifIndex in elements[apIndex]:
					APIfSnapshotData(apIfSnapshot=elements[apIndex][ifIndex], name=attr, value=value).save()
	except Exception as e:
		OperationalError(source='snmpAPDaemon - %s' % attr, error=str(e)).save()


def getAllAP(ip=wism[0], port=SNMPPORT, community=SNMPCOMMUNITY):
	''' Gather and cross reference all the information about the Access Points and their interfaces '''

	result = {}
	resultApSnapshot = {}
	resultInterfaces = {}
	resultIfSnapshot = {}

	# Get All Access Points (Mac Address)
	try:       
		tmp = getApMacAddresses(ip=wism[0])
		for index, mac in tmp.items():
			mac = parseMacAdresse(mac)
			try:
				result[index], created = AccessPoint.objects.get_or_create(macAddress=mac)
			except IntegrityError:
				# get_or_create is not thread safe
				result[index] = AccessPoint.objects.get(macAddress=mac)
			
			result[index].index = "." + index
			result[index].save(update_fields=['index'])

	except Exception as e:
		OperationalError(source='snmpAPDaemon - macAddress', error=str(e)).save()
	
	# Add/Update names
	getData(elements=result, attr='name', getter=getApNames, 
		ip=ip, port=port, community=community, 
		valueInBinaryString=True) 

	# Add/Update IP
	getData(elements=result, attr='ip', getter=getApIPs, 
		ip=ip, port=port, community=community) 

	# Add/Update Link Speed
	getData(elements=result, attr='ethernetLinkSpeed', getter=getAPEthernetLinkSpeed, 
		ip=ip, port=port, community=community) 

	# Create AP Snapshots
	for apIndex, ap in result.items():
		resultApSnapshot[apIndex] = APSnapshot(ap=ap)
		resultApSnapshot[apIndex].save()

	# Get the receptioned bytes counter
	getApSnapshotData(elements=resultApSnapshot, attr='ethernetRxTotalBytes', getter=getAPEthernetRxTotalBytes,
		ip=ip, port=port, community=community)

	# Get the transmitted bytes counter
	getApSnapshotData(elements=resultApSnapshot, attr='ethernetTxTotalBytes', getter=getAPEthernetTxTotalBytes,
		ip=ip, port=port, community=community)
	
	# Add/Update Interfaces
	try:
		tmp = getAPIfTypeface(ip=wism[0])
		for apIndex, interfaces in tmp.items():
			if apIndex in result:
				if apIndex not in resultInterfaces:
					resultInterfaces[apIndex] = {}

				for ifIndex, ifType in interfaces.items():
					try:
						resultInterfaces[apIndex][ifIndex], created = APInterface.objects.get_or_create(ifType=ifType, ap=result[apIndex])
					except IntegrityError:
						# get_or_create is not thread safe
						resultInterfaces[apIndex][ifIndex] = APInterface.objects.get(ifType=ifType, ap=result[apIndex])

					resultInterfaces[apIndex][ifIndex].index = ifIndex
					resultInterfaces[apIndex][ifIndex].save(update_fields=['index'])

	except Exception as e:
		OperationalError(source='snmpAPDaemon - AP Interface Types', error=str(e)).save()

	# Create a Snapshot for each interface
	for apIndex, ap in resultInterfaces.items():
		resultIfSnapshot[apIndex] = {}
		for ifIndex, interface in ap.items():
			resultIfSnapshot[apIndex][ifIndex] = APIfSnapshot(apinterface=interface)
			resultIfSnapshot[apIndex][ifIndex].save()
	
	# Add Channel Utilization
	getIfSnapshotData(resultIfSnapshot, 'channelUtilization', getAPIfLoadChannelUtilization, 
		ip=ip, port=port, community=community)

	# Add numOfClients
	getIfSnapshotData(resultIfSnapshot, 'numOfClients', getAPIfLoadNumOfClients, 
		ip=ip, port=port, community=community)

	# Add number Of poor SNR Clients
	getIfSnapshotData(resultIfSnapshot, 'numOfPoorSNRClients', getAPIfPoorSNRClients, 
		ip=ip, port=port, community=community)

	# Add Transmission Utilization
	getIfSnapshotData(resultIfSnapshot, 'txUtilization', getAPIfLoadTxUtilization, 
		ip=ip, port=port, community=community)

	# Add Reception Utilization
	getIfSnapshotData(resultIfSnapshot, 'rxUtilization', getAPIfLoadRxUtilization, 
		ip=ip, port=port, community=community)



def getAllMS(ip=wism[0], port=SNMPPORT, community=SNMPCOMMUNITY):
	''' Cross reference all the information on the Mobile Station and update the database '''
	
	result = {}
	# Get All Mobile Stations (Mac Address)	
	try:
		tmp = getMobileStationMacAddresses(ip=wism[0])
		for index, mac in tmp.items():
			mac = parseMacAdresse(mac)
				# Handle possible race condition (get_or_create not thread safe)
			try: 
				result[index], created = MobileStation.objects.get_or_create(macAddress=mac)
			except IntegrityError:
				result[index] = MobileStation.objects.get(macAddress=mac)
			
			result[index].index = "." + index
			result[index].save(update_fields=['index'])
	except Exception as e:
		OperationalError(source='snmpMSDaemon - MS Mac Address', error=str(e)).save()

	# Link to AP
	try:
		tmp = getMobileStationAPMacAddress(ip=wism[0])
		for index, apMac in tmp.items():
			if index in result:
				apMac = parseMacAdresse(apMac)
				try:
					result[index].ap, created = AccessPoint.objects.get_or_create(macAddress=apMac)
				except IntegrityError:
					result[index].ap = AccessPoint.objects.get_or_create(macAddress=apMac)
				result[index].save(update_fields=['ap'])

	except Exception as e:
		OperationalError(source='snmpMSDaemon - MS Associated AP', error=str(e)).save()


	# Add/Update SSID
	getData(elements=result, attr='ssid', getter=getMobileStationSSID, 
		ip=ip, port=port, community=community, 
		valueInBinaryString=True, source='snmpMSDaemon')   
	
	# Add/Update IP
	getData(elements=result, attr='ip', getter=getMobileStationIPs, 
		ip=ip, port=port, community=community, 
		source='snmpMSDaemon') 

	# Add Protocol
	getData(elements=result, attr='dot11protocol', getter=getMobileStationProtocol, 
		ip=ip, port=port, community=community, 
		source='snmpMSDaemon') 





def getAllRAP():
	''' Cross reference all the information on the Rogue Access Points and update the database '''
	result = {}
	# Get All Rogue Access Points (Mac Address)
	try:       
		tmp = getRAPMacAddresses(ip=wism[0])
		for index, mac in tmp.items():
			mac = parseMacAdresse(mac)
			try:
				result[index], created = RogueAccessPoint.objects.get_or_create(macAddress=mac)
			except IntegrityError:
				# get_or_create is not thread safe
				result[index] = RogueAccessPoint.objects.get(macAddress=mac)
			finally:
				result[index].index = "." + index
	except Exception as e:
		OperationalError(source='snmpRAPDaemon - Rogue Ap Mac Address', error=str(e)).save()
	
	# Add RAP SSID   
	try: 
		tmp = getRAPSSID(ip=wism[0])
		for index, ssid in tmp.items():
			if index in result:
				if ssid.startswith("b'") or ssid.startswith('b"'):
					result[index].ssid = ssid[2:-1]
				else:
					result[index].ssid = ssid
	except Exception as e:
		OperationalError(source='snmpRAPDaemon - Rogue Ap SSID', error=str(e)).save()

	# Add RAP Number of Clients   
	try: 
		tmp = getRAPNbrOfClients(ip=wism[0])
		for index, num in tmp.items():
			if index in result:
				result[index].nbrOfClients = num
	except Exception as e:
		OperationalError(source='snmpRAPDaemon - Rogue Ap SSID', error=str(e)).save()
	
	# Add RAP Closest AP   
	try: 
		tmp = getRAPClosestAP(ip=wism[0])
		for index, apMac in tmp.items():
			apMac = parseMacAdresse(apMac)
			if index in result:
				try:
					result[index].closestAp, created = AccessPoint.objects.get_or_create(macAddress=apMac)
				
				except IntegrityError:
					result[index].closestAp = AccessPoint.objects.get(macAddress=apMac)
				
				except ObjectDoesNotExist:
					pass
	except Exception as e:
		OperationalError(source='snmpRAPDaemon - Rogue Ap SSID', error=str(e)).save()


	# Update all the RAP
	for rap in result.values():
		rap.touch()
		rap.save()

###### Auxiliary Methods #######
def parseMacAdresse(macString):
	''' Parse a mac address in hexadecimal or byte into canonical form '''
	result = macString

	if result.startswith('0x'):
		result = result[2:]

	elif result.startswith("b'") or result.startswith('b"'):
		tmp = ""
		escaped = False
		for c in result[2:-1]:
			if c == '\\' and not escaped:
				escaped = True
			else:
				escaped = False
				tmp += "{:02x}".format(ord(c))
		result = tmp

	else:
		OperationalError(source='snmp macAddress parsing', error="Unknown format: %s" % result).save()
		raise Exception()


	if len(result) == 12:
		return "%s:%s:%s:%s:%s:%s" % (result[0:2],result[2:4],result[4:6],result[6:8],result[8:10],result[10:])
	
	else:
		OperationalError(source='snmp macAddress parsing', error="Length Error: %s" % result).save()
		raise Exception()



#####
if __name__ == '__main__':
	import sys

	for ap in getAPIfLoadNumOfClients(wism[0]):
		print(str(ap))
