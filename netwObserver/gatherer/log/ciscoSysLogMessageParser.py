import sys
from bs4 import BeautifulSoup

def parser(path):
	messagesMeanings = {}
	facilityCode = {}


	log = {}

	soup = BeautifulSoup(open(path))
	"""
	## Mnemo meanings
	for element in soup.find_all('span'):
		if 'class' in element.attrs and 'pEM_ErrMsg' in element['class']:
			tmp = element.get_text().find("%")
			tmp = element.get_text()[tmp:].split()

			code = tmp[0][1:-1].split('-')
			if code[0] not in messagesMeanings:
				messagesMeanings[code[0]] = {}
			messagesMeanings[code[0]][code[2]] = ' '.join(tmp[1:])

	"""
	## Facilities Meanings
	for element in soup.find_all(attrs={"class":"pB1_Body1"}):
		content = element.get_text()
		fac = content[content.find("(")+1:content.rfind(")")]
		facilityCode[fac] = ' '.join(content.split()[3:])
		print("%s: %s" % (fac,facilityCode[fac]))


	
	## mnemo
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

	print("%s\n\n%s"%(messagesMeanings,facilityCode))


if __name__ == '__main__':
	if len(sys.argv) > 1:
		parser(sys.argv[1])
	else:
		print('[-] Missing input file.')