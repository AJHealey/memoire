from gatherer.models import WismEvent, MobileStation


def getWismLogByType():
	stats = {}
	logs = WismEvent.objects
	categories = logs.distinct('category').values_list('category',flat=True).order_by('category')
	for cat in categories:
		stats[cat] = {}

		for element in logs.filter(category__exact=cat).distinct('severity','mnemo').values('severity','mnemo'):
			severity = element['severity']
			mnemo = element['mnemo']
			if not severity in stats[cat]:
				stats[cat][severity] = {}
			
			stats[cat][severity][mnemo] = logs.filter(category__exact=cat, severity__exact=severity, mnemo__exact=mnemo).count()

	return stats


def getUserByDot11Protocol():
	stats = {p:0 for _,p in MobileStation.DOT11_PROTOCOLS}
	
	for proto,display in MobileStation.DOT11_PROTOCOLS:
		stats[display] = MobileStation.objects.filter(dot11protocol__exact=proto).count()
	
	return sorted(stats)


