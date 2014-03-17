from django.contrib import admin
from gatherer.models import RadiusEvent, DHCPEvent, WismEvent, User, MobileStation, AccessPoint, BadLog, OperationalError, CurrentTask
# Register your models here.

admin.site.register(RadiusEvent)
admin.site.register(DHCPEvent)
admin.site.register(WismEvent)
admin.site.register(MobileStation)
admin.site.register(AccessPoint)
admin.site.register(User)
admin.site.register(BadLog)
admin.site.register(CurrentTask)
admin.site.register(OperationalError)
