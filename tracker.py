import requests
import urllib.parse
import hashlib
import random
import string
import struct

from bencode import decode  # adjust to your actual bencode filename


def get_info_hash(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()

    info_start = data.index(b'4:info') + len(b'4:info')
    info_dict, info_end = decode(data, info_start)

    info_hash = hashlib.sha1(data[info_start:info_end]).digest()
    return info_dict, info_hash


def generate_peer_id():
    rand_part = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
    return ('-PC0001-' + rand_part).encode()


def build_tracker_url(announce_url, info_hash, peer_id, port, left):
    params = {
        'port': port,
        'uploaded': 0,
        'downloaded': 0,
        'left': left,
        'compact': 0,
        'event': 'started',
        'numwant' : 50
    }
    query = urllib.parse.urlencode(params)
    query += '&info_hash=' + urllib.parse.quote_from_bytes(info_hash)
    query += '&peer_id=' + urllib.parse.quote_from_bytes(peer_id)
    return announce_url + '?' + query


def tracker_get(announce_url, info_hash, peer_id, port, left):
    url = build_tracker_url(announce_url, info_hash, peer_id, port, left)
    response = requests.get(url, timeout=10, headers={'User-Agent': 'PyTorrentClient/0.1'})
    if response.status_code != 200:
        raise RuntimeError(f'Tracker returned {response.status_code}: {response.content[:200]}')
    return response.content

def parse_peers(peers_bytes):
    peers = []
    for i in range(0, len(peers_bytes), 6):
        chunk = peers_bytes[i:i+6]
        ip = '.'.join(str(b) for b in chunk[:4])
        port = struct.unpack('>H', chunk[4:6])[0]
        peers.append((ip, port))
    return peers




if __name__ == '__main__':
    filepath = 'ubuntu.torrent'

    with open(filepath, 'rb') as f:
        data = f.read()
    decoded, _ = decode(data, 0)

    info, info_hash = get_info_hash(filepath)
    announce = decoded[b'announce']
    peer_id = generate_peer_id()
    left = info.get(b'length', 0)

    print('Announce:', announce)
    print('Info hash:', info_hash.hex())
    print('Peer ID:', peer_id)

    raw_response = tracker_get(announce.decode(), info_hash, peer_id, 6881, left)

    print('\n--- RAW RESPONSE (bytes) ---')
    print(raw_response)

    tracker_response, _ = decode(raw_response, 0)

    print('\n--- DECODED RESPONSE ---')
    print(tracker_response)

    peers = parse_peers(tracker_response[b'peers'])
    print('\n--- PEERS ---')
    for ip, port in peers:
        print(f'{ip}:{port}')

    print(tracker_response.get(b'complete'), tracker_response.get(b'incomplete'), tracker_response.get(b'interval'))

