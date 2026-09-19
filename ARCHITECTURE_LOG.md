# ARCHITECTURE_LOG.md - معماری پروژه ChatDash

## نمای کلی معماری

```
mydash/
├── app/                          # Python/FastAPI backend (ChatDash)
│   ├── api/                      # FastAPI routes
│   │   ├── main.py               # Application entry point + root routes
│   │   └── endpoints.py          # /api/v1 routes (APIRouter)
│   ├── connectors/               # Platform connectors
│   │   ├── base.py               # BaseConnector abstract class
│   │   └── bale/
│   │       └── connector.py      # Bale connector (mock + real)
│   ├── core/                     # Config, logging
│   │   ├── config.py             # Settings dataclass
│   │   └── logging.py            # structlog configuration
│   ├── db/                       # SQLAlchemy models, repositories, session
│   │   ├── models.py             # ORM models
│   │   ├── repositories.py       # Repository layer
│   │   └── session.py            # AsyncSession management
│   ├── schemas/                  # Pydantic request/response models
│   ├── sync/                     # Sync engine with cursor pagination
│   │   └── engine.py             # SyncEngine orchestration
│   ├── jobs/                     # Background jobs (empty placeholder)
│   └── utils/                    # Utilities (empty placeholder)
├── shared/                       # Cross-service shared utilities
│   └── cursor/                   # Unified cursor encode/decode
│       ├── factory.py            # CursorFactory
│       └── strategies/           # iso, mimo, open_code, raw
├── alembic/                      # SQLAlchemy migrations
├── tests/                        # Backend tests
└── submodules/                   # dashboard, crawler, chatbot, GhostRunner, ai-dashboard, chat-assistant
```

## استک تکنولوژی

### بک‌اند اصلی (ChatDash)
| لایه | تکنولوژی | نسخه/جزئیات |
|------|----------|-------------|
| زبان | Python | 3.11+ |
| وب‌فریم‌ورک | FastAPI | >=0.110 |
| ORM | SQLAlchemy | 2.0+ (async) |
| درایور دیتابیس | asyncpg | >=0.29 |
| مهاجرت | Alembic | >=1.13 |
| اعتبارسنجی | Pydantic | >=2.5 |
| لاگ | structlog | >=24.0 |
| HTTP client | httpx | >=0.27 |
| تست | pytest, pytest-asyncio | >=8, >=0.23 |
| Container | Docker | python:3.11-slim |

### ساب‌ماژول‌ها
| ساب‌ماژول | تکنولوژی |
|------------|----------|
| `dashboard` | Laravel 11 + Vue.js 3 + MySQL 8.0 + Pinia + Axios |
| `chatbot` | Node.js + vanilla JS + PWA |
| `crawler` | Laravel + Python Celery |
| `GhostRunner` | Python 3.11 + Playwright + httpx |
| `ai-dashboard` | OpenWebUI + Python (mimo-adapter) + Nginx |
| `chat-assistant` | Express + Prisma + React + Vite |

### دیتابیس
| نوع | استفاده |
|------|---------|
| PostgreSQL 15 | دیتابیس اصلی ChatDash |
| MySQL 8.0 | دیتابیس dashboard (submodule) |

## الگوهای طراحی (Design Patterns) استفاده‌شده

### 1. Repository Pattern
- پیاده‌سازی: `app/db/repositories.py`
- کلاس‌ها: `SourceRepository`, `ConversationRepository`, `MessageRepository`, `SyncStateRepository`
- مسئولیت: جداسازی منطق دسترسی به دیتابیس از API و Sync Engine

### 2. Abstract Base Class (ABC) / Interface Pattern
- پیاده‌سازی: `app/connectors/base.py`
- کلاس: `BaseConnector`
- متدهای انتزاعی: `sync_conversations()`, `fetch_messages()`, `test_connection()`
- هدف: تعریف قرارداد ثابت برای همه connectorها

### 3. Strategy Pattern
- پیاده‌سازی: `shared/cursor/strategies/`
- کلاس پایه: `CursorStrategy`
- استراتژی‌های کنکرت: `Base64ISOCursorStrategy`, `MimoCodeCursorStrategy`, `OpenCodeCursorStrategy`, `RawCursorStrategy`
- هدف: انعطاف‌پذیری در فرمت cursor برای پلتفرم‌های مختلف

### 4. Factory Pattern
- پیاده‌سازی: `shared/cursor/factory.py`
- کلاس: `CursorFactory`
- مسئولیت: ایجاد نمونه مناسب از استراتژی cursor بر اساس نام

### 5. Sync Engine / Orchestration Pattern
- پیاده‌سازی: `app/sync/engine.py`
- کلاس: `SyncEngine`
- مسئولیت: هماهنگی جریان کامل همگام‌سازی (fetch → upsert → update cursor)

### 6. Dependency Injection
- پیاده‌سازی: `app/db/session.py`
- تابع: `get_session()`
- استفاده: FastAPI `Depends(get_session)` برای تزریق AsyncSession

### 7. Data Transfer Object (DTO) / Pydantic Schemas
- پیاده‌سازی: `app/schemas/__init__.py`
- کلاس‌ها: `ConversationList`, `MessageList`, `SyncStatus`, `SyncRunResponse`, `SourceInfo`, `SourceListResponse`, `SyncStatusResponse`, `CursorResponse`, `HealthResponse`

### 8. Upsert Pattern
- پیاده‌سازی: `app/db/repositories.py`
- مکانیزم: PostgreSQL `INSERT ... ON CONFLICT DO UPDATE`
- هدف: idempotency در همگام‌سازی

### 9. Cursor-Based Pagination
- پیاده‌سازی: `shared/cursor/` + `app/db/repositories.py`
- هدف: pagination کارآمد برای دیتاست‌های بزرگ

### 10. Mock Object Pattern
- پیاده‌سازی: `app/connectors/bale/connector.py`
- حالت: `mode="mock"`
- هدف: توسعه و تست بدون وابستگی به API واقعی

## جریان داده (Data Flow)

### جریان همگام‌سازی (Sync Flow)
```
BaleConnector.sync_conversations()
    ↓
SyncEngine._sync_conversations()
    ↓
ConversationRepository.upsert_conversation()
    ↓
SyncEngine._sync_messages()
    ↓
MessageRepository.upsert_message()
    ↓
SyncStateRepository.create_or_update_state()
    ↓
API → Frontend (cursor pagination)
```

### جریان cursor
```
connector → sync engine → DB → API → frontend cards → cursor pagination
```

## ساختار دیتابیس (Schema)

### جدول `sources`
| فیلد | نوع | توضیح |
|------|-----|-------|
| id | Integer PK | کلید اصلی |
| type | String(50) | نوع منبع (فعلاً فقط bale) |
| created_at | DateTime | زمان ایجاد |

### جدول `conversations`
| فیلد | نوع | توضیح |
|------|-----|-------|
| id | Integer PK | کلید اصلی |
| source_id | Integer FK | ارجاع به sources |
| remote_conversation_id | String(255) | شناسه در پلتفرم مقصد |
| title | String(500) | عنوان مکالمه |
| avatar_url | String(1000) | URL آواتار |
| last_message_at | DateTime | زمان آخرین پیام |
| last_message_preview | String(500) | پیش‌نمایش آخرین پیام |
| unread_count | Integer | تعداد خوانده‌نشده‌ها |
| archived | Boolean | وضعیت بایگانی |
| pinned | Boolean | وضعیت سنجاق‌شده |
| sync_updated_at | DateTime | زمان آخرین همگام‌سازی |

**Constraintها:**
- `UniqueConstraint(source_id, remote_conversation_id)`
- `Index(source_id, last_message_at)`

### جدول `messages`
| فیلد | نوع | توضیح |
|------|-----|-------|
| id | Integer PK | کلید اصلی |
| conversation_id | Integer FK | ارجاع به conversations |
| source_message_id | String(255) | شناسه در پلتفرم مقصد |
| direction | String(10) | جهت پیام (in/out) |
| sender_name | String(255) | نام فرستنده |
| body_text | Text | متن پیام |
| body_type | String(50) | نوع بدنه |
| created_at | DateTime | زمان ایجاد |
| status | String(50) | وضعیت پیام |

**Constraintها:**
- `UniqueConstraint(conversation_id, source_message_id)`
- `Index(conversation_id, created_at)`

### جدول `sync_state`
| فیلد | نوع | توضیح |
|------|-----|-------|
| source_id | Integer PK/FK | ارجاع به sources |
| cursor | Text | cursor فعلی همگام‌سازی |
| last_success_at | DateTime | آخرین موفقیت |
| last_error_at | DateTime | آخرین خطا |
| last_error_msg | Text | پیام خطا |
| updated_at | DateTime | زمان به‌روزرسانی |

### جدول‌های Placeholder (Phase 3)
- `drafts`: برای ذخیره پیش‌نویس پیام‌ها
- `outbox_queue`: صف پیام‌های خروجی

## نکات معماری مهم

### 1. جداسازی لایه‌ها
- `app/api/` → endpointها
- `app/sync/` → منطق همگام‌سازی
- `app/connectors/` → ارتباط با پلتفرم‌های خارجی
- `app/db/` → دسترسی به دیتابیس
- `app/schemas/` → مدل‌های Pydantic

### 2. Async-first
تمام عملیات دیتابیس و I/O به صورت async طراحی شده‌اند.

### 3. Idempotency
با استفاده از unique constraints و upsert، همگام‌سازی‌های تکراری بدون ایجاد duplicate انجام می‌شوند.

### 4. Pluggable Architecture
با استفاده از `BaseConnector` و `CursorStrategy`، افزودن پلتفرم‌های جدید بدون تغییر در هسته سیستم ممکن است.

### 5. Mock-first Development
Bale connector به صورت mock-first طراحی شده تا توسعه و تست بدون وابستگی به API واقعی ممکن باشد.

## فایل‌های کلیدی برای توسعه آینده

| فایل | مسئولیت |
|------|---------|
| `app/connectors/base.py` | قرارداد connectorها |
| `app/connectors/bale/connector.py` | پیاده‌سازی Bale |
| `app/sync/engine.py` | موتور همگام‌سازی |
| `app/db/repositories.py` | لایه دسترسی به دیتابیس |
| `shared/cursor/` | سیستم cursor |
| `alembic/versions/` | مهاجرت‌های دیتابیس |

---

> **یادداشت**: این مستند تحلیل وضعیت فعلی معماری کدها را ثبت می‌کند. برای جزئیات بیشتر به `ROADMAP.md` مراجعه کنید.