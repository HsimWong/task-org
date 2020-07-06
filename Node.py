import configparser
import os
import json

import utils 
import socket
from getmac import get_mac_address as gma 


NODE_SERV_PORT = 23336
DNS_SERVER_IP = gma()
DNS_SERVER_PORT = 23333

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
        
    def __run(self):
        self.__register()
        
    def __ifImStillMaster(self):
        pass 
            
    def __register(self):
        masterInfo = self.__checkMasterInfo()
        regisInfo = {
            'type':'register',
            'params': {
                'mac': self.__mac,
                'IPAddress': self.__ip,
                'role': 'slave' if masterInfo['exist'] else 'master'
            }
        }
        regisResult = self.__send(json.dumps(regisInfo))
        if regisResult['result']:
            self.__nodename = regisResult['nodename']
            self.__role = regisInfo['params']['role']
            return True
        else:
            raise Exception("Error occurs when registering")
            
        
    def __checkMasterInfo(self):
        return json.loads(self.__send(json.dumps({
            'type':'checkMaster',
            'params': None 
        })))
        
            
            
    def __send(self, msg):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((DNS_SERVER_IP, DNS_SERVER_PORT))
        s.sendall(msg.encode())
        msg = s.recv(1024).decode()
        s.close()
        return msg
        
    def __readResources(self):
        conf = configparser.ConfigParser()
        conf.read('./node.conf')
        return ""
    
    