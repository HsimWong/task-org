
    # Need 2b updated
    def __userRequest(self, params):
        if params['instanceHash'] in self.__assignedInstances.keys():
            connection = (params['ip'], SLAVE_PORT)
            return self.__manipulate(self.__assignedInstances[params['instanceHash']])
        elif params['instanceHash'] in self.__unassignedInstances.keys():
            return json.dumps({
                'code': False,
                'msg': 'Not Deployed'
            })
        else:
            self.__unassignedInstances.update({params['instanceHash']: params})
            return {
                'code': True,
                'msg': 'Added To The Queue'
            }
              
            
    # for hostname in self.__members.keys():
    #     ip = self.__members['ip']
    #     if hostname == 'master'+DOMAIN_SUFFIX \
    #         or ip == DNS_HOST:
    #         continue 
    #     else:
    #         return hostname
    
    # Deprecated
    # def __monitor(self): # Activated when self is working 
    #     if not self.__status:
    #         return json.dumps({
    #             'success': False
    #         })

    # Subordinate function called by assignTasks
    # def __getSlave(self):
    #     return self.__members['node1'+DOMAIN_SUFFIX]


    # Concurrent threads
    def __assignTasks(self):
        while True:
            self.__mastServSema.acquire()
            task = self.__unassignedInstances.get(block=True)
            host = self.__getSlave(task)
            task['target'] = host
            if host == None:
                self.__unassignedInstances.put(task)
                continue
            # targetConn = (host, SLAVE_PORT)
            # utils.send(targetConn, json.dumps({
            #     'type': 'assignment',
            #     'params':task
            # }))
            # self.__deploy(task)
            self.__deploy(task)
            
            self.__assignedInstances.put(task)
            self.__mastServSema.release()
       
    def __deploy(self, task):
        pass    
    
    def __query(self, task):
        pass 
    
    def __manipulate(self, task):
        pass
    def __execute(self, target, api, method):
        return requests.request(method=method, url=(target+api))
        
        
            
    def __getSlave(self, task):
        return ''
    
    
    def __userQuery(self):
        return json.dumps({
            'members': self.__members,
            'tasks':{
                'assigned': self.__assignedInstances,
                'unassigned': self.__unassignedInstances
            }
        })

    

    # Concurrent Thread 0


    # Concurrent Thread 1

        
    # Subordinate function called by __sync


