
import codecs
import re
from datetime import *
from .events import *


def wismParser(infos):
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
	#2013-10-21T17:26:00+02:00 radius1.sri.ucl.ac.be radiusd[1523]: [ID 702911 local3.notice] Login OK: [@eur.nl] (from client WiSMPythagore-B port 29 cli e4-d5-3d-89-af-51)
	infos[0] = infos[0][:(infos[0].rfind(":"))] + infos[0][(infos[0].rfind(":"))+1:]
	
	try:
		date = datetime.strptime(infos[0], "%Y-%m-%dT%H:%M:%S%z")
	except:
		date = datetime.strptime(infos[0], "%Y-%m-%dT%H:%M:%S.%f%z")

	radiusUrl = infos[1]

	# Log from sipr.logs
	if infos[3].lower() == "login" :
		tmp = infos[4].lower()
		login = infos[5][1:-1]
		if tmp.startswith("ok"):
			return RadiusOk(date, login)
		elif tmp.startswith("incorrect"):
			return RadiusIncorrect(date, login)
		else:
			raise Exception()

	# Big Log file
	elif infos[6].lower() == "login" :
		tmp = infos[7].lower()
		login = infos[8][1:-1]

		if tmp.startswith("ok"):
			return RadiusOk(date, login)
			
		elif tmp.startswith("incorrect"):
			return RadiusIncorrect(date, login)

		else :
			raise Exception()

	elif 'error' in infos[5].lower():
		return RadiusError(date, ' '.join(infos[6:]).strip())

	elif 'notice' in infos[5].lower():
		return RadiusNotice(date, ' '.join(infos[6:]).strip())

	elif 'info' in infos[5].lower():
		return RadiusInfo(date, ' '.join(infos[6:]).strip())


def dhcpParser(infos):
	## Receive a splitted line of log and return an Event

	infos[0] = infos[0][:(infos[0].rfind(":"))] + infos[0][(infos[0].rfind(":"))+1:]
	
	date = datetime.strptime(infos[0], "%Y-%m-%dT%H:%M:%S.%f%z")
	dhcpServer = infos[1]
	dhcpType = infos[3]



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
		device = infos[7]
		if ':' in infos[9]:
			via = infos[9][:-1]
			message = ' '.join(infos[10:])
			return DHCPRequest(date, dhcpServer, ipRequested, device, via, message)
		else:
			via = infos[9]
			return DHCPRequest(date, dhcpServer, ipRequested, device, via)

	# Server acknoledge
	#2014-03-04T13:08:36.177061+01:00 dhcp-2 dhcpd: DHCPACK to 192.135.168.96 (e0:b9:a5:d9:69:cc) via eth0 
	elif infos[3] == "DHCPACK":
		ipAcked = infos[5]
		device = infos[7]
		if '(' in infos[8]:
			deviceName = infos[8]
			via = infos[10]
		else:
			deviceName = None
			via = infos[9]
		return DHCPAck(date, dhcpServer, ipAcked, device, deviceName, via)


	elif infos[3] == "DHCPINFORM":
		return NotAnEvent(date)

	elif syslog in infos[3]:
		message = ' '.join(infos[4:])
		return DHCPLog(date, dhcpServer, message)

	else :
		raise Exception()



def parser(path):
	'''Call by the data gatherer to parse a file holding logs'''

	if path == None:
		return

	with codecs.open(path,'r',encoding='CP1252') as logFile:
		tmp = logFile.readline()
		logFile.seek(0)

		# Radius packets file
		if 'Packet-Type' in tmp :
			pass

		# Normal logs
		else:
			for line in logFile:				
				try:
					log = line.split()

					#DHCP log
					if 'dhcp' in log[1].lower() :
						yield dhcpParser(log)

					# radius log
					elif 'radius' in log[1].lower():
						yield radiusParser(log)

					# controller log
					elif 'controller' in log[1].lower():
						yield None

					# wism log
					elif "wism" in log[2].lower() :
						yield wismParser(log)

					else:
						yield UnparsedLog(line, "Unknown log type")


				except Exception as e:
					# misunderstood log
					yield UnparsedLog(line, str(e))
			

