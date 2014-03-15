
import codecs
import re
from datetime import *

from gatherer.models import RadiusEvent, DHCPEvent, WismEvent, MobileStation, AccessPoint, BadLog
from django.db import IntegrityError


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
			return None

		# Generic logs
		else :
			mnemo = mnemo.replace('_',' ')
			message = ' '.join(infos[9:]).strip()
			return WismEvent(date=date, ip=ipWism, category=category, severity=severity, mnemo=mnemo, message=message)

	# Uncommon Wism log types
	elif logType == "-Traceback:" :
		return None

	elif logType == "pykota.sipr.ucl.ac.be" :
		return None

	elif logType == "postfix/smtpd[13316]:" :
		return None

	else :
		raise Exception("Wism: Unknown Service (" + " ".join(infos[3:]) + ")")


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
			return RadiusEvent(date=date, login=login, radiusType='OK')

		elif tmp.startswith("incorrect"):
			return RadiusEvent(date=date, login=login, radiusType='KO')

		else:
			raise Exception("DHCP unknown login operation")

	# Old Log file
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
			return RadiusEvent(date=date, login=login, radiusType='OK')

		elif tmp.startswith("incorrect"):
			return RadiusEvent(date=date, login=login, radiusType='KO')

		else:
			raise Exception("DHCP unknown login operation")


	elif 'error' in infos[5].lower():
		return RadiusEvent(date=date, message=(' '.join(infos[6:]).strip()), radiusType='error')

	elif 'notice' in infos[5].lower():
		return RadiusEvent(date=date, message=(' '.join(infos[6:]).strip()), radiusType='notice')

	elif 'info' in infos[5].lower():
		return RadiusEvent(date=date, message=(' '.join(infos[6:]).strip()), radiusType='info')


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
		return DHCPEvent(date=date, server=dhcpServer, dhcpType='Log', message=message)

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
				return DHCPEvent(date=date, server=dhcpServer, device=device, dhcpType='Discover', message=message)
			else:
				via = infos[7]
			return DHCPEvent(date=date, server=dhcpServer, device=device, dhcpType='Discover')

		# Server respond
		elif infos[3] == "DHCPOFFER":
			ipOffered = infos[5]
			device = infos[7]
			via = infos[9]
			return DHCPEvent(date=date, server=dhcpServer, device=device, dhcpType='Offer',  ip=ipOffered)

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

			return DHCPEvent(date=date, server=dhcpServer, device=device, dhcpType='Request', ip=ipRequested, message=message)


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
				raise Exception("DHCP: Weird Ack log")

			i += 1
			deviceName = ''
			if '(' in infos[i]:
				deviceName = infos[i][1:-1]
				i += 1

			if infos[i] == 'via':
				i += 1
				via = infos[i]
			return DHCPEvent(date=date, server=dhcpServer, device=device, dhcpType='Ack',  ip=ipAcked)

		# Ip needs to be renewed
		elif infos[3] == "DHCPNAK":
			ipNacked = infos[5]
			device = infos[7]
			via = infos[9]
			return DHCPEvent(date=date, server=dhcpServer, device=device, dhcpType='Nak',  ip=ipNacked)

		elif infos[3] == "DHCPINFORM":
			return None

		else :
			tmp = ' '.join(infos[2:])
			if 'ICMP Echo reply while lease' in tmp:
				return DHCPEvent(date=date, server=dhcpServer, dhcpType='Warning', message='pinged', ip=infos[7])
	
			elif 'incoming update is less critical than outgoing update' in tmp:
				return DHCPEvent(date=date, server=dhcpServer, dhcpType='Log', message='Incoming update is less critical than outgoing update', ip=infos[6])
			
			else:
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
			entries = []
			for i, line in enumerate(logFile):				
				
				try:
					# splits the log (required by the parsing methods)
					log = line.split()

					# DHCP log
					if 'dhcp' in log[1].lower() :
						entries.append(dhcpParser(log))

					# radius log
					elif 'radius' in log[1].lower() or 'radius' in log[2].lower():
						entries.append(radiusParser(log))

					# controller log
					elif 'controller' in log[1].lower():
						entries.append(BadLog(log=line, cause='Controller log not suported.'))

					# wism log
					elif "wism" in log[2].lower() :
						entries.append(wismParser(log))

					# unhandled log
					else:
						entries.append(BadLog(log=line, cause="Unknown log type"))

				except Exception as e:
					# misunderstood log
					entries.append(BadLog(log=line, cause=str(e)))
				
				finally:
					if (i+1) % 500 == 0:
						addBatch(entries)
						entries = []

			addBatch(entries)


def addBatch(entrieslist):
	""" Add all the entries in lists to the DB

	Argument:
	list -- list of entries
	"""
	for element in entrieslist:
		try:
			element.save()
		except IntegrityError:
			pass
		except AttributeError:
			# save() on None type
			pass


def saveBadLogs(path):
	""" Save the unparsed log in path and remove them from the DB

	Argument:
	path -- the path where the bad logs are saved
	"""
	
	badLogs = BadLog.objects.all()
	if len(badLogs) > 0:
		with open(path, 'w') as f:
			for element in badLogs:
				f.write(str(element) + '\n')

		badLogs.delete()

