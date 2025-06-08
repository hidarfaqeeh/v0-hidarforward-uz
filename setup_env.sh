#!/bin/bash

# =============================================================================
# سكربت إعداد متغيرات البيئة - Environment Setup Script
# =============================================================================

echo "🚀 مرحباً بك في معالج إعداد البوت!"
echo "Welcome to the Bot Setup Wizard!"
echo "=================================="

# التحقق من وجود ملف .env
if [ -f ".env" ]; then
    echo "⚠️  ملف .env موجود بالفعل. هل تريد إعادة إنشائه؟"
    echo "⚠️  .env file already exists. Do you want to recreate it?"
    read -p "y/N: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "تم إلغاء العملية."
        echo "Operation cancelled."
        exit 0
    fi
    mv .env .env.backup.$(date +%Y%m%d_%H%M%S)
    echo "تم إنشاء نسخة احتياطية من الملف القديم."
    echo "Backup created for the old file."
fi

# نسخ ملف المثال
cp .env.example .env

echo ""
echo "📝 الآن سنقوم بإعداد الإعدادات الأساسية..."
echo "📝 Now let's configure the basic settings..."
echo ""

# إعداد توكن البوت
echo "🤖 أدخل توكن البوت من @BotFather:"
echo "🤖 Enter your bot token from @BotFather:"
read -p "Bot Token: " BOT_TOKEN
if [ ! -z "$BOT_TOKEN" ]; then
    sed -i "s/BOT_TOKEN=.*/BOT_TOKEN=$BOT_TOKEN/" .env
    echo "✅ تم حفظ توكن البوت"
    echo "✅ Bot token saved"
fi

echo ""

# إعداد معرف المطور
echo "👨‍💻 أدخل معرف المطور (User ID):"
echo "👨‍💻 Enter developer user ID:"
echo "💡 يمكنك الحصول عليه من @userinfobot"
echo "💡 You can get it from @userinfobot"
read -p "Developer ID: " DEVELOPER_ID
if [ ! -z "$DEVELOPER_ID" ]; then
    sed -i "s/DEVELOPER_ID=.*/DEVELOPER_ID=$DEVELOPER_ID/" .env
    echo "✅ تم حفظ معرف المطور"
    echo "✅ Developer ID saved"
fi

echo ""

# إعداد اسم البوت
echo "📛 أدخل اسم البوت (اختياري):"
echo "📛 Enter bot name (optional):"
read -p "Bot Name: " BOT_NAME
if [ ! -z "$BOT_NAME" ]; then
    sed -i "s/BOT_NAME=.*/BOT_NAME=$BOT_NAME/" .env
    echo "✅ تم حفظ اسم البوت"
    echo "✅ Bot name saved"
fi

echo ""

# إعداد كلمة مرور الإدارة
echo "🔐 أدخل كلمة مرور لوحة الإدارة:"
echo "🔐 Enter admin panel password:"
read -s -p "Admin Password: " ADMIN_PASSWORD
echo
if [ ! -z "$ADMIN_PASSWORD" ]; then
    sed -i "s/ADMIN_PASSWORD=.*/ADMIN_PASSWORD=$ADMIN_PASSWORD/" .env
    echo "✅ تم حفظ كلمة مرور الإدارة"
    echo "✅ Admin password saved"
fi

echo ""

# إعداد مستوى السجلات
echo "📊 اختر مستوى السجلات:"
echo "📊 Choose log level:"
echo "1) DEBUG (تفصيلي جداً)"
echo "2) INFO (عادي) - مُوصى به"
echo "3) WARNING (تحذيرات فقط)"
echo "4) ERROR (أخطاء فقط)"
read -p "اختر (1-4): " LOG_CHOICE
case $LOG_CHOICE in
    1) LOG_LEVEL="DEBUG" ;;
    2) LOG_LEVEL="INFO" ;;
    3) LOG_LEVEL="WARNING" ;;
    4) LOG_LEVEL="ERROR" ;;
    *) LOG_LEVEL="INFO" ;;
esac
sed -i "s/LOG_LEVEL=.*/LOG_LEVEL=$LOG_LEVEL/" .env
echo "✅ تم تعيين مستوى السجلات إلى $LOG_LEVEL"
echo "✅ Log level set to $LOG_LEVEL"

echo ""

# إعداد قاعدة البيانات
echo "🗄️  اختر نوع قاعدة البيانات:"
echo "🗄️  Choose database type:"
echo "1) SQLite (بسيط ومُوصى به للبداية)"
echo "2) PostgreSQL (للإنتاج)"
echo "3) MySQL (للإنتاج)"
read -p "اختر (1-3): " DB_CHOICE
case $DB_CHOICE in
    1) 
        DATABASE_TYPE="sqlite"
        echo "✅ تم اختيار SQLite"
        echo "✅ SQLite selected"
        ;;
    2) 
        DATABASE_TYPE="postgresql"
        echo "تم اختيار PostgreSQL. ستحتاج لإعداد الاتصال يدوياً في ملف .env"
        echo "PostgreSQL selected. You'll need to configure connection manually in .env"
        ;;
    3) 
        DATABASE_TYPE="mysql"
        echo "تم اختيار MySQL. ستحتاج لإعداد الاتصال يدوياً في ملف .env"
        echo "MySQL selected. You'll need to configure connection manually in .env"
        ;;
    *) 
        DATABASE_TYPE="sqlite"
        echo "✅ تم اختيار SQLite (افتراضي)"
        echo "✅ SQLite selected (default)"
        ;;
esac
sed -i "s/DATABASE_TYPE=.*/DATABASE_TYPE=$DATABASE_TYPE/" .env

echo ""

# إنشاء مجلدات ضرورية
echo "📁 إنشاء المجلدات الضرورية..."
echo "📁 Creating necessary directories..."

mkdir -p data logs temp media backups

echo "✅ تم إنشاء المجلدات"
echo "✅ Directories created"

echo ""

# إنشاء مفتاح تشفير عشوائي
echo "🔑 إنشاء مفتاح تشفير عشوائي..."
echo "🔑 Generating random encryption key..."

ENCRYPTION_KEY=$(openssl rand -hex 16 2>/dev/null || python3 -c "import secrets; print(secrets.token_hex(16))" 2>/dev/null || echo "your_32_character_encryption_key_here")
sed -i "s/ENCRYPTION_KEY=.*/ENCRYPTION_KEY=$ENCRYPTION_KEY/" .env

echo "✅ تم إنشاء مفتاح التشفير"
echo "✅ Encryption key generated"

echo ""

# إنشاء مفتاح JWT عشوائي
echo "🎫 إنشاء مفتاح JWT عشوائي..."
echo "🎫 Generating random JWT secret..."

JWT_SECRET=$(openssl rand -base64 32 2>/dev/null || python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || echo "your_jwt_secret_key_here")
sed -i "s/JWT_SECRET=.*/JWT_SECRET=$JWT_SECRET/" .env

echo "✅ تم إنشاء مفتاح JWT"
echo "✅ JWT secret generated"

echo ""
echo "🎉 تم إكمال الإعداد الأساسي بنجاح!"
echo "🎉 Basic setup completed successfully!"
echo ""
echo "📋 الخطوات التالية:"
echo "📋 Next steps:"
echo "1. راجع ملف .env وعدّل الإعدادات حسب الحاجة"
echo "1. Review .env file and modify settings as needed"
echo "2. قم بتشغيل البوت باستخدام: docker-compose up -d"
echo "2. Start the bot using: docker-compose up -d"
echo "3. تحقق من السجلات باستخدام: docker-compose logs -f"
echo "3. Check logs using: docker-compose logs -f"
echo ""
echo "📖 للمزيد من المعلومات، راجع ملف INSTALL.md"
echo "📖 For more information, check INSTALL.md"
echo ""
echo "✨ حظاً موفقاً!"
echo "✨ Good luck!"
