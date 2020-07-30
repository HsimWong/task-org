import socket 
import json
import os
GATEWAY = '192.168.255.255'
def getIP():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect((GATEWAY, 1))
    ip = s.getsockname()[0]
    s.close()
    return ip

def send(target, msg):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(target)
    s.sendall(msg.encode())
    retMsg = s.recv(2048).decode()
    s.close()
    return json.loads(retMsg)

def recv(connection, dealers, logger):
    logger.info("listening on port %s"%connection[1])
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(connection)
    s.listen()
    while True:
        raw_conn = s.accept()
        conn = raw_conn[0]
        msgRaw = conn.recv(0x800).decode()
        if not msgRaw:
            continue
        else:
            msgParsed = json.loads(msgRaw)
            logger.info("received from %s: %s"%(raw_conn[1], msgParsed['type']))
            returnMsg = dealers[msgParsed['type']](msgParsed['params'])
            conn.sendall((json.dumps(returnMsg)).encode())
    s.close()

def ifReachable(host):
    return (os.system("ping -w 4 -q -c 1 %s>/dev/null"%host) == 0)

# def recv