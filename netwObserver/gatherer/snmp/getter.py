from pysnmp.entity.rfc3413.oneliner import cmdgen
 

wism = ['192.168.251.170']


def getApMacAdresses (ip, port=161, community='snmpstudentINGI'):
    cmdGen = cmdgen.CommandGenerator()

    errorIndication, errorStatus, errorIndex, varBinds = cmdGen.nextCmd(
    cmdgen.CommunityData(community),
    cmdgen.UdpTransportTarget((ip, port)),
    '1.3.6.1.4.1.14179.2.1.4.1.1')

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
            for name, val in varBinds:
                result[name.prettyPrint()] = val.prettyPrint()
            return result




if __name__ == '__main__':
    try:
        print(str(getApMacAdresses(wism[0])))
    except Exception as e:
        print(e)


        
# snmpwalk -v2c -c snmpstudentINGI -ObentU 192.168.15.202 1.3.6.1.4.1.14179
