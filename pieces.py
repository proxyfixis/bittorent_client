import hashlib

def check_piece_hash(downloaded_piece , index , pieces_hash) : 
    if(hashlib.sha1(downloaded_piece).digest() == pieces_hash[index*20 : index*20 + 20]) : 
        return True
    else : 
        return False 