from django.conf import settings
from datetime import timedelta

from django.utils import timezone
from gatherer.models import DHCPEvent


def getDhcpLeaseAlerts(fromDate=(timezone.now() - settings.DATAVALIDITY)):
	logs = DHCPEvent.objects.filter(dhcpType= "dis", date__gte=fromDate, message__icontains="peer holds all free leases")
	return logs

