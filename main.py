#!/usr/bin/env python3
"""
بوت تلغرام متقدم لمراقبة وتوجيه الرسائل
Bot Telegram Advanced for Message Monitoring and Forwarding
"""

import asyncio
import logging
import os
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from database.db_manager import DatabaseManager
from handlers.admin_handler import AdminHandler
from handlers.task_handler import TaskHandler
from handlers.user_handler import UserHandler
from services.message_forwarder import MessageForwarder
from handlers.webhook_handler import WebhookHandler
from config.settings import Settings
from utils.logger import setup_logger

# إعداد نظام السجلات
setup_logger()
logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self):
        self.settings = Settings()
        self.db = DatabaseManager()
        self.admin_handler = AdminHandler(self.db)
        self.task_handler = TaskHandler(self.db)
        self.user_handler = UserHandler(self.db)
        self.message_forwarder = MessageForwarder(self.db)
        self.webhook_handler = WebhookHandler(self.db)
        
    async def initialize(self):
        """تهيئة البوت وقاعدة البيانات"""
        try:
            # إنشاء قاعدة البيانات والجداول
            await self.db.initialize()
            logger.info("✅ تم تهيئة قاعدة البيانات بنجاح")
            
            # تهيئة الويب هوك
            await self.webhook_handler.setup_webhook()
            logger.info("✅ تم إعداد الويب هوك بنجاح")
            
            return True
        except Exception as e:
            logger.error(f"❌ خطأ في تهيئة البوت: {e}")
            return False
    
    def setup_handlers(self, application):
        """إعداد معالجات الأوامر والرسائل"""
        
        # معالجات الأوامر الأساسية
        application.add_handler(CommandHandler("start", self.user_handler.start_command))
        application.add_handler(CommandHandler("help", self.user_handler.help_command))
        application.add_handler(CommandHandler("status", self.user_handler.status_command))
        
        # معالجات الإدارة
        application.add_handler(CommandHandler("admin", self.admin_handler.admin_panel))
        application.add_handler(CommandHandler("stats", self.admin_handler.show_stats))
        application.add_handler(CommandHandler("users", self.admin_handler.manage_users))
        application.add_handler(CommandHandler("broadcast", self.admin_handler.broadcast_message))
        
        # معالجات المهام
        application.add_handler(CommandHandler("tasks", self.task_handler.list_tasks))
        application.add_handler(CommandHandler("newtask", self.task_handler.create_task))
        application.add_handler(CommandHandler("edittask", self.task_handler.edit_task))
        application.add_handler(CommandHandler("deltask", self.task_handler.delete_task))
        
        # معالج الرسائل العام
        application.add_handler(MessageHandler(
            filters.ALL, self.message_forwarder.handle_message
        ))
        
        # معالج الأخطاء
        application.add_error_handler(self.error_handler)
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج الأخطاء العام"""
        logger.error(f"خطأ في البوت: {context.error}")
        
        if update and update.effective_user:
            try:
                await update.message.reply_text(
                    "❌ حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى."
                )
            except:
                pass
    
    def run(self):
        """تشغيل البوت"""
        # إنشاء التطبيق
        application = Application.builder().token(self.settings.BOT_TOKEN).build()
        
        # إعداد المعالجات
        self.setup_handlers(application)
        
        logger.info("🚀 بدء تشغيل البوت...")
        
        # تشغيل البوت
        if self.settings.USE_WEBHOOK:
            application.run_webhook(
                listen="0.0.0.0",
                port=int(os.environ.get("PORT", 8443)),
                webhook_url=self.settings.WEBHOOK_URL,
                drop_pending_updates=True
            )
        else:
            application.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )

if __name__ == "__main__":
    bot = TelegramBot()
    
    # تشغيل التهيئة أولاً
    async def init_bot():
        await bot.initialize()
    
    # تشغيل التهيئة
    asyncio.run(init_bot())
    
    # ثم تشغيل البوت (بدون asyncio.run)
    bot.run()
