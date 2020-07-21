import json
import utils
def makeRequest(mirror, specs):
    
    print(utils.send(json.dumps({
        'type': 'userrq',
        'params': {
            'mirror': mirror,
            'specs': specs
        }
    })))