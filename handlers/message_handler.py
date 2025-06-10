"""
معالج الرسائل الرئيسي
Main Message Handler
"""

import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from database.db_manager import DatabaseManager
from services.message_forwarder import MessageForwarder
from utils.decorators import error_handler
from utils.logger import BotLogger

logger = BotLogger()

class MessageHandler:
    """معالج الرسائل الرئيسي"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.message_forwarder = MessageForwarder(db)
        self.initialized = False
    
    async def initialize(self):
        """تهيئة معالج الرسائل"""
        if not self.initialized:
            await self.message_forwarder.initialize()
            self.initialized = True
            logger.logger.info("✅ تم تهيئة معالج الرسائل")
    
    @error_handler
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج الرسائل العام"""
        try:
            if not self.initialized:
                await self.initialize()
            
            # فحص وجود الرسالة
            if not update.message:
                return
            
            # تحديث نشاط المستخدم
            if update.effective_user:
                await self.db.update_user_activity(update.effective_user.id)
            
            # تمرير الرسالة لخدمة التوجيه
            await self.message_forwarder.handle_message(update, context)
            
        except Exception as e:
            logger.log_error(e, {
                'function': 'handle_message',
                'user_id': update.effective_user.id if update.effective_user else None,
                'message_id': update.message.message_id if update.message else None,
                'chat_id': update.message.chat_id if update.message else None
            })
    
    @error_handler
    async def handle_edited_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج الرسائل المُعدلة"""
        if not self.initialized:
            await self.initialize()
        
        await self.message_forwarder.handle_message_edit(update, context)
    
    @error_handler
    async def handle_channel_post(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج منشورات القنوات"""
        if not self.initialized:
            await self.initialize()
        
        # تحويل منشور القناة إلى رسالة عادية للمعالجة
        if update.channel_post:
            # إنشاء update مؤقت مع الرسالة
            temp_update = Update(
                update_id=update.update_id,
                message=update.channel_post
            )
            await self.message_forwarder.handle_message(temp_update, context)
    
    @error_handler
    async def handle_edited_channel_post(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج منشورات القنوات المُعدلة"""
        if not self.initialized:
            await self.initialize()
        
        if update.edited_channel_post:
            temp_update = Update(
                update_id=update.update_id,
                edited_message=update.edited_channel_post
            )
            await self.message_forwarder.handle_message_edit(temp_update, context)
    
    async def reload_tasks(self):
        """إعادة تحميل المهام"""
        if self.initialized:
            await self.message_forwarder.reload_tasks()
    
    async def get_forwarding_stats(self) -> dict:
        """الحصول على إحصائيات التوجيه"""
        # سيتم تطويرها في المرحلة التالية
        return {
            'active_tasks': len(self.message_forwarder.active_tasks),
            'queue_size': self.message_forwarder.forwarding_queue.qsize(),
            'is_processing': self.message_forwarder.is_processing
        }
