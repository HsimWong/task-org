import json
import utils
import hashlib
from datetime import datetime
from getmac import get_mac_address as gma 


DOMAIN_SUFFIX = '.csu.ac.cn'
MASTER_PORT = 23335

def deploy(method, url_suffix, destination):
    utils.send(('master'+DOMAIN_SUFFIX, MASTER_PORT),
        json.dumps({
            'type': 'deploy',
            'params': {
                'dockerTask': {
                    'target': destination,
                    'cpu': None,
                    'command': {
                        'method': method,
                        'suffix': url_suffix
                    },
                    'instanceHash':hashlib.md5(
                        (str(datetime.now())+gma()).encode()
                    ).hexdigest()
                }
            }
        }))