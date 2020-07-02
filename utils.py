import socket 
GATEWAY = '10.255.255.255'
def getIP():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect((GATEWAY, 1))
    ip = s.getsockname()[0]
    s.close()
    return ip