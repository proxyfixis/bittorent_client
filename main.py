import peer , bencode , tracker , pieces
import traceback

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

name = info[b'name']


left = info[b'length']
piece_length = info[b'piece length']
pieces_hash = info[b'pieces']



encoded_response = tracker.tracker_get(announce_url, info_hash, peer_id, 6881 , left) ## port no is standard convention for bittorent

decoded_response , _ = bencode.decode(encoded_response , 0)
print(decoded_response)
if b'failure reason' in decoded_response :
          error = decoded_response[b'failure reason'].decode(errors='replace') #errors = replace parameter in case tracker gives back non UTF-8 chars
          raise RuntimeError(f"Tracker failure: {error}")



peers = tracker.parse_peers(decoded_response[b'peers'])

with open(name ,'wb') as file : 
    ## connects to peers in swarms and requests peices 
    for ip , port in peers :
        try :
            print(f"connecting to {ip}:{port}")
            sock = peer.do_handshake(ip , port , info_hash , peer_id)
            print(f"handshake succeeded with {ip}:{port}")

            ## with sock so socket cleanup is automatic
            print("waiting for first message")
            with sock : 
                message_id , payload  = peer.recv_message(sock)

                if(message_id == None) : 
                    print("Recieved a keep alive")
                elif(message_id == peer.BITFIELD) :
                    print(f"Message ID :{message_id}  Payload length : {len(payload)}" )
                    bitfield = payload
                else : 
                    print("not bitfield , handle later on")

                print("sending INTERESTED")
                ## send interested
                peer.send_message(sock , peer.INTERESTED)

                print("waiting for unchoke")
                ## waits till unchoked
                peer.wait_for_unchoke(sock)

                print("downloading piece 0")
                ## requesting first piece to test
                test_piece = peer.download_piece(sock, 0, piece_length)
                print(len(test_piece))

                piece_is_correct = pieces.check_piece_hash(test_piece , 0 , pieces_hash)
                print(f"Piece x hash : {piece_is_correct}")
                
                if(piece_is_correct) : 
                    ## write to file 
                    pieces.write_piece(0 , test_piece , piece_length , file)
                    break
                    

        except Exception as e:
            print(f"peer {ip}:{port} failed: {e}")
            traceback.print_exc()



