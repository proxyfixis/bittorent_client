# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project state

This is a from-scratch BitTorrent client written in Python, currently in early development. There is no build system, package manager config, test framework, or linter set up yet — just a few modules with bottom-of-file smoke tests (`if __name__ == '__main__':` blocks or bare top-level calls) that run against `ubuntu.torrent`, a real torrent file checked into the repo for manual testing.

`bittorent/` is a Python 3.14 virtualenv (created via `python3.14 -m venv bittorent`), not source code — ignore it when reading/searching the codebase. `requests` is the only third-party dependency (used by `tracker.py`); no requirements file exists yet, so install it manually in the venv if needed.

Running each module directly executes its ad-hoc test:

```
python3 bencode.py    # decodes ubuntu.torrent and prints metadata
python3 tracker.py    # does a full announce against ubuntu.torrent's tracker and prints peers
```

`personal_log.md` is the developer's running notes on issues hit and things to read up on — check it for context on known unresolved problems (e.g. the tracker currently only returns one peer despite `numwant`).

## Architecture

Two modules, connected by the bencode decoder as the shared foundation:

### `bencode.py` — bencode codec + torrent file parsing

Implements a bencode decoder (the encoding BitTorrent uses for `.torrent` files and tracker/peer wire messages) plus torrent-file-specific parsing on top of it.

- `decode(data, start)` — dispatches on `data[start]`: `i` → integer, ASCII digit → string, `l` → list, `d` → dict.
- `decode_int(data, start)` — parses `i<number>e`.
- `decode_string(data, start)` — parses `<length>:<bytes>`, the byte-string type used throughout bencode.
- `decode_list(data, start)` / `decode_dict(data, start)` — parse `l<items>e` / `d<kv-pairs>e` recursively via `decode`.

Every decode function takes `(data, start)` and returns `(value, next_start)`, where `next_start` is the index just past the parsed element. This pairing is the core convention of the module — any new decode function must follow it so `decode` can dispatch recursively and callers can keep advancing through a buffer. Decoded dict keys and strings are raw `bytes` (e.g. `decoded[b'announce']`), not `str` — bencode has no native text type.

- `decode_torrent(filepath)` — reads a `.torrent` file, decodes it fully, and separately re-locates and re-decodes just the `info` dict (by finding the `4:info` marker in the raw bytes) so its **exact original byte range** can be SHA1-hashed into `info_hash`. This byte-exact re-hash (rather than re-encoding the decoded dict) is required because the info hash must match what peers/trackers expect bit-for-bit.
- `parse_torrent(filepath)` — calls `decode_torrent` and extracts the fields a client needs (`name`, `piece_length`, `pieces`, `announce`). Handles single-file torrents (`info[b'length']`) vs multi-file torrents (`info[b'files']`), though the multi-file `files` list currently isn't included in the returned dict — that gap is worth checking before relying on it.

### `tracker.py` — HTTP tracker announce protocol

Talks to a torrent's tracker over HTTP to register the client and get a peer list. Depends on `bencode.decode` to parse the tracker's bencoded response, and independently recomputes the info hash from the raw file (`get_info_hash`) rather than importing torrent-parsing logic from `bencode.py`.

- `generate_peer_id()` — builds a 20-byte peer ID (Azureus-style `-PC0001-` prefix + random suffix).
- `build_tracker_url` / `tracker_get` — construct and issue the GET request against the announce URL with the standard tracker query params (`info_hash`, `peer_id`, `port`, `uploaded`, `downloaded`, `left`, `event`, `numwant`, etc.), and return the raw bencoded response body.
- `parse_peers(peers_bytes)` — parses the *compact* peer list format: 6 raw bytes per peer (4 bytes IP + 2 bytes big-endian port). Note the request currently sends `compact: 0` (non-compact) while `parse_peers` assumes the compact 6-byte format — if the tracker honors `compact=0` and returns a bencoded peer list instead, this parser will misbehave. Worth reconciling if peer parsing looks wrong.
