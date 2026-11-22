import hashlib

def check_piece_hash(downloaded_piece , index , pieces_hash) : 
    if(hashlib.sha1(downloaded_piece).digest() == pieces_hash[index*20 : index*20 + 20]) : 
        return True
    else : 
        return False 

def write_piece(index , data , piece_length , file ) : 
    offset = index * piece_length
    file.seek(offset)
    file.write(data)

def get_piece_length(index, piece_length, total_length):
    return min(piece_length , total_length- index * piece_length )

def has_piece(bitfield, index):
    byte_index = index // 8
    bit_position = index % 8

    if byte_index >= len(bitfield):
        return False

    return ((bitfield[byte_index] >> (7 - bit_position)) & 1) == 1

def find_completed(file, piece_count, piece_length, total_length, pieces_hash):
    done = set()
    for index in range(piece_count):
        length = get_piece_length(index, piece_length, total_length)
        file.seek(index * piece_length)
        data = file.read(length)

        if len(data) == length and check_piece_hash(data, index, pieces_hash):
            done.add(index)
    return done
    
    