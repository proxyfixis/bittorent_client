# TODO

## Not supported yet
- [ ] Multi-file torrents. `parse_torrent` and `main.py` currently raise `NotImplementedError` when `b'files'` is in the info dict. Needs a `total_length(info)` helper (sum of each file's `length`) and a piece-offset -> file mapping when writing to disk.
- [ ] IPv6 peers. Trackers return them under a separate `peers6` key (BEP 7), compact, 18 bytes per peer (16 IP + 2 port). `parse_peers` only reads `peers`.

## Known gaps
- [ ] After a `CHOKE` the pending request is dropped by the peer. Re-send `request_piece` after the next `UNCHOKE`.
- [ ] Handshake only checks the info hash (bytes 28:48). Also check the protocol string (bytes 0:20).
- [ ] CLAUDE.md is stale (still says the tracker request sends `compact: 0`).
