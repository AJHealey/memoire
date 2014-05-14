from __future__ import absolute_import
from gatherer.models import OperationalError
from celery import shared_task


@shared_task
def snmpAPDaemon():
	''' Background task gathering information on Access Point '''
	try:
		getAllAP()
	except:
		OperationalError(date=timezone.localtime(timezone.now()), source='snmpAPDaemon', error='Lap failed').save()

