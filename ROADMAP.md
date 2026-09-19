# ROADMAP.md - نقشه راه توسعه پروژه ChatDash

## وضعیت فعلی کد

بر اساس اسکن کامل ریپازیتوری، وضعیت کد عبارت است از:
- Phase 1 (Bale connector + Sync Engine + CRUD) در حال حاضر پیاده‌سازی شده
- فریم‌ورک Connector با قابلیت‌های محدود (فقط Bale و mock mode به صورت کامل)
- cursor-based pagination در عمل نیست (mock cursor واقعی مقدار numeric می‌دهد)
- دیتابیس Schema کامل هست اما آماری مهاجرت Alembic تنها 2 کلمن محدود اضافه می‌کند
- چندین file module placeholder هستند (jobs, utils, frontend) که هنوز پر نشده‌اند
- یک Plan مستند در `.mimocode/plans/` با گام‌های مشخص وجود دارد

## باگ‌های دیده‌شده در اسکن

### باگ 1: Cursor Mock نامرتبط با DB
**مشکل:** در `BaleConnector._mock_conversations()` cursor به صورت numeric (مثلاً `5`) بازگردانده می‌شود، اما `SyncEngine._sync_conversations()` سعی می‌کند از `cursor_factory.encode_cursor()` روی `last_message_at` استفاده کند که هیچ‌وقت تعریف نشده، بنابراین `None` می‌دهد.  
**فایل:** `app/connectors/bale/connector.py` و `app/sync/engine.py`  
**تأثیر:** همگام‌سازی واقعی cursor می‌شکند.

### باگ 2: هماهنگی Schema و Alembic
**مشکل:** `alembic/versions/0518da58b8c2_initial_migration.py` فقط 2 کلمن (`direction` روی `messages` و `type` روی `sources`) اضافه می‌کند، اما `app/db/models.py` تعریف کامل Schema دارد. هیچ `create_tables` در مهاجرت نیست.  
**فایل:** `alembic/versions/0518da58b8c2_initial_migration.py`  
**تأثیر:** در محیط توسعه جدید، دیتابیس با مدل‌ها هماهنگ نخواهد بود.

### باگ 3: تکراری بودن Endpoints
**مشکل:** هر دو `app/api/main.py` و `app/api/endpoints.py` همه endpoints را تعریف کرده‌اند. اگر هر دو به همین شکل registered شوند، conflict ایجاد می‌شود.  
**فایل:** `app/api/main.py` و `app/api/endpoints.py`  
**تأثیر:** نامشخص - ممکن است conflict در runtime ایجاد شود.

### باگ 4: `source_id` سخت‌افزاری در `Trigger Sync`
**مشکل:** در `app/api/endpoints.py:trigger_sync`، `source_id` به صورت `source.id if source else 1` تنظیم می‌شود و connector با `source_id=0` ایجاد می‌شود که با فرض DB inconsistent است.  
**فایل:** `app/api/endpoints.py`  
**تأثیر:** همگام‌سازی با source_id نادرست.

### باگ 5: `cursor` در `SyncEngine.run_sync` بازنویسی می‌شود
**مشکل:** در `app/sync/engine.py:run_sync`، `cursor` قبل از sync از DB خوانده می‌شود و در `create_or_update_state` با همان مقدار قبلی ذخیره می‌شود. با اینکه `_sync_conversations` تغییر `cursor` می‌دهد، اما مقدار آن در متغیر محلی `cursor` ذخیره نمی‌شود.  
**فایل:** `app/sync/engine.py`  
**تأثیر:** cursor پس از sync آپدیت نمی‌شود و no-op می‌شود.

### باگ 6: نبود `__init__` در `shared/models`
**مشکل:** دایرکتوری `shared/models` وجود دارد اما هیچ فایلی ندارد.  
**فایل:** `shared/models/`  
**تأثیر:** این ماژول import نمی‌شود و باعث import error می‌شود اگر استفاده شود.

### باگ 7: Mock Conversation Pagination Conflict
**مشکل:** در `BaleConnector._mock_conversations()`، IDها به صورت `bale_conv_{i}` تولید می‌شوند اما در تست‌های `test_cursor_strategies.py` و `test_bale_connector.py` بدون conflict تولید می‌شوند. در بارگذاری مجدد، conflict ایجاد می‌شود.  
**فایل:** `app/connectors/bale/connector.py`  
**تأثیر:** data inconsistency در حالت mock.

## فازبندی گام‌های بعدی

### فاز 0: امکان‌سنجی و رفع باگ‌ها (فوری)
**هدف:** پایدارسازی کد فعلی و رفع باگ‌های شناسایی‌شده  
**مدت تخمینی:** 1-2 هفته

| # | وظیفه | فایل | اولویت |
|---|--------|------|--------|
| 0.1 | رفع باگ cursor در BaleConnector mock mode | `app/connectors/bale/connector.py` | Critical |
| 0.2 | هماهنگی Alembic migration با models | `alembic/` | Critical |
| 0.3 | رفع تکراری بودن endpoints | `app/api/main.py`, `app/api/endpoints.py` | High |
| 0.4 | رفع source_id در trigger_sync | `app/api/endpoints.py` | High |
| 0.5 | رفع آپدیت cursor در SyncEngine | `app/sync/engine.py` | Critical |
| 0.6 | ایجاد `shared/models/` یا حذف دایرکتوری خالی | `shared/models/` | Medium |
| 0.7 | استقرار تست‌های یکپارچه | `tests/` | High |

### فاز 1: چندپلتفرمی و یکپارچگی Connector (هسته‌ای)
**هدف:** افزودن connectors جدید و یکپارچه‌سازی با dashboard  
**مدت تخمینی:** 3-4 هفته  
**مرتبط با Plan:** Phase 2 (Backend Integration)

| # | وظیفه | جزئیات |
|---|--------|---------|
| 1.1 | ساخت `shared/docs/CONNECTOR-CONTRACT.md` | قرارداد زبان‌مشترک connector |
| 1.2 | ایجاد `app/connectors/registry.py` | Registry pattern برای مدیریت connectorها |
| 1.3 | افزودن `StatefulBaseConnector` | پشتیبانی از connectors مرورگر |
| 1.4 | connector Eitaa | adapter with EitaaConnector |
| 1.5 | connector Rubika | stub + real |
| 1.6 | connector Telegram | stub + real |
| 1.7 | connector WhatsApp | stub + real |
| 1.8 | connector ChatGPT | stub + real |
| 1.9 | connector Grok | stub + real |
| 1.10 | connector Email | stub + real |
| 1.11 | connector Todo | stub + real |

### فاز 2: Frontend و یکپارچگی UI
**هدف:** پیاده‌سازی رابط کاربری و اتصال به backend  
**مدت تخمینی:** 4-5 هفته  
**مرتبط با Plan:** Phase 3 (Frontend Integration)

| # | وظیفه | جزئیات |
|---|--------|---------|
| 2.1 | پیاده‌سازی Frontend (`frontend/`) | Vue.js/React (Takhte Sholokhte style) |
| 2.2 | کارت چت با platform colors | Eitaa=Blue, Rubika=Yellow, Bale=Green |
| 2.3 | اتصال به backend cursor pagination | |
| 2.4 | Dashboard routing and responsive layout | |
| 2.5 | Chat card list + detail view | |
| 2.6 | Send/receive message flow | |
| 2.7 | Dashboard integration with submodule | |

### فاز 3: Crawler و GhostRunner
**هدف:** یکپارچه‌سازی داده‌های استخراج‌شده و نمایش به عنوان کارت | **مدت تخمینی:** 3-4 هفته  
**مرتبط با Plan:** Phase 4

| # | وظیفه | جزئیات |
|---|--------|---------|
| 3.1 | endpoint دریافت داده crawler | |
| 3.2 | endpoint job scraping GhostRunner | |
| 3.3 | نمایش داده‌های scrape شده به عنوان کارت | |
| 3.4 | enrichment برای تصاویر/فایل‌ها | |

### فاز 4: یکپارچگی AI
**هدف:** افزودن استعدادهای هوش مصنوعی | **مدت تخمینی:** 4-5 هفته  
**مرتبط با Plan:** Phase 5

| # | وظیفه | جزئیات |
|---|--------|---------|
| 4.1 | ChatGPT/Grok connectors | |
| 4.2 | رابط مکالمه AI | |
| 4.3 | خلاصه‌سازی پیام با AI | |
| 4.4 | AI assistant on top of chatbot | |

### فاز 5: Quality و DevOps
**هدف:** آماده‌سازی برای تولید | **مدت تخمینی:** 2-3 هفته

| # | وظیفه | جزئیات |
|---|--------|---------|
| 5.1 | CI/CD pipeline | GitHub Actions |
| 5.2 | Monitoring & Alerting | |
| 5.3 | Crash reporting | |
| 5.4 | Performance testing | |
| 5.5 | Security audit | |

---

## نکات پیاده‌سازی

### Branch Strategy (از Plan)
- `main` — تمام قابلیت‌های قابل اجرا
- `develop` — مستندات، prompt‌ها و توضیحات طراحی (در صورت نیاز)

### Docker-orchestration (از Plan)
- `docker-compose.yml` در ریشه برای تمامی سرویس‌ها
- per-service compose files با `extends` (در صورت نیاز)

### پیش‌نیازها برای شروع
- دسترسی به GitHub (ابزار submodule)
- نصب Docker و Docker Compose
- تنظیمات environment (.env)
- دسترسی به PostgreSQL

---

## مکانیزم Cursor فعلی

| مکانیزم | فرمت | توضیح |
|----------|-------|--------|
| `shared/cursor/encode_cursor(dt)` | base64(ISO timestamp) | پیش‌فرض |
| `shared/cursor/decode_cursor(cursor)` | از base64 به datetime | پیش‌فرض |
| `CursorFactory(strategy)` | چند استراتژی | iso, mimo, open_code, raw |

---

## مکانیزم Upsert فعلی

```python
# در repositories.py برای همه entity ها
pg_insert(Entity).values(...).on_conflict_do_update(
    index_elements=[...],
    set_={...}
).returning(Entity.id)
```

با fallback به:
1. `SELECT` برای چک کردن وجود
2. `UPDATE` اگر وجود دارد
3. `INSERT` اگر وجود ندارد

---

> **یادداشت**: این نقشه راه بر اساس اسکن کدها و مستند موجود در `.mimocode/plans/1789477899617-quick-star.md` تهیه شده است. برای تغییرات یا اضافه کردن فاز جدید، این فایل باید به‌روزرسانی شود.
