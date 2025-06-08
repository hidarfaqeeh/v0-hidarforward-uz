# دليل تنصيب البوت

## المتطلبات الأساسية

قبل البدء، تأكد من تثبيت:

- Docker
- Docker Compose

## خطوات التنصيب

### 1. إعداد ملف البيئة

قم بإنشاء ملف `.env` في المجلد الرئيسي للمشروع وأضف المتغيرات التالية:

\`\`\`
BOT_TOKEN=توكن_البوت_الخاص_بك
ADMIN_IDS=معرف_المسؤول_1,معرف_المسؤول_2
USE_WEBHOOK=false
WEBHOOK_URL=https://example.com/webhook
LOG_LEVEL=INFO
TIMEZONE=Asia/Riyadh
\`\`\`

### 2. بناء وتشغيل البوت باستخدام Docker Compose

\`\`\`bash
docker-compose up -d
\`\`\`

هذا سيقوم ببناء الصورة وتشغيل البوت في الخلفية.

### 3. مراقبة سجلات البوت

\`\`\`bash
docker-compose logs -f
\`\`\`

### 4. إيقاف البوت

\`\`\`bash
docker-compose down
\`\`\`

## استخدام Dockerfile مباشرة

إذا كنت ترغب في استخدام Dockerfile مباشرة بدون Docker Compose:

### 1. بناء الصورة

\`\`\`bash
docker build -t telegram-forward-bot .
\`\`\`

### 2. تشغيل الحاوية

\`\`\`bash
docker run -d --name telegram-forward-bot \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/.env:/app/.env:ro \
  -p 8443:8443 \
  -e BOT_TOKEN=توكن_البوت_الخاص_بك \
  -e ADMIN_IDS=معرف_المسؤول_1,معرف_المسؤول_2 \
  telegram-forward-bot
\`\`\`

## ملاحظات هامة

- تأكد من تعيين `BOT_TOKEN` الصحيح الذي حصلت عليه من BotFather.
- قم بتعيين `ADMIN_IDS` لمعرفات المستخدمين الذين سيكون لديهم صلاحيات المسؤول.
- إذا كنت تستخدم الويب هوك، قم بتعيين `USE_WEBHOOK=true` وتحديد `WEBHOOK_URL` المناسب.
- البيانات ستُخزن في مجلد `data` والسجلات في مجلد `logs`.

## تحديث البوت

لتحديث البوت إلى أحدث إصدار:

\`\`\`bash
git pull
docker-compose down
docker-compose up -d --build
\`\`\`

## استكشاف الأخطاء وإصلاحها

إذا واجهت أي مشاكل، تحقق من:

1. سجلات البوت: `docker-compose logs -f`
2. تأكد من صحة توكن البوت
3. تأكد من وجود الصلاحيات المناسبة للمجلدات `data` و `logs`
