from django.db import models
from custom import macField

# General Models
class UserDevice(models.Model):
	login = models.CharField(max_length=24)
	macAdress = macField.MACAddressField(primary_key=True)

	def __str__(self):
		return "" + self.login + " : " +  self.macAdress


# Log models

## DHCP models
class DHCPEvent(models.Model):
	date = models.DateTimeField()
	# Django datetime field does not support milisec !
	milisec = models.IntegerField()
	server = models.CharField(max_length=5)
	device = macField.MACAddressField()
	dhcpType = models.CharField(max_length=10)
	ip = models.GenericIPAddressField(null=True)
		
class BadLog(models.Model):
	log = models.CharField(max_length=256)

####################

