import socket

from threading import Thread
from time import sleep

MAX_DATA_RECEIVED = 2000
PROBEPORT = 3874

def responder():
	#create the server socket
	serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	#bind the socket
	serversocket.bind(('0.0.0.0', PROBEPORT))
	serversocket.listen(5)

	running = True
	while running:
		#accept connections from outside
		(clientsocket, address) = serversocket.accept()
		Thread(target=handler, args=(clientsocket,)).start()



def handler(clientsocket):
	

	#print("[+] Connection established")
	# Phase 1 : Probe send its identity
	identity = int.from_bytes(clientsocket.recv(4),byteorder='little') # identity of the probe
	#print("[+] Identity received: %s" % identity)
	clientsocket.send(b'1')

	## Phase 2 = Data receive
	dataSize = int.from_bytes(clientsocket.recv(4),byteorder='little')
	#print("[*] Size received (%s)" % dataSize)
	clientsocket.send(b'1')

	data = clientsocket.recv(min(dataSize,56))
	while len(data) < dataSize :
		data += clientsocket.recv(dataSize-len(data))

	clientsocket.close()
	print("%s" % data.decode())
	#print("[*] Connection closed.")


if __name__ == '__main__':
	responder()