from django.conf import settings
from datetime import timedelta

from django.utils import timezone
from gatherer.models import DHCPEvent


def getDhcpLeaseAlerts(fromDate=(timezone.now() - settings.DATAVALIDITY)):
	logs = DHCPEvent.objects.filter(dhcpType= "dis", date__gte=fromDate, message__icontains="peer holds all free leases")
	return logs

def getDhcpWrongPlugAlerts(fromDate=(timezone.now() - timedelta(hours=1))):
	result = {}

	logs = DHCPEvent.objects.filter(dhcpType= "dis", date__gte=fromDate, message__icontains="peer holds all free leases").order_by('date','microsecond')
	lastTime = None
	lastDevice = None
	lastServer = None
	lastVia = None
	for log in logs:
		time = log.date
		device = log.device
		server = log.server
		via = log.via
		if  lastTime == None:
			lastTime = time
			lastDevice = device
			lastServer = server
			lastVia = via

		elif (time - lastTime) < timedelta(seconds=2) and device == lastDevice and via == lastVia and server != lastServer:
			result[device] = {"date": timezone.localtime(time), "via": via}
		

		lastTime = time
		lastDevice = device
		lastServer = server
		lastVia = via


	return result

def isDhcpActive(lastAck=timedelta(minutes=15)):
	last = DHCPEvent.objects.filter(dhcpType= "ack").order_by("-date")
	if len(last) > 0 and (timezone.now() - last[0].date) < lastAck:
		return True

	else:
		return False
