from django.contrib import admin
from gatherer.models import RadiusEvent, DHCPEvent, WismEvent, MobileStation, AccessPoint, BadLog
# Register your models here.

admin.site.register(RadiusEvent)
admin.site.register(DHCPEvent)
admin.site.register(WismEvent)
admin.site.register(MobileStation)
admin.site.register(AccessPoint)
admin.site.register(BadLog)