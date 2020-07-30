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
        self.__tReport = threading.Thread(
            target=self.__report2Master, name='masterReport')
        self.__tReport.start()

    def __report2Master(self):
        while True:
            hardwareInfo = {
                'type': 'monitoringinfo',
                'params': {
                    'from': self.__nodename,
                    'cpu': {
                        'usage_percentage': psutil.cpu_percent(),
                        'cores': psutil.cpu_count(),
                        'cpu_freq': psutil.cpu_freq().current
                    },
                    'ram': psutil.virtual_memory().available,
                    'sensors': {
                        'fans': psutil.sensors_fans(),
                        'battery': psutil.sensors_battery(),
                        'temperature': psutil.sensors_temperatures()
                    }
                    # 'dockers':self.__tasks
                }
            }
            utils.send(('master'+DOMAIN_SUFFIX, MASTER_PORT), 
                        json.dumps(hardwareInfo))
            time.sleep(10)

    

    def __getFPGAStatus(self):
        return None

    def __getCPUStatus(self):
        return 

if __name__ == "__main__":
    slave = Slave('hello')

    