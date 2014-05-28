from django.conf import settings
from datetime import timedelta

from django.utils import timezone
from gatherer.models import DHCPEvent


def getDhcpLeaseAlerts(fromDate=(timezone.now() - settings.DATAVALIDITY)):
	logs = DHCPEvent.objects.filter(dhcpType= "dis", date__gte=fromDate, message__icontains="peer holds all free leases")
	return logs

def getDhcpWrongPlugAlerts(fromDate=(timezone.now() - settings.DATAVALIDITY)):
	result = []

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

		else:
			if (time - lastTime) < timedelta(seconds=2) and device == lastDevice and via=lastVia and server != lastServer:
				result.append({"date": time , "device": device, "via": via})

	return result

