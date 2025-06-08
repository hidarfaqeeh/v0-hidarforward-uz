"""
إعدادات البوت الأساسية
Bot Basic Settings
"""

import os
from typing import List, Optional
from dataclasses import dataclass, field

@dataclass
class Settings:
    """إعدادات البوت"""
    
    # إعدادات البوت الأساسية
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    BOT_USERNAME: str = os.getenv("BOT_USERNAME", "")
    
    # إعدادات قاعدة البيانات
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///bot_database.db")
    
    # إعدادات الويب هوك
    USE_WEBHOOK: bool = os.getenv("USE_WEBHOOK", "False").lower() == "true"
    WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "")
    WEBHOOK_SECRET: str = os.getenv("WEBHOOK_SECRET", "")
    
    # إعدادات المطورين والمشرفين - استخدام default_factory
    DEVELOPERS: List[int] = field(default_factory=list)
    ADMINS: List[int] = field(default_factory=list)
    
    # إعدادات Premium
    PREMIUM_TRIAL_HOURS: int = int(os.getenv("PREMIUM_TRIAL_HOURS", "48"))
    
    # إعدادات الإشعارات
    NOTIFICATION_CHANNEL: Optional[int] = int(os.getenv("NOTIFICATION_CHANNEL")) if os.getenv("NOTIFICATION_CHANNEL") else None
    
    # إعدادات الحماية من السبام
    SPAM_PROTECTION: bool = os.getenv("SPAM_PROTECTION", "True").lower() == "true"
    MAX_MESSAGES_PER_MINUTE: int = int(os.getenv("MAX_MESSAGES_PER_MINUTE", "20"))
    
    # إعدادات التخزين
    BACKUP_ENABLED: bool = os.getenv("BACKUP_ENABLED", "True").lower() == "true"
    BACKUP_INTERVAL_HOURS: int = int(os.getenv("BACKUP_INTERVAL_HOURS", "24"))
    
    def __post_init__(self):
        """التحقق من الإعدادات المطلوبة وتحميل القوائم"""
        # تحميل قوائم المطورين والمشرفين
        developers_str = os.getenv("DEVELOPERS", "")
        if developers_str:
            self.DEVELOPERS = [int(x) for x in developers_str.split(",") if x.strip()]
    
        admins_str = os.getenv("ADMINS", "")
        if admins_str:
            self.ADMINS = [int(x) for x in admins_str.split(",") if x.strip()]
    
        # باقي التحققات الموجودة
        if not self.BOT_TOKEN:
            raise ValueError("BOT_TOKEN مطلوب في متغيرات البيئة")
        
        if self.USE_WEBHOOK and not self.WEBHOOK_URL:
            raise ValueError("WEBHOOK_URL مطلوب عند استخدام الويب هوك")

# إعدادات الرسائل
class Messages:
    """رسائل البوت"""
    
    WELCOME = """
🎉 مرحباً بك في بوت التوجيه المتقدم!

🔥 الميزات الرئيسية:
• مراقبة مستمرة للرسائل
• نظام مهام متعدد
• فلاتر متقدمة
• دعم Bot Token و Userbot
• نظام Premium مع تجربة مجانية

📝 للبدء، استخدم الأوامر التالية:
/tasks - إدارة المهام
/help - المساعدة
/status - حالة الحساب

💎 تجربة Premium مجانية لمدة 48 ساعة!
    """
    
    HELP = """
📚 دليل استخدام البوت

🎯 الأوامر الأساسية:
/start - بدء استخدام البوت
/help - عرض هذه المساعدة
/status - عرض حالة حسابك
/tasks - إدارة مهام التوجيه

⚙️ إدارة المهام:
/newtask - إنشاء مهمة جديدة
/edittask - تعديل مهمة موجودة
/deltask - حذف مهمة

👑 أوامر المشرفين:
/admin - لوحة الإدارة
/stats - الإحصائيات
/users - إدارة المستخدمين
/broadcast - إرسال رسالة جماعية

💡 للحصول على دعم فني، تواصل مع المطور.
    """
    
    PREMIUM_EXPIRED = """
⚠️ انتهت فترة Premium الخاصة بك!

للاستمرار في استخدام جميع الميزات المتقدمة، يرجى تجديد اشتراكك.

تواصل مع المطور للحصول على Premium.
    """
    
    TASK_CREATED = "✅ تم إنشاء المهمة بنجاح!"
    TASK_UPDATED = "✅ تم تحديث المهمة بنجاح!"
    TASK_DELETED = "✅ تم حذف المهمة بنجاح!"
    
    ERROR_GENERAL = "❌ حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى."
    ERROR_PERMISSION = "❌ ليس لديك صلاحية لتنفيذ هذا الأمر."
    ERROR_NOT_FOUND = "❌ العنصر المطلوب غير موجود."

# إعدادات قاعدة البيانات
class DatabaseConfig:
    """إعدادات قاعدة البيانات"""
    
    TABLES = {
        'users': '''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                user_id BIGINT UNIQUE NOT NULL,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                is_premium BOOLEAN DEFAULT FALSE,
                premium_expires TIMESTAMP,
                trial_used BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_banned BOOLEAN DEFAULT FALSE,
                ban_reason TEXT
            )
        ''',
        
        'tasks': '''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id BIGINT NOT NULL,
                name TEXT NOT NULL,
                source_chat_id BIGINT NOT NULL,
                target_chat_ids TEXT NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                forward_type TEXT DEFAULT 'forward',
                filters TEXT,
                settings TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''',
        
        'messages': '''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                source_message_id INTEGER NOT NULL,
                target_message_ids TEXT,
                forwarded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks (id)
            )
        ''',
        
        'chats': '''
            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id BIGINT UNIQUE NOT NULL,
                chat_type TEXT NOT NULL,
                title TEXT,
                username TEXT,
                member_count INTEGER DEFAULT 0,
                is_verified BOOLEAN DEFAULT FALSE,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''',
        
        'admins': '''
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id BIGINT UNIQUE NOT NULL,
                added_by BIGINT NOT NULL,
                permissions TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''',
        
        'scheduled_messages': '''
            CREATE TABLE IF NOT EXISTS scheduled_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id BIGINT NOT NULL,
                message_text TEXT NOT NULL,
                target_type TEXT NOT NULL,
                target_ids TEXT,
                schedule_time TIMESTAMP NOT NULL,
                interval_minutes INTEGER,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''',
        
        'bot_clones': '''
            CREATE TABLE IF NOT EXISTS bot_clones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id BIGINT NOT NULL,
                bot_token TEXT NOT NULL,
                bot_username TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (owner_id) REFERENCES users (user_id)
            )
        '''
    }
