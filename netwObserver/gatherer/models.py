from django.db import models
from custom import macField
from datetime import datetime, timedelta
from django.utils import timezone

from django.conf import settings


## Device
class Device(models.Model):
	# If primary key => not inherited
	macAddress = macField.MACAddressField(unique=True)
	ip = models.GenericIPAddressField(null=True)
	lastTouched = models.DateTimeField(null=True, default=lambda:(timezone.localtime(timezone.now())) )

	def touch(self):
		self.lastTouched = timezone.localtime(timezone.now())

	class Meta:
		abstract = True
		ordering = ["macAddress"]


## Access Point Model
class APManage(models.Manager):
	def isUp(self):
		return super(APManage, self).filter(lastTouched__gte=(timezone.localtime(timezone.now()) - settings.SNMPAPLAP))

class AccessPoint(Device):
	name = models.CharField(max_length=50, null=True)
	location = models.CharField(max_length=50, null=True)
	
	objects = APManage()
	def __str__(self):
		return str(self.name) + " : " + str(self.macAddress) + ' (' + str(self.ip) + ')'


## Mobile stations Model
class MSManage(models.Manager):
	def isAssociated(self):
			return super(MSManage, self).filter(lastTouched__gte=(timezone.localtime(timezone.now()) - settings.SNMPMSLAP))

class MobileStation(Device):
	DOT11_PROTOCOLS = (('1',"802.11a"),('2',"802.11b"),('3',"802.11g"),('6',"802.11n (2.4Ghz)"),('7',"802.11n (5Ghz)"),('4',"Unknown"),('5',"Mobile"))

	ap = models.ForeignKey(AccessPoint, related_name='associated', null=True)
	ssid = models.CharField(max_length=25, null=True)
	dot11protocol = models.CharField(max_length=1, choices=DOT11_PROTOCOLS, null=True)
	
	objects = MSManage()
	def __str__(self):
		return str(self.macAddress) + ' on ' + str(self.ssid)


## User
class User(models.Model):
	login = models.CharField(max_length=128, primary_key=True)
	email = models.EmailField(max_length=254, null=True)
	def __str__(self):
		return self.login

	class Meta:
		ordering = ["login"]


# Log models
## Radius Model
class RadiusEvent(models.Model):
	date = models.DateTimeField()
	microsecond = models.DecimalField(max_digits=6, decimal_places=0)

	server = models.CharField(max_length=25)
	radiusType = models.CharField(max_length=10) #TODO choice
	
	user = models.ForeignKey(User,null=True)
	message = models.CharField(max_length=128,null=True)

	def __str__(self):
		return "" + self.radiusType + " : " +  self.user.login

	class Meta:
		unique_together = (('date', 'microsecond', 'user'),)

## DHCP model
class DHCPEvent(models.Model):
	date = models.DateTimeField()
	microsecond = models.DecimalField(max_digits=6, decimal_places=0)

	server = models.CharField(max_length=10)
	device = models.ForeignKey(MobileStation, null=True)
	dhcpType = models.CharField(max_length=10)
	ip = models.GenericIPAddressField(null=True)
	message = models.CharField(max_length=256, null=True)

	class Meta:
		unique_together = (('date', 'microsecond', 'server'),)

## Wism model
class WismEvent(models.Model):
	date = models.DateTimeField()
	microsecond = models.DecimalField(max_digits=6, decimal_places=0)
	
	wismIp = models.GenericIPAddressField()

	category = models.CharField(max_length=10)
	severity = models.DecimalField(max_digits=1,decimal_places=0)
	mnemo = models.CharField(max_length=56)

	message = models.CharField(max_length=256)

	class Meta:
		unique_together = (('date', 'microsecond', 'wismIp'),)


################## Auxiliary Models #######################

## Error Parsing
class BadLog(models.Model):
	log = models.CharField(max_length=256)
	cause = models.CharField(max_length=256)
	def __str__(self):
		return "" + self.log + " --> " +  self.cause + '\n'

## Tasks model
class CurrentTask(models.Model):
	lastTouched = models.DateTimeField(default=timezone.localtime(timezone.now()))
	name = models.CharField(max_length=25, primary_key=True)
	status = models.CharField(max_length=10)
 	
	def touch(self):
		self.lastTouched = timezone.localtime(timezone.now())

	def stillActive(self):
		return (timezone.localtime(timezone.now()) - self.lastTouched) < timedelta(minutes=10)

	def __str__(self):
		return self.name + ": " + ( "active" if self.stillActive() else "inactive") + ' - ' + self.status

## Operational Errors Model
class OperationalError(models.Model):
	date = models.DateTimeField()
	source = models.CharField(max_length=25)
	error = models.CharField(max_length=250)

	def __str__(self):
		return str(self.date) + ": " + self.error + " (from " + self.source + ")"

####################

