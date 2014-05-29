from __future__ import absolute_import
from django.utils import timezone
from gatherer.models import OperationalError
from django.db import IntegrityError
from gatherer.snmp import getter
from celery import shared_task
from celery.signals import celeryd_init
from gatherer.probe import responderClear
from gatherer.models import CurrentTask
from threading import Lock
from datetime import datetime, timedelta

SNMP_REQUEST_MIN_INTERVAL = timedelta(minutes=10)

apLock = Lock()
@shared_task
def snmpAPDaemon():
	''' Background task gathering information on Access Point '''
	if apLock.acquire(blocking=False):
		try:
			task, created = CurrentTask.objects.get_or_create(name="snmpAPDaemon")
			if created or task.lastTouched < (timezone.now() - SNMP_REQUEST_MIN_INTERVAL):
				getter.getAllAP()
				task.touch()
		except IntegrityError:
			pass
		except Exception as e:
			OperationalError(source='snmpAPDaemon', error='%s' % e).save()
		finally:
			apLock.release()



msLock = Lock()
@shared_task
def snmpMSDaemon():
	''' Background task gathering information on Mobile Station 

		Argument:
		laps -- duration between update. Instance of timedelta
	'''
	if msLock.acquire(blocking=False):	
		try:
			task, created = CurrentTask.objects.get_or_create(name="snmpMSDaemon")
			if created or task.lastTouched < (timezone.now() - SNMP_REQUEST_MIN_INTERVAL):
				getter.getAllMS()
				task.touch()
		except IntegrityError:
			pass
		except Exception as e:
			OperationalError(source='snmpMSDaemon', error='%s' % e).save()
		finally:
			msLock.release()

rapLock = Lock()
@shared_task
def snmpRAPDaemon():
	''' Background task gathering information on Rogue Access Point 

		Argument:
		laps -- duration between update. Instance of timedelta
	'''
	if rapLock.acquire(blocking=False):
		try:
			task, created = CurrentTask.objects.get_or_create(name="snmpRAPDaemon")
			if created or task.lastTouched < (timezone.now() - SNMP_REQUEST_MIN_INTERVAL):
				getter.getAllRAP()
				task.touch()
		except IntegrityError:
			pass
		except Exception as e:
			OperationalError(source='snmpRAPDaemon', error='%s' % e).save()
		finally:
			rapLock.release()

responderLock = Lock()
@shared_task
def startResponder(conf=None, **kwargs):
	if responderLock.acquire(blocking=False):
		try:
			responderClear.responder()
		except Exception as e:
			OperationalError(source='ProbeResponder', error='%s' % e).save()
		finally:
			responderLock.release()




