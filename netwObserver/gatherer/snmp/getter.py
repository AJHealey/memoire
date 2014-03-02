from pysnmp.entity.rfc3413.oneliner import cmdgen


wism1IP = ['192.168.251.177', '192.168.251.178', '192.168.251.181', '192.168.251.182']
wism2IP = ['192.168.251.169', '192.168.251.170']

cmdGen = cmdgen.CommandGenerator()

def walker(ip):
    errorIndication, errorStatus, errorIndex, varBindTable = cmdGen.nextCmd(
        cmdgen.CommunityData('snmpstudentINGI'),
        cmdgen.UdpTransportTarget((ip, 161)),
        '1.3.6.1.4.1.14179',
        lookupNames=True, lookupValues=True
    )

    if errorIndication:
        print(errorIndication)
    else:
        if errorStatus:
            print('%s at %s' % (
                errorStatus.prettyPrint(),
                errorIndex and varBindTable[-1][int(errorIndex)-1] or '?'
                )
            )
        else:
            for varBindTableRow in varBindTable:
                for name, val in varBindTableRow:
                    print('%s = %s' % (name.prettyPrint(), val.prettyPrint()))



if __name__ == '__main__':
    for ip in wism1IP:
        print(ip + ':\n')
        walker(ip)
        print('\n------------------------\n')