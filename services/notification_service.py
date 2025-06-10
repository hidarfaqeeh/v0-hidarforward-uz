"""
خدمة الإشعارات المتقدمة
Advanced Notification Service
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from telegram import Bot
from telegram.error import TelegramError
from database.db_manager import DatabaseManager
from config.messages import NotificationMessages
from utils.logger import BotLogger

logger = BotLogger()

class NotificationService:
    """خدمة الإشعارات الشاملة"""
    
    def __init__(self, db: DatabaseManager, bot_token: str):
        self.db = db
        self.bot = Bot(token=bot_token)
        self.notification_queue = asyncio.Queue()
        self.is_running = False
        
    async def start(self):
        """بدء خدمة الإشعارات"""
        if not self.is_running:
            self.is_running = True
            asyncio.create_task(self.notification_processor())
            logger.logger.info("✅ تم بدء خدمة الإشعارات")
    
    async def stop(self):
        """إيقاف خدمة الإشعارات"""
        self.is_running = False
        logger.logger.info("⏹️ تم إيقاف خدمة الإشعارات")
    
    async def notification_processor(self):
        """معالج طابور الإشعارات"""
        while self.is_running:
            try:
                notification = await asyncio.wait_for(
                    self.notification_queue.get(),
                    timeout=1.0
                )
                await self.send_notification(notification)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.log_error(e, {'function': 'notification_processor'})
                await asyncio.sleep(1)
    
    async def send_notification(self, notification: Dict[str, Any]):
        """إرسال إشعار"""
        try:
            user_id = notification['user_id']
            message = notification['message']
            notification_type = notification.get('type', 'info')
            
            # إضافة أيقونة حسب النوع
            icons = {
                'info': 'ℹ️',
                'success': '✅',
                'warning': '⚠️',
                'error': '❌',
                'premium': '💎',
                'task': '📋',
                'system': '🔧'
            }
            
            icon = icons.get(notification_type, 'ℹ️')
            formatted_message = f"{icon} {message}"
            
            await self.bot.send_message(
                chat_id=user_id,
                text=formatted_message,
                parse_mode='HTML'
            )
            
            # تسجيل الإشعار في قاعدة البيانات
            await self.log_notification(notification)
            
        except TelegramError as e:
            logger.log_error(e, {
                'function': 'send_notification',
                'user_id': notification.get('user_id'),
                'type': notification.get('type')
            })
        except Exception as e:
            logger.log_error(e, {'function': 'send_notification'})
    
    async def queue_notification(self, user_id: int, message: str, 
                                notification_type: str = 'info', 
                                priority: int = 1, data: Dict = None):
        """إضافة إشعار للطابور"""
        notification = {
            'user_id': user_id,
            'message': message,
            'type': notification_type,
            'priority': priority,
            'data': data or {},
            'created_at': datetime.now().isoformat()
        }
        
        await self.notification_queue.put(notification)
    
    async def log_notification(self, notification: Dict[str, Any]):
        """تسجيل الإشعار في قاعدة البيانات"""
        query = """
        INSERT INTO notifications 
        (user_id, notification_type, title, message, data, priority, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        self.db.execute_update(query, (
            notification['user_id'],
            notification['type'],
            notification.get('title', ''),
            notification['message'],
            json.dumps(notification.get('data', {})),
            notification['priority'],
            notification['created_at']
        ))
    
    async def notify_new_user(self, user_id: int, user_name: str):
        """إشعار مستخدم جديد"""
        message = NotificationMessages.NEW_USER.format(
            user_name=user_name,
            user_id=user_id
        )
        
        # إشعار المشرفين
        admins = await self.db.get_admin_user_ids()
        for admin_id in admins:
            await self.queue_notification(
                admin_id, message, 'info', priority=2
            )
    
    async def notify_premium_expired(self, user_id: int):
        """إشعار انتهاء Premium"""
        message = NotificationMessages.PREMIUM_EXPIRED.format(user_id=user_id)
        
        # إشعار المستخدم
        await self.queue_notification(
            user_id, 
            "💎 انتهت فترة Premium الخاصة بك. قم بالتجديد للاستمرار في الاستفادة من الميزات المتقدمة.",
            'warning',
            priority=3
        )
        
        # إشعار المشرفين
        admins = await self.db.get_admin_user_ids()
        for admin_id in admins:
            await self.queue_notification(admin_id, message, 'info')
    
    async def notify_task_error(self, user_id: int, task_id: int, error_message: str):
        """إشعار خطأ في المهمة"""
        user_message = f"❌ حدث خطأ في المهمة {task_id}: {error_message}"
        await self.queue_notification(user_id, user_message, 'error', priority=3)
        
        # إشعار المشرفين
        admin_message = NotificationMessages.TASK_ERROR.format(
            task_id=task_id,
            error_message=error_message
        )
        admins = await self.db.get_admin_user_ids()
        for admin_id in admins:
            await self.queue_notification(admin_id, admin_message, 'error')
    
    async def notify_system_error(self, error_details: str):
        """إشعار خطأ في النظام"""
        message = NotificationMessages.SYSTEM_ERROR.format(error_details=error_details)
        
        # إشعار جميع المشرفين والمطورين
        admins = await self.db.get_admin_user_ids()
        developers = await self.db.get_developer_user_ids()
        
        all_recipients = list(set(admins + developers))
        
        for recipient_id in all_recipients:
            await self.queue_notification(
                recipient_id, message, 'error', priority=5
            )
    
    async def notify_high_usage(self, usage_details: str):
        """إشعار استخدام عالي"""
        message = NotificationMessages.HIGH_USAGE.format(usage_details=usage_details)
        
        admins = await self.db.get_admin_user_ids()
        for admin_id in admins:
            await self.queue_notification(admin_id, message, 'warning', priority=4)
    
    async def notify_security_alert(self, alert_details: str):
        """إشعار تنبيه أمني"""
        message = NotificationMessages.SECURITY_ALERT.format(alert_details=alert_details)
        
        # إشعار فوري لجميع المشرفين والمطورين
        admins = await self.db.get_admin_user_ids()
        developers = await self.db.get_developer_user_ids()
        
        all_recipients = list(set(admins + developers))
        
        for recipient_id in all_recipients:
            await self.queue_notification(
                recipient_id, message, 'error', priority=5
            )
    
    async def send_bulk_notification(self, user_ids: List[int], message: str, 
                                   notification_type: str = 'info'):
        """إرسال إشعار جماعي"""
        for user_id in user_ids:
            await self.queue_notification(user_id, message, notification_type)
    
    async def get_user_notifications(self, user_id: int, limit: int = 50) -> List[Dict]:
        """الحصول على إشعارات المستخدم"""
        query = """
        SELECT * FROM notifications 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT ?
        """
        return self.db.execute_query(query, (user_id, limit))
    
    async def mark_notification_read(self, notification_id: int, user_id: int) -> bool:
        """تمييز الإشعار كمقروء"""
        query = """
        UPDATE notifications 
        SET is_read = TRUE, read_at = ? 
        WHERE id = ? AND user_id = ?
        """
        return self.db.execute_update(query, (datetime.now(), notification_id, user_id))
    
    async def get_unread_count(self, user_id: int) -> int:
        """الحصول على عدد الإشعارات غير المقروءة"""
        query = "SELECT COUNT(*) as count FROM notifications WHERE user_id = ? AND is_read = FALSE"
        result = self.db.execute_query(query, (user_id,))
        return result[0]['count'] if result else 0

class PushNotificationService:
    """خدمة الإشعارات الفورية"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.subscribers = {}  # WebSocket connections
    
    async def subscribe(self, user_id: int, connection):
        """اشتراك في الإشعارات الفورية"""
        self.subscribers[user_id] = connection
    
    async def unsubscribe(self, user_id: int):
        """إلغاء الاشتراك"""
        if user_id in self.subscribers:
            del self.subscribers[user_id]
    
    async def push_to_user(self, user_id: int, notification: Dict[str, Any]):
        """إرسال إشعار فوري للمستخدم"""
        if user_id in self.subscribers:
            try:
                connection = self.subscribers[user_id]
                await connection.send_json(notification)
            except Exception as e:
                logger.log_error(e, {
                    'function': 'push_to_user',
                    'user_id': user_id
                })
                # إزالة الاتصال المعطل
                await self.unsubscribe(user_id)

class EmailNotificationService:
    """خدمة الإشعارات عبر البريد الإلكتروني"""
    
    def __init__(self, smtp_config: Dict[str, Any]):
        self.smtp_config = smtp_config
        self.enabled = smtp_config.get('enabled', False)
    
    async def send_email(self, to_email: str, subject: str, body: str, 
                        is_html: bool = False):
        """إرسال بريد إلكتروني"""
        if not self.enabled:
            return False
        
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart()
            msg['From'] = self.smtp_config['from_email']
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'html' if is_html else 'plain', 'utf-8'))
            
            server = smtplib.SMTP(
                self.smtp_config['smtp_server'],
                self.smtp_config['smtp_port']
            )
            
            if self.smtp_config.get('use_tls', True):
                server.starttls()
            
            server.login(
                self.smtp_config['username'],
                self.smtp_config['password']
            )
            
            server.send_message(msg)
            server.quit()
            
            return True
            
        except Exception as e:
            logger.log_error(e, {
                'function': 'send_email',
                'to_email': to_email
            })
            return False
    
    async def send_welcome_email(self, user_email: str, user_name: str):
        """إرسال بريد ترحيب"""
        subject = "مرحباً بك في بوت التوجيه المتقدم"
        body = f"""
        <h2>مرحباً {user_name}!</h2>
        <p>نرحب بك في بوت التوجيه المتقدم.</p>
        <p>يمكنك الآن الاستفادة من جميع الميزات المتاحة.</p>
        <p>للبدء، قم بزيارة البوت على تلغرام.</p>
        """
        
        await self.send_email(user_email, subject, body, is_html=True)
    
    async def send_premium_expiry_email(self, user_email: str, user_name: str, 
                                      expiry_date: datetime):
        """إرسال بريد انتهاء Premium"""
        subject = "تذكير: انتهاء اشتراك Premium"
        body = f"""
        <h2>عزيزي {user_name}</h2>
        <p>ينتهي اشتراكك في Premium في {expiry_date.strftime('%Y-%m-%d')}.</p>
        <p>قم بالتجديد الآن للاستمرار في الاستفادة من الميزات المتقدمة.</p>
        """
        
        await self.send_email(user_email, subject, body, is_html=True)
