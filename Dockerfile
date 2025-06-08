# استخدام صورة Python الرسمية كأساس
FROM python:3.11-slim

# معلومات عن مطور الصورة
LABEL maintainer="HidarForward <hidarforward@example.com>"
LABEL version="1.0"
LABEL description="بوت تلغرام متقدم لمراقبة وتوجيه الرسائل"

# تعيين متغيرات البيئة
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Riyadh \
    DEBIAN_FRONTEND=noninteractive

# تثبيت المتطلبات الأساسية للنظام
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libffi-dev \
    libssl-dev \
    git \
    curl \
    tzdata \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# إنشاء وتعيين دليل العمل
WORKDIR /app

# نسخ ملف المتطلبات أولاً للاستفادة من التخزين المؤقت في Docker
COPY requirements.txt .

# تثبيت متطلبات Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# نسخ باقي ملفات المشروع
COPY . .

# إنشاء مستخدم غير جذري لتشغيل التطبيق
RUN groupadd -r botuser && useradd -r -g botuser botuser && \
    mkdir -p /app/data /app/logs && \
    chown -R botuser:botuser /app

# التبديل إلى المستخدم غير الجذري
USER botuser

# إنشاء حجم للبيانات المستمرة
VOLUME ["/app/data", "/app/logs"]

# تعريض المنفذ الذي سيستخدمه الويب هوك (إذا تم استخدامه)
EXPOSE 8443

# سكربت الإعداد والتشغيل
RUN chmod +x /app/entrypoint.sh

# تعيين نقطة الدخول
ENTRYPOINT ["/app/entrypoint.sh"]

# الأمر الافتراضي
CMD ["python", "main.py"]
