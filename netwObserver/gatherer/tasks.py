from __future__ import absolute_import
from django.utils import timezone
from gatherer.models import OperationalError
from django.db import IntegrityError
from gatherer.snmp import getter
from celery import shared_task
from gatherer.models import CurrentTask
from threading import Lock
from datetime import datetime, timedelta

apLock = Lock()
@shared_task
def snmpAPDaemon():
	''' Background task gathering information on Access Point '''
	apLock.acquire()
	try:
		task, created = CurrentTask.objects.get_or_create(name="snmpAPDaemon")
		if created or task.lastTouched < (timezone.localtime(timezone.now()) - timedelta(minutes=10)):
			getter.getAllAP()
			task.touch()
	except IntegrityError:
		pass
	except Exception as e:
		OperationalError(date=timezone.localtime(timezone.now()), source='snmpAPDaemon', error='%s' % e).save()
	finally:
		apLock.release()



msLock = Lock()
@shared_task
def snmpMSDaemon():
	''' Background task gathering information on Mobile Station 

		Argument:
		laps -- duration between update. Instance of timedelta
	'''
	msLock.acquire()
	try:
		task, created = CurrentTask.objects.get_or_create(name="snmpMSDaemon")
		if created or task.lastTouched < (timezone.localtime(timezone.now()) - timedelta(minutes=10)):
			getter.getAllMS()
			task.touch()
	except IntegrityError:
		pass
	except Exception as e:
		OperationalError(date=timezone.localtime(timezone.now()), source='snmpMSDaemon', error='%s' % e).save()
	finally:
		msLock.release()

rapLock = Lock()
@shared_task
def snmpRAPDaemon():
	''' Background task gathering information on Rogue Access Point 

		Argument:
		laps -- duration between update. Instance of timedelta
	'''
	rapLock.acquire()
	try:
		task, created = CurrentTask.objects.get_or_create(name="snmpRAPDaemon")
		if created or task.lastTouched < (timezone.localtime(timezone.now()) - timedelta(minutes=10)):
			getter.getAllRAP()
			task.touch()
	except IntegrityError:
		pass
	except Exception as e:
		OperationalError(date=timezone.localtime(timezone.now()), source='snmpRAPDaemon', error='%s' % e).save()
	finally:
		rapLock.release()


