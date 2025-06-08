"""
مزخرفات البوت
Bot Decorators
"""

import functools
import asyncio
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from config.settings import Settings, Messages
from utils.logger import BotLogger

logger = BotLogger()
settings = Settings()

def user_required(func):
    """مزخرف للتأكد من تسجيل المستخدم"""
    @functools.wraps(func)
    async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if not user:
            return
        
        # إضافة/تحديث المستخدم في قاعدة البيانات
        await self.db.add_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # تحديث آخر نشاط
        await self.db.update_user_activity(user.id)
        
        # تسجيل النشاط
        logger.log_user_action(user.id, func.__name__)
        
        return await func(self, update, context)
    return wrapper

def premium_required(func):
    """مزخرف للتأكد من اشتراك Premium"""
    @functools.wraps(func)
    async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        # فحص حالة Premium
        is_premium = await self.db.check_premium(user_id)
        
        if not is_premium:
            await update.message.reply_text(
                Messages.PREMIUM_EXPIRED,
                parse_mode='HTML'
            )
            return
        
        return await func(self, update, context)
    return wrapper

def admin_required(func):
    """مزخرف للتأكد من صلاحيات الإدارة"""
    @functools.wraps(func)
    async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        # فحص إذا كان مطور
        if user_id in settings.DEVELOPERS:
            return await func(self, update, context)
        
        # فحص إذا كان مشرف
        is_admin = await self.db.is_admin(user_id)
        if not is_admin:
            await update.message.reply_text(
                Messages.ERROR_PERMISSION,
                parse_mode='HTML'
            )
            return
        
        # تسجيل العملية الإدارية
        logger.log_admin_action(user_id, func.__name__)
        
        return await func(self, update, context)
    return wrapper

def rate_limit(max_calls: int = 5, window_seconds: int = 60):
    """مزخرف لتحديد معدل الاستخدام"""
    def decorator(func):
        # قاموس لتتبع استخدام كل مستخدم
        user_calls = {}
        
        @functools.wraps(func)
        async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
            user_id = update.effective_user.id
            current_time = datetime.now()
            
            # تنظيف السجلات القديمة
            if user_id in user_calls:
                user_calls[user_id] = [
                    call_time for call_time in user_calls[user_id]
                    if current_time - call_time < timedelta(seconds=window_seconds)
                ]
            else:
                user_calls[user_id] = []
            
            # فحص الحد الأقصى
            if len(user_calls[user_id]) >= max_calls:
                await update.message.reply_text(
                    f"⚠️ تم تجاوز الحد المسموح. يرجى الانتظار {window_seconds} ثانية."
                )
                return
            
            # إضافة الاستدعاء الحالي
            user_calls[user_id].append(current_time)
            
            return await func(self, update, context)
        return wrapper
    return decorator

def error_handler(func):
    """مزخرف لمعالجة الأخطاء"""
    @functools.wraps(func)
    async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            return await func(self, update, context)
        except Exception as e:
            # تسجيل الخطأ
            logger.log_error(e, {
                'function': func.__name__,
                'user_id': update.effective_user.id if update.effective_user else None,
                'chat_id': update.effective_chat.id if update.effective_chat else None
            })
            
            # إرسال رسالة خطأ للمستخدم
            try:
                await update.message.reply_text(Messages.ERROR_GENERAL)
            except:
                pass
            
            raise e
    return wrapper

def log_execution_time(func):
    """مزخرف لتسجيل وقت التنفيذ"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = datetime.now()
        result = await func(*args, **kwargs)
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        logger.logger.info(f"Function {func.__name__} executed in {execution_time:.2f} seconds")
        return result
    return wrapper

def async_retry(max_retries: int = 3, delay: float = 1.0):
    """مزخرف لإعادة المحاولة في حالة الفشل"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        await asyncio.sleep(delay * (2 ** attempt))  # Exponential backoff
                        continue
                    break
            
            # إذا فشلت جميع المحاولات
            logger.log_error(last_exception, {
                'function': func.__name__,
                'attempts': max_retries,
                'final_attempt': True
            })
            raise last_exception
        return wrapper
    return decorator
