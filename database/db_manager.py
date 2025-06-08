"""
مدير قاعدة البيانات
Database Manager
"""

import sqlite3
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from config.settings import DatabaseConfig

logger = logging.getLogger(__name__)

class DatabaseManager:
    """مدير قاعدة البيانات"""
    
    def __init__(self, db_path: str = "bot_database.db"):
        self.db_path = db_path
        self.connection = None
    
    async def initialize(self):
        """تهيئة قاعدة البيانات وإنشاء الجداول"""
        try:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
            
            # إنشاء الجداول
            for table_name, create_sql in DatabaseConfig.TABLES.items():
                self.connection.execute(create_sql)
            
            self.connection.commit()
            logger.info("✅ تم إنشاء قاعدة البيانات والجداول بنجاح")
            
        except Exception as e:
            logger.error(f"❌ خطأ في تهيئة قاعدة البيانات: {e}")
            raise
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """تنفيذ استعلام وإرجاع النتائج"""
        try:
            cursor = self.connection.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"خطأ في تنفيذ الاستعلام: {e}")
            return []
    
    def execute_update(self, query: str, params: tuple = ()) -> bool:
        """تنفيذ استعلام تحديث"""
        try:
            self.connection.execute(query, params)
            self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"خطأ في تنفيذ التحديث: {e}")
            return False
    
    # إدارة المستخدمين
    async def add_user(self, user_id: int, username: str = None, 
                      first_name: str = None, last_name: str = None) -> bool:
        """إضافة مستخدم جديد"""
        query = """
            INSERT OR REPLACE INTO users 
            (user_id, username, first_name, last_name, last_active)
            VALUES (?, ?, ?, ?, ?)
        """
        return self.execute_update(query, (user_id, username, first_name, last_name, datetime.now()))
    
    async def get_user(self, user_id: int) -> Optional[Dict]:
        """الحصول على بيانات المستخدم"""
        query = "SELECT * FROM users WHERE user_id = ?"
        results = self.execute_query(query, (user_id,))
        return results[0] if results else None
    
    async def update_user_activity(self, user_id: int):
        """تحديث آخر نشاط للمستخدم"""
        query = "UPDATE users SET last_active = ? WHERE user_id = ?"
        self.execute_update(query, (datetime.now(), user_id))
    
    async def set_premium(self, user_id: int, days: int = 30) -> bool:
        """تفعيل Premium للمستخدم"""
        expires = datetime.now() + timedelta(days=days)
        query = "UPDATE users SET is_premium = TRUE, premium_expires = ? WHERE user_id = ?"
        return self.execute_update(query, (expires, user_id))
    
    async def check_premium(self, user_id: int) -> bool:
        """فحص حالة Premium للمستخدم"""
        user = await self.get_user(user_id)
        if not user or not user['is_premium']:
            return False
        
        if user['premium_expires'] and datetime.fromisoformat(user['premium_expires']) < datetime.now():
            # انتهت صلاحية Premium
            query = "UPDATE users SET is_premium = FALSE WHERE user_id = ?"
            self.execute_update(query, (user_id,))
            return False
        
        return True
    
    async def activate_trial(self, user_id: int) -> bool:
        """تفعيل التجربة المجانية"""
        user = await self.get_user(user_id)
        if user and user['trial_used']:
            return False
        
        expires = datetime.now() + timedelta(hours=48)
        query = """
            UPDATE users 
            SET is_premium = TRUE, premium_expires = ?, trial_used = TRUE 
            WHERE user_id = ?
        """
        return self.execute_update(query, (expires, user_id))
    
    # إدارة المهام
    async def create_task(self, user_id: int, name: str, source_chat_id: int, 
                         target_chat_ids: List[int], settings: Dict = None) -> int:
        """إنشاء مهمة جديدة"""
        query = """
            INSERT INTO tasks (user_id, name, source_chat_id, target_chat_ids, settings)
            VALUES (?, ?, ?, ?, ?)
        """
        cursor = self.connection.execute(query, (
            user_id, name, source_chat_id, 
            json.dumps(target_chat_ids), 
            json.dumps(settings or {})
        ))
        self.connection.commit()
        return cursor.lastrowid
    
    async def get_user_tasks(self, user_id: int) -> List[Dict]:
        """الحصول على مهام المستخدم"""
        query = "SELECT * FROM tasks WHERE user_id = ? ORDER BY created_at DESC"
        tasks = self.execute_query(query, (user_id,))
        
        # تحويل JSON strings إلى objects
        for task in tasks:
            task['target_chat_ids'] = json.loads(task['target_chat_ids'])
            task['settings'] = json.loads(task['settings'] or '{}')
        
        return tasks
    
    async def get_active_tasks(self) -> List[Dict]:
        """الحصول على جميع المهام النشطة"""
        query = "SELECT * FROM tasks WHERE is_active = TRUE"
        tasks = self.execute_query(query)
        
        for task in tasks:
            task['target_chat_ids'] = json.loads(task['target_chat_ids'])
            task['settings'] = json.loads(task['settings'] or '{}')
        
        return tasks
    
    async def update_task(self, task_id: int, **kwargs) -> bool:
        """تحديث مهمة"""
        if not kwargs:
            return False
        
        # تحويل القوائم والقواميس إلى JSON
        for key, value in kwargs.items():
            if isinstance(value, (list, dict)):
                kwargs[key] = json.dumps(value)
        
        set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        query = f"UPDATE tasks SET {set_clause}, updated_at = ? WHERE id = ?"
        
        values = list(kwargs.values()) + [datetime.now(), task_id]
        return self.execute_update(query, values)
    
    async def delete_task(self, task_id: int, user_id: int) -> bool:
        """حذف مهمة"""
        query = "DELETE FROM tasks WHERE id = ? AND user_id = ?"
        return self.execute_update(query, (task_id, user_id))
    
    # إدارة الرسائل
    async def log_forwarded_message(self, task_id: int, source_msg_id: int, 
                                   target_msg_ids: Dict[int, int]):
        """تسجيل رسالة تم توجيهها"""
        query = """
            INSERT INTO messages (task_id, source_message_id, target_message_ids)
            VALUES (?, ?, ?)
        """
        self.execute_update(query, (task_id, source_msg_id, json.dumps(target_msg_ids)))
    
    # إدارة الدردشات
    async def add_chat(self, chat_id: int, chat_type: str, title: str = None, 
                      username: str = None, member_count: int = 0) -> bool:
        """إضافة دردشة جديدة"""
        query = """
            INSERT OR REPLACE INTO chats 
            (chat_id, chat_type, title, username, member_count, last_updated)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        return self.execute_update(query, (
            chat_id, chat_type, title, username, member_count, datetime.now()
        ))
    
    async def get_user_chats(self, user_id: int) -> List[Dict]:
        """الحصول على دردشات المستخدم"""
        # هذا يتطلب جدول إضافي لربط المستخدمين بالدردشات
        # سنضيفه في التحديث القادم
        query = "SELECT * FROM chats ORDER BY last_updated DESC"
        return self.execute_query(query)
    
    # الإحصائيات
    async def get_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات البوت"""
        stats = {}
        
        # عدد المستخدمين
        result = self.execute_query("SELECT COUNT(*) as count FROM users")
        stats['total_users'] = result[0]['count'] if result else 0
        
        # عدد المستخدمين Premium
        result = self.execute_query("SELECT COUNT(*) as count FROM users WHERE is_premium = TRUE")
        stats['premium_users'] = result[0]['count'] if result else 0
        
        # عدد المهام
        result = self.execute_query("SELECT COUNT(*) as count FROM tasks")
        stats['total_tasks'] = result[0]['count'] if result else 0
        
        # عدد المهام النشطة
        result = self.execute_query("SELECT COUNT(*) as count FROM tasks WHERE is_active = TRUE")
        stats['active_tasks'] = result[0]['count'] if result else 0
        
        # عدد الرسائل المُوجهة
        result = self.execute_query("SELECT COUNT(*) as count FROM messages")
        stats['forwarded_messages'] = result[0]['count'] if result else 0
        
        # عدد الدردشات
        result = self.execute_query("SELECT COUNT(*) as count FROM chats")
        stats['total_chats'] = result[0]['count'] if result else 0
        
        return stats
    
    # إدارة المشرفين
    async def add_admin(self, user_id: int, added_by: int, permissions: List[str] = None) -> bool:
        """إضافة مشرف جديد"""
        query = """
            INSERT OR REPLACE INTO admins (user_id, added_by, permissions)
            VALUES (?, ?, ?)
        """
        return self.execute_update(query, (user_id, added_by, json.dumps(permissions or [])))
    
    async def is_admin(self, user_id: int) -> bool:
        """فحص إذا كان المستخدم مشرف"""
        query = "SELECT id FROM admins WHERE user_id = ?"
        result = self.execute_query(query, (user_id,))
        return len(result) > 0
    
    # الرسائل المجدولة
    async def add_scheduled_message(self, user_id: int, message_text: str, 
                                   target_type: str, target_ids: List[int],
                                   schedule_time: datetime, interval_minutes: int = None) -> int:
        """إضافة رسالة مجدولة"""
        query = """
            INSERT INTO scheduled_messages 
            (user_id, message_text, target_type, target_ids, schedule_time, interval_minutes)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        cursor = self.connection.execute(query, (
            user_id, message_text, target_type, 
            json.dumps(target_ids), schedule_time, interval_minutes
        ))
        self.connection.commit()
        return cursor.lastrowid
    
    async def get_pending_scheduled_messages(self) -> List[Dict]:
        """الحصول على الرسائل المجدولة المعلقة"""
        query = """
            SELECT * FROM scheduled_messages 
            WHERE is_active = TRUE AND schedule_time <= ?
            ORDER BY schedule_time ASC
        """
        messages = self.execute_query(query, (datetime.now(),))
        
        for msg in messages:
            msg['target_ids'] = json.loads(msg['target_ids'])
        
        return messages
    
    # نسخ البوت
    async def add_bot_clone(self, owner_id: int, bot_token: str, bot_username: str = None) -> int:
        """إضافة نسخة من البوت"""
        query = """
            INSERT INTO bot_clones (owner_id, bot_token, bot_username)
            VALUES (?, ?, ?)
        """
        cursor = self.connection.execute(query, (owner_id, bot_token, bot_username))
        self.connection.commit()
        return cursor.lastrowid
    
    async def get_user_bot_clones(self, user_id: int) -> List[Dict]:
        """الحصول على نسخ البوت للمستخدم"""
        query = "SELECT * FROM bot_clones WHERE owner_id = ? ORDER BY created_at DESC"
        return self.execute_query(query, (user_id,))
    
    def close(self):
        """إغلاق الاتصال بقاعدة البيانات"""
        if self.connection:
            self.connection.close()
