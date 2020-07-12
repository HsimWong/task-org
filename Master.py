import threading
from threading import Semaphore
from threading import Thread
import socket
import utils
import json
import time
 
MASTER_PORT = 23335
DNS_PORT = 23333
DNS_HOST = '127.0.0.1'

class Master(object):
    '''
    
    if status == False:
        ALWAYS check with master
            if next is me:
                sync
            else: 
                wait
    elif status == true:
        change online to true
        select an inheritant
        ALWAYS recv register rq from other nodes
        ALWAYS sync with inheritant
        ALWAYS check deploy rq
            for node in members:
                if there is resources:
                    allocate the rq to the node
                else:
                    continue        
    '''
    def __init__(self):
        self.__status = False
        self.__online = False
        self.__members = {}
        self.__tasks = []
        self.__ifNextMaster = False 
        self.__mastServSema = Semaphore(0)
        self.__dealers = {
            'syncrq': self.__syncRequest,
            'syncinfo': self.__syncInfo,
            'userrq': self.__userRequest
        }
        self.__run()    
    
    def __run(self):
        tMemberSync = Thread(self.__fetchMembersFromDNS)
        tMemberSync.join()
        connection = ('127.0.0.1', MASTER_PORT)
        tRqListen = Thread(utils.recv(connection, self.__dealers))
        tRqListen.join()
        tRecvMasterInfo = Thread(self.__syncInfo)
        tRecvMasterInfo.join()
        
    
        
    def __fetchMembersFromDNS(self):
        target = (DNS_HOST, DNS_PORT)
        while True:    
            self.__members = json.loads(
                utils.send(target, json.dumps({
                    'type': 'syncMembers',
                    'params': None
                }))
            )
            time.sleep(10)   

    def __syncRequest(self, params):
        self.__ifNextMaster = True 
        return json.dumps({
            'prepared': True 
        })
        
    def __syncInfo(self, params):
        self.__members, self.__tasks
    
    def __userRequest(self, params):
        pass 
        
    def __masterInfoSyncSource(self):
        pass 
    
    def __masterInfoSyncTarget(self):
        pass 
        
    def __getBackUp(self):
        for hostname in self.__members.keys():
            if self.__members[hostname]['ip'] == DNS_HOST\
                or self.__members[hostname]['role'] == "master":
                continue
            else:
                return hostname
    
    def enable(self):
        if not self.__status:
            self.__status = True
            self.__mastServSema.release() 
            self.__ifNextMaster = False
            for hostname in self.__members.keys():
                
        else:
            raise Exception("Master is running")
    
    def disable(self):
        if self.__status:
            self.__status = False
            self.__mastServSema.acquire() 
        else:
            raise Exception("Master already shutdown")
        
if __name__ == "__main__":
    master = Master()
    
    