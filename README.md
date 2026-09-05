# Narra

**Narra** is an audiobook-only Usenet indexer. It is designed to index audiobook releases directly rather than operate as a generic Usenet indexer with an audiobook filter bolted on afterward.

> Current version: `0.1.0-alpha`

## What Narra does

- Connects to one or more SSL-capable NNTP providers.
- Incrementally scans configured Usenet groups using `GROUP` + `OVER`/`XOVER` style overview retrieval.
- Persists group high-water marks so restarts do not trigger full rescans.
- Parses multipart subjects and groups related Usenet articles into releases.
- Classifies audiobook candidates using deterministic audiobook/audio/archive/video signals.
- Probes the first yEnc article when a release is obfuscated so Narra can recover the encoded filename without downloading the full payload.
- Extracts common author/title/series/narrator/abridged/codec metadata from release names.
- Stores authors, narrators, series, books, editions, releases, files, articles, providers, groups, API keys, scan state, and metadata matches.
- Provides PostgreSQL full-text search plus `pg_trgm` fuzzy matching.
- Generates valid NZB XML directly from stored Usenet message IDs.
- Exposes a lightweight web UI and a Newznab-compatible `/api` endpoint.

## Quick start with Docker

Requirements: Docker with the Compose plugin.

```bash
git clone https://github.com/terralayer/Narra.git
cd Narra
cp .env.example .env
docker compose up -d --build
```

Open:

```text
http://localhost:8787
```

The Docker stack contains Narra plus PostgreSQL 16. PostgreSQL data is persisted in the `narra-db` volume.

To stop Narra:

```bash
docker compose down
```

To remove the development database too:

```bash
docker compose down -v
```

## First-time setup

1. Open **Settings**.
2. Add your NNTP provider host, SSL port, username, and password.
3. Add an audiobook-related Usenet group.
4. Click **Scan now** for the group.
5. Accepted audiobook releases will appear in Dashboard/Search.
6. Open a release to inspect classification reasons, completeness, Usenet articles, and download its generated NZB.

Narra currently stores NNTP credentials in its application database. Treat `0.1.0-alpha` as a private/self-hosted test build and restrict access accordingly.

## Newznab API

Capabilities:

```text
GET /api?t=caps
```

Search:

```text
GET /api?t=search&q=mistborn&apikey=YOUR_KEY
```

Book-style search is advertised in caps and uses the same audiobook-only result set.

The default development key is `narra-dev-key`. Change it before exposing Narra outside a trusted network:

```bash
NARRA_API_KEY='replace-this' docker compose up -d
```

## Local Python development

Narra targets Python 3.12.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e '.[test]'
pytest
uvicorn narra.app:app --reload
```

Without `NARRA_DATABASE_URL`, local development defaults to SQLite at `./narra.db`. Docker uses PostgreSQL.

## Database migrations

```bash
alembic upgrade head
```

On PostgreSQL, migration `0002` enables `pg_trgm` and creates trigram/full-text indexes for release search.

## Architecture

```text
NNTP provider
    |
    v
incremental overview scanner
    |
    v
subject parser -> multipart grouper -> audiobook classifier
                                      |
                         rejected <---+---> accepted
                                               |
                         yEnc filename probe --+
                                               |
                                               v
                                      metadata extraction
                                               |
                                               v
                                          PostgreSQL
                                          /        \
                                         v          v
                                    Web search   Newznab API
                                         \          /
                                          v        v
                                           NZB output
```

Core modules:

- `narra/nntp.py` — NNTP connection, overview scanning, yEnc filename probing.
- `narra/subjects.py` — Usenet subject parsing.
- `narra/grouping.py` — multipart grouping and completeness calculation.
- `narra/classifier.py` — deterministic audiobook acceptance/rejection logic.
- `narra/metadata.py` — common audiobook metadata extraction.
- `narra/scanner.py` — incremental ingestion and persistence.
- `narra/search.py` — SQLite-compatible search plus PostgreSQL FTS/trigram search.
- `narra/nzb.py` — NZB XML generation.
- `narra/app.py` — FastAPI web UI and Newznab API.

## CI verification

GitHub Actions verifies:

- subject parsing
- multipart grouping/completeness
- audiobook classification/rejection
- metadata extraction
- NZB generation
- Newznab caps/API-key behavior
- persistent high-water scanning
- Alembic migration application
- Docker Compose build/startup against PostgreSQL

## Scope of `0.1.0-alpha`

This release is intended to prove the end-to-end private-indexer flow: configure NNTP, scan incrementally, identify audiobooks, search them, and produce usable NZBs/Newznab results.

Planned follow-on work includes richer external metadata matching, provider failover/connection pools, background/continuous scanning, more advanced duplicate/repost consolidation, encrypted credential storage, API-key management UI, and deeper Newznab compatibility.
