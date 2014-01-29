import codecs
import sys
import re
from multiprocessing import Pool
from datetime import *
from logStructures import *

def wismParser(infos):

	# Remove the colon in the time to be compatible with the strptime method
	infos[0] = infos[0][:(infos[0].rfind(":"))] + infos[0][(infos[0].rfind(":"))+1:]
	date = datetime.strptime(infos[0], "%Y-%m-%dT%H:%M:%S.%f%z")

	# What kind of log
	if(infos[3] == '*DHCP' and infos[4] == 'Server:'):
		msgType = re.split("[%-]",infos[8])
		additionalMsg = ' '.join(infos[10:])
	
	elif(infos[3] == '*DHCP'):
		msgType = re.split("[%-]",infos[11])
		additionalMsg = ' '.join(infos[13:])
	
	elif(infos[3] == '-Traceback:'):
		return "traceback", None
	
	else:
		msgType = re.split("[%-]",infos[7])
		additionalMsg = ' '.join(infos[9:])
	
	
	return "wism", WismLog(date, infos[1], msgType[1], msgType[2], msgType[3], additionalMsg)
	




def radiusParser(path, delta=timedelta(days=99999), maxPackets=float('inf')):
	'''	
	Parse a radius log file and return a list of report

	Arguments:
	path -- path of the log file

	Keyword Arguments:	
	delta -- max duration of a report
	maxPacket -- number of packet to parse (at most) in the log file
	'''

	userHistory = dict()

	with codecs.open(path,'r',encoding='CP1252') as logFile:
		nbrPackets = 0
		for line in logFile:
			if(nbrPackets > maxPackets):
				break

			if(not line.isspace()):
				
				# New packet to parse
				currentPacket = radiusPacket()
				
				while(not line.isspace()):
					if(not '=' in line):
						currentPacket.date = datetime.strptime(line.strip(),"%a %b %d %H:%M:%S %Y")
					else:
						tmp = line.split()
						currentPacket.set(tmp[0],tmp[2])

					line = logFile.readline()

				nbrPackets += 1

				# Handle Access Request
				if(currentPacket.iscomplete() and currentPacket.get('Packet-Type') == 'Access-Request'):
					if(currentPacket.get('User-Name') in userHistory):
						if(currentPacket in userHistory[currentPacket.get('User-Name')][-1]):
							userHistory[currentPacket.get('User-Name')][-1].addRetry(currentPacket)
						else:
							userHistory[currentPacket.get('User-Name')].append(logAttemp(currentPacket))
					else:
						userHistory[currentPacket.get('User-Name')] = [logAttemp(currentPacket)]

				# Handle Accept Request



	return userHistory

	

def parser(path, limit=float('inf')):
	'''Dispatch to the apropriate parser'''

	result = Report()

	with codecs.open(path,'r',encoding='CP1252') as logFile:
		tmp = logFile.next()
		logFile.seek(0)

		# Radius packet file
		if 'Packet-Type' in tmp :
			pass

		# Normal log
		else:
			# multi processing parser
			with Pool() as pool:
				for logType, log in pool.imap(_lineParser, logFile,10000):
					# Wism log
					if logType == "wism":
						result.addLog(log)
					# Traceback (Wism)
					elif logType == "traceback":
						result.addTraceback(log)
					# Problematic logs
					elif logType == "ignore":
						result.addIgnored(log)

	return result

def _lineParser(line):
	try:
		# Radius Packet
		'''if (line.startswith('Packet-Type')) :
									# get all line
									continue'''

		log = line.split()

		#DHCP log
		if ('dhcp' in log[1].lower()) :
			pass

		# radius log
		elif ('radius' in log[1].lower()):
			pass

		# controller log
		elif ('controller' in log[1].lower()):
			pass

		# wism log
		else:
			return wismParser(log)
			

	except Exception as e:
		return "ignore", line





if __name__ == '__main__':
	if (len(sys.argv) > 1):
		import cProfile
		cProfile.run("reports = parser(sys.argv[1])")
		print(reports)
	else:
		logging.error("[-] Specify path please.")



''' Wism logs:
	2013-10-21T17:26:00.104727+02:00  
	192.168.251.178 
	WiSMPythagore-B: 
	*Dot1x_NW_MsgTask_0: 
	Oct 
	21
	17:26:00.062: 
	%APF-6-RADIUS_OVERRIDE_DISABLED: 
	apf_ms_radius_override.c:204 
	Radius overrides disabled, ignoring source 2
'''
