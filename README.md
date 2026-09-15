# ChatDash

Offline-first messaging aggregator backend. Phase 1 ships the **Bale**
connector, a PostgreSQL-backed store, an incremental sync engine, and a
REST API for an Android client.

## Stack

- Python 3.11+, FastAPI
- PostgreSQL (asyncpg) + Alembic migrations
- Structured logging (structlog)
- Docker Compose for local run

## Quick start

```bash
cp .env.example .env   # edit values as needed
docker compose up --build
```

API is then available at `http://localhost:8000`.

## Endpoints

| Method | Path                          | Description                              |
| ------ | ----------------------------- | ---------------------------------------- |
| GET    | `/health`                     | Liveness probe                           |
| GET    | `/sources`                    | Available connector sources              |
| GET    | `/conversations`              | Cursor-paginated conversation list       |
| GET    | `/conversations/{id}/messages`| Cursor-paginated messages for a convo    |
| GET    | `/sync/status`                | Last sync state for a source             |
| POST   | `/sync/run`                   | Trigger a sync run for a source          |

## Triggering a sync manually

```bash
curl -X POST "http://localhost:8000/sync/run?sourceType=bale"
```

## Known limitations (Phase 1)

- Bale connector is a **pluggable adapter**. Real mode issues HTTP calls to
  `BALE_BASE_URL` using the configured endpoints; if the exact Bale API is
  unknown, set `BALE_CONNECTOR_MODE=mock` for local development. The adapter
  interface is stable for Phases 2-5.
- No background scheduler process is wired yet; `POST /sync/run` runs the sync
  synchronously with bounded batch sizes.
- Drafts / outbox are schema placeholders only.