## Talks to the tracker server to get information on peers


import requests
import urllib.parse
import random
import string
import struct

from bencode import decode  , get_info_hash  # adjust to your actual bencode filename



## generate random peer id
def generate_peer_id():
    rand_part = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
    return ('-PC0001-' + rand_part).encode()


def build_tracker_url(announce_url, info_hash, peer_id, port, left):
    params = {
        'port': port,
        'uploaded': 0,
        'downloaded': 0,
        'left': left,
        'compact': 1,
        'event': 'started',
        'numwant' : 50
    }
    query = urllib.parse.urlencode(params)
    query += '&info_hash=' + urllib.parse.quote_from_bytes(info_hash)
    query += '&peer_id=' + urllib.parse.quote_from_bytes(peer_id)
    print("tracker url : " + announce_url + '?' + query)
    return announce_url + '?' + query


def tracker_get(announce_url, info_hash, peer_id, port, left):
    url = build_tracker_url(announce_url, info_hash, peer_id, port, left)
    response = requests.get(url, timeout=10, headers={'User-Agent': 'PyTorrentClient/0.1'})
    if response.status_code != 200:
        raise RuntimeError(f'Tracker returned {response.status_code}: {response.content[:200]}')
    return response.content

def parse_peers(peers_data):
    peers = []

    if isinstance(peers_data, bytes): #byte format - compact
        for i in range(0, len(peers_data), 6):
            chunk = peers_data[i:i+6]
            ip = '.'.join(str(b) for b in chunk[:4])
            port = struct.unpack('>H', chunk[4:6])[0]
            peers.append((ip, port))
        return peers

    else:
        # non-compact format, list of dicts
        for peer in peers_data:
            ip = peer[b'ip'].decode()
            port = peer[b'port']
            peers.append((ip, port))

        return peers


