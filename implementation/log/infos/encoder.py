#!/usr/bin/python3.3

import json
import fileDescriptions
import sys
# GUI
from gi.repository import Gtk as gtk
import string


def updateFacilities(codedict):
	with open(fileDescriptions.FACILITIES, "w+") as f:
		tmp = dict()
		try:
		    f.seek(0)
		    tmp = json.load(f)
		except ValueError:
			pass
		finally:
			f.seek(0)
			tmp.update(codedict)
			json.dump(tmp,f)


def toDict(s):
	result = dict()
	infos = iter([e for e in s.split('\n') if not len(e) == 0 and e[0].isalnum()])
	
	for elmt in infos:
		try:
			value = next(infos)
		except StopIteration:
			break
		else:
			result[elmt] = value
	
    
	return result


def handleClick(widget,text):

	tampon = text.get_buffer() #Obtenir le tampon de la zone de texte
	debut = tampon.get_start_iter() #Obtenir le debut de la zone de texte
	fin = tampon.get_end_iter() #Obtenir la fin de la zone de texte
	tmp = tampon.get_text(debut, fin, True)
	updateFacilities(toDict(tmp))

def main():
	fenetre = gtk.ScrolledWindow()
	fenetre.set_policy(gtk.PolicyType.AUTOMATIC,gtk.PolicyType.AUTOMATIC)
	mainWindow = gtk.Window()
	mainWindow.set_title("Hello World!")
	mainWindow.set_position(gtk.WindowPosition.CENTER)
	mainWindow.connect("destroy", gtk.main_quit)

	myButton = gtk.Button("Save")
	myText = gtk.TextView()

	myButton.connect("clicked", handleClick, myText)


	vBox = gtk.VBox()
	fenetre.add(myText)
	vBox.pack_start(fenetre, True, True, 0)
	vBox.pack_start(myButton, False, False, 0)

	mainWindow.add(vBox)
	mainWindow.show_all()

	gtk.main()


if __name__ == '__main__':
	main()
