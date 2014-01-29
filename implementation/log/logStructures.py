from datetime import *
import fileDescriptions
import structures
import json 
import codecs
import re


class Log:
	def __init__(self):
		self.date = None


class RadiusLog(Log):
	TYPE = {}

	def __init__(self):
		super().__init__(self)
		self.infos = dict()
		

	def set(self, attr, value):
		self.infos[str.lower(attr)] = value

	def get(self, attr):
		if(str.lower(attr) in self.infos):
			return self.infos[str.lower(attr)]
		else:
			None

	def iscomplete(self):
		return (self.date != None and 'user-name' in self.infos)


class DhcpLog(Log):

	def __init__(self):
		self.ip

class WismLog(Log):
	#Mac address pattern
	macPattern = "[0-9A-Fa-f][0-9A-Fa-f][:-]?[0-9A-Fa-f][0-9A-Fa-f][:-]?[0-9A-Fa-f][0-9A-Fa-f][:-]?[0-9A-Fa-f][0-9A-Fa-f][:-]?[0-9A-Fa-f][0-9A-Fa-f][:-]?[0-9A-Fa-f][0-9A-Fa-f]"

	def __init__(self, date, device, facility, severity, mnemonic, message):
		super().__init__()
		self.date = date
		self.device = device
		self.facility = facility
		self.severity = severity
		self.mnemonic = mnemonic
		self.message = message

	def getMacInMessage(self):
		result = []

		try:
			result = re.findall(WismLog.macPattern,self.message)
		except:
			pass
		finally:
			return result

	def __str__(self):
		return self.device + " " + self.facility + " " + self.severity + " " + self.mnemonic

	def __repr__(self):
		return self.device + ":" + self.facility + "_" + self.severity + "_" + self.mnemonic



class Report:
	'''
	Represent the information contained in a set of logs.
	'''

	def __init__(self):

		self.ignoredMsg = []
		self.traceback = 0

		self.users = {}
		self.devices = {}

		self.logByMac = {}



	def addLog(self, log):
		# Wism Log
		if isinstance(log, WismLog):
			# new device reported
			if not log.device in self.devices:
				self.devices[log.device] = structures.Device(log.device)
			
			self.devices[log.device].addLog(log)

			''' # Deeper Message Processing HERE
			relatives = log.getMacInMessage()
			for m in relatives:
				if m not in self.logByMac:
					self.logByMac[m] = []

				self.logByMac[m].append(log)'''

	def addIgnored(self, msg):
		self.ignoredMsg.append(msg)

	def addTraceback(self, log):
		# TODO : looking for usefull information in traceback
		self.traceback += 1

	def __str__(self):
		result = ''

		for d in self.devices:
			result += str(self.devices[d])


		result += '-' * 40 + '\n' 
		result += 'Traceback messages: ' + str(self.traceback) + '\n'
		result += 'Ignored Messages: ' + str(len(self.ignoredMsg)) + '\n\n'

		return result

#### Useless : Check if is no more used
class logAttemp:
	'''DHCP packet containing a logging attemp'''
	delta = timedelta(seconds=5)
	def __init__(self,packet):
		self.start = packet.date
		self.tries = [packet]
		self.success = False

	def __contains__(self, packet):
		element = packet.date
		if( (not self.success) and isinstance(element, datetime) and (self.start + self.delta) < element):
			return True

		else:
			return False

	def setDelta(self, ndelta):
		if (isinstance(ndelta, timedelta)):	
			self.delta = ndelta

	def addRetry(self,packet):
		if( (not self.success) and isinstance(packet,radiusPacket)):
			self.tries.append(packet)

	def success(self):
		self.success = True

	def getAttemps(self):
		return self.tries

	def getAttempsCount(self):
		return len(self.tries)

##################################################


