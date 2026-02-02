# EmailSorter (Standalone EXE)

A fully offline, append-only email classification and summary tool.

## Features

- Drag & drop `.eml` and `.msg` files
- Local parsing (no Outlook dependency)
- Local clustering (HashingVectorizer + MiniBatchKMeans)
- Append-only Excel writing (openpyxl)
- Safe idempotency with `_Index`
- Topic mapping with editable `_TopicMap`
- Rebuild Summary dynamically
- Near-duplicate detection with semantic Jaccard similarity
- Zero cloud usage, works offline

## Excel Structure

- `_Index` — processed email keys
- `_TopicMap` — domain + subtopic mappings (editable)
- `Summary` — rebuilt each run
- `topic_<domain>` — append-only rows per domain

## Build (GitHub)

Tag a release:
