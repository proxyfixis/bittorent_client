import peer , bencode , tracker

filepath = 'ubuntu.torrent'

with open(filepath , 'rb') as file :
    data = file.read()

decoded , _ = bencode.decode(data , 0)

announce = decoded[b'announce'] # using the decode we defined to convert bencoded to python dicts
announce_url = announce.decode()  #using pythons inbuilt function , not the one we defined

info , info_hash = bencode.get_info_hash(data)

peer_id =tracker.generate_peer_id()

if b'files' in info:
    raise NotImplementedError("multi-file torrents are not supported yet")
left = info[b'length']


encoded_response = tracker.tracker_get(announce_url, info_hash, peer_id, 6881 , left) ## port no is standard convention for bittorent

decoded_response , _ = bencode.decode(encoded_response , 0)
print(decoded_response)
if b'failure reason' in decoded_response :
          error = decoded_response[b'failure reason'].decode(errors='replace') #errors = replace parameter in case tracker gives back non UTF-8 chars
          raise RuntimeError(f"Tracker failure: {error}")



peers = tracker.parse_peers(decoded_response[b'peers'])

## connects to peers in swarms and requests peices 
for ip , port in peers :
    try :
        sock = peer.do_handshake(ip , port , info_hash , peer_id)
        print(f"handshake succeeded with {ip}:{port}")

        ## with sock so socket cleanup is automatic
        with sock : 
            message_id , payload  = peer.recv_message(sock)

            if(message_id == None) : 
                print("Recieved a keep alive")
            elif(message_id == peer.BITFIELD) :
                print(f"Message ID :{message_id}  Payload : {payload}" )
                bitfield = payload
            else : 
                print("not bitfield , handle later on")

            ## send interested
            peer.send_message(sock , peer.INTERESTED)

            ## waits till unchoked
            peer.wait_for_unchoke(sock)

            
            ## requesting first block of first piece
            peer.request_piece(sock , 0 , 0, peer.BLOCK_SIZE)


            ## waits till piece arrives 
            while True : 
                
                message_id , response = peer.recv_message(sock) 

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



