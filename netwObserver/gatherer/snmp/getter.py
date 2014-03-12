from pysnmp.entity.rfc3413.oneliner import cmdgen
 

wism = ['192.168.251.170']


def getApMacAdresses (ip, port=161, community='snmpstudentINGI'):
    cmdGen = cmdgen.CommandGenerator()

    errorIndication, errorStatus, errorIndex, varBindTable = cmdGen.nextCmd(
    cmdgen.CommunityData(community),
    cmdgen.UdpTransportTarget((ip, port)),
    '1.3.6.1.4.1.14179.2.2.1.1.3', lookupValues=True)

    if errorIndication:
        raise Exception(str(errorIndication))

    else:
        if errorStatus:
            raise Exception('%s at %s' % (
            errorStatus.prettyPrint(),
            errorIndex and varBinds[int(errorIndex)-1] or '?'
            ))
        else:
            result = {}
            print(len(varBindTable))
            for varBindTableRow in varBindTable:
                for name, val in varBindTableRow:
                    result[name.prettyPrint()] = val.prettyPrint()
            return result


def parseMacAdresse(macString):
    result = macString

    if result.startswith('0x'):
        result = result[2:]

    if len(result) == 12:
        return result[0:2] + ":" + result[2:4] + ":" + result[4:6] + ":" + result[6:8] + ":" + result[8:10] + ":" +result[10:]
    else:
        return ''

if __name__ == '__main__':
    r = getApMacAdresses(wism[0])
    for k in sorted(r):
        print(k + ' : ' + r[k])
    print(str(len(r)))


        
# snmpwalk -v2c -c snmpstudentINGI -ObentU 192.168.15.202 1.3.6.1.4.1.14179
