from django.contrib import admin
from gatherer.models import UserDevice,RadiusEvent, DHCPEvent, WismEvent, BadLog
# Register your models here.

admin.site.register(UserDevice)
admin.site.register(RadiusEvent)
admin.site.register(DHCPEvent)
admin.site.register(WismEvent)
admin.site.register(BadLog)