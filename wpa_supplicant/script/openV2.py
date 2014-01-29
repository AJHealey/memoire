#!/usr/bin/env python

import telnetlib
import paramiko
import netifaces
import socket
import getpass
import sys
import cmd
import time
import platform
import os
import string
import signal



class openWRT(cmd.Cmd):

	def __init__(self):
		cmd.Cmd.__init__(self)
		self.prompt = '> '
		self.password = ''
		self.ip_addr = ''
		self.ssh_client = []
		self.channel = "7"
		self.routeur_mac = "a0:f3:c1:36:87:c6"
		self.ssid = "Montoise"
		self.bssid = "00:23:54:b5:c4:58"
		self.key = "Bf3-aZ47"
		self.encryption = "psk2"


	""" Resets the router to default firmware """
	def do_reset(self, args):
		self.ip_addr = "192.168.1.1"
		signal.signal(signal.SIGALRM, self.signalHandler)
		signal.alarm(6)
		try:
			tn = telnetlib.Telnet(self.ip_addr)
			tn.write("mtd -r erase rootfs_data\n")
			tn.read_all()
			tn.close()
		except Exception, msg:
			print 'Rebooting...'
			time.sleep(35)
			self.prompt = '> '


	""" Initialize the root password for the first time and make ssh connection available """
	def do_init(self, args):
		passwords = lambda : (getpass.getpass(), getpass.getpass('Retype password: '))
		p1, p2 = passwords()
		while p1 != p2 or p1 == '' or p2 == '':
			if p1 != p2:
				print 'Passwords do not match. Try again'
				p1, p2 = passwords()
			else:
				print 'Password must be at least 4 characters. Try again'
				p1, p2 = passwords()
		self.password = p1
		self.ip_addr = "192.168.1.1"

		try:
			tn = telnetlib.Telnet(self.ip_addr)
		except socket.error:
			print 'Network unreachable. Try again.'
			return
		finally:
			tn.write("passwd\n")
			tn.read_until("Changing password for root")
			tn.read_until("New password:")
			tn.write(p1 + "\n")
			tn.read_until("Retype password:")
			tn.write(p1 + "\n")
			tn.write("exit\n")
			tn.read_all()
			tn.close()
			time.sleep(2)
			self.connectToHost()

	""" Changes the router IP address """
	def do_changeIP(self, args):
		newAddr = "192.168.2.1"
		if args:
			if len(args.split('.')) != 4:
				print 'Usage: changeIP <IP Address>'
				return
			newAddr = args
		if not self.ssh_client:
			self.connectToHost()
		self.ip_addr = newAddr
		for host in self.ssh_client:
			host.exec_command("uci set network.lan.ipaddr="+self.ip_addr)
			host.exec_command("uci commit")
			host.exec_command("reboot")
			self.close()
		print 'Rebooting...'
		time.sleep(30)
		self.prompt = '['+self.ip_addr+'] > '


	""" Connects the router to the specified wireless network """
	def do_connect(self, args):
		if not self.ssh_client:
			self.connectToHost()
		for host in self.ssh_client:
			host.exec_command("uci set wireless.radio0.disabled=0")
			host.exec_command("uci set wireless.radio0.channel="+self.channel)
			host.exec_command("uci set wireless.radio0.macaddr="+self.routeur_mac)
			host.exec_command("uci set wireless.@wifi-iface[0].network=wwan")
			host.exec_command("uci set wireless.@wifi-iface[0].ssid="+self.ssid)
			host.exec_command("uci set wireless.@wifi-iface[0].bssid="+self.bssid)
			host.exec_command("uci set wireless.@wifi-iface[0].mode=sta")
			host.exec_command("uci set wireless.@wifi-iface[0].key="+self.key)
			host.exec_command("uci set wireless.@wifi-iface[0].encryption="+self.encryption)
			host.exec_command("uci set network.wwan=interface")
			host.exec_command("uci set network.wwan.proto=dhcp")
			host.exec_command("uci commit wireless")
			host.exec_command("uci commit network")
			host.exec_command("/etc/init.d/network restart")
			host.exec_command("wifi up")
			print 'Restarting network...'
			self.close()
			time.sleep(20)
			print 'Installing missing packages...'
			self.installPackages()
			print 'Uploading chain RADIUS certificate...'
			self.uploadCertificate()
			self.prompt = '['+self.ip_addr+'] > '
			

	""" Clears the terminal screen """
	def do_clear(self, args):
		os.system('clear')

	def do_transfer(self, args):
		self.uploadCertificate()


	""" Displays available commands for the user """
	def do_help(self, args):
		print '===HELP====================================================='
		print ' reset : Reset the routeur to initial openWRT firmware'
		print ' init : Initialize the router with root password for the'
		print '        the first time'
		print ' changeIP <IP Address>: Change router IP address to choosen'
		print ' one. If none specified, default [192.168.2.1] is used.'
		print ' connect: Connect to network'
		print ' clear : Clear screen'
		print ' help : Get allowed commands'
		print ' exit : Exit the program' 
		print '------------------------------------------------------------'


	""" Exits script """
	def do_exit(self, args):
		self.close()
		sys.exit()


	""" Installs missing packages """
	def installPackages(self):
		if not self.ssh_client:
			self.connectToHost()
		for host in self.ssh_client:
			channel = host.get_transport().open_session()
			channel.get_pty()
			f = channel.makefile()
			channel.exec_command('opkg update')
			f.read()

			channel = host.get_transport().open_session()
			channel.get_pty()
			g = channel.makefile()
			channel.exec_command('opkg install openssh-sftp-server')
			g.read()
			

	""" Uploads chain RADIUS certificate to router wpa_supplicant folder """
	def uploadCertificate(self):
		try:
			with open('chain-radius.pem'):
				local = 'chain-radius.pem'
				remote = '/var/run/wpa_supplicant-wlan0/chain-radius.pem'
				if not self.ssh_client:
					self.connectToHost()
				if not self.ip_addr:
					self.getIPADDR()
				try:
					transport = paramiko.Transport((self.ip_addr, 22))
					transport.connect(username="root", password=self.password)
					sftp = paramiko.SFTPClient.from_transport(transport)
					sftp.put(local, remote)
					sftp.close()
				finally:
					transport.close()
		except IOError:
			print 'Error. File <chain-radius.pem> missing.'
			return
	

	""" Creates a SSH client """
	def connectToHost(self):
		client = paramiko.SSHClient()
		client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		if not self.ip_addr:
			self.getIPADDR()
		if not self.password:
			self.password = getpass.getpass()
		try :
			client.connect(self.ip_addr, 22, username="root", password=self.password)
		except socket.error: 
			print "Error. Reset your router and try again."
			return
		finally:
			self.ssh_client.append(client)
			self.prompt = '['+self.ip_addr+'] > '


	""" Closes a SSH connection with router """
	def close(self):
		for host in self.ssh_client:
			host.close()
		self.ssh_client = []
	

	""" Returns the router IP address """
	def getIPADDR(self):
		if sys.platform.startswith('linux'):
			ip = netifaces.ifaddresses("eth0")[netifaces.AF_INET][0]["addr"]
		else: 
			ip = netifaces.ifaddresses("en0")[netifaces.AF_INET][0]["addr"]
		ip_addr = ip.split('.')
		ip_addr[3] = '1'
		self.ip_addr = string.join(ip_addr, ".")


	""" Displays intial information to the user """
	def displayInfo(self):
		print '===WELCOME TO THE OPENWRT SCRIPT HANDLER==================='
		print ' - Enter \'help\' for a list of built-in commands'
		print ' - If you want to reset the router first power it up and'
		print '   track the SYS light. When it starts to blink press and'
		print '   hold the QSS button till SYS light starts to blink faster'
		print '   then type \'reset\''
		print ' - paramiko module has to be installed for SSH connections.'
		print ' - netifaces module has to be installed for IP management.'
		print '-----------------------------------------------------------'


	""" Signal handler routine """
	def signalHandler(self, signum, frame): 
		raise Exception("Timed out !")

if __name__ == '__main__':
	openWRT().displayInfo()
	openWRT().cmdloop()
