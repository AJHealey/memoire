
import codecs
import re
from datetime import *
from .events import *


def wismParser(infos):
	""" Parse a log from the WiSM and return an Event instance

	Argument:
	infos -- a splitted log string
	"""

	# Remove the colon in the time to be compatible with the strptime method
	infos[0] = infos[0][:(infos[0].rfind(":"))] + infos[0][(infos[0].rfind(":"))+1:]
	date = datetime.strptime(infos[0], "%Y-%m-%dT%H:%M:%S.%f%z")
	
	ipWism = infos[1]
	wismName = infos[2][:-1]
	logType = infos[3]
	i = 4
	
	while ':' not in logType:
		logType += " " + infos[i]
		i += 1

	# Common category of logs
	if logType[0] == '*' and logType[-1] == ':':
		category = infos[7].replace("%", "").replace("-", " ").replace(":","").split()
		
		severity = int(float(category[1]))
		mnemo = category[2]
		category = category[0]

		# les logs de type %LOG-X-Q_IND: ne sont qu'un duplicata de log precedent
		if category == "LOG" and mnemo == "Q_IND":
			return NotAnEvent(date)

		# Generic logs
		else : 
			return WismLog(date, ipWism, category, severity, mnemo.replace('_',' '), ' '.join(infos[9:]).strip() )

	# Uncommon Wism log types
	elif logType == "-Traceback:" :
		return WismTraceback(date)

	elif logType == "pykota.sipr.ucl.ac.be" :
		return NotAnEvent(date)

	elif logType == "postfix/smtpd[13316]:" :
		return NotAnEvent(date)

	else :
		return UnknownServiceWismLog(date, infos[3:].join(" "))


def radiusParser(infos):
	""" Parse a log from the radius and return an Event instance

	Argument:
	infos -- a splitted log string
	"""
	#2013-10-21T17:27:37+02:00 radius1.sri.ucl.ac.be radiusd[1523]: [ID 702911 local3.notice] Login incorrect (rlm_ldap: User not found): [host/MAIGA-Portable] (from client WiSMPythagore-B port 29 cli 50-63-13-c2-6e-25)
	#2013-10-21T17:26:00+02:00 radius1.sri.ucl.ac.be radiusd[1523]: [ID 702911 local3.notice] Login OK: [@eur.nl] (from client WiSMPythagore-B port 29 cli e4-d5-3d-89-af-51)
	infos[0] = infos[0][:(infos[0].rfind(":"))] + infos[0][(infos[0].rfind(":"))+1:]
	
	try:
		date = datetime.strptime(infos[0], "%Y-%m-%dT%H:%M:%S%z")
	except:
		date = datetime.strptime(infos[0], "%Y-%m-%dT%H:%M:%S.%f%z")

	radiusUrl = infos[1]

	# Log from sipr.logs
	if infos[3].lower() == "login" :
		i = 4
		tmp = infos[i].lower()
		i += 1
		if ':' not in tmp:
			while '):' not in infos[i]:
				i += 1
			i += 1

		login = infos[i][1:-1]
		if tmp.startswith("ok"):
			return RadiusOk(date, login)

		elif tmp.startswith("incorrect"):
			return RadiusIncorrect(date, login)

		else:
			raise Exception("DHCP unknown login operation")

	# Big Log file
	elif infos[6].lower() == "login" :
		i = 7
		tmp = infos[i].lower()
		i += 1
		if ':' not in tmp:
			while '):' not in infos[i]:
				i += 1
			i += 1

		login = infos[i][1:-1]
		if tmp.startswith("ok"):
			return RadiusOk(date, login)

		elif tmp.startswith("incorrect"):
			return RadiusIncorrect(date, login)

		else:
			raise Exception("DHCP unknown login operation")


	elif 'error' in infos[5].lower():
		return RadiusError(date, ' '.join(infos[6:]).strip())

	elif 'notice' in infos[5].lower():
		return RadiusNotice(date, ' '.join(infos[6:]).strip())

	elif 'info' in infos[5].lower():
		return RadiusInfo(date, ' '.join(infos[6:]).strip())


def dhcpParser(infos):
	""" Parse a log from the DHCP and return an Event instance

	Argument:
	infos -- a splitted log string
	"""

	infos[0] = infos[0][:(infos[0].rfind(":"))] + infos[0][(infos[0].rfind(":"))+1:]
	date = datetime.strptime(infos[0], "%Y-%m-%dT%H:%M:%S.%f%z")
	
	dhcpServer = infos[1]
	dhcpType = infos[3]

	# Sys log message
	if 'syslog' in infos[2]:
		message = ' '.join(infos[4:])
		return DHCPLog(date, dhcpServer, message)

	# DHCP events
	elif 'dhcp' in infos[2]:

		## Client broadcasted asking
		if infos[3] == "DHCPDISCOVER":
			device = infos[5]
			
			if ':' in infos[7]:
				via = infos[7][:-1]
				message = ' '.join(infos[8:])
				if 'load balance' in message:
					message = ''
				return DHCPDiscover(date, dhcpServer, device, via, message)
			else:
				via = infos[7]
			return DHCPDiscover(date, dhcpServer, device, via)

		# Server respond
		elif infos[3] == "DHCPOFFER":
			ipOffered = infos[5]
			device = infos[7]
			via = infos[9]
			return DHCPOffer(date, dhcpServer, ipOffered, device, via)

		# Client choose ip
		elif infos[3] == "DHCPREQUEST":
			ipRequested = infos[5]
			i = 6
			if '(' in infos[i]:
				# Not used
				otherIp = infos[i][1:-1]
				i += 1

			if infos[i] == 'from':
				i += 1
				device = infos[i]

			i += 1
			deviceName = '' 
			if '(' in infos[i]:
				deviceName = infos[i][1:-1]
				i += 1

			message = ''
			if infos[i] == 'via':
				i += 1
				if ':' in infos[i]:
					via = infos[i][:-1]
					i += 1 
					message = ' '.join(infos[i:])
				else:
					via = infos[i]
		
			return DHCPRequest(date, dhcpServer, ipRequested, device, via, message)


		# Server acknoledge
		elif infos[3] == "DHCPACK":
			#2013-10-21T17:26:00.113239+02:00 dhcp-1 dhcpd: DHCPACK on 192.168.32.43 to cc:fe:3c:26:5c:3f via 192.168.35.253

			ipAcked = infos[5]
			i = 6

			if infos[i] == 'to':
				i += 1
				device = infos[i]
			elif '(' in infos[i]:
				device = infos[i][1:-1]
			else:
				raise Exception("DHCP weird Ack log")

			i += 1
			deviceName = ''
			if '(' in infos[i]:
				deviceName = infos[i][1:-1]
				i += 1

			if infos[i] == 'via':
				i += 1
				via = infos[i]
			
			return DHCPAck(date, dhcpServer, ipAcked, device, deviceName, via)

		# Ip needs to be renewed
		elif infos[3] == "DHCPNAK":
			ipNacked = infos[5]
			device = infos[7]
			via = infos[9]
			return DHCPNak(date, dhcpServer, ipNacked, device, via)

		elif infos[3] == "DHCPINFORM":
			return NotAnEvent(date)

		else :
			tmp = ' '.join(infos[2:])
			if 'ICMP Echo reply while lease' in tmp:
				return DHCPWarning(date, dhcpServer, infos[7], 'pinged')
	
			elif 'incoming update is less critical than outgoing update' in tmp:
				return DHCPLog(date, dhcpServer, 'Incoming update is less critical than outgoing update', infos[6])

			raise Exception('DHCP event: ' + infos[3] + ' unknown')

		
	else :
		raise Exception('DHCP category unknown: ' + infos[2])



def parser(path):
	''' Parse a file containing logs and yields Event instances

	Argument:
	path -- the path of the file to be parse
	'''

	if path == None:
		return

	with codecs.open(path,'r',encoding='CP1252') as logFile:
		# Look to the first line to get the category of the log file
		tmp = logFile.readline()
		logFile.seek(0)

		# Radius packets file
		if 'Packet-Type' in tmp :
			pass

		# Normal logs
		else:
			for line in logFile:				
				try:
					# splits the log (required by the parsing methods)
					log = line.split()

					# DHCP log
					if 'dhcp' in log[1].lower() :
						yield dhcpParser(log)

					# radius log
					elif 'radius' in log[1].lower() or 'radius' in log[2].lower():
						yield radiusParser(log)

					# controller log
					elif 'controller' in log[1].lower():
						yield UnparsedLog(line, 'Controller log')

					# wism log
					elif "wism" in log[2].lower() :
						yield wismParser(log)

					# unhandled log
					else:
						yield UnparsedLog(line, "Unknown log type")


				except Exception as e:
					# misunderstood log
					yield UnparsedLog(line, str(e))
			

