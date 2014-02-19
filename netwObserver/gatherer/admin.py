from django.contrib import admin
from gatherer.models import UserDevice, DHCPEvent
# Register your models here.

admin.site.register(UserDevice)
admin.site.register(DHCPEvent)