"""
نظام ترقيات قاعدة البيانات
Database Migrations System
"""

import os
import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Any
from database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)

class MigrationManager:
    """مدير ترقيات قاعدة البيانات"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.migrations_table = "schema_migrations"
        self.migrations_dir = "database/migrations"
        
    async def initialize_migrations_table(self):
        """إنشاء جدول الترقيات"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version VARCHAR(255) NOT NULL UNIQUE,
            description TEXT,
            executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            execution_time_ms INTEGER,
            checksum VARCHAR(255)
        )
        """
        self.db.execute_update(create_table_sql)
        logger.info("✅ تم إنشاء جدول الترقيات")
    
    async def get_applied_migrations(self) -> List[str]:
        """الحصول على الترقيات المطبقة"""
        query = "SELECT version FROM schema_migrations ORDER BY version"
        results = self.db.execute_query(query)
        return [row['version'] for row in results]
    
    async def get_pending_migrations(self) -> List[Dict[str, Any]]:
        """الحصول على الترقيات المعلقة"""
        applied = await self.get_applied_migrations()
        all_migrations = self.get_all_migrations()
        
        pending = []
        for migration in all_migrations:
            if migration['version'] not in applied:
                pending.append(migration)
        
        return pending
    
    def get_all_migrations(self) -> List[Dict[str, Any]]:
        """الحصول على جميع الترقيات المتاحة"""
        migrations = [
            {
                'version': '001',
                'description': 'إضافة فهارس الأداء',
                'sql': self.migration_001_add_indexes()
            },
            {
                'version': '002',
                'description': 'إضافة جدول الإحصائيات',
                'sql': self.migration_002_add_statistics_table()
            },
            {
                'version': '003',
                'description': 'إضافة جدول الإشعارات',
                'sql': self.migration_003_add_notifications_table()
            },
            {
                'version': '004',
                'description': 'إضافة جدول جلسات المستخدمين',
                'sql': self.migration_004_add_user_sessions_table()
            },
            {
                'version': '005',
                'description': 'إضافة جدول سجل العمليات',
                'sql': self.migration_005_add_audit_log_table()
            },
            {
                'version': '006',
                'description': 'إضافة جدول التحليلات',
                'sql': self.migration_006_add_analytics_table()
            },
            {
                'version': '007',
                'description': 'إضافة جدول الأمان',
                'sql': self.migration_007_add_security_table()
            },
            {
                'version': '008',
                'description': 'إضافة جدول الحملات',
                'sql': self.migration_008_add_campaigns_table()
            },
            {
                'version': '009',
                'description': 'تحسين هيكل الجداول',
                'sql': self.migration_009_optimize_tables()
            },
            {
                'version': '010',
                'description': 'إضافة القيود والعلاقات',
                'sql': self.migration_010_add_constraints()
            }
        ]
        return migrations
    
    async def run_migrations(self) -> Dict[str, Any]:
        """تشغيل جميع الترقيات المعلقة"""
        await self.initialize_migrations_table()
        
        pending = await self.get_pending_migrations()
        if not pending:
            logger.info("لا توجد ترقيات معلقة")
            return {'applied': 0, 'skipped': 0, 'errors': []}
        
        applied = 0
        errors = []
        
        for migration in pending:
            try:
                start_time = datetime.now()
                
                # تنفيذ الترقية
                for sql_statement in migration['sql']:
                    self.db.execute_update(sql_statement)
                
                end_time = datetime.now()
                execution_time = int((end_time - start_time).total_seconds() * 1000)
                
                # تسجيل الترقية
                self.record_migration(
                    migration['version'],
                    migration['description'],
                    execution_time
                )
                
                applied += 1
                logger.info(f"✅ تم تطبيق الترقية {migration['version']}: {migration['description']}")
                
            except Exception as e:
                error_msg = f"خطأ في الترقية {migration['version']}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        return {
            'applied': applied,
            'skipped': len(pending) - applied,
            'errors': errors
        }
    
    def record_migration(self, version: str, description: str, execution_time: int):
        """تسجيل ترقية مطبقة"""
        query = """
        INSERT INTO schema_migrations (version, description, execution_time_ms)
        VALUES (?, ?, ?)
        """
        self.db.execute_update(query, (version, description, execution_time))
    
    # الترقيات المحددة
    def migration_001_add_indexes(self) -> List[str]:
        """إضافة فهارس الأداء"""
        return [
            "CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_users_is_premium ON users(is_premium)",
            "CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_is_active ON tasks(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_source_chat_id ON tasks(source_chat_id)",
            "CREATE INDEX IF NOT EXISTS idx_messages_task_id ON messages(task_id)",
            "CREATE INDEX IF NOT EXISTS idx_messages_forwarded_at ON messages(forwarded_at)",
            "CREATE INDEX IF NOT EXISTS idx_chats_chat_id ON chats(chat_id)",
            "CREATE INDEX IF NOT EXISTS idx_scheduled_messages_user_id ON scheduled_messages(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_scheduled_messages_schedule_time ON scheduled_messages(schedule_time)",
            "CREATE INDEX IF NOT EXISTS idx_bot_clones_owner_id ON bot_clones(owner_id)"
        ]
    
    def migration_002_add_statistics_table(self) -> List[str]:
        """إضافة جدول الإحصائيات"""
        return [
            """
            CREATE TABLE IF NOT EXISTS statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id BIGINT,
                task_id INTEGER,
                stat_type VARCHAR(50) NOT NULL,
                stat_key VARCHAR(100) NOT NULL,
                stat_value TEXT,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (task_id) REFERENCES tasks (id)
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_statistics_user_id ON statistics(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_statistics_task_id ON statistics(task_id)",
            "CREATE INDEX IF NOT EXISTS idx_statistics_type_key ON statistics(stat_type, stat_key)",
            "CREATE INDEX IF NOT EXISTS idx_statistics_recorded_at ON statistics(recorded_at)"
        ]
    
    def migration_003_add_notifications_table(self) -> List[str]:
        """إضافة جدول الإشعارات"""
        return [
            """
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id BIGINT,
                notification_type VARCHAR(50) NOT NULL,
                title VARCHAR(255) NOT NULL,
                message TEXT NOT NULL,
                data TEXT,
                is_read BOOLEAN DEFAULT FALSE,
                priority INTEGER DEFAULT 1,
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                read_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(notification_type)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at)"
        ]
    
    def migration_004_add_user_sessions_table(self) -> List[str]:
        """إضافة جدول جلسات المستخدمين"""
        return [
            """
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id BIGINT NOT NULL,
                session_id VARCHAR(255) UNIQUE NOT NULL,
                session_data TEXT,
                ip_address VARCHAR(45),
                user_agent TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_sessions_session_id ON user_sessions(session_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_sessions_is_active ON user_sessions(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at)"
        ]
    
    def migration_005_add_audit_log_table(self) -> List[str]:
        """إضافة جدول سجل العمليات"""
        return [
            """
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id BIGINT,
                action VARCHAR(100) NOT NULL,
                resource_type VARCHAR(50),
                resource_id VARCHAR(100),
                old_values TEXT,
                new_values TEXT,
                ip_address VARCHAR(45),
                user_agent TEXT,
                success BOOLEAN DEFAULT TRUE,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action)",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_resource ON audit_log(resource_type, resource_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at)"
        ]
    
    def migration_006_add_analytics_table(self) -> List[str]:
        """إضافة جدول التحليلات"""
        return [
            """
            CREATE TABLE IF NOT EXISTS analytics_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id BIGINT,
                event_type VARCHAR(50) NOT NULL,
                event_name VARCHAR(100) NOT NULL,
                properties TEXT,
                session_id VARCHAR(255),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS analytics_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name VARCHAR(100) NOT NULL,
                metric_value REAL NOT NULL,
                dimensions TEXT,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_analytics_events_user_id ON analytics_events(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_analytics_events_type ON analytics_events(event_type)",
            "CREATE INDEX IF NOT EXISTS idx_analytics_events_timestamp ON analytics_events(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_analytics_metrics_name ON analytics_metrics(metric_name)",
            "CREATE INDEX IF NOT EXISTS idx_analytics_metrics_recorded_at ON analytics_metrics(recorded_at)"
        ]
    
    def migration_007_add_security_table(self) -> List[str]:
        """إضافة جدول الأمان"""
        return [
            """
            CREATE TABLE IF NOT EXISTS security_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id BIGINT,
                event_type VARCHAR(50) NOT NULL,
                severity VARCHAR(20) DEFAULT 'medium',
                description TEXT NOT NULL,
                ip_address VARCHAR(45),
                user_agent TEXT,
                additional_data TEXT,
                resolved BOOLEAN DEFAULT FALSE,
                resolved_at TIMESTAMP,
                resolved_by BIGINT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS rate_limits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id BIGINT,
                action_type VARCHAR(50) NOT NULL,
                count INTEGER DEFAULT 1,
                window_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_security_events_user_id ON security_events(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_security_events_type ON security_events(event_type)",
            "CREATE INDEX IF NOT EXISTS idx_security_events_severity ON security_events(severity)",
            "CREATE INDEX IF NOT EXISTS idx_rate_limits_user_id ON rate_limits(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_rate_limits_action_type ON rate_limits(action_type)",
            "CREATE INDEX IF NOT EXISTS idx_rate_limits_expires_at ON rate_limits(expires_at)"
        ]
    
    def migration_008_add_campaigns_table(self) -> List[str]:
        """إضافة جدول الحملات"""
        return [
            """
            CREATE TABLE IF NOT EXISTS campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id BIGINT NOT NULL,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                campaign_type VARCHAR(50) DEFAULT 'broadcast',
                status VARCHAR(20) DEFAULT 'draft',
                target_criteria TEXT,
                message_template TEXT,
                schedule_config TEXT,
                statistics TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS campaign_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id INTEGER NOT NULL,
                scheduled_message_id INTEGER,
                target_user_id BIGINT,
                target_chat_id BIGINT,
                status VARCHAR(20) DEFAULT 'pending',
                sent_at TIMESTAMP,
                error_message TEXT,
                FOREIGN KEY (campaign_id) REFERENCES campaigns (id),
                FOREIGN KEY (scheduled_message_id) REFERENCES scheduled_messages (id)
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_campaigns_user_id ON campaigns(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns(status)",
            "CREATE INDEX IF NOT EXISTS idx_campaign_messages_campaign_id ON campaign_messages(campaign_id)",
            "CREATE INDEX IF NOT EXISTS idx_campaign_messages_status ON campaign_messages(status)"
        ]
    
    def migration_009_optimize_tables(self) -> List[str]:
        """تحسين هيكل الجداول"""
        return [
            # إضافة أعمدة مفقودة للجداول الموجودة
            "ALTER TABLE users ADD COLUMN phone_number VARCHAR(20)",
            "ALTER TABLE users ADD COLUMN language_code VARCHAR(10) DEFAULT 'ar'",
            "ALTER TABLE users ADD COLUMN timezone VARCHAR(50) DEFAULT 'Asia/Riyadh'",
            "ALTER TABLE users ADD COLUMN preferences TEXT",
            "ALTER TABLE users ADD COLUMN last_ip VARCHAR(45)",
            
            "ALTER TABLE tasks ADD COLUMN priority INTEGER DEFAULT 1",
            "ALTER TABLE tasks ADD COLUMN retry_count INTEGER DEFAULT 0",
            "ALTER TABLE tasks ADD COLUMN last_error TEXT",
            "ALTER TABLE tasks ADD COLUMN performance_stats TEXT",
            
            "ALTER TABLE chats ADD COLUMN chat_permissions TEXT",
            "ALTER TABLE chats ADD COLUMN bot_permissions TEXT",
            "ALTER TABLE chats ADD COLUMN last_message_id INTEGER",
            
            "ALTER TABLE scheduled_messages ADD COLUMN timezone VARCHAR(50)",
            "ALTER TABLE scheduled_messages ADD COLUMN retry_count INTEGER DEFAULT 0",
            "ALTER TABLE scheduled_messages ADD COLUMN last_attempt TIMESTAMP",
            
            "ALTER TABLE bot_clones ADD COLUMN config TEXT",
            "ALTER TABLE bot_clones ADD COLUMN performance_stats TEXT",
            "ALTER TABLE bot_clones ADD COLUMN last_heartbeat TIMESTAMP"
        ]
    
    def migration_010_add_constraints(self) -> List[str]:
        """إضافة القيود والعلاقات"""
        return [
            # إنشاء جداول مؤقتة مع القيود
            """
            CREATE TABLE users_new (
                id INTEGER PRIMARY KEY,
                user_id BIGINT UNIQUE NOT NULL,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                phone_number VARCHAR(20),
                language_code VARCHAR(10) DEFAULT 'ar',
                timezone VARCHAR(50) DEFAULT 'Asia/Riyadh',
                is_premium BOOLEAN DEFAULT FALSE,
                premium_expires TIMESTAMP,
                trial_used BOOLEAN DEFAULT FALSE,
                preferences TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_ip VARCHAR(45),
                is_banned BOOLEAN DEFAULT FALSE,
                ban_reason TEXT,
                CHECK (user_id > 0),
                CHECK (language_code IN ('ar', 'en', 'es', 'fr', 'de', 'ru')),
                CHECK (is_premium IN (0, 1)),
                CHECK (trial_used IN (0, 1)),
                CHECK (is_banned IN (0, 1))
            )
            """,
            
            # نسخ البيانات
            """
            INSERT INTO users_new SELECT 
                id, user_id, username, first_name, last_name, 
                phone_number, language_code, timezone,
                is_premium, premium_expires, trial_used, preferences,
                created_at, last_active, last_ip, is_banned, ban_reason
            FROM users
            """,
            
            # استبدال الجدول
            "DROP TABLE users",
            "ALTER TABLE users_new RENAME TO users",
            
            # إعادة إنشاء الفهارس
            "CREATE INDEX idx_users_user_id ON users(user_id)",
            "CREATE INDEX idx_users_is_premium ON users(is_premium)",
            "CREATE INDEX idx_users_created_at ON users(created_at)"
        ]

class BackupManager:
    """مدير النسخ الاحتياطية"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.backup_dir = "backups"
        
    async def create_backup(self) -> str:
        """إنشاء نسخة احتياطية"""
        os.makedirs(self.backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_{timestamp}.db"
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        try:
            # نسخ قاعدة البيانات
            source_conn = sqlite3.connect(self.db.db_path)
            backup_conn = sqlite3.connect(backup_path)
            
            source_conn.backup(backup_conn)
            
            source_conn.close()
            backup_conn.close()
            
            logger.info(f"✅ تم إنشاء نسخة احتياطية: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"❌ خطأ في إنشاء النسخة الاحتياطية: {e}")
            raise
    
    async def restore_backup(self, backup_path: str) -> bool:
        """استرداد نسخة احتياطية"""
        try:
            if not os.path.exists(backup_path):
                raise FileNotFoundError(f"ملف النسخة الاحتياطية غير موجود: {backup_path}")
            
            # إنشاء نسخة احتياطية من الحالة الحالية
            current_backup = await self.create_backup()
            logger.info(f"تم إنشاء نسخة احتياطية من الحالة الحالية: {current_backup}")
            
            # استرداد النسخة الاحتياطية
            backup_conn = sqlite3.connect(backup_path)
            current_conn = sqlite3.connect(self.db.db_path)
            
            backup_conn.backup(current_conn)
            
            backup_conn.close()
            current_conn.close()
            
            logger.info(f"✅ تم استرداد النسخة الاحتياطية: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في استرداد النسخة الاحتياطية: {e}")
            return False
    
    async def cleanup_old_backups(self, keep_count: int = 7):
        """تنظيف النسخ الاحتياطية القديمة"""
        try:
            if not os.path.exists(self.backup_dir):
                return
            
            backup_files = []
            for filename in os.listdir(self.backup_dir):
                if filename.startswith("backup_") and filename.endswith(".db"):
                    filepath = os.path.join(self.backup_dir, filename)
                    backup_files.append((filepath, os.path.getctime(filepath)))
            
            # ترتيب حسب تاريخ الإنشاء
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            # حذف النسخ الزائدة
            for filepath, _ in backup_files[keep_count:]:
                os.remove(filepath)
                logger.info(f"تم حذف النسخة الاحتياطية القديمة: {filepath}")
                
        except Exception as e:
            logger.error(f"خطأ في تنظيف النسخ الاحتياطية: {e}")
