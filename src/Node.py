import configparser
import os
import json
import threading
import utils 
import socket
import Master
import Slave
import hashlib 
from getmac import get_mac_address as gma 
from time import sleep


NODE_SERV_PORT = 23336
DNS_SERVER_IP = gma() # needs 2b changes
DNS_SERVER_PORT = 23333
DOMAIN_SUFFIX = '.csu.ac.cn'


'''
docker_task = {
    'target': ip (None),
    'cpu': float (none),
    'image' = str (not null),
    'command': str,
    'idHash'
}
'''

class Node(object):
    '''
    Working Procedures:
    1. Read resources from external file
    2. Init Client service and Master Service
    3. Check if master registered
      no: 1)register as master;2)start server
          & client 
      yes: 1)regis as client; 2) only start client
    ALWAYS check is master has changed
        if it's me:
            turn on master
        else: turn off the master
    '''
    
    def __init__(self):
        self.__resources = self.__readResources()
        self.__ip = utils.getIP()
        self.__mac = gma()
        self.__run()
        self.__role = None
        self.__nodename = None 
        self.__register()
        self.__masterserv = Master.Master()
        self.__slaveserv = Slave.Slave(self.__nodename)
        
    def __run(self):
        self.__slaveserv.enable()
        self.__register()
        t1 = threading.Thread(target=self.__masterServMonitor)
        t1.start()
        
        
    def __masterServMonitor(self):
        masterServCtrl = {
            True: self.__masterserv.enable,
            False: self.__masterserv.disable
        }
        while True:
            masterServCtrl[
                self.__ip == \
                socket.gethostbyname('master'\
                + DOMAIN_SUFFIX)
            ]()    
            sleep(5)
            
    def __register(self):
        masterInfo = self.__checkMasterInfo()
        regisInfo = {
            'type':'register',
            'params': {
                'mac': self.__mac,
                'IPAddress': self.__ip,
                'role': 'slave' if masterInfo['exist'] 
                    else 'master'
            }
        }
        regisResult = utils.send((DNS_SERVER_IP, DNS_SERVER_PORT),
                                 json.dumps(regisInfo))
        if regisResult['result']:
            self.__nodename = regisResult['nodename']
            self.__role = regisInfo['params']['role']
            return True
        else:
            raise Exception("Error occurs when registering")
               
    def __checkMasterInfo(self):
        return json.loads(utils.send(
            (DNS_SERVER_IP,DNS_SERVER_PORT),
            json.dumps({
                        'type':'checkMaster',
                        'params': None 
            })))
        
    def __readResources(self):
        conf = configparser.ConfigParser()
        conf.read('./node.conf')
        return ""
    
    