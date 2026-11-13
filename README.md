# BitTorrent client in Python

A BitTorrent client written from scratch in Python as a learning project. No BitTorrent libraries are used: the bencode codec, tracker announce, peer wire protocol and piece verification are all hand-written. The only third-party dependency is `requests`, used for the HTTP tracker call.

## Status

Work in progress. Implemented:

- Bencode decoder and info-hash computation (SHA-1 over the exact bytes of the `info` dict)
- HTTP tracker announce, with compact and non-compact peer lists (including IPv6 addresses)
- Peer handshake and length-prefixed message framing
- Bitfield parsing, so only pieces a peer has are requested
- Block-by-block piece download, with re-request after a CHOKE
- SHA-1 verification of every piece against the torrent before it is written
- Writing verified pieces at the correct offset in the output file
- Download loop over all pieces, tracking completed pieces so a failed peer can be replaced

Not yet implemented (see [TODO.md](TODO.md)): pipelined requests, HAVE messages, resuming a partial download, several peers in parallel, multi-file torrents, UDP trackers, seeding.

The full-file download has not yet been confirmed end to end against a live swarm. The Ubuntu tracker often returns a single peer that does not respond.

## Setup

Requires Python 3.

```
python3 -m venv bittorent
source bittorent/bin/activate
pip install -r requirements.txt
```

## Usage

```
python main.py        # announce, connect to peers, download and verify all pieces
python bencode.py     # decode ubuntu.torrent and print its metadata
```

`main.py` reads `ubuntu.torrent` (a single-file torrent included for testing). To use another single-file torrent, change `filepath` at the top of `main.py`. The output file is created in the working directory, named after the torrent.

## Layout

| File | Purpose |
|---|---|
| `bencode.py` | Bencode codec, info-hash, torrent parsing |
| `tracker.py` | Tracker announce and peer-list parsing |
| `peer.py` | Handshake, message framing, block and piece download |
| `pieces.py` | Piece length, SHA-1 check, bitfield lookup, disk writes |
| `main.py` | Entry point tying the pieces together |

## How a download works

1. Decode the `.torrent` and compute the info hash.
2. Announce to the tracker and get a list of peers.
3. For each peer: handshake, read its bitfield, send INTERESTED, and wait for UNCHOKE.
4. For each piece the peer has and we still need: request it block by block (16 KiB), check its SHA-1, write it to its offset, and mark it done.
5. If a peer fails, move on to the next one. Completed pieces are kept, so work is not repeated.
