import os
import json
import threading
import utils 
import socket
import hashlib 
import logging
from getmac import get_mac_address as gma 
from time import sleep


NODE_SERV_PORT = 23336
MASTER_PORT = 23335
# DNS_SERVER_IP = gma() # needs 2b changes
DNS_SERVER = '47.103.45.126'
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

logging.basicConfig(datefmt='%d-%b-%y %H:%M:%S',
    format='[%(asctime)s] %(levelname)s Node: %(message)s',
    level=logging.DEBUG)
logger = logging.getLogger("Node")

  
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
        # self.__resources = self.__readResources()
        logger.info("Node start initializing")
        self.__ip = utils.getIP()
        self.__mac = gma()
        self.__run()
        self.__role = None
        self.__nodename = None 
        logger.info("Node Initializing finished")
        self.__register()
        self.__master = None
        # self.__run()
        # self.__masterserv = Master.Master()
        # self.__slaveserv = Slave.Slave(self.__nodename)
        
    def __run(self):
        t1 = threading.Thread(target=self.__masterServMonitor,\
            name='masterServMonitor')
        t1.start()
        
        
    def __masterServMonitor(self):
        while True:
            currentMaster = None
            try:
                currentMaster = socket.gethostbyname('master'+ DOMAIN_SUFFIX)
            except:
                currentMaster = None
             
            logger.debug("currentMaster:%s"%currentMaster)
            if self.__ip == currentMaster:
                utils.send(('localhost', MASTER_PORT), json.dumps({
                    'type': 'enable',
                    'params': None 
                })) 
            else:
                utils.send(('localhost', MASTER_PORT), json.dumps({
                    'type': 'disable',
                    'params': None 
                })) 
            sleep(5)
            
    def __register(self):
        logger.info("Start registering")
        masterInfo = (self.__checkMasterInfo())
        logger.debug("masterInfo: %s, type: %s"%(masterInfo, type(masterInfo)))
        regisInfo = {
            'type':'register',
            'params': {
                'mac': self.__mac,
                'IPAddress': self.__ip,
                'role': 'slave' if masterInfo['exist'] 
                    else 'master'
            }
        }
        regisResult = utils.send((DNS_SERVER, DNS_SERVER_PORT),
                                 json.dumps(regisInfo))
        
        logger.info("RegisResult: %s, type: %s"%(regisResult, type(regisResult)))
        
        if regisResult['result']:
            self.__nodename = regisResult['nodename']
            self.__role = regisInfo['params']['role']
            return True
        else:
            raise Exception("Error occurs when registering")
               
    def __checkMasterInfo(self):
        logger.debug("Checking if master exists")
        masterResult = json.loads(utils.send(
            (DNS_SERVER,DNS_SERVER_PORT),
            json.dumps({
                        'type':'checkMaster',
                        'params': None 
            })))
        print(masterResult)
        return masterResult
        
    # def __readResources(self):
    #     conf = configparser.ConfigParser()
    #     conf.read('./node.conf')
        # return ""

if __name__ == '__main__':
    node = Node()
        
    