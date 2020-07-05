import socket 

CLIENT_PORT = 23334


class Client(object):
    '''
    init
    ALWAYS recv tasks
    ALWAYS report to server resources & docker status
    ALWAYS 
    '''
    
    def __init__(self):
        self.__status = True
        self.__tasksQ = []
        
        
    def recvTask(self):
        pass 
    
    def getResourceStatus(self):
        pass 
    
    def getDockerStatus(self):
        pass 