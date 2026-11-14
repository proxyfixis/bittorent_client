import peer , bencode , tracker , pieces
import traceback
import config

filepath = config.TORRENT_PATH

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


total_length = info[b'length']
piece_length = info[b'piece length']
pieces_hash = info[b'pieces']



encoded_response = tracker.tracker_get(announce_url, info_hash, peer_id, config.PORT , total_length) ## port no is standard convention for bittorent

decoded_response , _ = bencode.decode(encoded_response , 0)
print(decoded_response)
if b'failure reason' in decoded_response :
          error = decoded_response[b'failure reason'].decode(errors='replace') #errors = replace parameter in case tracker gives back non UTF-8 chars
          raise RuntimeError(f"Tracker failure: {error}")



peers = tracker.parse_peers(decoded_response[b'peers'])
piece_count = len(pieces_hash) // 20
completed = set()
print(f"Total no of pieces : {piece_count}")

with open(name ,'wb') as file : 
    ## connects to peers in swarms and requests peices 
    for ip , port in peers :
        try :
            print(f"connecting to {ip}:{port}")
            sock = peer.do_handshake(ip , port , info_hash , peer_id)
            print(f"handshake succeeded with {ip}:{port}")

            ## with sock so socket cleanup is automatic
            with sock : 
                
                print("sending INTERESTED")
                ## send interested
                peer.send_message(sock , peer.INTERESTED)

                print("waiting for unchoke")
                ## waits till unchoked
                bitfield = peer.wait_for_unchoke(sock, piece_count)

                for index in range(piece_count):
                    if index in completed  : 
                        continue 
                    elif pieces.has_piece(bitfield , index) == False  : 
                        continue

                    ## calculate length of current piece to request
                    current_piece_length = pieces.get_piece_length(index , piece_length , total_length )

                    ## download piece
                    downloaded_piece = peer.download_piece(sock, index, current_piece_length)
                    print(len(downloaded_piece))

                    ## verify hash
                    piece_is_correct = pieces.check_piece_hash(downloaded_piece , index , pieces_hash)
                    print(f"Piece {index} hash : {piece_is_correct}")

                    ## if hash if same -> write to file 
                    if(piece_is_correct) : 
                        ## write to file 
                        pieces.write_piece(index , downloaded_piece , piece_length , file)
                        completed.add(index)
                        print(f"Completed {len(completed)} out of {piece_count}")
                    else : 
                        print(f"bad piece : {index}")

            if len(completed) == piece_count : 
                break 

        except Exception as e:
            print(f"peer {ip}:{port} failed: {e}")
            traceback.print_exc()



