import json

LOGDB = "./logDB.txt"

class Log:
	def __init__(self,n,m,r,s=''):
		self.name = n
		self.meaning = m
		self.reqAction = r
		self.supplement = s

	def __str__(self):
		return self.name + "\n\tMeaning: " + self.m + 
		"\n\tAction Required: " + self.r + 
		"\n\tAdditional Information: " + self.s



def logInfoLoader(path=LOGDB):
	logDictionary = dict()
	with open(path,'r') as f:

		for line in f:
			tmp = json.loads(line)
			if(tmp['name'] in logDictionary):
				print('[*] ' + tmp['name'] + ' already in the DB. Old value overrided.')
			logDictionary['name'] = tmp

	return logDictionary

def saveLogInfo(logDictionary,path=LOGDB):
	with open(path,'w') as f:
		for key in logDictionary:
			json.dump(logDictionary[key],f)







