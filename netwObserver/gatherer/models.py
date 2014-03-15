from django.db import models
from custom import macField
from datetime import datetime, timedelta
from django.utils import timezone


## Mobile stations Model
class MobileStation(models.Model):
	macAddress = macField.MACAddressField(primary_key=True)
	ip = models.GenericIPAddressField(null=True)
	ssid = models.CharField(max_length=25, null=True)
	dot11protocol = models.CharField(max_length=10, null=True)


## Access Point Model
class AccessPoint(models.Model):
	macAddress = macField.MACAddressField(primary_key=True)
	name = models.CharField(max_length=50, null=True)
	ip = models.GenericIPAddressField(null=True)
	location = models.CharField(max_length=50, null=True)
	def __str__(self):
		return self.name + " : " + self.macAdress

# Log models
## Radius Model
class RadiusEvent(models.Model):
	date = models.DateTimeField()
	server = models.CharField(max_length=25)
	radiusType = models.CharField(max_length=10) #TODO choice
	login = models.CharField(max_length=128,null=True)
	message = models.CharField(max_length=128,null=True)

	def __str__(self):
		return "" + self.radiusType + " : " +  str(self.login)

	class Meta:
		unique_together = (('date', 'server'),)

## DHCP model
class DHCPEvent(models.Model):
	date = models.DateTimeField()
	server = models.CharField(max_length=5)
	device = macField.MACAddressField(null=True)
	dhcpType = models.CharField(max_length=10)
	ip = models.GenericIPAddressField(null=True)
	message = models.CharField(max_length=256, null=True)

## Wism model
class WismEvent(models.Model):
	date = models.DateTimeField(primary_key=True)
	ip = models.GenericIPAddressField()

	category = models.CharField(max_length=10)
	severity = models.DecimalField(max_digits=1,decimal_places=0)
	mnemo = models.CharField(max_length=56)

	message = models.CharField(max_length=256)


## Error Parsing
class BadLog(models.Model):
	log = models.CharField(max_length=256)
	cause = models.CharField(max_length=256)
	def __str__(self):
		return "" + self.log + " --> " +  self.cause + '\n'



# Tasks model
class CurrentTask(models.Model):
	lastTouched = models.DateTimeField()
	name = models.CharField(max_length=25)
	state = models.CharField(max_length=25)
	progress = models.CharField(max_length=4)
 
	def stillActive(self):
		return (timezone.now() - self.lastTouched) < timedelta(minutes=10)

	def __str__(self):
		return self.name + " by " + self.owner + ": " + ( "active" if self.stillActive() else "inactive")


####################

