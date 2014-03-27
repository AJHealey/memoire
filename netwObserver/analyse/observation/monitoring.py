from gatherer.models import AccessPoint, OperationalError
from gatherer.snmp import getAPIfLoadRxUtilization, getAPIfLoadTxUtilization, getAPIfLoadChannelUtilization, getAPIfLoadNumOfClients, getAPIfPoorSNRClients
import rrdtool
from datetime import timedelta


def customEXP(laps=timedelta(minutes=5)):
    ''' Experiment on the science 10 from the March 28th 2013

        Generate information every five minues to the observed AccessPoint
    '''
    
    # Get the AP entities
    MACAdresses = ['88:75:56:c6:00:00']

    # Generate the Data Source for RRDtool
    dsList = []
    for i in range(len(observedAP)):
        # No of user per AP
        dsList.append('DS:rxUtilizationAP'+ str(i) +':GAUGE:600:0:100')
        dsList.append('DS:txUtilizationAP'+ str(i) +':GAUGE:600:0:100')
        dsList.append('DS:channelUtilizationAP'+ str(i) +':GAUGE:600:0:100')
        dsList.append('DS:noOfClientsAP'+ str(i) +':GAUGE:600:0:U')
        dsList.append('DS:noOfPoorSNRClientsAP'+ str(i) +':GAUGE:600:0:U')

    rrd = RRDtool.create('experiment28-03.rrd', '--no-overwrite' ,'--start', 'now', '--step', '300', 'RRA:AVERAGE:0.5:1:15000', dsList)

    # Main loop gathering the information
    while True:
		values = [0,0,0,0,0]*len(observedAP)

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
                    values[(i*5)+0]=getAPIfLoadRxUtilization(ip='192.168.251.170', index=ap.index)
                except Exception as e:
                    OperationalError(date=timezone.localtime(timezone.now()), source='experiment28-03', error=('getAPIfLoadRxUtilization failed on ' + ap + ': ' + str(e))).save()

                try:
                    values[(i*5)+1]=getAPIfLoadTxUtilization(ip='192.168.251.170', index=ap.index)
                except Exception as e:
                    OperationalError(date=timezone.localtime(timezone.now()), source='experiment28-03', error=('getAPIfLoadTxUtilization failed on ' + ap + ': ' + str(e))).save()
            
                try:
                    values[(i*5)+2]=getAPIfLoadChannelUtilization(ip='192.168.251.170', index=ap.index)
                except Exception as e:
                    OperationalError(date=timezone.localtime(timezone.now()), source='experiment28-03', error=('getAPIfLoadChannelUtilization failed on ' + ap + ': ' + str(e))).save()
				
				try:
                    values[(i*5)+3]=getAPIfLoadNumOfClients(ip='192.168.251.170', index=ap.index)
                except Exception as e:
                    OperationalError(date=timezone.localtime(timezone.now()), source='experiment28-03', error=('getAPIfLoadNumOfClients failed on ' + ap + ': ' + str(e))).save()
            
            	try:
                    values[(i*5)+4]=getAPIfPoorSNRClients(ip='192.168.251.170', index=ap.index)
                except Exception as e:
                    OperationalError(date=timezone.localtime(timezone.now()), source='experiment28-03', error=('getAPIfPoorSNRClients failed on ' + ap + ': ' + str(e))).save()
            
			values = [None] + values
            rrd.update(tuple(values))            
            time.sleep(laps.total_seconds())

        except Exception as e:
            OperationalError(date=timezone.localtime(timezone.now()), source='experiment28-03', error='measurement failed: ' + str(e)).save()
            time.sleep(laps.total_seconds())

