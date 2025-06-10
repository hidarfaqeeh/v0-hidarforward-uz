"""
خدمة الأمان المتقدمة
Advanced Security Service
"""

import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from database.db_manager import DatabaseManager
from utils.logger import BotLogger

logger = BotLogger()

class SecurityService:
    """خدمة الأمان الشاملة"""
    
    def __init__(self, db: DatabaseManager, secret_key: str):
        self.db = db
        self.secret_key = secret_key
        self.failed_attempts = {}
        self.rate_limits = {}
        
    async def hash_password(self, password: str) -> str:
        """تشفير كلمة المرور"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', 
                                          password.encode('utf-8'), 
                                          salt.encode('utf-8'), 
                                          100000)
        return f"{salt}:{password_hash.hex()}"
    
    async def verify_password(self, password: str, hashed_password: str) -> bool:
        """التحقق من كلمة المرور"""
        try:
            salt, password_hash = hashed_password.split(':')
            new_hash = hashlib.pbkdf2_hmac('sha256',
                                         password.encode('utf-8'),
                                         salt.encode('utf-8'),
                                         100000)
            return new_hash.hex() == password_hash
        except Exception:
            return False
    
    async def generate_session_token(self, user_id: int, expires_hours: int = 24) -> str:
        """إنشاء رمز جلسة"""
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(hours=expires_hours),
            'iat': datetime.utcnow(),
            'type': 'session'
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    async def verify_session_token(self, token: str) -> Optional[Dict[str, Any]]:
        """التحقق من رمز الجلسة"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            logger.logger.warning("انتهت صلاحية رمز الجلسة")
            return None
        except jwt.InvalidTokenError:
            logger.logger.warning("رمز جلسة غير صحيح")
            return None
    
    async def create_user_session(self, user_id: int, ip_address: str = None, 
                                 user_agent: str = None) -> str:
        """إنشاء جلسة مستخدم"""
        session_id = secrets.token_urlsafe(32)
        session_token = await self.generate_session_token(user_id)
        
        query = """
        INSERT INTO user_sessions 
        (user_id, session_id, session_data, ip_address, user_agent, expires_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        
        expires_at = datetime.now() + timedelta(hours=24)
        session_data = {
            'token': session_token,
            'created_at': datetime.now().isoformat()
        }
        
        self.db.execute_update(query, (
            user_id, session_id, json.dumps(session_data),
            ip_address, user_agent, expires_at
        ))
        
        return session_id
    
    async def validate_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """التحقق من صحة الجلسة"""
        query = """
        SELECT * FROM user_sessions 
        WHERE session_id = ? AND is_active = TRUE AND expires_at > ?
        """
        
        result = self.db.execute_query(query, (session_id, datetime.now()))
        if not result:
            return None
        
        session = result[0]
        
        # تحديث آخر نشاط
        update_query = """
        UPDATE user_sessions 
        SET last_activity = ? 
        WHERE session_id = ?
        """
        self.db.execute_update(update_query, (datetime.now(), session_id))
        
        return session
    
    async def invalidate_session(self, session_id: str) -> bool:
        """إلغاء الجلسة"""
        query = """
        UPDATE user_sessions 
        SET is_active = FALSE 
        WHERE session_id = ?
        """
        return self.db.execute_update(query, (session_id,))
    
    async def check_rate_limit(self, user_id: int, action_type: str, 
                              max_attempts: int = 5, window_minutes: int = 15) -> bool:
        """فحص حدود المعدل"""
        current_time = datetime.now()
        window_start = current_time - timedelta(minutes=window_minutes)
        
        # تنظيف السجلات القديمة
        cleanup_query = """
        DELETE FROM rate_limits 
        WHERE expires_at < ?
        """
        self.db.execute_update(cleanup_query, (current_time,))
        
        # فحص المحاولات الحالية
        check_query = """
        SELECT SUM(count) as total_attempts 
        FROM rate_limits 
        WHERE user_id = ? AND action_type = ? AND window_start >= ?
        """
        
        result = self.db.execute_query(check_query, (user_id, action_type, window_start))
        current_attempts = result[0]['total_attempts'] if result and result[0]['total_attempts'] else 0
        
        if current_attempts >= max_attempts:
            # تسجيل محاولة تجاوز الحد
            await self.log_security_event(
                user_id, 'rate_limit_exceeded', 'high',
                f"تجاوز حد المعدل لـ {action_type}: {current_attempts}/{max_attempts}"
            )
            return False
        
        # تسجيل المحاولة الجديدة
        insert_query = """
        INSERT INTO rate_limits 
        (user_id, action_type, count, window_start, expires_at)
        VALUES (?, ?, 1, ?, ?)
        """
        
        expires_at = current_time + timedelta(minutes=window_minutes)
        self.db.execute_update(insert_query, (
            user_id, action_type, current_time, expires_at
        ))
        
        return True
    
    async def log_security_event(self, user_id: int, event_type: str, 
                                severity: str, description: str,
                                ip_address: str = None, user_agent: str = None,
                                additional_data: Dict[str, Any] = None):
        """تسجيل حدث أمني"""
        query = """
        INSERT INTO security_events 
        (user_id, event_type, severity, description, ip_address, user_agent, additional_data)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        self.db.execute_update(query, (
            user_id, event_type, severity, description,
            ip_address, user_agent, json.dumps(additional_data or {})
        ))
        
        # إشعار فوري للأحداث الحرجة
        if severity in ['high', 'critical']:
            await self.notify_security_alert(event_type, description, user_id)
    
    async def notify_security_alert(self, event_type: str, description: str, user_id: int):
        """إشعار تنبيه أمني"""
        # إشعار المشرفين والمطورين
        alert_message = f"🚨 تنبيه أمني: {event_type}\n📝 التفاصيل: {description}\n👤 المستخدم: {user_id}"
        
        # هنا يمكن إضافة إشعار عبر NotificationService
        logger.logger.critical(f"Security Alert: {alert_message}")
    
    async def detect_suspicious_activity(self, user_id: int, activity_data: Dict[str, Any]) -> bool:
        """كشف النشاط المشبوه"""
        suspicious_indicators = []
        
        # فحص تكرار الطلبات
        if await self.check_request_frequency(user_id):
            suspicious_indicators.append("high_request_frequency")
        
        # فحص أنماط الاستخدام غير العادية
        if await self.check_unusual_patterns(user_id, activity_data):
            suspicious_indicators.append("unusual_patterns")
        
        # فحص محاولات الوصول غير المصرح بها
        if await self.check_unauthorized_access(user_id, activity_data):
            suspicious_indicators.append("unauthorized_access")
        
        if suspicious_indicators:
            await self.log_security_event(
                user_id, 'suspicious_activity', 'medium',
                f"نشاط مشبوه: {', '.join(suspicious_indicators)}",
                additional_data={'indicators': suspicious_indicators, 'activity': activity_data}
            )
            return True
        
        return False
    
    async def check_request_frequency(self, user_id: int) -> bool:
        """فحص تكرار الطلبات"""
        # فحص آخر 5 دقائق
        recent_time = datetime.now() - timedelta(minutes=5)
        
        query = """
        SELECT COUNT(*) as request_count 
        FROM analytics_events 
        WHERE user_id = ? AND timestamp >= ?
        """
        
        result = self.db.execute_query(query, (user_id, recent_time))
        request_count = result[0]['request_count'] if result else 0
        
        # إذا كان أكثر من 100 طلب في 5 دقائق
        return request_count > 100
    
    async def check_unusual_patterns(self, user_id: int, activity_data: Dict[str, Any]) -> bool:
        """فحص الأنماط غير العادية"""
        # فحص الوقت غير العادي للنشاط
        current_hour = datetime.now().hour
        if current_hour < 6 or current_hour > 23:  # نشاط في ساعات غير عادية
            return True
        
        # فحص تغيير مفاجئ في السلوك
        # يمكن تطوير هذا باستخدام خوارزميات التعلم الآلي
        
        return False
    
    async def check_unauthorized_access(self, user_id: int, activity_data: Dict[str, Any]) -> bool:
        """فحص محاولات الوصول غير المصرح بها"""
        # فحص محاولة الوصول لموارد غير مصرح بها
        restricted_actions = ['admin_panel', 'user_management', 'system_settings']
        
        if activity_data.get('action') in restricted_actions:
            # فحص إذا كان المستخدم مشرف
            is_admin = await self.db.is_admin(user_id)
            if not is_admin:
                return True
        
        return False
    
    async def encrypt_sensitive_data(self, data: str) -> str:
        """تشفير البيانات الحساسة"""
        from cryptography.fernet import Fernet
        
        # إنشاء مفتاح من المفتاح السري
        key = hashlib.sha256(self.secret_key.encode()).digest()
        key = base64.urlsafe_b64encode(key)
        
        fernet = Fernet(key)
        encrypted_data = fernet.encrypt(data.encode())
        
        return base64.urlsafe_b64encode(encrypted_data).decode()
    
    async def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """فك تشفير البيانات الحساسة"""
        from cryptography.fernet import Fernet
        import base64
        
        try:
            # إنشاء مفتاح من المفتاح السري
            key = hashlib.sha256(self.secret_key.encode()).digest()
            key = base64.urlsafe_b64encode(key)
            
            fernet = Fernet(key)
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = fernet.decrypt(encrypted_bytes)
            
            return decrypted_data.decode()
        except Exception as e:
            logger.log_error(e, {'function': 'decrypt_sensitive_data'})
            raise
    
    async def generate_api_key(self, user_id: int, permissions: List[str] = None) -> str:
        """إنشاء مفتاح API"""
        api_key = secrets.token_urlsafe(32)
        
        # تشفير المفتاح
        encrypted_key = await self.encrypt_sensitive_data(api_key)
        
        # حفظ في قاعدة البيانات
        query = """
        INSERT INTO api_keys 
        (user_id, key_hash, permissions, created_at, expires_at)
        VALUES (?, ?, ?, ?, ?)
        """
        
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        expires_at = datetime.now() + timedelta(days=365)  # صالح لسنة
        
        self.db.execute_update(query, (
            user_id, key_hash, json.dumps(permissions or []),
            datetime.now(), expires_at
        ))
        
        return api_key
    
    async def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """التحقق من صحة مفتاح API"""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        query = """
        SELECT * FROM api_keys 
        WHERE key_hash = ? AND is_active = TRUE AND expires_at > ?
        """
        
        result = self.db.execute_query(query, (key_hash, datetime.now()))
        if result:
            return result[0]
        return None
    
    async def audit_user_action(self, user_id: int, action: str, resource_type: str = None,
                               resource_id: str = None, old_values: Dict = None,
                               new_values: Dict = None, ip_address: str = None,
                               user_agent: str = None, success: bool = True,
                               error_message: str = None):
        """تدقيق عمليات المستخدم"""
        query = """
        INSERT INTO audit_log 
        (user_id, action, resource_type, resource_id, old_values, new_values,
         ip_address, user_agent, success, error_message)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        self.db.execute_update(query, (
            user_id, action, resource_type, resource_id,
            json.dumps(old_values) if old_values else None,
            json.dumps(new_values) if new_values else None,
            ip_address, user_agent, success, error_message
        ))
    
    async def get_security_report(self, days: int = 30) -> Dict[str, Any]:
        """تقرير الأمان"""
        start_date = datetime.now() - timedelta(days=days)
        
        # إحصائيات الأحداث الأمنية
        events_query = """
        SELECT 
            event_type,
            severity,
            COUNT(*) as count
        FROM security_events 
        WHERE created_at >= ?
        GROUP BY event_type, severity
        ORDER BY count DESC
        """
        events_stats = self.db.execute_query(events_query, (start_date,))
        
        # المستخدمين المشبوهين
        suspicious_users_query = """
        SELECT 
            user_id,
            COUNT(*) as incident_count,
            MAX(created_at) as last_incident
        FROM security_events 
        WHERE created_at >= ? AND severity IN ('high', 'critical')
        GROUP BY user_id
        ORDER BY incident_count DESC
        LIMIT 10
        """
        suspicious_users = self.db.execute_query(suspicious_users_query, (start_date,))
        
        # إحصائيات تجاوز الحدود
        rate_limit_stats_query = """
        SELECT 
            action_type,
            COUNT(DISTINCT user_id) as affected_users,
            SUM(count) as total_violations
        FROM rate_limits 
        WHERE window_start >= ?
        GROUP BY action_type
        """
        rate_limit_stats = self.db.execute_query(rate_limit_stats_query, (start_date,))
        
        # الجلسات النشطة
        active_sessions_query = """
        SELECT COUNT(*) as count 
        FROM user_sessions 
        WHERE is_active = TRUE AND expires_at > ?
        """
        active_sessions = self.db.execute_query(active_sessions_query, (datetime.now(),))
        
        return {
            'period_days': days,
            'security_events': events_stats,
            'suspicious_users': suspicious_users,
            'rate_limit_violations': rate_limit_stats,
            'active_sessions': active_sessions[0]['count'] if active_sessions else 0,
            'generated_at': datetime.now().isoformat()
        }
    
    async def cleanup_expired_sessions(self):
        """تنظيف الجلسات المنتهية الصلاحية"""
        query = """
        UPDATE user_sessions 
        SET is_active = FALSE 
        WHERE expires_at < ? OR last_activity < ?
        """
        
        # إلغاء الجلسات المنتهية الصلاحية أو غير النشطة لأكثر من 7 أيام
        inactive_threshold = datetime.now() - timedelta(days=7)
        
        self.db.execute_update(query, (datetime.now(), inactive_threshold))
    
    async def enable_two_factor_auth(self, user_id: int) -> str:
        """تفعيل المصادقة الثنائية"""
        import pyotp
        
        # إنشاء مفتاح سري
        secret = pyotp.random_base32()
        
        # حفظ المفتاح مشفراً
        encrypted_secret = await self.encrypt_sensitive_data(secret)
        
        query = """
        UPDATE users 
        SET two_factor_secret = ?, two_factor_enabled = TRUE 
        WHERE user_id = ?
        """
        
        self.db.execute_update(query, (encrypted_secret, user_id))
        
        # إنشاء QR code URL
        totp = pyotp.TOTP(secret)
        qr_url = totp.provisioning_uri(
            name=f"User_{user_id}",
            issuer_name="Telegram Forward Bot"
        )
        
        return qr_url
    
    async def verify_two_factor_code(self, user_id: int, code: str) -> bool:
        """التحقق من رمز المصادقة الثنائية"""
        import pyotp
        
        # الحصول على المفتاح السري
        query = "SELECT two_factor_secret FROM users WHERE user_id = ?"
        result = self.db.execute_query(query, (user_id,))
        
        if not result or not result[0]['two_factor_secret']:
            return False
        
        try:
            # فك تشفير المفتاح
            encrypted_secret = result[0]['two_factor_secret']
            secret = await self.decrypt_sensitive_data(encrypted_secret)
            
            # التحقق من الرمز
            totp = pyotp.TOTP(secret)
            return totp.verify(code, valid_window=1)
            
        except Exception as e:
            logger.log_error(e, {
                'function': 'verify_two_factor_code',
                'user_id': user_id
            })
            return False

class InputSanitizer:
    """منظف المدخلات"""
    
    @staticmethod
    def sanitize_text(text: str, max_length: int = 1000) -> str:
        """تنظيف النص"""
        if not text:
            return ""
        
        # إزالة الأحرف الخطيرة
        dangerous_chars = ['<', '>', '"', "'", '&', '\x00']
        for char in dangerous_chars:
            text = text.replace(char, '')
        
        # تحديد الطول
        if len(text) > max_length:
            text = text[:max_length]
        
        return text.strip()
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """تنظيف اسم الملف"""
        import re
        
        # إزالة الأحرف غير المسموحة
        filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', filename)
        
        # إزالة النقاط في البداية والنهاية
        filename = filename.strip('.')
        
        # تحديد الطول
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255-len(ext)] + ext
        
        return filename
    
    @staticmethod
    def validate_chat_id(chat_id: str) -> bool:
        """التحقق من صحة معرف الدردشة"""
        try:
            chat_id_int = int(chat_id)
            return abs(chat_id_int) > 0
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_user_id(user_id: str) -> bool:
        """التحقق من صحة معرف المستخدم"""
        try:
            user_id_int = int(user_id)
            return user_id_int > 0
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_bot_token(token: str) -> bool:
        """التحقق من صحة توكن البوت"""
        import re
        
        if not token:
            return False
        
        # تنسيق توكن البوت: bot_id:token
        pattern = r'^\d+:[a-zA-Z0-9_-]{35}$'
        return bool(re.match(pattern, token))
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """التحقق من صحة الرابط"""
        import re
        
        if not url:
            return False
        
        # نمط بسيط للروابط
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return bool(re.match(pattern, url))
    
    @staticmethod
    def escape_html(text: str) -> str:
        """تجنب HTML"""
        import html
        return html.escape(text)
    
    @staticmethod
    def validate_json(json_string: str) -> bool:
        """التحقق من صحة JSON"""
        try:
            json.loads(json_string)
            return True
        except (json.JSONDecodeError, TypeError):
            return False
