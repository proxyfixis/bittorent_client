from pathlib import Path
import hashlib
import config

testpath = config.TORRENT_PATH

## decoding for each type
def decode_int(data,start) : 
    end = data.index(b'e' , start)
    number = int(data[start+1 : end])
    return number , end +1 

def decode_string(data,start) : 
    colon = data.index(b':', start) 
    length = int(data[start : colon])
    string = data[colon+1 : colon + length+1] 
    return string , colon + length +1

def decode_list(data, start):
    pos = start + 1  # skip 'l'
    output_list = []
    while data[pos:pos+1] != b'e':
        value, pos = decode(data, pos)
        output_list.append(value)
    return output_list, pos + 1  # skip 'e'

def decode_dict(data, start):
    pos = start + 1  # skip 'd'
    output_dict = {}
    while data[pos:pos+1] != b'e':
        key, pos = decode(data, pos)      # keys are always strings
        value, pos = decode(data, pos)
        output_dict[key] = value
    return output_dict, pos + 1  


## put the above decode functions together 
def decode(data,start) : 
    if(data[start:start+1] == b'i') : 
        return decode_int(data,start) 
    
    elif(data[start:start+1].isdigit()):
        return decode_string(data,start)
    
    elif(data[start:start+1] == b'l') : 
        return decode_list(data,start)
    
    elif data[start:start+1] == b'd':
        return decode_dict(data, start)

    else:
        raise ValueError(f"bad bencode byte {data[start:start+1]!r} at position {start}")

## put the above decode function to use on a torrent
def decode_torrent(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()
    decoded, _ = decode(data, 0)

   
    _ , info_hash = get_info_hash(data)
    
    return decoded, info_hash

## take the above decoded data and parse it and retrieve relevant data 
def parse_torrent(filepath):
    decoded , _ = decode_torrent(filepath)
    info = decoded[b'info']

    if b'files' in info:
        raise NotImplementedError("multi-file torrents are not supported yet")

    name = info[b'name']
    piece_length = info[b'piece length']
    pieces = info[b'pieces']  # raw bytes, every 20 bytes = one SHA1 hash
    announce = decoded[b'announce']  # tracker URL
    length = info[b'length']  # single-file torrents only

    return {
        'name': name,
        'piece_length': piece_length,
        'pieces': pieces,
        'announce': announce,
        'length': length
    }

def find_info_range(data):
    pos = 1  # skip the opening 'd' of the top-level dict
    while data[pos:pos+1] != b'e':
        key, pos = decode(data, pos)
        value_start = pos
        value, pos = decode(data, pos)
        if key == b'info':
            return value_start, pos
    raise ValueError("no info dict found in torrent")

def get_info_hash(data):

     # FIND THE INFO HASH - Needs getting the beginning and ending index from and slicing that part alone - then hash
    start, end = find_info_range(data)
    info_dict, _ = decode(data, start)
    info_hash = hashlib.sha1(data[start:end]).digest()
    return info_dict, info_hash

if __name__ == '__main__':
    ## testing , remove later    
    torrent = parse_torrent(testpath)
    print('Name:', torrent['name'])
    print('Announce:', torrent['announce'])
    print('Piece length:', torrent['piece_length'])
    print('Number of pieces:', len(torrent['pieces']) // 20)
    print('Length:', torrent['length'])



