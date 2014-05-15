from __future__ import absolute_import
from django.utils import timezone
from gatherer.models import OperationalError
from django.db import IntegrityError
from gatherer.snmp import getter
from celery import shared_task

@shared_task
def snmpAPDaemon():
	''' Background task gathering information on Access Point '''
	try:
		CurrentTask.objects.get_or_create(name="snmpAPDaemon").touch()
		getter.getAllAP()
	except IntegrityError:
		pass
	except:
		OperationalError(date=timezone.localtime(timezone.now()), source='snmpAPDaemon', error='Lap failed').save()

@shared_task
def snmpMSDaemon():
	''' Background task gathering information on Mobile Station 

		Argument:
		laps -- duration between update. Instance of timedelta
	'''
	try:
		CurrentTask.objects.get_or_create(name="snmpMSDaemon").touch()
		getter.getAllMS()
	except IntegrityError:
		pass
	except:
		OperationalError(date=timezone.localtime(timezone.now()), source='snmpMSDaemon', error='Lap failed').save()


@shared_task
def snmpRAPDaemon():
	''' Background task gathering information on Rogue Access Point 

		Argument:
		laps -- duration between update. Instance of timedelta
	'''
	try:
		CurrentTask.objects.get_or_create(name="snmpRAPDaemon").touch()
		getter.getAllRAP()
	except IntegrityError:
		pass
	except:
		OperationalError(date=timezone.localtime(timezone.now()), source='snmpMSDaemon', error='Lap failed').save()


