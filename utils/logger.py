"""
نظام السجلات المتقدم
Advanced Logging System
"""

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import json

def setup_logger():
    """إعداد نظام السجلات"""
    
    # إنشاء مجلد السجلات
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # إعداد التنسيق
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # السجل الرئيسي
    main_handler = RotatingFileHandler(
        'logs/bot.log', 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    main_handler.setFormatter(formatter)
    main_handler.setLevel(logging.INFO)
    
    # سجل الأخطاء
    error_handler = RotatingFileHandler(
        'logs/errors.log',
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)
    
    # سجل المستخدمين
    user_handler = TimedRotatingFileHandler(
        'logs/users.log',
        when='midnight',
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )
    user_handler.setFormatter(formatter)
    user_handler.setLevel(logging.INFO)
    
    # إعداد اللوغر الرئيسي
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(main_handler)
    root_logger.addHandler(error_handler)
    
    # إعداد لوغر المستخدمين
    user_logger = logging.getLogger('user_activity')
    user_logger.addHandler(user_handler)
    user_logger.setLevel(logging.INFO)
    
    # إعداد لوغر وحدة التحكم للتطوير
    if os.getenv('DEBUG', 'False').lower() == 'true':
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(console_handler)
        root_logger.setLevel(logging.DEBUG)

class BotLogger:
    """مسجل أحداث البوت المخصص"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.user_logger = logging.getLogger('user_activity')
    
    def log_user_action(self, user_id: int, action: str, details: dict = None):
        """تسجيل نشاط المستخدم"""
        log_data = {
            'user_id': user_id,
            'action': action,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        self.user_logger.info(json.dumps(log_data, ensure_ascii=False))
    
    def log_task_action(self, user_id: int, task_id: int, action: str, details: dict = None):
        """تسجيل أحداث المهام"""
        log_data = {
            'user_id': user_id,
            'task_id': task_id,
            'action': action,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        self.logger.info(f"Task Action: {json.dumps(log_data, ensure_ascii=False)}")
    
    def log_message_forward(self, task_id: int, source_chat: int, target_chats: list, 
                           message_id: int, success: bool, error: str = None):
        """تسجيل توجيه الرسائل"""
        log_data = {
            'task_id': task_id,
            'source_chat': source_chat,
            'target_chats': target_chats,
            'message_id': message_id,
            'success': success,
            'error': error,
            'timestamp': datetime.now().isoformat()
        }
        
        if success:
            self.logger.info(f"Message Forwarded: {json.dumps(log_data, ensure_ascii=False)}")
        else:
            self.logger.error(f"Forward Failed: {json.dumps(log_data, ensure_ascii=False)}")
    
    def log_error(self, error: Exception, context: dict = None):
        """تسجيل الأخطاء مع السياق"""
        error_data = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context or {},
            'timestamp': datetime.now().isoformat()
        }
        self.logger.error(f"Bot Error: {json.dumps(error_data, ensure_ascii=False)}")
    
    def log_admin_action(self, admin_id: int, action: str, target: str = None, details: dict = None):
        """تسجيل أحداث الإدارة"""
        log_data = {
            'admin_id': admin_id,
            'action': action,
            'target': target,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        }
        self.logger.warning(f"Admin Action: {json.dumps(log_data, ensure_ascii=False)}")
