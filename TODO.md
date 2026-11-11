# TODO

## Next up (roughly in order)
- [ ] Outer loop over every piece. The last piece is shorter: its length is the file length minus `index * piece_length`.
- [ ] Track which pieces are done / still needed (a set or list). Only mark a piece done after the hash matches and the write succeeded.
- [ ] Use the peer's bitfield (`main.py` saves it but never reads it) so we only ask a peer for pieces it has. Update it on HAVE messages.
- [ ] Retry a piece when the hash fails (ideally from another peer) instead of writing it.
- [ ] Resume: don't truncate the output with `'wb'` if it already exists; check which pieces are already on disk.

## Known gaps
- [ ] `download_block`: after a `CHOKE` the peer drops the pending request. Call `wait_for_unchoke`, then re-send the request.
- [ ] `download_block`: compare the reply's index/begin with what was requested (a stray or duplicate PIECE would otherwise land in the wrong place).
- [ ] The first message after the handshake is assumed to be a bitfield; anything else is skipped silently. Print/handle other IDs (the Ubuntu server peer sends something else, then HAVE, and never unchokes).
- [ ] 10 s socket timeout may be too short to wait for an unchoke (peers rotate optimistic unchokes about every 30 s). Untested idea: raise it for `wait_for_unchoke`.
- [ ] Handshake only checks the info hash (bytes 28:48). Also check the protocol string (bytes 0:20).
- [ ] Pipelining: keep about 5 requests in flight per peer instead of one at a time.
- [ ] `slice assignment` in `download_piece` silently resizes the buffer if a block comes back the wrong length; check `len()` first.

## Not supported yet
- [ ] Multi-file torrents. `parse_torrent` and `main.py` raise `NotImplementedError` when `b'files'` is in the info dict. Needs a total length (sum of each file's `length`) and a piece-offset -> file mapping when writing to disk.
- [ ] `peers6` (BEP 7) from compact responses. The tracker currently also returns IPv6 peers inline in the non-compact list, which `parse_peers` handles.
- [ ] Several peers at once (`threading` + shared queue, or `asyncio`).
- [ ] `announce-list`, re-announcing (`interval`), UDP trackers (BEP 15), DHT/PEX.
- [ ] Seeding (answering REQUESTs, sending our own bitfield/HAVE).

## Housekeeping
- [ ] Add a `requirements.txt` (`requests`).
