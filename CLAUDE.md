# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project state

This is a from-scratch BitTorrent client written in Python, currently in very early development. There is no build system, package manager config, test framework, or linter set up yet — just a single module (`bencode.py`) with a bottom-of-file smoke test (`print` statements run on import).

Running the module directly executes the ad-hoc test at the bottom of the file:

```
python3 bencode.py
```

## Architecture

`bencode.py` implements a bencode decoder (the encoding BitTorrent uses for `.torrent` files and tracker/peer wire messages). The decoder works on raw `bytes`, not `str`, and follows a recursive-descent structure keyed off the leading byte at the current position:

- `decode(data, start)` — dispatches on `data[start]`: `i` → integer, ASCII digit → string, `l` → list (dict `d` and end markers are not yet handled).
- `decode_int(data, start)` — parses `i<number>e`.
- `decode_string(data, start)` — parses `<length>:<bytes>`, the byte-string type used throughout bencode.
- `decode_list(data, start)` — parses `l<items>e`; **currently unimplemented** (stubbed out, returns `None`).

Every decode function takes `(data, start)` and returns `(value, next_start)`, where `next_start` is the index just past the parsed element. This pairing is the core convention of the module — any new decode function (e.g. for dicts, or completing `decode_list`) must follow it so `decode` can dispatch recursively and callers can keep advancing through a buffer.
