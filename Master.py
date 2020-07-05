
SERVER_PORT = 23335 

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
        self.__members = [] 

    def __masterInfoSync(self):
        pass 
    
            
    def start(self):
        if not self.__status:
            self.__status = True 
        else:
            raise Exception("Master is running")
    
    def stop(self):
        pass