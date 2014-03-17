import time

from django.utils import timezone

from pysnmp.entity.rfc3413.oneliner import cmdgen
from gatherer.models import AccessPoint, MobileStation, OperationalError

wism = ['192.168.251.170']
protocolsCode = {'dot11a' : 'a', 'dot11b' : 'b', 'dot11g' : 'g', 'unknown' : 'u', 'mobile' : 'm', 'dot11n24' : 'n2', 'dot11n5' : 'n5'}

def walker(ip, oib, port=161, community='snmpstudentINGI'):
    cmdGen = cmdgen.CommandGenerator()

    errorIndication, errorStatus, errorIndex, varBindTable = cmdGen.nextCmd(
    cmdgen.CommunityData(community),
    cmdgen.UdpTransportTarget((ip, port)),
    oib, lookupValues=True)

    if errorIndication:
        raise Exception(str(errorIndication))

    else:
        if errorStatus:
            raise Exception('%s at %s' % (
            errorStatus.prettyPrint(),
            errorIndex and varBindTable[int(errorIndex)-1] or '?'
            ))
        else:
            result = {}
            print(len(varBindTable))
            for varBindTableRow in varBindTable:
                for name, val in varBindTableRow:
                    result[name.prettyPrint()[len(oib)+1:]] = val.prettyPrint()
            return result


## Access Points
def getApNames(ip, port=161, community='snmpstudentINGI'):
    """ Name of each Access Point """
    return walker(ip,'1.3.6.1.4.1.14179.2.2.1.1.3', port=port, community=community)

def getApMacAddresses(ip, port=161, community='snmpstudentINGI'):
    """ MAC address of Access Point """
    return walker(ip,'1.3.6.1.4.1.14179.2.2.1.1.1', port=port, community=community)

def getApIPs(ip, port=161, community='snmpstudentINGI'):
    """ IP address of Access Point """
    return walker(ip,'1.3.6.1.4.1.14179.2.2.1.1.19', port=port, community=community)

def getApLocation(ip, port=161, community='snmpstudentINGI'):
    """ Location of the access point (if configured) """
    return walker(ip,'1.3.6.1.4.1.14179.2.2.1.1.4', port=port, community=community)

## Mobile Stations
def getMobileStationMacAddresses(ip, port=161, community='snmpstudentINGI'):
    """ Mac Address of each station connected to an AP """
    return walker(ip,'1.3.6.1.4.1.14179.2.1.4.1.1', port=port, community=community)

def getMobileStationIPs(ip, port=161, community='snmpstudentINGI'):
    """ IP address of each station connected to an AP """
    return walker(ip,'1.3.6.1.4.1.14179.2.1.4.1.2', port=port, community=community)

def getMobileStationProtocol(ip, port=161, community='snmpstudentINGI'):
    """ Protocol used by the station (e.g 802.11a, b, g, n) """
    return walker(ip,'1.3.6.1.4.1.14179.2.1.4.1.25', port=port, community=community)

def getMobileStationSSID(ip, port=161, community='snmpstudentINGI'):
    """ SSID advertised by the mobile station """
    return walker(ip,'1.3.6.1.4.1.14179.2.1.4.1.7', port=port, community=community)

def getAllAP():
    result = {}
    try:
        # Get All Access Points (Mac Address)
        tmp = getApMacAddresses(ip=wism[0])
        for index, mac in tmp.items():
            result[index], created = AccessPoint.objects.get_or_create(macAddress=parseMacAdresse(mac))
        
        # Add names    
        tmp = getApNames(ip=wism[0])
        for index, name in tmp.items():
            if index in result:
                result[index].name = name

        # Add IP
        tmp = getApIPs(ip=wism[0])
        for index, ip in tmp.items():
            if index in result:
                result[index].ip = ip

    except Exception as e:
        OperationalError(date=timezone.now(), source='snmpAPDaemon', error=str(e)).save()

    finally:
        for ap in result.values():
            ap.lastTouched = timezone.now()
            ap.save()

def getAllMS():
    result = {}
    try:
        # Get All Access Points (Mac Address)
        tmp = getMobileStationMacAddresses(ip=wism[0])
        for index, mac in tmp.items():
            mac = parseMacAdresse(mac)
            if not mac == '':
                result[index], created = MobileStation.objects.get_or_create(macAddress=mac)
       
        # Add names    
        tmp = getMobileStationSSID(ip=wism[0])
        for index, ssid in tmp.items():
            if index in result:
                if 'b\'' in ssid:
                    result[index].ssid = ssid[2:-1]
                else:
                    result[index].ssid = ssid


        # Add IP
        tmp = getMobileStationIPs(ip=wism[0])
        for index, ip in tmp.items():
            if index in result:
                result[index].ip = ip

        # Add Protocol
        tmp = getMobileStationProtocol(ip=wism[0])
        for index, proto in tmp.items():
            if index in result:
                result[index].dot11protocol = proto

    except Exception as e:
        OperationalError(date=timezone.now(), source='snmpMSDaemon', error=str(e)).save()

    finally:
        for ms in result.values():
            ms.lastTouched = timezone.now()
            ms.save()


def snmpAPDaemon():
    while True:
        try:
            getAllAP()
            time.sleep(60*60)
        except:
            time.sleep(24*60*60)


def snmpMSDaemon():
    time.sleep(30)
    while True:
        try:
            getAllMS()
            time.sleep(66*60)
        except:
            time.sleep(24*60*60)




###### Auxiliary Methods #######
def parseMacAdresse(macString):
    result = macString

    if result.startswith('0x'):
        result = result[2:]

    if len(result) == 12:
        return result[0:2] + ":" + result[2:4] + ":" + result[4:6] + ":" + result[6:8] + ":" + result[8:10] + ":" +result[10:]
    else:
        OperationalError(date=timezone.now(), source='snmp macAddress parsing', error=macString).save()
        return ''



#####
if __name__ == '__main__':
    import sys
    for ap in getAllAP():
        print(str(ap))
    '''
    result = []
    if len(sys.argv) > 1:
        if sys.argv[1] == 'apname':
            result = getApNames
        elif sys.argv[1] == 'apmac':
            result = getApMacAddresses
        elif sys.argv[1] == 'apip':
            result = getApIPs
        elif sys.argv[1] == 'msmac':
            result = getMobileStationMacAddresses
        elif sys.argv[1] == 'macip':
            result = getMobileStationIPs 
        elif sys.argv[1] == 'macprot':
            result = getMobileStationProtocol
    
    print("[*] Results:")
    for k in sorted(r):
        print("\t" + k + ' : ' + r[k])
    print("-" * 50)
    print(str(len(r)) + " results")
    '''
       
