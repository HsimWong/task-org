class Node(object):
    '''
    Working Procedures:
    1. Read resources from external file
    2. Init Client service and Master Service
    3. Check if master registered
      no: 1)register as master;2)start server
          & client 
      yes: 1)regis as client; 2) only start client
    ALWAYS check is master has changed
        if it's me:
            turn on master
        else: turn off the master
    
    '''
    
    def __init__(self):
        self.__resources = self.__readResources()
        
    def __readResources(self):
        return ""