# import docker
# import queue
import logging
import utils 
import json
import psutil
import threading
import time
SLAVE_PORT = 23334
MASTER_PORT = 23335
DOMAIN_SUFFIX = '.csu.ac.cn'

logging.basicConfig(datefmt='%d-%b-%y %H:%M:%S',
    format='[%(asctime)s] %(levelname)s Slave: %(message)s',
    level=logging.DEBUG)
logger = logging.getLogger()

class Slave(object):
    def __init__(self, nodename):
        self.__nodename = nodename
        self.__report2Master()
        
        # self.__client = docker.from_env()
        
        


    # def __monitor(self):
    #     for container in self.__client.

    # def __taskRun(self, params):
    #     # param_dealers = {
    #     #     'run': self.__client.containers.run,

    #     # }
    #     self.__client.containers.run(image=params['image'],\
    #         command=params['command'], detach=params['detach'],)
    
    def __report2Master(self):
        connection = ('master'+DOMAIN_SUFFIX, MASTER_PORT)
        while True:
            utils.send(connection, json.dumps({
                'type': 'monitoringinfo',
                'params': {
                    'from': self.__nodename,
                    'cpu': self.__getCPUStatus(),
                    'RAM': psutil.virtual_memory(),
                    'sensors': {
                        'fans': psutil.sensors_fans(),
                        'battery': psutil.sensors_battery(),
                        'temperature': psutil.sensors_temperatures()
                    }
                    # 'dockers':self.__tasks
                }
            }))
            time.sleep(5)
    

    def __getFPGAStatus(self):
        return None

    def __getCPUStatus(self):
        return {
            'usage_percentage': psutil.cpu_percent(),
            'cores': psutil.cpu_count,
            'cpu_freq': psutil.cpu_freq()
        }

    