import socket 
import os
import json 
import sys
import utils
import threading 
import logging
import utils
from getmac import get_mac_address as gma 


'''
Following static variables will be
re-arranged to an external file to 
avoid redundancy of codes.
'''

DOMAIN_SUFFIX = '.csu.ac.cn'
HOST_CONF_FILE = '/etc/dnsmasq.d/hosts.conf'
DNS_RQ_PORT = 23333

logging.basicConfig(datefmt='%d-%b-%y %H:%M:%S',
    format='[%(asctime)s] %(levelname)s DNSServer: %(message)s',
    level=logging.DEBUG)

logger = logging.getLogger('DNSServer')

class DNSServer(object):
    def __init__(self):
        # __members = {'domainName': member}
        self.__members = {}#'master'+DOMAIN_SUFFIX: None}
        self.__offlineMembers = {} # {'mac': member}
        self.__master = None
        self.__nextMaster = None  
        self.__provision()
        dealers = {
            'register': self.__registerNode,
            'updateMaster': self.__updateMasterDomain,
            'checkMaster': self.__checkMaster,
            'syncMembers': self.__syncMembers
        }
        utils.recv(("0.0.0.0", DNS_RQ_PORT), dealers, logger)

        # DNS Service running in the background, started
        # with `systemctl start dnsmasq`
        

    def __provision(self):
        logger.info("start provisioning")
        if not os.geteuid() == 0:
            logger.error("This script must be"\
                + "executed under super user")
            sys.exit(1)
        os.system('fuser -k 53/tcp')
        os.system('fuser -k 23333/tcp')
        os.system('fuser -k 23333/udp')
        os.system('systemctl start dnsmasq')
        os.system('rm %s && touch %s'%\
            (HOST_CONF_FILE, HOST_CONF_FILE))

    def __registerNode(self, params):
        '''Note: term `domainName` here refers to the 
        name that identifies each node, by which it means
        that even nodes with specific intention also has
        got one, i.e. master node has two domainName(s)
        1. master.DOMAIN_SUFFIX;
        2. node(i).DOMAIN_SUFFIX
        '''
        mac, role, IPAddress = params['mac'],\
            params['role'], params['IPAddress']
        # Member construction
        member = {
            'ip': IPAddress,
            'mac': mac,
            'status': 'online',
            'role':'Slave', 
            'domainName':'node' \
                + str(len(self.__members)) + (DOMAIN_SUFFIX)
        }
        record = 'address=/%s/%s\n'%(member['domainName'], IPAddress)
        with open(HOST_CONF_FILE, 'a+') as dnsConfFile:
            dnsConfFile.write(record)
            if role == 'slave':
                self.__members.update({member['domainName']: member})
            elif role == 'master':
                masterDom = 'master' + DOMAIN_SUFFIX
                self.__members.update({masterDom: member})
                self.__master = member
                masterAddRec = 'address=/%s/%s\n'%(masterDom, \
                    IPAddress)
                dnsConfFile.write(masterAddRec)
            else:
                raise Exception("Role tag error")
        os.system('systemctl restart dnsmasq')
        return {
            'result': True,
            'nodename': member['domainName']
        }

    def __syncMembers(self, params):
        return json.dumps(self.__members)
        

    def __DNSList(self):
        # telling other nodes other options when 
        # this server is down
        pass

    

    def __updateMasterDomain(self, params):
        # mark master node as offline
        self.__members['master'+(DOMAIN_SUFFIX)].update({
            'status':'offline',
            'role':'none',
            'domainName':'offline'+(\
                str(len(self.__offlineMembers)) + DOMAIN_SUFFIX)
        })
        domainName = ""
        # choose a node as master candidate
        for domain in self.__members.keys():
            if self.__members[domain]['status'] == 'online' and \
                not self.__members[domain]['ip'] == utils.getIP():
                domainName = domain
        
        # Reassigning master domainName to new node
        self.__members['master'+(DOMAIN_SUFFIX)] \
            = self.__members[domainName]
        os.system(r"sed -i 's/master.*$/master.csu.ac.cn\/%s/' %s"\
            %(self.__members[domainName]['ip'], \
                HOST_CONF_FILE))
        self.__master = self.__members[domainName]
        # restarting dnsmasq service
        os.system('systemctl restart dnsmasq')
        return True
    
    def __checkMaster(self, param = None):
        return json.dumps({
            'exist': ('master'+DOMAIN_SUFFIX 
            in self.__members.keys())
        })
        

 
            
if __name__ == "__main__":
    dnsserver = DNSServer()
    
    
    # 82693332