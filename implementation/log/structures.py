import re
import fileDescriptions
import json 
import codecs
from datetime import *
import logStructures


class AuthChain:	
	'''
	Represent an user authentification

	The entire chain from 802.1x to DHCP
	'''
	def __init__(self):
		# 802.1x
		self.dot1xPackets = []
		self.dot1xSucces = False
		# EAP-TTLS or EAP-PEAP
		self.eapType = None
		self.eapPackets = []
		self.eapSucces = False
		#DHCP
		self.dhcpPackets = []
		self.ip = None


class User:
	"""Represent an user in the network"""
	def __init__(self, username):
		"""	Each user have an unique username """
		self.username = username
		self._macAdresses = set()
		self.authentifications = []
		self._relatedLog = []

	def __eq__(self, other):
		if isinstance(other,User):
			return self.username == other.username
		elif isinstance(other,str):
			return self.username == other or (other in self)
		else:
			return False

	def __ne__(self,other):
		return not (self==other)

	def __contains__(self, mac):
		# check if mac adress belong to the users
		# transform the mac adress in a canonical form
		tmp = "".join(re.split("[:-]",mac))
		return tmp in self.authentifications

	def __repr__(self):
		return self.username

	def __str__(self):
		result = self.username 
		for m in self._macAdresses:
			result += "\n\t" + m
		return result + "\n\t" + str(len(self.authentifications)) + " authentifications" 

	def merge(self,other):
		# Concatenation of two users
		if self.username == other.username:
			self._macAdresses |= other._macAdresses
			self.authentifications += other.authentifications

	def addMacAddress(self, mac):
		# Add a mac Address to the user
		tmp = "".join(re.split("[:-]",mac))
		self._macAdresses.add(tmp)

	def addRelatedLog(self, log):
		self._relatedLog.append(log)


class Device:
	'''Represent on device (ex: Radius, AP, controller, etc. )'''
	facilityMeaning = {}
	try :
		facilityMeaning = json.load(codecs.open(fileDescriptions.FACILITIES,'r',encoding='CP1252'))
	except:
		pass	
	severityMeaning = {'0':'Emergency', '1': 'Alert', '2':'Critical', '3':'Error', '4':'Warning', '5':'Notification', '6':'Information', '7':'Debugging'}

	def __init__(self, name):
		self.name = name
		self.ip = ''
		# [facility][gravity][mnemonic]->log
		self.sysLog = {}

		self._allLogs = set()

	def __eq__(self,other):
		if isinstance(other,Device):
			return self.name == other.name
		else:
			return false

	def __repr__(self):
		return self.name + " <" + self.ip + ">"

	def __str__(self):
		result = self.name + ":\n"
		for fac in sorted(self.sysLog.keys()):
			result += fac
			
			if(fac in Device.facilityMeaning):
				result += ' (' + Device.facilityMeaning[fac] + ' messages)'
			result += ":\n"
			
			for sev in sorted(self.sysLog[fac].keys()):
				result += '\t' + sev + ":" + Device.severityMeaning[sev] + ':\n'
			
				for mnemo in sorted(self.sysLog[fac][sev].keys()):
					mTotal = 0
					for v in self.sysLog[fac][sev][mnemo].values():
						mTotal += v
					result += '\t\t' + mnemo + ' (' + str(mTotal) + ' times)\n'
				result += '\n'


		return result


	def addLog(self, log):
		'''Add a new log to the device'''
		if not log in self._allLogs:

			if isinstance(log, logStructures.WismLog):

				if(not log.facility in self.sysLog):
					self.sysLog[log.facility] = {}

				if(not log.severity in self.sysLog[log.facility]):
					self.sysLog[log.facility][log.severity] = {}

				if(not log.mnemonic in self.sysLog[log.facility][log.severity]):
					self.sysLog[log.facility][log.severity][log.mnemonic] = {}

				if(not log.message in self.sysLog[log.facility][log.severity][log.mnemonic]):
					self.sysLog[log.facility][log.severity][log.mnemonic][log.message] = 0

				self.sysLog[log.facility][log.severity][log.mnemonic][log.message] += 1


	def purge(self, delta=timedelta(days=1)):
		'''Remove all logs older than delta'''
		now = datetime.today()
		result = self._allLogs
		for log in self._allLogs:
			if (log.date + delta) < now:
				self.sysLog[log.facility][log.severity][log.mnemonic].remove(log)
				result.remove(log)
		self._allLogs = result 
