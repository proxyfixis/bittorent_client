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
            block = peer.download_block(sock , 0 , 0 , peer.BLOCK_SIZE)
            print(len(block))


           
    except Exception as e:
          print(f"peer {ip}:{port} failed: {e}")



