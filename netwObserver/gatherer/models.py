from django.db import models
from custom import macField
from datetime import datetime, timedelta
from django.utils import timezone

from django.conf import settings

# SNMP Models
## Device
class Device(models.Model):
	# primary key => not inherited
	macAddress = macField.MACAddressField(unique=True)
	ip = models.GenericIPAddressField(null=True)
	lastTouched = models.DateTimeField(null=True, default=lambda:(timezone.now()) )
	index = models.CharField(max_length=20, null=True) 

	def touch(self):
		self.lastTouched = timezone.now()
		self.save()

	class Meta:
		abstract = True
		ordering = ["macAddress"]


## Access Point Model
class APManage(models.Manager):
	def isUp(self):
		return super(APManage, self).filter(lastTouched__gte=(timezone.now() - settings.SNMPAPLAP))

class AccessPoint(Device):
	ETHERNETLINKTYPE = ((10,'10 Mbps'),(100,'100 Mbps'),(1000,'1 Gbps'))

	name = models.CharField(max_length=50, null=True)
	location = models.CharField(max_length=50, null=True)

	ethernetLinkSpeed = models.DecimalField(max_digits=5, decimal_places=0, choices=ETHERNETLINKTYPE, null=True)
	ethernetRxTotalBytes = models.DecimalField(max_digits=10, decimal_places=0, default=0)
	ethernetTxTotalBytes = models.DecimalField(max_digits=10, decimal_places=0, default=0)

	objects = APManage()
	def __str__(self):
		return str(self.name) + " : " + str(self.macAddress) + ' (' + str(self.ip) + ')'
	
	def isUp(self):
		return lastTouched > (timezone.now() - settings.SNMPAPLAP)

	def nbrOfClients(self):
		result = 0
		for i in self.apinterface_set:
			result += i.numOfClients
		return result

## Access Point Interface Model
class APInterface(models.Model):
	TYPES = ((1,'Dot11b'),(2,'Dot11a'),(4,'Ultra-Wide Band'))

	index = models.CharField(max_length=3)
	ap = models.ForeignKey(AccessPoint)
	ifType = models.DecimalField(max_digits=1, decimal_places=0, choices=TYPES,null=True)
	
	channelUtilization = models.DecimalField(max_digits=3, decimal_places=0, default=0)
	numOfClients = models.DecimalField(max_digits=4, decimal_places=0, default=0)
	numOfPoorSNRClients = models.DecimalField(max_digits=4, decimal_places=0, default=0)

	class Meta:
		unique_together = (('ap', 'index'),)


## Rogue Access Point Model
class RAPManage(models.Manager):
	def isUp(self):
		return super(APManage, self).filter(lastTouched__gte=(timezone.now() - settings.SNMPAPLAP))

class RogueAccessPoint(Device):

	ssid = models.CharField(max_length=50, default='')
	nbrOfClients = models.DecimalField(max_digits=3, decimal_places=0, default=0)
	closestAp = models.ForeignKey(AccessPoint, null= True)

	objects = RAPManage()
	def __str__(self):
		return str(self.name) + " : " + str(self.macAddress) + ' (' + str(self.ip) + ')'
	
	def isUp(self):
		return lastTouched > (timezone.now()- settings.SNMPRAPLAP)


## Mobile stations Model
class MSManage(models.Manager):
	def isAssociated(self):
			return super(MSManage, self).filter(lastTouched__gte=(timezone.now() - settings.SNMPMSLAP))

class MobileStation(Device):
	DOT11_PROTOCOLS = (('1',"802.11a"),('2',"802.11b"),('3',"802.11g"),('6',"802.11n (2.4Ghz)"),('7',"802.11n (5Ghz)"),('4',"Unknown"),('5',"Mobile"))

	ap = models.ForeignKey(AccessPoint, related_name='associated', null=True)
	ssid = models.CharField(max_length=25, null=True)
	dot11protocol = models.CharField(max_length=1, choices=DOT11_PROTOCOLS, null=True)
	
	objects = MSManage()
	def __str__(self):
		return str(self.macAddress) + ' on ' + str(self.ssid)

## SNMP Snapshot
class APSnapshot(models.Model):
	ap = models.ForeignKey(AccessPoint)
	date = models.DateTimeField(default=lambda:(timezone.now()))

	ethernetRxTotalBytes = models.DecimalField(max_digits=10, decimal_places=0, default=0)
	ethernetTxTotalBytes = models.DecimalField(max_digits=10, decimal_places=0, default=0)

class APIfSnapshot(models.Model):
	apsnapshot = models.ForeignKey(APSnapshot)
	apinterface = models.ForeignKey(APInterface)
	channelUtilization = models.DecimalField(max_digits=3, decimal_places=0, default=0)
	numOfClients = models.DecimalField(max_digits=4, decimal_places=0, default=0)
	numOfPoorSNRClients = models.DecimalField(max_digits=4, decimal_places=0, default=0)



######################################################################################
######################################################################################
# Log Models
## Radius Model
class RadiusEvent(models.Model):
	RADIUS_TYPES = (("ok","Login Ok"),("ko","Login Incorrect"),("er","Error"),("no","Notice"),("in","Information"))

	date = models.DateTimeField()
	microsecond = models.DecimalField(max_digits=6, decimal_places=0)

	server = models.CharField(max_length=25)
	radiusType = models.CharField(max_length=2, choices=RADIUS_TYPES) #TODO choice
	
	login = models.CharField(max_length=128, default="")
	message = models.CharField(max_length=128,default="")

	def __str__(self):
		return "" + self.radiusType + " : " +  self.login

	class Meta:
		unique_together = (('date', 'microsecond', 'login', 'message'),)

## DHCP model
class DHCPEvent(models.Model):
	DHCP_TYPES = (("log","Syslog"), ("war","Warning"), ("dis","Discover"), ("off","Offer"), ("req","Request"), ("ack","Ack"), ("nak","Nak"), ("inf", "Inform"))

	date = models.DateTimeField()
	microsecond = models.DecimalField(max_digits=6, decimal_places=0)

	server = models.CharField(max_length=10)
	device = macField.MACAddressField(null=True)
	dhcpType = models.CharField(max_length=3, choices=DHCP_TYPES)
	ip = models.GenericIPAddressField(null=True)
	message = models.CharField(max_length=256, null=True)

	class Meta:
		unique_together = (('date', 'microsecond', 'server'),)


## Wism model
class WismEvent(models.Model):
	SEVERITY_MEANING = ((0,'Emergency: System is unusable'),(1,'Alert: Action must be taken immediately'), (2,'Critical: Critical conditions'), (3,'Error: Error conditions'), (4,'Warning: Warning conditions'), (5,'Notice: Normal but significant condition'), (6,'Informational: Informational messages'), (7,'Debug: Debug-level messages'))
	date = models.DateTimeField()
	microsecond = models.DecimalField(max_digits=6, decimal_places=0)
	
	wismIp = models.GenericIPAddressField()

	category = models.CharField(max_length=10)
	severity = models.DecimalField(max_digits=1,decimal_places=0, choices=SEVERITY_MEANING)
	mnemo = models.CharField(max_length=56)

	message = models.CharField(max_length=256)

	class Meta:
		unique_together = (('date', 'microsecond', 'wismIp'),)


#class ProbeEvent(models.Model):




## Error Parsing
class BadLog(models.Model):
	log = models.CharField(max_length=256)
	cause = models.CharField(max_length=256)
	def __str__(self):
		return "" + self.log + " --> " +  self.cause + '\n'



################## Auxiliary Models #######################
## Tasks model
class CurrentTask(models.Model):
	lastTouched = models.DateTimeField(default=lambda:(timezone.now()))
	name = models.CharField(max_length=25, primary_key=True)
 	
	def touch(self):
		self.lastTouched = timezone.now()
		self.save()

	def __str__(self):
		return self.name

## Operational Errors Model
class OperationalError(models.Model):
	date = models.DateTimeField(default=lambda:(timezone.now()))
	source = models.CharField(max_length=100)
	error = models.CharField(max_length=250)

	def __str__(self):
		return str(self.date) + ": " + self.error + " (from " + self.source + ")"

####################

