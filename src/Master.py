import threading
from threading import Semaphore
from threading import Thread
import socket
import utils
import json
import time
import queue
import requests
import logging

SLAVE_PORT = 23334
MASTER_PORT = 23335
DNS_PORT = 23333
DNS_HOST = '47.103.45.126'
DOMAIN_SUFFIX = '.csu.ac.cn'


logging.basicConfig(datefmt='%d-%b-%y %H:%M:%S',
    format='[%(asctime)s] %(levelname)s Master: %(message)s',
    level=logging.DEBUG)


# logger = logging.getLogger()


'''
docker_task = {
    'target': ip (None),
    'cpu': float (none),
    'image' = str (not null),
    'command': str,
    'instanceHash':string (not null)
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
        print("FUCK")
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
            'enable': self.__enable
            # 'monitoringinfo': self.__monitor,
            # 'userrq': self.__userRequest,
            # 'query': self.__userQuery
        }
        self.__logger.info("Provisioning finished, start running")   

        self.__tRecv = Thread(target=utils.recv,\
            args=(('0.0.0.0', MASTER_PORT),\
            self.__dealers, logging))
        self.__tRecv.start()
        # self.__logger
        self.__logger.info("receiver prepared")
        self.__tDnsMemberUpdate = Thread(
            target=self.__fetchMembersFromDNS
        )
        self.__tDnsMemberUpdate.start()
        self.__tsync = Thread(target=self.__sync)
        self.__tsync.start()
        self.__tAssign = Thread(target=self.__assignTasks)
        self.__tAssign.start()
        

    # Need re-implementation
    def __userQuery(self):
        return json.dumps({
            'members': self.__members,
            'tasks':{
                'assigned': self.__assignedTasks,
                'unassigned': self.__unassignedTasks
            }
        })

    # Need re-implementation on
    # slave-related movements
    # def __run(self):
        
        
    def __enable(self, params):
        if not self.__status:
            self.__logger.info("The module is enabled")
            self.__status = True
            self.__mastServSema.release() 
            self.__ifNextMaster = False
            self.__nextMaster = self.__selectNextMaster()
            # self.__tMemberSync = Thread(self.__fetchMembersFromDNS)
            # self.__tMemberSync.join()

        else:
            raise Exception("Master is running")
    
    def __disable(self, params):
        if self.__status:
            self.__status = False
            self.__mastServSema.acquire() 
            self.__logger.info("Master service disabled")
        else:
            raise Exception("Master already shutdown")



    # Dealer functions called by self.__dealers
    # Belongs to thread utils.recv
    def __syncRequest(self, params): # activated when self is working
        self.__logger.info("received a syncing request")
        self.__ifNextMaster = True 
        return json.dumps({
            'prepared': True 
        })
    
    def __syncInfo(self, params): # Activated when self is idling
        self.__logger.info("start syncing...")
        if not self.__ifNextMaster:
            return json.dumps({
                'success': False
            })
        self.__members.update(params['members'])
        # self.__tasks = params['tasks']
        self.__assignedTasks = params['assigned']
        self.__unassignedTasks = params['unassigned']
        self.__members = params['members']
        self.__logger.debug("Received #members:%s"%str(len(self.__members)))
        self.__logger.info("syncing finished.")
        return json.dumps({
            'success': True
        })
        
    def __fetchMembersFromDNS(self):
        # Called during initialization period
        self.__logger.info("Start thread for fetching"
                           +" members from dns")
        target = (DNS_HOST, DNS_PORT)
        self.__logger.info("target:%s"%str(target))
                    
        while True:    
            if self.__status:

                self.__members = json.loads(
                    utils.send(target, json.dumps({
                        'type': 'syncMembers',
                        'params': None
                    }))
                )
                self.__logger.info("member update finished")
                self.__logger.info("current #members: %s"%str(len(self.__members)))
                # self.__logger.debug(str(self.__members))
            else:
                self.__logger.warning("Tried to fetch "
                    + "members from DNS but failed")
                self.__logger.warning("not yet a master.")
            time.sleep(10)   
            
    def __selectNextMaster(self):
        return 'hongkong.chn.ryan1202.wang'
    
    def __sync(self):
        while True:
            nextMasterTarget = (self.__selectNextMaster(), MASTER_PORT)
            if self.__status:
                self.__logger.info("Trying to sync info to %s"%nextMasterTarget[0])
                # self.__logger.info("status:%s"%str(self.__status))
                nxtMstReadiness = json.loads(
                    utils.send(nextMasterTarget, json.dumps(
                        {
                            'type':'syncrq',
                            'params': None
                        }
                    ))
                )
                self.__logger.info("Respond from next slave:%s"%str(nxtMstReadiness))
                
                if not nxtMstReadiness['prepared']:
                    raise Exception("Target is not yet ready")

            
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

    # Need 2b updated
    def __userRequest(self, params):
        if params['instanceHash'] in self.__assignedTasks.keys():
            connection = (params['ip'], SLAVE_PORT)
            return self.__manipulate(self.__assignedTasks[params['instanceHash']])
        elif params['instanceHash'] in self.__unassignedTasks.keys():
            return json.dumps({
                'code': False,
                'msg': 'Not Deployed'
            })
        else:
            self.__unassignedTasks.update({params['instanceHash']: params})
            return {
                'code': True,
                'msg': 'Added To The Queue'
            }
              
            
    # for hostname in self.__members.keys():
    #     ip = self.__members['ip']
    #     if hostname == 'master'+DOMAIN_SUFFIX \
    #         or ip == DNS_HOST:
    #         continue 
    #     else:
    #         return hostname
    
    # Deprecated
    # def __monitor(self): # Activated when self is working 
    #     if not self.__status:
    #         return json.dumps({
    #             'success': False
    #         })

    # Subordinate function called by assignTasks
    # def __getSlave(self):
    #     return self.__members['node1'+DOMAIN_SUFFIX]


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
            # targetConn = (host, SLAVE_PORT)
            # utils.send(targetConn, json.dumps({
            #     'type': 'assignment',
            #     'params':task
            # }))
            # self.__deploy(task)
            self.__deploy(task)
            
            self.__assignedTasks.put(task)
            self.__mastServSema.release()
       
    def __deploy(self, task):
        pass    
    
    def __query(self, task):
        pass 
    
    def __manipulate(self, task):
        pass
    def __execute(self, target, api, method):
        return requests.request(method=method, url=(target+api))
        
        
            
    def __getSlave(self, task):
        return 'hongkong.chn.ryan1202.wang'
    
    

    # Concurrent Thread 0


    # Concurrent Thread 1

        
    # Subordinate function called by __sync



    

if __name__ == "__main__":
    master = Master()
    
    