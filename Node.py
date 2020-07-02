import json
import socket 
# def node
# info = {
#     'type':'register',
#     'params':{
#         'mac':'randomMac',
#         'role':'master',
#         'IPAddress':'192.168.0.105'
#     }
# }
info = {
    'type': 'updateMaster'
}


send_str = json.dumps(info)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('localhost', 23333))
s.sendall(send_str.encode())
data = s.recv(1024)
print(data.decode())