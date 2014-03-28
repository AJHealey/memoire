import time

from datetime import timedelta

from django.utils import timezone
from django.conf import settings
from django.db import IntegrityError

from pysnmp.entity.rfc3413.oneliner import cmdgen
from gatherer.models import AccessPoint, MobileStation, OperationalError, CurrentTask

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


## Access Points Requests
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

def getAPIfLoadRxUtilization(ip, port=161, community='snmpstudentINGI', ap=''):
    """ This is the percentage of time the Airespace AP
        receiver is busy operating on packets. It is a number 
        from 0-100 representing a load from 0 to 1.) 
    """
    result = {}
    for index, rx in walker(ip,'1.3.6.1.4.1.14179.2.2.13.1.1' + ap, port=port, community=community).items():
        if index[:-2] not in result:
            result[index[:-2]] = 0

        result[index[:-2]] += (float(rx)/2)

    return result

def getAPIfLoadTxUtilization(ip, port=161, community='snmpstudentINGI', ap=''):
    """ This is the percentage of time the Airespace AP
        transmitter is busy operating on packets. It is a number 
        from 0-100 representing a load from 0 to 1.) 
    """
    result = {}
    for index, tx in walker(ip,'1.3.6.1.4.1.14179.2.2.13.1.2' + ap, port=port, community=community).items():
        if index[:-2] not in result:
            result[index[:-2]] = 0

        result[index[:-2]] += (float(tx)/2)

    return result

def getAPIfLoadChannelUtilization(ip, port=161, community='snmpstudentINGI', ap=''):
    """ Channel Utilization """
    result = {}
    for index, ch in walker(ip,'1.3.6.1.4.1.14179.2.2.13.1.3' + ap, port=port, community=community).items():
        if index[:-2] not in result:
            result[index[:-2]] = 0

        result[index[:-2]] += (float(ch)/2)

    return result

def getAPIfLoadNumOfClients(ip, port=161, community='snmpstudentINGI', ap=''):
    """ This is the number of clients attached to this Airespace
        AP at the last measurement interval(This comes from 
        APF)
    """
    result = {}
    for index, noUsers in walker(ip,'1.3.6.1.4.1.14179.2.2.13.1.4' + ap, port=port, community=community).items():
        if index[:-2] not in result:
            result[index[:-2]] = 0

        result[index[:-2]] += int(noUsers)

    return result

def getAPIfPoorSNRClients(ip, port=161, community='snmpstudentINGI', ap=''):
    """ This is the number of clients attached to this Airespace
        AP at the last measurement interval(This comes from 
        APF)
    """
    result = {}
    for index, noUsers in walker(ip,'1.3.6.1.4.1.14179.2.2.13.1.24' + ap, port=port, community=community).items():
        if index[:-2] not in result:
            result[index[:-2]] = 0

        result[index[:-2]] += int(noUsers)

    return result



## Mobile Stations Requests
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

def getMobileStationAPMacAddress(ip, port=161, community='snmpstudentINGI'):
    """ SSID advertised by the mobile station """
    return walker(ip,'1.3.6.1.4.1.14179.2.1.4.1.4', port=port, community=community)




def getAllAP():
    ''' Cross reference all the information on the Access Point and update the database '''

    result = {}
    try:
        # Get All Access Points (Mac Address)
        tmp = getApMacAddresses(ip=wism[0])
        for index, mac in tmp.items():
            try:
                result[index], created = AccessPoint.objects.get_or_create(macAddress=parseMacAdresse(mac))
            except IntegrityError:
                result[index] = MobileStation.objects.get(macAddress=mac)
            finally:
                result[index].index = "." + index

        
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
        OperationalError(date=timezone.localtime(timezone.now()), source='snmpAPDaemon', error=str(e)).save()

    finally:
        for ap in result.values():
            ap.touch()
            ap.save()


def getAllMS():
    ''' Cross reference all the information on the Mobile Station and update the database '''
    result = {}
    try:
        # Get All Access Points (Mac Address)
        tmp = getMobileStationMacAddresses(ip=wism[0])
        for index, mac in tmp.items():
            mac = parseMacAdresse(mac)
            if not mac == '':
                # Handle possible race condition (get_or_create not thread safe)
                try:
                    result[index], created = MobileStation.objects.get_or_create(macAddress=mac)
                except IntegrityError:
                    result[index] = MobileStation.objects.get(macAddress=mac)

                finally:
                    result[index].index = "." + index

       
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

        '''
        # Link to AP
        tmp = getMobileStationAPMacAddress(ip=wism[0])
        for index, apMac in tmp.items():
            if index in result:
                apMac = parseMacAdresse(apMac)
                if not apMac == '': 
                    result[index].ap, created = AccessPoint.objects.get_or_create(macAddress=apMac)
                    '''

    except Exception as e:
        OperationalError(date=timezone.localtime(timezone.now()), source='snmpMSDaemon', error=str(e)).save()

    finally:
        for ms in result.values():
            ms.touch()
            ms.save()


def snmpAPDaemon(laps=timedelta(hours=1)):
    ''' Background task gathering information on Access Point '''
    task, _ = CurrentTask.objects.get_or_create(name="apdaemon")
    task.touch()
    while True:
        try:
            getAllAP()
            task.touch()
            time.sleep(laps.total_seconds())
        except:
            OperationalError(date=timezone.localtime(timezone.now()), source='snmpAPDaemon', error='Laps failed').save()
            time.sleep(10*laps.total_seconds())


def snmpMSDaemon(laps=timedelta(minutes=30)):
    ''' Background task gathering information on Mobile Station 

        Argument:
        laps -- duration between update. Instance of timedelta
    '''
    task, _ = CurrentTask.objects.get_or_create(name="msdaemon")
    task.touch()
    time.sleep(30)
    while True:
        try:
            getAllMS()
            task.touch()
            time.sleep(laps.total_seconds())
        except:
            OperationalError(date=timezone.localtime(timezone.now()), source='snmpMSDaemon', error='Laps failed').save()
            time.sleep(10*laps.total_seconds())



###### Auxiliary Methods #######
def parseMacAdresse(macString):
    ''' Parse a mac address in hexadecimal into canonical form '''
    result = macString

    if result.startswith('0x'):
        result = result[2:]

    if len(result) == 12:
        return result[0:2] + ":" + result[2:4] + ":" + result[4:6] + ":" + result[6:8] + ":" + result[8:10] + ":" +result[10:]
    else:
        OperationalError(date=timezone.localtime(timezone.now()), source='snmp macAddress parsing', error=macString).save()
        return ''



#####
if __name__ == '__main__':
    import sys
    for ap in getMobileStationAPMacAddress(wism[0]):
        print(str(ap))
       
