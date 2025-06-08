# 📋 دليل متغيرات البيئة - Environment Variables Guide

هذا الدليل يشرح جميع متغيرات البيئة المتاحة في البوت وكيفية استخدامها.

This guide explains all available environment variables in the bot and how to use them.

## 🚀 البدء السريع - Quick Start

1. انسخ ملف `.env.example` إلى `.env`:
   \`\`\`bash
   cp .env.example .env
   \`\`\`

2. أو استخدم السكربت التفاعلي:
   \`\`\`bash
   chmod +x setup_env.sh
   ./setup_env.sh
   \`\`\`

## 📚 فهرس المتغيرات - Variables Index

### 🤖 إعدادات البوت الأساسية - Basic Bot Settings

| المتغير | مطلوب | الوصف | مثال |
|---------|-------|-------|------|
| `BOT_TOKEN` | ✅ | توكن البوت من BotFather | `1234567890:ABC...` |
| `BOT_NAME` | ❌ | اسم البوت | `ForwardBot` |
| `DEVELOPER_ID` | ✅ | معرف المطور الرئيسي | `123456789` |

### 🗄️ إعدادات قاعدة البيانات - Database Settings

| المتغير | مطلوب | الوصف | القيم المقبولة |
|---------|-------|-------|---------------|
| `DATABASE_TYPE` | ✅ | نوع قاعدة البيانات | `sqlite`, `postgresql`, `mysql` |
| `DATABASE_PATH` | ❌ | مسار قاعدة SQLite | `data/bot.db` |
| `DATABASE_HOST` | ❌ | عنوان خادم قاعدة البيانات | `localhost` |
| `DATABASE_PORT` | ❌ | منفذ قاعدة البيانات | `5432` |
| `DATABASE_NAME` | ❌ | اسم قاعدة البيانات | `telegram_bot` |
| `DATABASE_USER` | ❌ | مستخدم قاعدة البيانات | `bot_user` |
| `DATABASE_PASSWORD` | ❌ | كلمة مرور قاعدة البيانات | `password` |
| `DATABASE_URL` | ❌ | رابط قاعدة البيانات الكامل | `postgresql://user:pass@host:port/db` |

### 🔐 إعدادات الأمان - Security Settings

| المتغير | مطلوب | الوصف | ملاحظات |
|---------|-------|-------|---------|
| `ENCRYPTION_KEY` | ✅ | مفتاح التشفير | يجب أن يكون 32 حرف |
| `ADMIN_PASSWORD` | ✅ | كلمة مرور لوحة الإدارة | استخدم كلمة مرور قوية |
| `JWT_SECRET` | ✅ | مفتاح JWT للمصادقة | يُنشأ تلقائياً |

### 🌐 إعدادات Webhook - Webhook Settings

| المتغير | مطلوب | الوصف | القيم المقبولة |
|---------|-------|-------|---------------|
| `USE_WEBHOOK` | ❌ | تفعيل وضع Webhook | `true`, `false` |
| `WEBHOOK_URL` | ❌ | رابط الخادم للـ Webhook | `https://yourdomain.com/webhook` |
| `WEBHOOK_PORT` | ❌ | منفذ الخادم المحلي | `8443` |
| `SSL_CERT_PATH` | ❌ | مسار شهادة SSL | `/path/to/cert.pem` |
| `SSL_KEY_PATH` | ❌ | مسار المفتاح الخاص | `/path/to/key.pem` |

### 📊 إعدادات السجلات - Logging Settings

| المتغير | مطلوب | الوصف | القيم المقبولة |
|---------|-------|-------|---------------|
| `LOG_LEVEL` | ❌ | مستوى السجلات | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `LOG_TO_FILE` | ❌ | حفظ السجلات في ملف | `true`, `false` |
| `LOG_FILE_PATH` | ❌ | مسار ملف السجلات | `logs/bot.log` |
| `LOG_MAX_SIZE` | ❌ | الحد الأقصى لحجم ملف السجل (MB) | `10` |
| `LOG_BACKUP_COUNT` | ❌ | عدد ملفات السجل المحفوظة | `5` |

### ⚡ إعدادات الأداء - Performance Settings

| المتغير | مطلوب | الوصف | القيم الافتراضية |
|---------|-------|-------|-----------------|
| `MAX_CONCURRENT_OPERATIONS` | ❌ | عدد العمليات المتزامنة القصوى | `10` |
| `OPERATION_TIMEOUT` | ❌ | مهلة انتظار العمليات (ثانية) | `30` |
| `CACHE_SIZE_LIMIT` | ❌ | حجم ذاكرة التخزين المؤقت | `1000` |
| `CACHE_EXPIRATION` | ❌ | مدة انتهاء صلاحية التخزين المؤقت (ثانية) | `3600` |

### 📤 إعدادات التوجيه - Forwarding Settings

| المتغير | مطلوب | الوصف | القيم الافتراضية |
|---------|-------|-------|-----------------|
| `DEFAULT_FORWARD_DELAY` | ❌ | التأخير الافتراضي بين الرسائل (ثانية) | `1` |
| `MAX_MESSAGES_PER_MINUTE` | ❌ | الحد الأقصى للرسائل في الدقيقة | `20` |
| `SAVE_DELETED_MESSAGES` | ❌ | حفظ الرسائل المحذوفة | `true` |
| `TRACK_MESSAGE_EDITS` | ❌ | تتبع تعديل الرسائل | `true` |

### 👤 إعدادات Userbot - Userbot Settings

| المتغير | مطلوب | الوصف | ملاحظات |
|---------|-------|-------|---------|
| `ENABLE_USERBOT` | ❌ | تفعيل دعم Userbot | `true`, `false` |
| `TELEGRAM_API_ID` | ❌ | API ID من my.telegram.org | احصل عليه من my.telegram.org |
| `TELEGRAM_API_HASH` | ❌ | API Hash من my.telegram.org | احصل عليه من my.telegram.org |
| `USERBOT_PHONE` | ❌ | رقم الهاتف للـ Userbot | بصيغة دولية |

### 🔔 إعدادات الإشعارات - Notification Settings

| المتغير | مطلوب | الوصف | القيم الافتراضية |
|---------|-------|-------|-----------------|
| `ENABLE_ERROR_NOTIFICATIONS` | ❌ | تفعيل إشعارات الأخطاء | `true` |
| `NOTIFICATION_CHANNEL_ID` | ❌ | معرف قناة الإشعارات | - |
| `ENABLE_DAILY_STATS` | ❌ | تفعيل الإحصائيات اليومية | `false` |
| `DAILY_STATS_TIME` | ❌ | وقت إرسال الإحصائيات | `09:00` |

### 💾 إعدادات النسخ الاحتياطي - Backup Settings

| المتغير | مطلوب | الوصف | القيم الافتراضية |
|---------|-------|-------|-----------------|
| `ENABLE_AUTO_BACKUP` | ❌ | تفعيل النسخ الاحتياطي التلقائي | `true` |
| `BACKUP_DIR` | ❌ | مجلد النسخ الاحتياطية | `backups` |
| `BACKUP_FREQUENCY` | ❌ | تكرار النسخ الاحتياطي (ساعة) | `24` |
| `BACKUP_KEEP_COUNT` | ❌ | عدد النسخ المحفوظة | `7` |

### 🛠️ إعدادات التطوير - Development Settings

| المتغير | مطلوب | الوصف | القيم المقبولة |
|---------|-------|-------|---------------|
| `DEBUG_MODE` | ❌ | وضع التطوير | `true`, `false` |
| `AUTO_RELOAD` | ❌ | إعادة التحميل التلقائي | `true`, `false` |
| `SHOW_ERROR_DETAILS` | ❌ | عرض تفاصيل الأخطاء | `true`, `false` |

### 🌍 الخدمات الخارجية - External Services

| المتغير | مطلوب | الوصف | الاستخدام |
|---------|-------|-------|---------|
| `VIRUS_TOTAL_API_KEY` | ❌ | مفتاح VirusTotal | فحص الروابط الضارة |
| `GOOGLE_TRANSLATE_API_KEY` | ❌ | مفتاح Google Translate | ترجمة الرسائل |
| `SENTIMENT_API_KEY` | ❌ | مفتاح تحليل المشاعر | تحليل محتوى الرسائل |

### ⚡ إعدادات الحدود - Rate Limiting

| المتغير | مطلوب | الوصف | القيم الافتراضية |
|---------|-------|-------|-----------------|
| `USER_RATE_LIMIT` | ❌ | الحد الأقصى للطلبات/دقيقة/مستخدم | `30` |
| `MESSAGE_RATE_LIMIT` | ❌ | الحد الأقصى للرسائل/ساعة | `1000` |
| `RATE_LIMIT_BAN_DURATION` | ❌ | مدة الحظر عند التجاوز (دقيقة) | `60` |

### 📁 إعدادات التخزين - Storage Settings

| المتغير | مطلوب | الوصف | القيم الافتراضية |
|---------|-------|-------|-----------------|
| `TEMP_DIR` | ❌ | مجلد الملفات المؤقتة | `temp` |
| `MEDIA_DIR` | ❌ | مجلد الوسائط | `media` |
| `MAX_FILE_SIZE` | ❌ | الحد الأقصى لحجم الملف (MB) | `50` |
| `TEMP_CLEANUP_INTERVAL` | ❌ | تنظيف الملفات المؤقتة (ساعة) | `24` |

## 🔧 أمثلة التكوين - Configuration Examples

### تكوين أساسي للتطوير
\`\`\`env
BOT_TOKEN=your_bot_token_here
DEVELOPER_ID=123456789
DATABASE_TYPE=sqlite
LOG_LEVEL=DEBUG
DEBUG_MODE=true
\`\`\`

### تكوين للإنتاج
\`\`\`env
BOT_TOKEN=your_bot_token_here
DEVELOPER_ID=123456789
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://user:pass@localhost:5432/telegram_bot
LOG_LEVEL=INFO
USE_WEBHOOK=true
WEBHOOK_URL=https://yourdomain.com/webhook
ENABLE_AUTO_BACKUP=true
\`\`\`

### تكوين مع Userbot
\`\`\`env
BOT_TOKEN=your_bot_token_here
DEVELOPER_ID=123456789
ENABLE_USERBOT=true
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
USERBOT_PHONE=+1234567890
\`\`\`

## ⚠️ تحذيرات مهمة - Important Warnings

1. **لا تشارك ملف .env أبداً** - Never share your .env file
2. **استخدم كلمات مرور قوية** - Use strong passwords
3. **احتفظ بنسخة احتياطية من الإعدادات** - Keep backup of your settings
4. **تأكد من صحة التوكن قبل التشغيل** - Verify token before running

## 🆘 استكشاف الأخطاء - Troubleshooting

### البوت لا يبدأ
- تحقق من صحة `BOT_TOKEN`
- تأكد من وجود `DEVELOPER_ID`
- راجع مستوى السجلات

### مشاكل قاعدة البيانات
- تحقق من إعدادات الاتصال
- تأكد من وجود قاعدة البيانات
- راجع صلاحيات المستخدم

### مشاكل الأداء
- قلل من `MAX_CONCURRENT_OPERATIONS`
- زد من `OPERATION_TIMEOUT`
- فعّل التخزين المؤقت

## 📞 الدعم - Support

إذا واجهت مشاكل في التكوين، يمكنك:
- مراجعة ملف `INSTALL.md`
- فحص السجلات في مجلد `logs`
- التأكد من صحة جميع المتغيرات المطلوبة
