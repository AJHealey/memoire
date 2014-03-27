from gatherer.models import AccessPoint, OperationalError
from gatherer.snmp.getter import getAPIfLoadRxUtilization, getAPIfLoadTxUtilization, getAPIfLoadChannelUtilization, getAPIfLoadNumOfClients, getAPIfPoorSNRClients
import RRDtool
from datetime import timedelta
from django.utils import timezone
import time


def customEXP(laps=timedelta(minutes=5)):
	''' Experiment on the science 10 from the March 28th 2013

		Generate information every five minues to the observed AccessPoint
	'''
	
	# Get the AP entities
	MACAdresses = ['b8:38:61:43:91:50']

	# Generate the Data Source for RRDtool
	dsList = []
	for i in range(len(MACAdresses)):
		# No of user per AP
		dsList.append('DS:rxUtilizationAP'+ str(i) +':GAUGE:600:0:100')
		dsList.append('DS:txUtilizationAP'+ str(i) +':GAUGE:600:0:100')
		dsList.append('DS:channelAP'+ str(i) +':GAUGE:600:0:100')
		dsList.append('DS:noOfClients'+ str(i) +':GAUGE:600:0:U')
		dsList.append('DS:noOfPoorSNR'+ str(i) +':GAUGE:600:0:U')

	try:
		rrd = RRDtool.create('/srv/memoire/experiment2803.rrd' ,'--start', 'now', '--step', '300', 'RRA:AVERAGE:0.5:1:15000', dsList)
	except Exception as e:
		OperationalError(date=timezone.localtime(timezone.now()), source='experiment28-03', error=str(e)).save()
		return	
	

	# Main loop gathering the information
	while True:
		values = [0,0,0,0,0]*len(MACAdresses)

		foundAP = []
		for i,mac in enumerate(MACAdresses):
			try:
				ap = AccessPoint.objects.get(macAddress=mac)
				foundAP.append((i,ap))
			except:
				OperationalError(date=timezone.localtime(timezone.now()), source='experiment28-03', error='Not found AP: ' + mac).save()


		try:
			for i,ap in foundAP:
				try:
					tmp = getAPIfLoadRxUtilization(ip='192.168.251.170', ap=ap.index)
					for k in tmp:
						values[(i*5)+0] = tmp[k]
				except Exception as e:
					OperationalError(date=timezone.localtime(timezone.now()), source='experiment28-03', error=('getAPIfLoadRxUtilization failed on ' + ap.macAddress + ': ' + str(e))).save()

				try:
					tmp = getAPIfLoadTxUtilization(ip='192.168.251.170', ap=ap.index)
					for k in tmp:
						values[(i*5)+1] = tmp[k]
				except Exception as e:
					OperationalError(date=timezone.localtime(timezone.now()), source='experiment28-03', error=('getAPIfLoadTxUtilization failed on ' + ap.macAddress + ': ' + str(e))).save()
			
				try:
					tmp = getAPIfLoadChannelUtilization(ip='192.168.251.170', ap=ap.index)
					for k,v in tmp:
						values[(i*5)+2] = tmp[k]
				except Exception as e:
					OperationalError(date=timezone.localtime(timezone.now()), source='experiment28-03', error=('getAPIfLoadChannelUtilization failed on ' + ap.macAddress + ': ' + str(e))).save()
				
				try:
					tmp = getAPIfLoadNumOfClients(ip='192.168.251.170', ap=ap.index)
					for k in tmp:
						values[(i*5)+3] = tmp[k]
				except Exception as e:
					OperationalError(date=timezone.localtime(timezone.now()), source='experiment28-03', error=('getAPIfLoadNumOfClients failed on ' + ap.macAddress+ ': ' + str(e))).save()
			
				try:
					tmp = getAPIfPoorSNRClients(ip='192.168.251.170', ap=ap.index)
					for k,v in tmp:
						values[(i*5)+4] = tmp[k]
				except Exception as e:
					OperationalError(date=timezone.localtime(timezone.now()), source='experiment28-03', error=('getAPIfPoorSNRClients failed on ' + ap.macAddress + ': ' + str(e))).save()
			
			values = [None] + values
			rrd.update([tuple(values)])            
			time.sleep(laps.total_seconds())

		except Exception as e:
			OperationalError(date=timezone.localtime(timezone.now()), source='experiment28-03', error='measurement failed: ' + str(e)).save()
			time.sleep(laps.total_seconds())

