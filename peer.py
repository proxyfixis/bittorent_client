
import socket
import time

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
UNCHOKE_TIMEOUT = 60    # seconds to wait for UNCHOKE
BLOCK_TIMEOUT = 30      # seconds to wait for one block
PIPELINE_DEPTH = 5      # requests allowed in flight at once
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

    old_timeout = sock.gettimeout()                 # remember the normal 10s timeout
    sock.settimeout(UNCHOKE_TIMEOUT)                # a silent peer may stay quiet longer
    deadline = time.monotonic() + UNCHOKE_TIMEOUT   # hard stop, even if keep-alives arrive

    try:
        while True:
            if time.monotonic() > deadline:
                raise TimeoutError(f"no UNCHOKE within {UNCHOKE_TIMEOUT}s")

            message_id, payload = recv_message(sock)

            if message_id is None:                  # keep-alive
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
    finally:
        sock.settimeout(old_timeout)                # put the 10s timeout back

## downlaods a block - loop over all blocks in download_piece
def download_block(sock ,index , begin , length) : 

    print(f"requesting block begin={begin}")
    request_block(sock , index , begin , length)
    deadline = time.monotonic() + BLOCK_TIMEOUT

    ## waits till piece arrives 
    while True : 
        if time.monotonic() > deadline :
            raise TimeoutError(f"block {begin} of piece {index} not received within {BLOCK_TIMEOUT}s")

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
            deadline = time.monotonic() + BLOCK_TIMEOUT


    
    resp_block = response[8:]

    print(f"got block: piece {resp_index}, offset {resp_begin}, {len(resp_block)} bytes")
    return resp_block


## downloads a piece with several block requests in flight at once
def download_piece(sock, piece_index , length) : 
    buf = bytearray(length)
    waiting = set()          # begins we asked for and have no reply yet
    next_begin = 0           # next block we have not asked for yet
    deadline = time.monotonic() + BLOCK_TIMEOUT ## set deadline time

    while True :
        ## when waiting set has blocks in it we haven't pushed all the blocks to waiting yet - keeps the window full
        while len(waiting) < PIPELINE_DEPTH and next_begin < length :
            block_len = min(BLOCK_SIZE , length - next_begin)
            request_block(sock , piece_index , next_begin , block_len) ## request and add to waiting , update next begin
            waiting.add(next_begin)
            next_begin += BLOCK_SIZE

        ## nothing in flight and nothing left to send: the piece is complete
        if not waiting :
            return buf

        ## if deadline over raise error
        if time.monotonic() > deadline :
            raise TimeoutError(f"no block of piece {piece_index} received within {BLOCK_TIMEOUT}s")

        message_id , payload = recv_message(sock)
        
        if message_id == PIECE :
            resp_index = int.from_bytes(payload[0:4] , byteorder = "big")
            resp_begin = int.from_bytes(payload[4:8] , byteorder = "big")
            data = payload[8:]

            if resp_index == piece_index and resp_begin in waiting :
                expected_len = min(BLOCK_SIZE , length - resp_begin)
                if len(data) != expected_len :
                    raise ValueError(f"block length {len(data)} does not match requested length {expected_len}")

                buf[resp_begin : resp_begin + expected_len] = data
                waiting.discard(resp_begin)
                deadline = time.monotonic() + BLOCK_TIMEOUT
            else :
                print(f"ignoring block: piece {resp_index} offset {resp_begin} (not requested)")

        elif message_id == CHOKE :
            print("You got choked , you are waiting")
            wait_for_unchoke(sock , 0)
            for begin in sorted(waiting) :
                request_block(sock , piece_index , begin , min(BLOCK_SIZE , length - begin))
            deadline = time.monotonic() + BLOCK_TIMEOUT

## request a specific block of the file
def request_block(sock , piece_index , begin , length) : 
    payload = piece_index.to_bytes(4 , byteorder = "big") + begin.to_bytes(4 , byteorder = "big") + length.to_bytes(4 , byteorder = "big")
    send_message(sock ,REQUEST ,payload)
     

