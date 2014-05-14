from __future__ import absolute_import
from gatherer.models import OperationalError
from gatherer.snmp import getter
from celery import shared_task

@shared_task
def debug():
	print("OK")

@shared_task
def snmpAPDaemon():
	''' Background task gathering information on Access Point '''
	try:
		getter.getAllAP()
	except:
		OperationalError(date=timezone.localtime(timezone.now()), source='snmpAPDaemon', error='Lap failed').save()

@shared_task
def snmpMSDaemon():
	''' Background task gathering information on Mobile Station 

		Argument:
		laps -- duration between update. Instance of timedelta
	'''
	try:
		getter.getAllRAP()
	except:
		OperationalError(date=timezone.localtime(timezone.now()), source='snmpRAPDaemon', error='Lap failed').save()


@shared_task
def snmpRAPDaemon():
	''' Background task gathering information on Rogue Access Point 

		Argument:
		laps -- duration between update. Instance of timedelta
	'''
	try:
		getter.getAllMS()
	except:
		OperationalError(date=timezone.localtime(timezone.now()), source='snmpMSDaemon', error='Lap failed').save()

