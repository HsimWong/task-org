import socket 
import os
import json 
import sys
import utils
import threading 
import logging
from getmac import get_mac_address as gma 

DOMAIN_SUFFIX = '.csu.ac.cn'
HOST_CONF_FILE = '/etc/dnsmasq.d/hosts.conf'
DNS_RQ_PORT = 23333



class DNSServer(object):
    def __init__(self):
        self.__members = {} # {'domainName': member}
        self.__offlineMembers = {} # {'mac': member}
        self.__master = None
        self.__provision()
        self.__masterUpdateRqListener()

        # DNS Service running in the background, started
        # with `systemctl start dnsmasq`
        

    def __provision(self):
        if not os.geteuid() == 0:
            sys.exit("This script must be executed under super user")
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
        return True

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
        os.system("sed -i 's/master.*$/master.csu.ac.cn\/%s/' %s"\
            %(self.__members[domainName]['ip'], \
                HOST_CONF_FILE))
        self.__master = self.__members[domainName]
        # restarting dnsmasq service
        os.system('systemctl restart dnsmasq')
        return True

    def __masterUpdateRqListener(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("127.0.0.1", DNS_RQ_PORT))

        s.listen()
        dealers = {
            'register': self.__registerNode,
            'updateMaster': self.__updateMasterDomain
        }
        while True:
            print("Listening for requests")
            conn, addr = s.accept()
            msgRaw = conn.recv(0x400).decode()
            if not msgRaw:
                continue
            else:
                msgParsed = json.loads(msgRaw)
                print(msgParsed)
                returnMsg = dealers[msgParsed['type']](msgParsed['params'])
                conn.sendall(str(returnMsg).encode())
        s.close()
            
if __name__ == "__main__":
    dnsserver = DNSServer()
    