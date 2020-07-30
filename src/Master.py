import threading
from threading import Semaphore
from threading import Thread
import socket
import utils
import json
import time
import os
import queue
import requests
import logging

from collections import OrderedDict

SLAVE_PORT = 23334
MASTER_PORT = 23335
DNS_PORT = 23333
DNS_HOST = '192.168.123.225'
DOMAIN_SUFFIX = '.csu.ac.cn'


logging.basicConfig(datefmt='%d-%b-%y %H:%M:%S',
    format='[%(asctime)s] %(levelname)s Master: %(message)s',
    level=logging.DEBUG)


# logger = logging.getLogger()


'''
docker_task = {
    'target': ip (None),
    'cpu': float (none),
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
        self.__status = False
        self.__online = False
        self.__members = {}
        self.__tasks = []
        self.__unassignedInstances = OrderedDict()
        self.__assignedInstances = OrderedDict()
        self.__ifNextMaster = False 
        self.__nextMaster = None
        self.__logger = logging.getLogger("Master")
        self.__mastServSema = Semaphore(0)
        self.__dealers = {
            'syncrq': self.__syncRequest,
            'syncinfo': self.__syncInfo,
            'enable': self.__enable,
            'disable': self.__disable,
            'monitoringinfo': self.__slaveMonitor,
            'userrq': self.__userRequest,
            # 'query': self.__userQuery
        }
        self.__logger.info("Provisioning finished, start running")   
        self.__run()

    def __slaveMonitor(self, params):
        pass

    def __run(self):
        self.__tRecv = Thread(target=utils.recv,\
            args=(('0.0.0.0', MASTER_PORT),\
            self.__dealers, logging), name="Master::Recv")
        self.__tRecv.start()
        self.__logger.info("receiver prepared")
        self.__tDnsMemberUpdate = Thread(
            target=self.__fetchMembersFromDNS
        )
        self.__tDnsMemberUpdate.start()
        time.sleep(3)
        self.__tsync = Thread(target=self.__sync,name="mastersync")
        self.__tsync.start()
        # self.__tAssign = Thread(target=self.__assignTasks,name='masterTaskAssign')
        # self.__tAssign.start()
            
    def __enable(self, params):
        if not self.__status:
            self.__status = True
            self.__mastServSema.release() 
            self.__ifNextMaster = False
            self.__nextMaster = self.__selectNextMaster()
            self.__logger.info("The module is enabled"\
                + " with next master prepared: %s"%self.__nextMaster)
            self.__logger.debug("Master Status: %s"%self.__status)
        
    def __disable(self, params):
        if self.__status:
            self.__status = False
            self.__mastServSema.acquire() 
            self.__logger.info("Master service disabled")
        
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
        self.__assignedInstances = params['assigned']
        self.__unassignedInstances = params['unassigned']
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
                self.__logger.info("members:%s"%(self.__members))
                self.__logger.info("member update finished")
                self.__logger.info("current #members: %s"%str(len(self.__members)))
                # self.__logger.debug(str(self.__members))
            else:
                self.__logger.warning("Tried to fetch "
                    + "members from DNS but failed")
                self.__logger.warning("not yet a master.")
            time.sleep(10)   
            
    def __selectNextMaster(self):
        nextMaster = ""
        for domainname in self.__members.keys():
            if utils.ifReachable(domainname):
                nextMaster = domainname
            
        if nextMaster == "":
            nextMaster = '192.168.123.152'
        utils.send((DNS_HOST, DNS_PORT), json.dumps({
            'type': 'logNextMaster',
            'params': {
                'nextMaster': nextMaster
            }
        }))
        
        return nextMaster
    
    def __sync(self):
        self.__logger.info("Waiting 10s to start syncing")
        self.__logger.info("Current Status: %s"%self.__status)
            
        time.sleep(5)
        while True:
            nextMasterTarget = (self.__nextMaster, MASTER_PORT)
            self.__logger.info("Get Next Master:%s"%nextMasterTarget[0])
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
                        'assigned': self.__assignedInstances,
                        'unassigned': self.__unassignedInstances,
                        'members': self.__members
                    }
                }))
                self.__mastServSema.release()
            time.sleep(5)

    def __userRequest(self, params):
        
        return os.popen(params['curlCommand']).read()

if __name__ == "__main__":
    master = Master()
    
    