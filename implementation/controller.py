import sys
import threading
import log.logParser
from cmdLineUI import *
import time
import traceback

def singleton(classe_definie):
	instances = {}
	def get_instance():
		if (classe_definie not in instances):
			instances[classe_definie] = classe_definie()
			return instances[classe_definie]
	return get_instance


@singleton
class Controller:
	'''Main class'''
	def __init__(self, *args, **kwargs):
		self.running = True
		self.frequency = 5

		self.users = []
		self.devices = None

		self.lock = threading.RLock()
		self._input = []
		self.ui = cmdLineGUI(self)

		self.mainLoop()
		



	def mainLoop(self):
		while(self.running):
			try:
				cmd = self.popCmd()
				# Dispatch the command
				if cmd != None:
					cmd = cmd.split()
					if len(cmd) == 0:
						pass
					elif cmd[0].lower() == 'show':
						self.show(cmd[1:])
					elif cmd[0].lower() == 'log':
						pass
					elif cmd[0].lower() == 'kill':
						break
					elif cmd[0].lower() == 'help':
						# Todo Print help page
						pass
					else:
						self.ui.addEvent(" ".join(cmd) + ' : cmd unknown')
				# Check if the UI is still alive
				if not self.ui.uiThread.isAlive() and self.running:
					#UI down
					print('Restart UI in 5 secondes')
					time.sleep(5)
					self.ui = cmdLineGUI(self)
				
				# Regulate the server activity
				time.sleep(1/self.frequency)

			except Exception as e:
				exc_type, exc_value, exc_traceback = sys.exc_info()
				self.ui.setStatus('Error in controller execution.')
				self.ui.addEvent(repr(traceback.format_tb(exc_traceback)))




	def show(self, args):
		'''Send information to be shown to the UI'''
		if len(args) < 1:
			self.ui.addEvent('show : specify what to show')
		elif args[0] == 'users':
			self.ui.addEvent(str(len(self.users)) + ' users' + (':' if len(self.users) else ""))
			for u in self.users:
				self.ui.addEvent(repr(u))
		else:
			self.ui.addEvent('show : ' + str(args) + ' bad arguments')


	def logAnalyse(self, path):
		"""Analyse a log file"""
		results = parser(path)

	def newCmd(self,cmd):
		'''Send a new command to the controller'''
		with self.lock:
			self._input = self._input + [cmd]

	def popCmd(self):
		'''Pop the first command sent to the controller'''
		if len(self._input):
			self.lock.acquire()
			tmp = self._input[0]
			self._input = self._input[1:]
			self.lock.release()
			return tmp
		return None

	def exit(self):
		'''Stop the controller'''
		self.running = False

		



if __name__ == '__main__':
	Controller()
