import socket
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
from Crypto import Random
from threading import Thread
from time import sleep
import base64

MAX_DATA_RECEIVED = 2000
PROBEPORT = 45678
PRIVKEY = '../../credentials/memKey.pem'
PUBKEY = '../../credentials/memKey.pub'
PROBEKEY = '../../credentials/authorizedProbes/probe1Key.pub'

def step1(privkeypath=PRIVKEY, pubkeypath=PUBKEY):
	# Load RSA keys
	with open(privkeypath, 'rb') as privatefile, open(pubkeypath, 'rb') as publicfile:
		privkey = privatefile.read()
		pubkey = publicfile.read()

	privkey = RSA.importKey(privkey)
	pubkey = RSA.importKey(pubkey)

	#create the server socket
	serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	#bind the socket
	serversocket.bind(('127.0.0.1', PROBEPORT))
	serversocket.listen(5)

	running = True
	while running:
		#accept connections from outside
		(clientsocket, address) = serversocket.accept()
		#print("[+] Connection received.")
		Thread(target=handler, args=(clientsocket,)).start()



def handler(clientsocket):
	# Generate an AES cypher
	aeskey = Random.new().read(32) # AES key with random 256 bits key
	iv = Random.new().read(AES.block_size) # 128 bits iv (random)
	aesCypher = AES.new(aeskey, AES.MODE_CBC, iv)

	# Phase 1 : Probe send its identity
	identity = clientsocket.recv(1).decode() # identity of the probe
	#print("[+] Identity received: %s" % identity)

	probPublicKey = getProbePublicKey(identity) # probe public key

	# Phase 2 : Send the encrypted AES key to the probe
	encryptedAESKey, = probPublicKey.encrypt(aeskey,'None')
	clientsocket.send(encryptedAESKey)

	# Phase 3 : Send the encrypted IV to the probe
	encryptedIV, = probPublicKey.encrypt(iv,'None') # encrypt the IV with the probe public key
	clientsocket.send(encryptedIV)

	BS = 16
	pad = lambda s: s + (BS - (len(s) % BS)) * chr(BS - (len(s) % BS))
	unpad = lambda s : s[:-ord(s[len(s)-1:])]
	#print("[*] test string: %s" % (''.join( [ "%02X " % ord(x) for x in pad("test") ] )))
	#print("[*] test encryption: %s" % (''.join( [ "%02X " % x for x in aesCypher.encrypt(pad("test")) ] )))
	
	# Phase 4 : Data Transmission
	aesCypher = AES.new(aeskey, AES.MODE_CBC, iv) # Need to regenerate the cipher to decrypt	
	data = clientsocket.recv(MAX_DATA_RECEIVED)
	print("[*] Data received (%s): %s" % (len(data),''.join( [ "%02X " % x for x in data ] )))
	decryptedData = unpad(aesCypher.decrypt(data))
	print("[*] Data decripted (%s): %s" % (len(decryptedData),''.join( [ "%s" % chr(x) for x in decryptedData ] )))
	
	data = clientsocket.recv(MAX_DATA_RECEIVED)
	# Phase 5 : Integrity check
	
	print("[*] SHA256 Hash (%s): %s" % (len(data),''.join( [ "%02X " % x for x in data ] )))
	#print("[*] Cyphered IV sent (%s): %s" % (len(encryptedIV),''.join( [ "%02X " % x for x in cypherIV ] )))
	
	#answer = clientsocket.recv(32)
	clientsocket.close()
	result = ""

def getProbePublicKey(identity):
	with open(PROBEKEY, 'rb') as publicfile:
		probekey = publicfile.read()
	return RSA.importKey(probekey)




if __name__ == '__main__':
	step1()