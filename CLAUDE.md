# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project state

A from-scratch BitTorrent client in Python, built as a learning project. It can announce to a tracker, handshake with a peer, download one piece block by block, verify its SHA1 against the torrent, and write it to disk at the right offset. It does **not** yet download a whole file: `main.py` only fetches piece 0 (hardcoded) and stops after the first verified piece.

There is no build system, test framework, or linter. `main.py` is the runnable entry point and `bencode.py` has a small `__main__` smoke test. `ubuntu.torrent` is a real single-file torrent checked in for manual testing.

`bittorent/` is a Python 3.14 virtualenv (created via `python3.14 -m venv bittorent`), not source code — ignore it when reading/searching. `requests` is the only third-party dependency (used by `tracker.py`); there is no requirements file, so install it into the venv by hand. Run from the venv: `source bittorent/bin/activate`, then:

```
python main.py        # announce, connect to peers, download + verify + write piece 0
python bencode.py     # decode ubuntu.torrent and print its metadata
```

The output file (named after the torrent, e.g. `ubuntu-*.iso`) is created in the working directory; `*.iso` is gitignored.

`personal_log.md` holds the developer's own notes; `TODO.md` lists known gaps.

Live testing is flaky for reasons outside the code: the Ubuntu tracker often returns a single peer (`185.125.190.59`) that completes the handshake but never unchokes, so runs time out. The peer list varies from run to run (sometimes a list with working IPv6 peers). Don't hammer the tracker with rapid re-announces.

## Flow (main.py)

1. Read `ubuntu.torrent`, decode it, compute the info hash (`bencode`).
2. Announce to the tracker (`tracker`) and parse the peer list.
3. Open the output file once (`'wb'`, which truncates), then for each peer: handshake → read first message (bitfield) → send INTERESTED → `wait_for_unchoke` → `download_piece(sock, 0, piece_length)` → `check_piece_hash` → if it matches, `write_piece` and `break`. Any exception for a peer is printed with a traceback and the loop moves on to the next peer.

## Modules

### `bencode.py` — bencode codec + torrent parsing
- `decode(data, start)` dispatches on the first byte (`i`, digit, `l`, `d`). Every decode function takes `(data, start)` and returns `(value, next_start)`; keep this convention. Strings and dict keys are raw `bytes` (e.g. `decoded[b'announce']`).
- `find_info_range` / `get_info_hash(data)` locate the `info` dict's exact byte range in the raw file and SHA1 it. The hash must come from the original bytes, not a re-encode. `get_info_hash` returns `(info_dict, info_hash)`.
- `parse_torrent` / `decode_torrent` are helpers; multi-file torrents raise `NotImplementedError`.
- Info-dict keys used elsewhere: `b'name'`, `b'length'`, `b'piece length'` (with a space), `b'pieces'` (concatenated 20-byte SHA1s, one per piece).

### `tracker.py` — HTTP tracker announce
- `generate_peer_id()`: Azureus-style `-PC0001-` + random suffix.
- `build_tracker_url` / `tracker_get`: GET with `compact=1`, `numwant=50`, `event=started`. Returns the raw bencoded body.
- `parse_peers`: handles the compact format (6 bytes per peer) and the non-compact list of dicts (the tracker sometimes answers with this, including IPv6 addresses). The separate `peers6` key is not read.

### `peer.py` — peer wire protocol
- Message ID constants, `BLOCK_SIZE = 16384`.
- `recv_exact`, `do_handshake` (checks only the info hash, 10 s socket timeout), `recv_message` (4-byte length prefix; returns `(None, None)` for keep-alives), `send_message`.
- `wait_for_unchoke(sock)`: loops until UNCHOKE, ignoring other messages.
- `request_block` sends a REQUEST. `download_block(sock, index, begin, length)` sends it and waits for the PIECE reply, returning the block data. `download_piece(sock, piece_index, length)` loops over a piece's blocks (last block shortened with `min`) into a `bytearray`.
- Not yet handled in `download_block`: a CHOKE just prints and keeps waiting (the peer drops the request), and the reply's index/begin are parsed but not compared with what was asked.

### `pieces.py` — verify and store
- `check_piece_hash(piece, index, pieces_hash)`: SHA1 of the bytes vs `pieces_hash[index*20 : index*20+20]`.
- `write_piece(index, data, piece_length, file)`: `seek(index * piece_length)` then `write`. Offset uses the standard piece length, so out-of-order pieces land correctly. Tested offline with fake pieces; piece 0 has also been verified end to end against a live peer (file SHA1 matched the torrent's piece-0 hash).

## Next steps
Outer loop over all pieces (last piece is shorter), track which pieces are done, use the peer's bitfield, retry on a bad hash, then CHOKE handling and the reply check, and finally multiple peers in parallel. See `TODO.md`.

## Working style
This is a learning project. The developer writes the code; Claude guides with hints, syntax and review rather than writing source for them, unless they ask explicitly.
