import sys
import codecs
from datetime import *
from logStructures import *




'''
Packet-Type = Access-Request
Thu Oct 17 13:11:57 2013
	User-Name = "judemolder@wifi.uclouvain.be"
	Calling-Station-Id = "bc-b1-f3-2a-bc-dc"
	Called-Station-Id = "00-1c-b1-8a-05-b0:student.UCLouvain"
	NAS-Port = 29
	Cisco-AVPair = "audit-session-id=c0a8fbb200000083525fc5ed"
	NAS-IP-Address = 192.168.251.178
	NAS-Identifier = "WiSMPythagore-B"
	Airespace-Wlan-Id = 2
	Service-Type = Framed-User
	Framed-MTU = 1300
	NAS-Port-Type = Wireless-802.11
	Tunnel-Type:0 = VLAN
	Tunnel-Medium-Type:0 = IEEE-802
	Tunnel-Private-Group-Id:0 = "226"
	EAP-Message = 0x02010021016a7564656d6f6c64657240776966692e75636c6f757661696e2e6265
	Message-Authenticator = 0xb580eac2363c364b8d9ad8eae201a8ee
	Client-IP-Address = 192.168.251.178
	Huntgroup-Name = "clients802.1X-student"
'''



def radiusParser(path, delta=timedelta(days=99999), maxPackets=float('inf')):

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





if __name__ == '__main__':
	if (len(sys.argv) < 2):
		print('[-] Usage : <file to parse> [<time delta>]')
	else:
		result = radiusParser(sys.argv[1])
		for user in sorted(result.keys()):
			total = 0
			for attemp in result[user]:
				total += attemp.getAttempsCount()
			print(user + ' : ' +  str(len(result[user])) + " connections (with an average of " + str(total/ len(result[user])) + " attemps by connection)")

