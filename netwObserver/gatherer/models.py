from django.db import models
from custom import macField

# Log models
## Radius Model
class RadiusEvent(models.Model):
	date = models.DateTimeField()
	server = models.CharField(max_length=25)
	radiusType = models.CharField(max_length=10)
	login = models.CharField(max_length=128,null=True)
	message = models.CharField(max_length=128,null=True)

	def __str__(self):
		return "" + self.radiusType + " : " +  str(self.login)

	class Meta:
		unique_together = (("date", "login","radiusType"),('date', 'server','message'))

## DHCP model
class DHCPEvent(models.Model):
	date = models.DateTimeField(primary_key=True)
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


## Mobile stations Model
class MobileStation(models.Model):
	index = models.CharField(max_length=25, null=True)
	macAddress = macField.MACAddressField(primary_key=True)
	ip = models.GenericIPAddressField(null=True)
	SSID = models.CharField(max_length=25, null=True)
	Dot11Proto = models.CharField(max_length=10, null=True)


## Access Point Model
class AccessPoint(models.Model):
	index = models.CharField(max_length=25, null=True)
	name = models.CharField(max_length=50, null=True)
	macAddress = macField.MACAddressField(primary_key=True)
	ip = models.GenericIPAddressField(null=True)
	location = models.CharField(max_length=50, null=True)
	def __str__(self):
		return self.name + " : " + self.macAdress


## Error Parsing
class BadLog(models.Model):
	log = models.CharField(max_length=256)
	cause = models.CharField(max_length=256)
	def __str__(self):
		return "" + self.log + "--> " +  self.cause + '\n'

####################

