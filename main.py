import socket
from tracker import parse_peers , generate_peer_id , tracker_get 
from bencode import decode , get_info_hash
from peer import do_handshake , recv_message , send_message 
import peer

filepath = 'ubuntu.torrent'

with open(filepath , 'rb') as file :
    data = file.read()

decoded , _ = decode(data , 0)

announce = decoded[b'announce'] # using the decode we defined to convert bencoded to python dicts
announce_url = announce.decode()  #using pythons inbuilt function , not the one we defined

info , info_hash = get_info_hash(data)

peer_id = generate_peer_id()

left = info.get(b'length', 0)

encoded_response = tracker_get(announce_url, info_hash, peer_id, 6881 , left) ## port no is standard convention for bittorent

decoded_response , _ = decode(encoded_response , 0)
print(decoded_response)
if b'failure reason' in decoded_response :
          error = decoded_response[b'failure reason'].decode(errors='replace') #errors = replace parameter in case tracker gives back non UTF-8 chars
          raise RuntimeError(f"Tracker failure: {error}")



peers = parse_peers(decoded_response[b'peers'])

## connects to peers in swarms and requests peices 
for ip , port in peers :
    try :
        sock = do_handshake(ip , port , info_hash , peer_id)
        print(f"handshake succeeded with {ip}:{port}")
        message_id , payload  = recv_message(sock)

        if(message_id == None) : 
            print("Recieved a keep alive")
        elif(message_id == peer.BITFIELD) :
            print(f"Message ID :{message_id}  Payload : {payload}" )
            bitfield = payload
        else : 
            print("not bitfield , handle later on")


        send_message(sock , peer.INTERESTED)

        ## waits till unchoked
        while True : 
            message_id , payload = recv_message(sock)

            if message_id == peer.UNCHOKE : 
                  print("Unchoke recieved , ready to request pieces")
                  break
            elif message_id is None :
                  continue
            else :
                  print(f"waiting for unchoke, got message id {message_id}") 

        

        peer.request_piece(sock , 0 , 0, peer.BLOCK_SIZE)


        ## waits till piece arrives 
        while True : 
             
            message_id , response = recv_message(sock) 

            if message_id == peer.PIECE : 
                break
                
            elif message_id == peer.CHOKE : 
                print(f"Recieved message : {message_id}")

        index = int.from_bytes(response[0:4] , byteorder = "big")
        begin = int.from_bytes(response[4:8] , byteorder= "big")
        piece = response[8:]

        print(f"got block: piece {index}, offset {begin}, {len(piece)} bytes")
        break
    
    except Exception as e:
          print(f"peer {ip}:{port} failed: {e}")



