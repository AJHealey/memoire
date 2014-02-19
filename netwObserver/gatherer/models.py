from django.db import models
from custom import macField

# General Models
class UserDevice(models.Model):
	login = models.CharField(max_length=24)
	macAdress = macField.MACAddressField()

	def __str__(self):
		return "" + self.login + " : " +  self.macAdress
 
## DHCP models
class DHCPEvent(models.Model):
	date = models.DateTimeField()
	server = models.CharField(max_length=5)
	device = macField.MACAddressField()
		
	

