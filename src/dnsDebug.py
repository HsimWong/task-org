import json
import socket 
import utils 
# def node




def regisMaster():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    info = {
        'type':'register',
        'params':{
            'mac':'randomMac',
            'role':'master',
            'IPAddress':'47.103.45.126'
        }
    }

    send_str = json.dumps(info)
    s.connect(('localhost', 23333))
    s.sendall(send_str.encode())
    data = s.recv(1024)
    print(data.decode())

    s.close()
    
def enableMaster():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    info = {
        'type':'enable',
        'params':None
    }

    send_str = json.dumps(info)
    s.connect(('localhost', 23335))
    s.sendall(send_str.encode())
    data = s.recv(1024)
    print(data.decode())

    s.close()


def regis107():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    info = {
        'type':'register',
        'params':{
            'mac':'randomMac',
            'role':'slave',
            'IPAddress':'192.168.0.107'
        }
    }

    send_str = json.dumps(info)
    s.connect(('localhost', 23333))
    s.sendall(send_str.encode())
    data = s.recv(1024)
    print(data.decode())

    s.close()
    
def updateMaster():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    info = {
        'type': 'updateMaster',
        'params': 'None'
    }
    send_str = json.dumps(info)
    s.connect(('localhost', 23333))
    s.sendall(send_str.encode())
    data = s.recv(1024)
    print(data.decode())

    s.close()
    
def checkMaster():
    info = json.dumps({
        'type': 'checkMaster',
        'params': None
    })
    print(utils.send(('localhost', 23333), info))
    
def syncMembers():
    info = json.dumps({
        'type': 'syncMembers',
        'params': None
    })
    print(json.loads(utils.send(('localhost', 23333), info)))

def getSlaveReport():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    info = {
        'type': 'hardware',
        'params': 'None'
    }
    send_str = json.dumps(info)
    s.connect(('localhost', 23334))
    s.sendall(send_str.encode())
    data = s.recv(1024)
    print(data.decode())

    s.close()