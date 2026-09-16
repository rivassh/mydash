# ChatDash — Unified Messaging Dashboard

Offline-first messaging aggregator backend for the unified dashboard.

## Architecture

```
mydash/
├── app/                   # Python/FastAPI backend (ChatDash)
│   ├── api/               # FastAPI routes
│   ├── connectors/        # Platform connectors (Bale, Eitaa, etc.)
│   ├── core/              # Config, logging
│   ├── db/                # SQLAlchemy models, repositories, session
│   ├── schemas/           # Pydantic models
│   ├── sync/              # Sync engine with cursor pagination
│   └── jobs/              # Background jobs
├── shared/                # Cross-service shared utilities
│   └── cursor/            # Unified cursor encode/decode
├── frontend/              # Vue.js/React frontend (Takhte Sholokhte style)
├── dashboard/             # Laravel 11 + Vue.js 3 messaging hub (submodule)
├── crawler/               # Laravel + Python Celery data extraction (submodule)
├── chatbot/               # Node.js PWA chatbot (submodule)
├── GhostRunner/           # Job scraper for jobinja.ir, jobvision.ir (submodule)
├── ai-dashboard/          # OpenWebUI + custom dashboard (submodule)
├── tests/                 # Backend tests
├── alembic/               # SQLAlchemy migrations
├── docs/                  # Documentation
└── prompts/               # Original prompts and design notes
```

## Submodules

| Submodule       | Purpose                                        | URL                                      |
|-----------------|------------------------------------------------|------------------------------------------|
| `dashboard`     | Laravel 11 + Vue.js 3 messaging hub            | github.com/rivassh/dashboard             |
| `crawler`       | Laravel + Python Celery data extraction        | github.com/rivassh/crawler               |
| `chatbot`       | Node.js PWA AI chatbot                         | github.com/rivassh/chatbot               |
| `GhostRunner`   | Job scraper (jobinja.ir, jobvision.ir)         | github.com/rivassh/GhostRunner           |
| `ai-dashboard`  | OpenWebUI + custom dashboard                   | github.com/rivassh/ai-dashboard          |

## Cursor Flow

Central pagination thread across all services:

```
connector → sync engine → DB → API → frontend cards → cursor pagination
```

Cursor format: base64-encoded ISO timestamp (see `shared/cursor/`).

## Visual Style

Takhte Sholokhte / stickynote — each chat becomes a card with:
- Avatar, last message preview
- Position on the board
- Color by platform (Eitaa=Blue, Rubika=Yellow, Bale=Green, etc.)
- Priority level

## Getting Started

```bash
cp .env.example .env
docker compose up
```

API will be available at `http://localhost:8000`.