from gatherer.models import AccessPoint, OperationalError
from gatherer.snmp.getter import getAPIfLoadRxUtilization, getAPIfLoadTxUtilization, getAPIfLoadChannelUtilization, getAPIfLoadNumOfClients, getAPIfPoorSNRClients
import RRDtool
from datetime import timedelta
from django.utils import timezone
import time


def customEXP(laps=timedelta(minutes=1)):
	''' Experiment on the science 10 from the March 28th 2013

		Generate information every five minues to the observed AccessPoint
	'''
	
	# Get the AP entities
	MACAdresses = ['b8:38:61:43:91:50', 'b8:38:61:3c:25:80', 'b8:38:61:43:8f:b0']

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
		rrd = RRDtool.create('/srv/memoire/experiment2803.rrd' ,'--start', 'now', '--step', '60', 'RRA:AVERAGE:0.5:1:1500', dsList)
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
					values[(i*5)+0] = getAPIfLoadRxUtilization(ip='192.168.251.170', ap=ap.index)[ap.index[1:]]
				except Exception as e:
					OperationalError(date=timezone.localtime(timezone.now()), source='experiment28-03', error=('getAPIfLoadRxUtilization failed on ' + ap.macAddress + ': ' + str(e))).save()

				try:
					values[(i*5)+1] = getAPIfLoadTxUtilization(ip='192.168.251.170', ap=ap.index)[ap.index[1:]]
				except Exception as e:
					OperationalError(date=timezone.localtime(timezone.now()), source='experiment28-03', error=('getAPIfLoadTxUtilization failed on ' + ap.macAddress + ': ' + str(e))).save()
			
				try:
					values[(i*5)+2] = getAPIfLoadChannelUtilization(ip='192.168.251.170', ap=ap.index)[ap.index[1:]]
				except Exception as e:
					OperationalError(date=timezone.localtime(timezone.now()), source='experiment28-03', error=('getAPIfLoadChannelUtilization failed on ' + ap.macAddress + ': ' + str(e))).save()
				
				try:
					values[(i*5)+3] = getAPIfLoadNumOfClients(ip='192.168.251.170', ap=ap.index)[ap.index[1:]]
				except Exception as e:
					OperationalError(date=timezone.localtime(timezone.now()), source='experiment28-03', error=('getAPIfLoadNumOfClients failed on ' + ap.macAddress+ ': ' + str(e))).save()
			
				try:
					values[(i*5)+4] = getAPIfPoorSNRClients(ip='192.168.251.170', ap=ap.index)[ap.index[1:]]
				except Exception as e:
					OperationalError(date=timezone.localtime(timezone.now()), source='experiment28-03', error=('getAPIfPoorSNRClients failed on ' + ap.macAddress + ': ' + str(e))).save()
			
			f = open("/srv/memoire/exp.txt", 'a')
			f.write(str(values)+'\n')
			f.close()
			values = [None] + values
			rrd.update([tuple(values)])            
			time.sleep(laps.total_seconds())


		except Exception as e:
			OperationalError(date=timezone.localtime(timezone.now()), source='experiment28-03', error='measurement failed: ' + str(e)).save()
			time.sleep(laps.total_seconds())

if __name__ == '__main__':
	print(getAPIfLoadRxUtilization(ip='192.168.251.170', ap=ap.index))