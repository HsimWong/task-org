from threading import Semaphore
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
        self.__run()
        self.__mastServSema = Semaphore(0)

    def __masterInfoSync(self):
        pass 
    
    
    def __run(self):
        pass
        
    def enable(self):
        if not self.__status:
            self.__status = True
            self.__mastServSema.release() 
        else:
            raise Exception("Master is running")
    
    def disable(self):
        if self.__status:
            self.__status = False
            self.__mastServSema.acquire() 
        else:
            raise Exception("Master already shutdown")
    
    