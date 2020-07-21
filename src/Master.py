import threading
from threading import Semaphore
from threading import Thread
import socket
import utils
import json
import time
import queue
import logging

SLAVE_PORT = 23334
MASTER_PORT = 23335
DNS_PORT = 23333
DNS_HOST = '127.0.0.1'
DOMAIN_SUFFIX = '.csu.ac.cn'


logging.basicConfig(datefmt='%d-%b-%y %H:%M:%S',
    format='[%(asctime)s] %(levelname)s Master: %(message)s',
    level=logging.DEBUG)


logger = logging.getLogger()


'''
docker_task = {
    'target': ip (None),
    'cpu': float (none),
    'image' = str (not null),
    'command': str,
    'idHash':string (not null)
}
'''
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
        self.__unassignedTasks = {}
        self.__assignedTasks = {}
        self.__ifNextMaster = False 
        self.__nextMaster = None
        self.__logger = logging.getLogger("Master")
        self.__mastServSema = Semaphore(0)
        self.__dealers = {
            'syncrq': self.__syncRequest,
            'syncinfo': self.__syncInfo,
            'monitoringinfo': self.__monitor,
            'userrq': self.__userRequest,
            'query': self.__userQuery
        }
        self.__run()    

    def __userQuery(self):
        return json.dumps({
            'members': self.__members,
            'tasks':{
                'assigned': self.__assignTasks,
                'unassigned': self.__unassignedTasks
            }
        })


    def __run(self):
        self.__logger.info("started initializing")
        self.__tRecv = Thread(utils.recv(('localhost', MASTER_PORT),\
            self.__dealers, logging))
        self.__tDnsMemberUpdate = Thread(
            self.__fetchMembersFromDNS
        )
        self.__tRecv.join()
        self.__tDnsMemberUpdate.join()

    def __userRequest(self, params):
        if params['idHash'] in self.__assignedTasks.keys():
            connection = (params['ip'], SLAVE_PORT)
            return utils.send(connection, json.dumps({
                'type': 'taskrun',
                'params': self.__assignTasks[params['idHash']]
            }))
        elif params['idHash'] in self.__unassignedTasks.keys():
            return json.dumps({
                'code': False,
                'msg': 'Not Deployed'
            })
        else:
            self.__unassignedTasks.update({params['idHash']: params})
            return {
                'code': True,
                'msg': 'Added To The Queue'
            }
    


    # Dealer functions called by self.__dealers
    # Belongs to thread utils.recv
    def __syncRequest(self, params): # activated when self is working
        self.__ifNextMaster = True 
        return json.dumps({
            'prepared': True 
        })
    
    def __syncInfo(self, params): # Activated when self is idling
        if not self.__ifNextMaster:
            return json.dumps({
                'success': False
            })
        self.__members.update(params['members'])
        self.__tasks = params['tasks']
        return json.dumps({
            'success': True
        })
    
    def __monitor(self): # Activated when self is working 
        if not self.__status:
            return json.dumps({
                'success': False
            })

    # Subordinate function called by assignTasks
    def __getSlave(self):
        return self.__members['node1'+DOMAIN_SUFFIX]

    # Concurrent threads
    def __assignTasks(self):
        while True:
            self.__mastServSema.acquire()
            task = self.__unassignedTasks.get(block=True)
            host = self.__getSlave(task)
            task['target'] = host
            if host == None:
                self.__unassignedTasks.put(task)
                continue
            targetConn = (host, SLAVE_PORT)
            utils.send(targetConn, json.dumps({
                'type': 'assignment',
                'params':task
            }))
            self.__assignTasks.put(task)
            self.__mastServSema.release()

    # Concurrent Thread 0
    def __fetchMembersFromDNS(self):
        # Called during initialization period
        target = (DNS_HOST, DNS_PORT)
        while True:    
            self.__members = json.loads(
                utils.send(target, json.dumps({
                    'type': 'syncMembers',
                    'params': None
                }))
            )
            time.sleep(10)   

    # Concurrent Thread 1
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
            self.__mastServSema.acquire()
            utils.send(nextMasterTarget, json.dumps({
                'type':'syncinfo',
                'params': {
                    'assigned': self.__assignedTasks,
                    'unassigned': self.__unassignedTasks,
                    'members': self.__members
                }
            }))
            self.__mastServSema.release()
            time.sleep(5)
        
    # Subordinate function called by __sync
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
            logger.info("The module is enabled")
            self.__status = True
            self.__mastServSema.release() 
            self.__ifNextMaster = False
            self.__nextMaster = self.__selectNextMaster()
            # self.__tMemberSync = Thread(self.__fetchMembersFromDNS)
            # self.__tMemberSync.join()

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
    
    