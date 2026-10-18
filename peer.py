
import socket

CHOKE = 0
UNCHOKE = 1
INTERESTED = 2
NOT_INTERESTED = 3
HAVE = 4
BITFIELD = 5
REQUEST = 6
PIECE = 7
CANCEL = 8

## ensuring we recieve the required number of bytes - handshake is 68 bytes exactly
def recv_exact(sock , n) :
        buffer = b''
        while(len(buffer) < n) :
                chunk = sock.recv(n-len(buffer))
                if not chunk:
                    raise ConnectionError("Peer closed connection")
                buffer += chunk
        return buffer

## handshake with peer
def do_handshake(ip , port , info_hash , peer_id) :

    handshake_bytes = b'\x13' +  b'BitTorrent protocol' + b'\x00'*8+ info_hash + peer_id

    sock  = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    sock.connect((ip,port))
    sock.send(handshake_bytes)

    response = recv_exact(sock , 68)

    if(response[28:48] != info_hash) :
        sock.close()
        raise RuntimeError("Info hash doesn't match")

    return sock

## reading a length prefixed message
def recv_message(sock) :
     length_bytes = recv_exact(sock , 4)
     length = int.from_bytes(length_bytes, byteorder='big')

     if length == 0 :
        return None

     message = recv_exact(sock , length)
     message_id = message[0]
     payload = message[1:]
     return message_id , payload




