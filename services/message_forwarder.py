"""
خدمة توجيه الرسائل المتقدمة
Advanced Message Forwarding Service
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from telegram import Bot, Message, Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError, Forbidden, BadRequest
from database.db_manager import DatabaseManager
from utils.helpers import TextProcessor, TimeHelper
from utils.logger import BotLogger
from filters.message_filters import MessageFilterManager

logger = BotLogger()

class MessageForwarder:
    """خدمة توجيه الرسائل المتقدمة"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.filter_manager = MessageFilterManager()
        self.active_tasks = {}  # كاش للمهام النشطة
        self.last_messages = {}  # تتبع آخر الرسائل لتجنب التكرار
        self.forwarding_queue = asyncio.Queue()  # طابور التوجيه
        self.is_processing = False
        
    async def initialize(self):
        """تهيئة خدمة التوجيه"""
        await self.load_active_tasks()
        await self.start_forwarding_processor()
        logger.logger.info("✅ تم تهيئة خدمة توجيه الرسائل")
    
    async def load_active_tasks(self):
        """تحميل المهام النشطة"""
        try:
            tasks = await self.db.get_active_tasks()
            self.active_tasks = {task['source_chat_id']: task for task in tasks}
            logger.logger.info(f"تم تحميل {len(tasks)} مهمة نشطة")
        except Exception as e:
            logger.log_error(e, {'function': 'load_active_tasks'})
    
    async def start_forwarding_processor(self):
        """بدء معالج طابور التوجيه"""
        if not self.is_processing:
            self.is_processing = True
            asyncio.create_task(self.process_forwarding_queue())
    
    async def process_forwarding_queue(self):
        """معالجة طابور التوجيه"""
        while self.is_processing:
            try:
                # انتظار عنصر في الطابور
                forward_data = await asyncio.wait_for(
                    self.forwarding_queue.get(), 
                    timeout=1.0
                )
                
                await self.process_forward_request(forward_data)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.log_error(e, {'function': 'process_forwarding_queue'})
                await asyncio.sleep(1)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج الرسائل الرئيسي"""
        if not update.message:
            return
        
        message = update.message
        chat_id = message.chat_id
        
        # فحص إذا كانت الدردشة مصدر لأي مهمة
        if chat_id not in self.active_tasks:
            return
        
        task = self.active_tasks[chat_id]
        
        # فحص ساعات العمل
        if not TimeHelper.is_working_hours(task['settings'].get('working_hours', {})):
            return
        
        # فحص الفلاتر
        if not await self.filter_manager.check_message(message, task['settings'].get('filters', {})):
            return
        
        # فحص التكرار
        if await self.is_duplicate_message(message, task['id']):
            return
        
        # إضافة للطابور
        forward_data = {
            'task': task,
            'message': message,
            'timestamp': datetime.now()
        }
        
        await self.forwarding_queue.put(forward_data)
        
        # تسجيل النشاط
        logger.log_message_forward(
            task['id'], 
            chat_id, 
            task['target_chat_ids'], 
            message.message_id, 
            True
        )
    
    async def process_forward_request(self, forward_data: Dict[str, Any]):
        """معالجة طلب التوجيه"""
        task = forward_data['task']
        message = forward_data['message']
        
        try:
            # تطبيق التأخير إذا كان محدداً
            delay = task['settings'].get('delay_seconds', 0)
            if delay > 0:
                await asyncio.sleep(delay)
            
            # معالجة النص إذا كان نوع التوجيه "copy"
            processed_content = None
            if task['forward_type'] == 'copy':
                processed_content = await self.process_message_content(message, task['settings'])
            
            # توجيه للأهداف
            successful_targets = []
            failed_targets = []
            
            for target_chat_id in task['target_chat_ids']:
                try:
                    if task['forward_type'] == 'forward':
                        forwarded_msg = await self.forward_message(message, target_chat_id, task, context)
                    else:
                        forwarded_msg = await self.copy_message(message, target_chat_id, task, context, processed_content)
                    
                    if forwarded_msg:
                        successful_targets.append({
                            'chat_id': target_chat_id,
                            'message_id': forwarded_msg.message_id
                        })
                        
                        # تثبيت الرسالة إذا كان مطلوباً
                        if task['settings'].get('advanced', {}).get('pin_messages', False):
                            try:
                                await context.bot.pin_chat_message(
                                    chat_id=target_chat_id,
                                    message_id=forwarded_msg.message_id,
                                    disable_notification=True
                                )
                            except Exception:
                                pass  # تجاهل أخطاء التثبيت
                    
                except Exception as e:
                    failed_targets.append({
                        'chat_id': target_chat_id,
                        'error': str(e)
                    })
                    logger.log_error(e, {
                        'task_id': task['id'],
                        'target_chat_id': target_chat_id,
                        'message_id': message.message_id
                    })
            
            # تسجيل النتائج
            await self.log_forwarding_results(task, message, successful_targets, failed_targets)
            
        except Exception as e:
            logger.log_error(e, {
                'task_id': task['id'],
                'message_id': message.message_id,
                'function': 'process_forward_request'
            })
    
    async def forward_message(self, message: Message, target_chat_id: int, task: Dict[str, Any], context: ContextTypes.DEFAULT_TYPE) -> Optional[Message]:
        """توجيه الرسالة (Forward)"""
        try:
            # استخدام البوت الحالي من context
            bot = context.bot
            
            forwarded_message = await bot.forward_message(
                chat_id=target_chat_id,
                from_chat_id=message.chat_id,
                message_id=message.message_id
            )
            
            return forwarded_message
            
        except Forbidden:
            # البوت محظور أو لا يملك صلاحيات
            await self.handle_forwarding_error(task, target_chat_id, "البوت محظور أو لا يملك صلاحيات")
            return None
        except BadRequest as e:
            # خطأ في الطلب
            await self.handle_forwarding_error(task, target_chat_id, f"خطأ في الطلب: {str(e)}")
            return None
        except Exception as e:
            logger.log_error(e, {
                'task_id': task['id'],
                'target_chat_id': target_chat_id,
                'function': 'forward_message'
            })
            return None
    
    async def copy_message(self, message: Message, target_chat_id: int, task: Dict[str, Any], context: ContextTypes.DEFAULT_TYPE,
                          processed_content: Dict[str, Any] = None) -> Optional[Message]:
        """نسخ الرسالة (Copy)"""
        try:
            # استخدام البوت الحالي من context
            bot = context.bot
            
            # تحديد المحتوى المُعالج
            if processed_content:
                text = processed_content.get('text')
                caption = processed_content.get('caption')
                reply_markup = processed_content.get('reply_markup')
            else:
                text = message.text
                caption = message.caption
                reply_markup = message.reply_markup
            
            # تحديد نوع الرسالة وإرسالها
            if message.text:
                sent_message = await bot.send_message(
                    chat_id=target_chat_id,
                    text=text,
                    parse_mode='HTML',
                    reply_markup=reply_markup,
                    disable_web_page_preview=task['settings'].get('disable_web_preview', False)
                )
            elif message.photo:
                sent_message = await bot.send_photo(
                    chat_id=target_chat_id,
                    photo=message.photo[-1].file_id,
                    caption=caption,
                    parse_mode='HTML',
                    reply_markup=reply_markup
                )
            elif message.video:
                sent_message = await bot.send_video(
                    chat_id=target_chat_id,
                    video=message.video.file_id,
                    caption=caption,
                    parse_mode='HTML',
                    reply_markup=reply_markup
                )
            elif message.document:
                sent_message = await bot.send_document(
                    chat_id=target_chat_id,
                    document=message.document.file_id,
                    caption=caption,
                    parse_mode='HTML',
                    reply_markup=reply_markup
                )
            elif message.audio:
                sent_message = await bot.send_audio(
                    chat_id=target_chat_id,
                    audio=message.audio.file_id,
                    caption=caption,
                    parse_mode='HTML',
                    reply_markup=reply_markup
                )
            elif message.voice:
                sent_message = await bot.send_voice(
                    chat_id=target_chat_id,
                    voice=message.voice.file_id,
                    caption=caption,
                    parse_mode='HTML',
                    reply_markup=reply_markup
                )
            elif message.sticker:
                sent_message = await bot.send_sticker(
                    chat_id=target_chat_id,
                    sticker=message.sticker.file_id,
                    reply_markup=reply_markup
                )
            elif message.location:
                sent_message = await bot.send_location(
                    chat_id=target_chat_id,
                    latitude=message.location.latitude,
                    longitude=message.location.longitude,
                    reply_markup=reply_markup
                )
            elif message.contact:
                sent_message = await bot.send_contact(
                    chat_id=target_chat_id,
                    phone_number=message.contact.phone_number,
                    first_name=message.contact.first_name,
                    last_name=message.contact.last_name,
                    reply_markup=reply_markup
                )
            else:
                # نوع رسالة غير مدعوم
                return None
            
            return sent_message
            
        except Exception as e:
            logger.log_error(e, {
                'task_id': task['id'],
                'target_chat_id': target_chat_id,
                'function': 'copy_message'
            })
            return None
    
    async def process_message_content(self, message: Message, settings: Dict[str, Any]) -> Dict[str, Any]:
        """معالجة محتوى الرسالة"""
        text_processing = settings.get('text_processing', {})
        
        # النص الأساسي
        original_text = message.text or message.caption or ""
        
        # تطبيق معالجة النصوص
        processed_text = TextProcessor.clean_text(original_text, text_processing)
        
        # إضافة رأس وتذييل
        processed_text = TextProcessor.add_header_footer(
            processed_text,
            text_processing.get('add_header'),
            text_processing.get('add_footer')
        )
        
        # تحديد طول النص
        char_limit = settings.get('advanced', {}).get('char_limit', 0)
        if char_limit > 0:
            processed_text = TextProcessor.limit_text_length(processed_text, char_limit)
        
        # معالجة الأزرار المخصصة
        custom_buttons = settings.get('advanced', {}).get('custom_buttons', [])
        reply_markup = None
        
        if custom_buttons:
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = []
            for button_row in custom_buttons:
                row = []
                for button in button_row:
                    row.append(InlineKeyboardButton(
                        text=button['text'],
                        url=button.get('url'),
                        callback_data=button.get('callback_data')
                    ))
                keyboard.append(row)
            reply_markup = InlineKeyboardMarkup(keyboard)
        
        return {
            'text': processed_text if message.text else None,
            'caption': processed_text if message.caption else None,
            'reply_markup': reply_markup
        }
    
    async def is_duplicate_message(self, message: Message, task_id: int) -> bool:
        """فحص تكرار الرسالة"""
        # إنشاء مفتاح فريد للرسالة
        message_key = f"{message.chat_id}_{message.message_id}"
        
        # فحص إذا كانت الرسالة مُعالجة مؤخراً
        if task_id in self.last_messages:
            if message_key in self.last_messages[task_id]:
                return True
        else:
            self.last_messages[task_id] = set()
        
        # إضافة الرسالة للقائمة
        self.last_messages[task_id].add(message_key)
        
        # تنظيف القائمة (الاحتفاظ بآخر 1000 رسالة)
        if len(self.last_messages[task_id]) > 1000:
            # إزالة أقدم 200 رسالة
            old_messages = list(self.last_messages[task_id])[:200]
            for old_msg in old_messages:
                self.last_messages[task_id].discard(old_msg)
        
        return False
    
    async def handle_forwarding_error(self, task: Dict[str, Any], target_chat_id: int, error_message: str):
        """معالجة أخطاء التوجيه"""
        # تسجيل الخطأ
        logger.logger.error(f"خطأ في توجيه المهمة {task['id']} للهدف {target_chat_id}: {error_message}")
        
        # إشعار المستخدم إذا كان الخطأ خطيراً
        if "محظور" in error_message or "صلاحيات" in error_message:
            # يمكن إضافة إشعار للمستخدم هنا
            pass
    
    async def log_forwarding_results(self, task: Dict[str, Any], message: Message, 
                                   successful_targets: List[Dict], failed_targets: List[Dict]):
        """تسجيل نتائج التوجيه"""
        # تسجيل في قاعدة البيانات
        target_message_ids = {
            target['chat_id']: target['message_id'] 
            for target in successful_targets
        }
        
        await self.db.log_forwarded_message(
            task['id'],
            message.message_id,
            target_message_ids
        )
        
        # تسجيل الإحصائيات
        logger.log_message_forward(
            task['id'],
            message.chat_id,
            [t['chat_id'] for t in successful_targets],
            message.message_id,
            len(failed_targets) == 0,
            f"نجح: {len(successful_targets)}, فشل: {len(failed_targets)}" if failed_targets else None
        )
    
    async def handle_message_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة تعديل الرسائل"""
        if not update.edited_message:
            return
        
        edited_message = update.edited_message
        chat_id = edited_message.chat_id
        
        # فحص إذا كانت الدردشة مصدر لأي مهمة
        if chat_id not in self.active_tasks:
            return
        
        task = self.active_tasks[chat_id]
        
        # البحث عن الرسالة الأصلية في قاعدة البيانات
        # وتحديث الرسائل المُوجهة
        # سيتم تطوير هذه الوظيفة في المرحلة التالية
    
    async def handle_message_delete(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة حذف الرسائل"""
        # سيتم تطوير هذه الوظيفة في المرحلة التالية
        pass
    
    async def reload_tasks(self):
        """إعادة تحميل المهام النشطة"""
        await self.load_active_tasks()
    
    async def stop_forwarding(self):
        """إيقاف خدمة التوجيه"""
        self.is_processing = False
        logger.logger.info("تم إيقاف خدمة توجيه الرسائل")
