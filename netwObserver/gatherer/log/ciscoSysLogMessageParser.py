import sys
from bs4 import BeautifulSoup
import json
import urllib.request

URL = "http://www.cisco.com/c/en/us/td/docs/wireless/controller/message/guide/controller_smg/msgs%s.html"


def getFacilitiesMeaning(html):
	soup = BeautifulSoup(html)
	facilityCode = {}

	## Facilities Meanings
	for element in soup.find_all(attrs={"class":"pB1_Body1"}):
		content = element.get_text()
		fac = content[content.find("(")+1:content.rfind(")")]
		meaning = ' '.join(content.split()[3:]).title()
		meaning = meaning[:meaning.find("(")].strip()
		if len(fac) < 7 and meaning != "":
			facilityCode[fac] = ("%s (%s)") % (fac,meaning)

	return facilityCode

def getMessageMeaning(html):
	soup = BeautifulSoup(html)
	messagesMeanings = {}

	for element in soup.find_all(attrs={"class":"pEM_ErrMsg"}):
		errorMessage = element.get_text().strip()
		start = element.get_text().find("%")
		errorMessage = errorMessage[start:].split()

		# Stock error message
		code = errorMessage[0][1:-1].split('-')
		if code[0] not in messagesMeanings:
			messagesMeanings[code[0]] = {}
		messagesMeanings[code[0]][code[2]] = {}
		messagesMeanings[code[0]][code[2]]["error"] = ' '.join(errorMessage[1:])

		# Stock Explanation message
		explanation = element.parent.find_next_sibling(attrs={"class":"pEE_ErrExp"}).get_text().split()
		messagesMeanings[code[0]][code[2]]["explanation"] = ' '.join(explanation[1:])

		# Stock Recommanded Action message
		recommendedAction = element.parent.find_next_sibling(attrs={"class":"pEA_ErrAct"}).get_text().split()
		recommendedAction = ' '.join(recommendedAction[1:])
		if "http://tools.cisco.com/Support/BugToolKit/" in recommendedAction:
			recommendedAction = "Use Bug Toolkit at http://tools.cisco.com/Support/BugToolKit/"
		messagesMeanings[code[0]][code[2]]["action"] = recommendedAction


def parser(path):
	
	
	facilityCode = {}
	try:
		facilityCode = json.load(open("facilitiesDico.json",'r'))
	except:
		pass

	for i in range(10):
		html = urllib.request.urlopen(URL%(i+1)).read()
		fac = getFacilitiesMeaning(html)
		facilityCode.update(fac)

	json.dump( facilityCode,open("facilitiesDico.json",'w'))

	for (fac,m) in sorted(facilityCode.items()):
		print("%s : %s" % (fac,m))






if __name__ == '__main__':
	if len(sys.argv) > 1:
		parser(sys.argv[1])
	else:
		print('[-] Missing input file.')