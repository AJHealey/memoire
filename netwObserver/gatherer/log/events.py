class Event:
	def __init__(self,date):
		self.date = date


class NotAnEvent(Event):
	# Empty Event
	def __init__(self, date):
		super().__init__(date)

#Radius
class RadiusOk(Event):
	def __init__(self, date, login):
		super().__init__(date)
		self.login = login

class RadiusIncorrect(Event):
	def __init__(self, date, login):
		super().__init__(date)
		self.login = login

class RadiusError(Event):
	def __init__(self, date, message):
		super().__init__(date)
		self.message = message

class RadiusNotice(Event):
	def __init__(self, date, message):
		super().__init__(date)
		self.message = message

class RadiusInfo(Event):
	def __init__(self, date, message):
		super().__init__(date)
		self.message = message

#DHCP
class DHCPDiscover(Event):
	def __init__(self, date, dhcpServer, device, via):
		super().__init__(date)
		self.dhcpServer = dhcpServer
		self.device = device
		self.via = via

class DHCPRequest(Event):
	def __init__(self, date, dhcpServer, ipRequested, device, via):
		super().__init__(date)
		self.dhcpServer = dhcpServer
		self.ipRequested = ipRequested
		self.device = device
		self.via = via

class DHCPOffer(Event):
	def __init__(self, date, dhcpServer, ipOffered, device, via):
		super().__init__(date)
		self.dhcpServer = dhcpServer
		self.ipOffered = ipOffered
		self.device = device
		self.via = via


class DHCPAck(Event):
	def __init__(self, date, dhcpServer, ipAcked, device, deviceName, via):
		super().__init__(date)
		self.dhcpServer = dhcpServer
		self.ipAcked = ipAcked
		self.device = device
		self.deviceName = deviceName
		self.via = via


#Wism
class WismLog(Event):
	# Represent a log with no usefull information
	def __init__(self, date, ip, category, severity, mnemo, message):
		super().__init__(date)
		self.ip = ip

		self.category = category
		self.severity = severity
		self.mnemo = mnemo

		self.message = message


class WismTraceback(Event):
	# traceback log
	def __init__(self, date):
		super().__init__(date)

class UnmanagedWismLog(Event):
	# Represent a log with no usefull information
	def __init__(self, date, ip, wismName, category, severity, mnemo):
		super().__init__(date)
		self.ip = ip
		self.wismName = wismName
		self.category = category
		self.severity = severity
		self.mnemo = mnemo

class UnknownServiceWismLog(Event):
	# log from unknown source
	def __init__(self, date, log):
		super().__init__(date)
		self.log = log


class UnparsedLog(Event):
	def __init__(self, log, cause):
		super().__init__(None)
		self.log = log
		self.cause = cause
		
