
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
PROTOCOL_HEADER = b'\x13' + b'BitTorrent protocol'


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

    handshake_bytes = PROTOCOL_HEADER + b'\x00'*8+ info_hash + peer_id

    ## decide ipv4 or ipv6
    family = socket.AF_INET6 if ':' in ip else socket.AF_INET
    sock  = socket.socket(family, socket.SOCK_STREAM)
    sock.settimeout(10)
    
    ## enclose in try block to handle errors and close the socket in case it runs into an error
    try : 
        sock.connect((ip,port))
        sock.sendall(handshake_bytes)

        response = recv_exact(sock , 68)

        if response[0:20] != PROTOCOL_HEADER :
            raise RuntimeError("Peer did not reply with a BitTorrent handshake")
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

## peers might choke you for wtv reason , when choked run this to keep waiting for the unchoke
def wait_for_unchoke(sock, piece_count):
    bitfield = bytearray((piece_count + 7) // 8)   # all zeros: peer has nothing yet

    while True:
        message_id, payload = recv_message(sock)

        if message_id is None:                      # keep-alive
            continue
        elif message_id == BITFIELD:
            bitfield = bytearray(payload)
        elif message_id == HAVE:
            index = int.from_bytes(payload[0:4], byteorder="big")
            byte_index = index // 8
            if byte_index < len(bitfield):
                bitfield[byte_index] |= 1 << (7 - index % 8)
        elif message_id == UNCHOKE:
            print("Unchoke received, ready to request pieces")
            return bitfield
        else:
            print(f"waiting for unchoke, got message id {message_id}")

## downlaods a block - loop over all blocks in download_piece
def download_block(sock ,index , begin , length) : 

    print(f"requesting block begin={begin}")
    request_block(sock , index , begin , length)

    ## waits till piece arrives 
    while True : 
        message_id , response = recv_message(sock) 

        if message_id == PIECE : 

            resp_index = int.from_bytes(response[0:4] , byteorder = "big")
            resp_begin = int.from_bytes(response[4:8] , byteorder= "big")

            if(resp_index == index and resp_begin == begin) : 
                break

            else : 
                print(f"mismatch: asked piece {index} offset {begin}, got piece {resp_index} offset {resp_begin}")
            
        elif message_id == CHOKE : 
            print(f"You got choked , you are waiting")
            wait_for_unchoke(sock, 0)
            request_block(sock , index , begin , length)


    
    resp_block = response[8:]

    print(f"got block: piece {resp_index}, offset {resp_begin}, {len(resp_block)} bytes")
    return resp_block

## downloads a piece block by block - loop over in main to download all pieces
def download_piece(sock, piece_index , length) : 
    buf = bytearray(length)

    for begin in range(0 , length , BLOCK_SIZE) : 
        bytes_left = length - begin 
        block_len = min(bytes_left , BLOCK_SIZE)
        downloaded_block = download_block(sock , piece_index , begin , block_len)
        if len(downloaded_block) != block_len : 
            raise ValueError(f"downloaded block's length : {len(downloaded_block)} does not match with requested block length : {block_len}")
        else : 
            buf[begin : begin + block_len] = downloaded_block
            

    return buf

## request a specific block of the file
def request_block(sock , piece_index , begin , length) : 
    payload = piece_index.to_bytes(4 , byteorder = "big") + begin.to_bytes(4 , byteorder = "big") + length.to_bytes(4 , byteorder = "big")
    send_message(sock ,REQUEST ,payload)
     

