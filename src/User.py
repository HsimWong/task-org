import json
import utils
def makeRequest(mirror, target):
    
    print(utils.send(json.dumps({
        'type': 'userrq',
        'params': {
            'mirror': mirror,
            
        }
    }))