# GOAL.md - هدف پروژه ChatDash

## هدف کلی پروژه

**ChatDash** یک پلتفرم تجمع پیام‌های چندمنبعی (Unified Messaging Dashboard) است که امکان دریافت، نگهداری، و نمایش پیام‌ها از پلتفرم‌های مختلف گفتگو را فراهم می‌کند. پروژه از معماری **آفلاین-فرست** (Offline-First) پیروی می‌کند.

## قابلیت‌های پیاده‌شده فعلی

### 1. بک‌اند (Python/FastAPI)
| قابلیت | جزئیات | وضعیت |
|--------|---------|--------|
| فریم‌ورک وب | FastAPI با async support | ✅ پیاده‌شده |
| دیتابیس | PostgreSQL + SQLAlchemy 2.0 (async) | ✅ پیاده‌شده |
| مهاجرت‌ها | Alembic | ✅ پیاده‌شده |
| لاگ‌گذاری | structlog با خروجی JSON | ✅ پیاده‌شده |
| CORS | Middleware برای درخواست‌های بین‌سروری | ✅ پیاده‌شده |

### 2. ماژول Connection چت‌باش (Bale)
| قابلیت | جزئیات | وضعیت |
|--------|---------|--------|
| اتصال به Bale API | BaleConnector با پشتیبانی از حالت mock و real | ✅ پیاده‌شده |
| تست اتصال | `test_connection()` | ✅ پیاده‌شده |
| همگام‌سازی مکالمات | `sync_conversations()` با pagination | ✅ پیاده‌شده |
| دریافت پیام‌ها | `fetch_messages()` با cursor pagination | ✅ پیاده‌شده |
| rate limiting | محدودیت درخواست با تنظیمات قابل تنظیم | ✅ پیاده‌شده |

### 3. لایه دیتابیس
| جدول | فیلدهای کلیدی | وضعیت |
|-------|---------------|--------|
| `sources` | id, type, created_at | ✅ پیاده‌شده |
| `conversations` | id, source_id, remote_conversation_id, title, avatar_url, last_message_at, last_message_preview, unread_count, archived, pinned | ✅ پیاده‌شده |
| `messages` | id, conversation_id, source_message_id, direction, sender_name, body_text, body_type, created_at, status | ✅ پیاده‌شده |
| `sync_state` | source_id, cursor, last_success_at, last_error_at, last_error_msg, updated_at | ✅ پیاده‌شده |
| `drafts` | (Placeholder - Phase 3) | ⏳ نگهداری برای آینده |
| `outbox_queue` | (Placeholder - Phase 3) | ⏳ نگهداری برای آینده |

### 4. لایه API
| endpoint | متد | توضیح | وضعیت |
|----------|------|-------|--------|
| `/health` | GET | بررسی سلامت سرویس | ✅ پیاده‌شده |
| `/sources` | GET | لیست منابع پیام | ✅ پیاده‌شده |
| `/conversations` | GET | لیست مکالمات با cursor بردونی | ✅ پیاده‌شده |
| `/conversations/{conv_id}/messages` | GET | پیام‌های مکالمه | ✅ پیاده‌شده |
| `/sync/status` | GET | وضعیت همگام‌سازی | ✅ پیاده‌شده |
| `/sync/run` | POST | اجرای همگام‌سازی دستی | ✅ پیاده‌شده |

### 5. استراتژی‌های Cursor
پشتیبانی از چندین فرمت cursor برای هماهنگی با پلتفرم‌های مختلف:
| استراتژی | فرمت | استفاده |
|----------|--------|---------|
| ISO | base64-encoded ISO 8601 | ✅ پیش‌فرض |
| Mimo | `mimo:base64_iso` | ✅ پشتیبانی‌شده |
| OpenCode | `open:base64_millis` | ✅ پشتیبانی‌شده |
| Raw | رشته‌های خام | ✅ پشتیبانی‌شده |

### 6. زیرساخت‌ها
| مؤلفه | جزئیات | وضعیت |
|-------|---------|--------|
| Docker | تصویر پایه Python 3.11-slim | ✅ آماده |
| Docker Compose | سرویس db و api | ✅ پیاده‌شده |
| تست‌ها | pytest + pytest-asyncio | ✅ پیاده‌شده |
| .env | فایل تنظیمات محیطی | ✅ الگو موجود |

### 7. ساب‌ماژول‌ها (در پروژه حضور دارند اما فعلی توسط این ریپازیتوری مدیریت نمی‌شوند)
| ساب‌ماژول | پلتفرم | وضعیت |
|------------|---------|--------|
| `dashboard` | Laravel 11 + Vue.js 3 | ✅ موجود |
| `chatbot` | Node.js PWA | ✅ موجود |
| `crawler` | Laravel + Python Celery | ✅ موجود |
| `GhostRunner` | Playwright + Python | ✅ موجود |
| `ai-dashboard` | OpenWebUI + Mimo | ✅ موجود |
| `chat-assistant` | تعامل‌گر Chat + Dashboard | ✅ موجود |
| `frontend` | خالی (برای پیاده‌سازی بعدی) | ⏳ خالی |

## هدف‌های آینده (Phase‌های برنامه‌ریزی‌شده)

### Phase 1 فعلی (در حال اجرا)
- افزودن کانکتورهای دیگر (Eitaa, Rubika, Telegram, WhatsApp)
- تکمیل فریم‌ورک کانکتور
- یکپارچه‌سازی Frontend

### Phase 2
- افزودن queue برای پیام‌های خروجی
- پشتیبانی از ارسال پیام

### Phase 3
- افزودن جدول `drafts` برای پیش‌نویس‌ها
- افزودن `outbox_queue` برای صف خروجی

---

> **یادداشت**: این مستندات تحلیل وضعیت فعلی کدها را به‌روزرسانی می‌کند. برای نقشه راه دقیق‌تر، به `ROADMAP.md` مراجعه کنید.