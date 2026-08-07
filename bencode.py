from pathlib import Path
import hashlib

testpath = "ubuntu.torrent"

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



def decode(data,start) : 
    if(data[start:start+1] == b'i') : 
        return decode_int(data,start) 
    
    elif(data[start:start+1].isdigit()):
        return decode_string(data,start)
    
    elif(data[start:start+1] == b'l') : 
        return decode_list(data,start)
    
    elif data[start:start+1] == b'd':
        return decode_dict(data, start)
    
def decode_torrent(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()
    decoded, _ = decode(data, 0)

    # find where b'4:info' starts, then decode again from just after that
    info_start = data.index(b'4:info') + len(b'4:info')
    info_dict, info_end = decode(data, info_start)
    info_hash = hashlib.sha1(data[info_start:info_end]).digest()

    return decoded, info_hash

def parse_torrent(filepath):
    decoded , _ = decode_torrent(filepath)
    info = decoded[b'info']
    
    name = info[b'name']
    piece_length = info[b'piece length']
    pieces = info[b'pieces']  # raw bytes, every 20 bytes = one SHA1 hash
    announce = decoded[b'announce']  # tracker URL
    
    # single file torrent
    if b'length' in info:
        length = info[b'length']
    
    # multi file torrent
    elif b'files' in info:
        files = info[b'files']  # list of dicts with 'path' and 'length'
    
    return {
        'name': name,
        'piece_length': piece_length,
        'pieces': pieces,
        'announce': announce
    }
    

    
torrent = parse_torrent('ubuntu.torrent')
print('Name:', torrent['name'])
print('Announce:', torrent['announce'])
print('Piece length:', torrent['piece_length'])
print('Number of pieces:', len(torrent['pieces']) // 20)



