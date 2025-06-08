#!/bin/bash
set -e

# إنشاء ملف البيئة إذا لم يكن موجودًا
if [ ! -f .env ]; then
    echo "إنشاء ملف .env افتراضي..."
    touch .env
    
    # إضافة متغيرات البيئة الافتراضية إذا لم تكن موجودة
    if [ -z "$BOT_TOKEN" ]; then
        echo "⚠️ تحذير: لم يتم تعيين BOT_TOKEN. يرجى تعيينه قبل تشغيل البوت."
    else
        echo "BOT_TOKEN=$BOT_TOKEN" >> .env
    fi
    
    # إعدادات قاعدة البيانات
    echo "DATABASE_URL=${DATABASE_URL:-sqlite:///data/bot.db}" >> .env
    
    # إعدادات المسؤول
    echo "ADMIN_IDS=${ADMIN_IDS:-}" >> .env
    
    # إعدادات الويب هوك
    echo "USE_WEBHOOK=${USE_WEBHOOK:-false}" >> .env
    echo "WEBHOOK_URL=${WEBHOOK_URL:-}" >> .env
    
    # إعدادات أخرى
    echo "LOG_LEVEL=${LOG_LEVEL:-INFO}" >> .env
    echo "TIMEZONE=${TIMEZONE:-Asia/Riyadh}" >> .env
fi

# إنشاء الدلائل اللازمة إذا لم تكن موجودة
mkdir -p data logs

# تنفيذ أي ترقيات لقاعدة البيانات إذا لزم الأمر
if [ -f "alembic.ini" ]; then
    echo "تطبيق ترقيات قاعدة البيانات..."
    alembic upgrade head
fi

# تنفيذ الأمر المحدد
exec "$@"
