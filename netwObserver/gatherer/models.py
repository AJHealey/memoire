from django.db import models
from custom import macField

# General Models
class UserDevice(models.Model):
	name = models.CharField(max_length=24)
	macAdress = macField.MACAddressField(primary_key=True)

	def __str__(self):
		return "" + self.login + " : " +  self.macAdress


# Log models

## Radius Model
class RadiusEvent(models.Model):
	date = models.DateTimeField()
	server = models.CharField(max_length=25)
	radiusType = models.CharField(max_length=10)
	login = models.CharField(max_length=128,null=True)
	message = models.CharField(max_length=128,null=True)

	class Meta:
		unique_together = (("date", "login","radiusType"),('date', 'server','message'))


## DHCP model
class DHCPEvent(models.Model):
	date = models.DateTimeField(primary_key=True)
	server = models.CharField(max_length=5)
	device = macField.MACAddressField()
	dhcpType = models.CharField(max_length=10)
	ip = models.GenericIPAddressField(null=True)

## Wism model
class WismEvent(models.Model):
	date = models.DateTimeField(primary_key=True)
	ip = models.GenericIPAddressField()

	category = models.CharField(max_length=10)
	severity = models.DecimalField(max_digits=1,decimal_places=0)
	mnemo = models.CharField(max_length=56)

	message = models.CharField(max_length=256)

class BadLog(models.Model):
	log = models.CharField(max_length=256)
	cause = models.CharField(max_length=256)

####################

