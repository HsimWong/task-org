import threading
from threading import Semaphore
from threading import Thread
import socket
import utils
import json
import time
import queue

SLAVE_PORT = 23334
MASTER_PORT = 23335
DNS_PORT = 23333
DNS_HOST = '127.0.0.1'
DOMAIN_SUFFIX = '.csu.ac.cn'

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
        self.__unassignedTasks = queue.Queue()
        self.__assignedTasks = queue.Queue()
        self.__ifNextMaster = False 
        self.__nextMaster = None
        self.__mastServSema = Semaphore(0)
        self.__dealers = {
            'syncrq': self.__syncRequest,
            'syncinfo': self.__syncInfo,
            'userrq': lambda params: \
                self.__unassignedTasks.append(params['task'])
        }
        self.__run()    

    def __getSlave(self):
        pass
    
    def __run(self):
        connection = ('127.0.0.1', MASTER_PORT)
        tRqListen = Thread(utils.recv(connection, self.__dealers))
        tRqListen.join()

    def __assignTasks(self):
        while True:
            task = self.__unassignedTasks.get(block=True)
            host = self.__getSlave(task)
            if host == None:
                self.__unassignedTasks.put(task)
                continue
            targetConn = (host, SLAVE_PORT)
            utils.send(targetConn, json.dumps({
                'type': 'assignment',
                'params':task
            }))
            self.__assignTasks.put(task)

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
        if not self.__ifNextMaster:
            return json.dumps({
                'success': False
            })
        self.__members.update(params['members'])
        self.__tasks = params['tasks']
        return json.dumps({
            'success': True
        })

    def __sync(self):
        nextMasterTarget = (self.__selectNextMaster(), MASTER_PORT)
        nxtMstReadiness = json.loads(
            utils.send(nextMasterTarget, json.dumps(
                {
                    'type':'syncrq',
                    'params': None
                }
            ))
        )
        if not nxtMstReadiness['prepared']:
            raise Exception("Target is not yet ready")

        while True:
            utils.send(nextMasterTarget, json.dumps({
                'type':'syncinfo',
                'params': {
                    'assigned': self.__assignedTasks,
                    'unassigned': self.__unassignedTasks,
                    'members': self.__members
                }
            }))
            time.sleep(5)
        

    def __selectNextMaster(self):
        for hostname in self.__members.keys():
            ip = self.__members['ip']
            if hostname == 'master'+DOMAIN_SUFFIX \
                or ip == DNS_HOST:
                continue 
            else:
                return hostname

    def enable(self):
        if not self.__status:
            self.__status = True
            self.__mastServSema.release() 
            self.__ifNextMaster = False
            self.__nextMaster = self.__selectNextMaster()
            self.__tMemberSync = Thread(self.__fetchMembersFromDNS)
            self.__tMemberSync.join()

        else:
            raise Exception("Master is running")
    
    def disable(self):
        if self.__status:
            self.__status = False
            self.__mastServSema.acquire() 
        else:
            raise Exception("Master already shutdown")
    
    # def assign_for_debug(self):
    #     self.__un


if __name__ == "__main__":
    master = Master()
    
    