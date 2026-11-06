
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

BLOCK_SIZE = 16384


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

    ## decide ipv4 or ipv6
    family = socket.AF_INET6 if ':' in ip else socket.AF_INET
    sock  = socket.socket(family, socket.SOCK_STREAM)
    sock.settimeout(10)
    
    ## enclose in try block to handle errors and close the socket in case it runs into an error
    try : 
        sock.connect((ip,port))
        sock.sendall(handshake_bytes)

        response = recv_exact(sock , 68)

        ##check if info hash matches
        if(response[28:48] != info_hash) :
            raise RuntimeError("Info hash doesn't match")
        
    except Exception:
        sock.close()
        raise
    

    return sock

## reading a length prefixed message
def recv_message(sock) :
    length_bytes = recv_exact(sock , 4)
    length = int.from_bytes(length_bytes, byteorder='big')

    if length == 0 :
        return None , None

    message = recv_exact(sock , length)
    message_id = message[0]
    payload = message[1:]
    return message_id , payload

## sending message to the server - needs message_id to determine type and payload to send
def send_message(sock , message_id , payload = b'') : 
    length = 1 + len(payload)
    message = length.to_bytes(4, byteorder="big") + bytes([message_id]) + payload
    sock.sendall(message)

def wait_for_unchoke(sock) : 
    while True :    
        message_id , _ = recv_message(sock)

        if message_id == UNCHOKE : 
            print("Unchoke recieved , ready to request pieces")
            return
        elif message_id is None :
            continue
        else :
            print(f"waiting for unchoke, got message id {message_id}") 

## request a specific piece of the file
def request_piece(sock , piece_index , begin , length) : 
    payload = piece_index.to_bytes(4 , byteorder = "big") + begin.to_bytes(4 , byteorder = "big") + length.to_bytes(4 , byteorder = "big")
    send_message(sock ,REQUEST ,payload)
     

