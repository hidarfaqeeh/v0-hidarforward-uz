"""
خدمة جدولة الرسائل
Message Scheduling Service
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from telegram import Bot
from telegram.error import TelegramError
from database.db_manager import DatabaseManager
from utils.helpers import TimeHelper
from utils.logger import BotLogger

logger = BotLogger()

class MessageScheduler:
    """خدمة جدولة الرسائل المتقدمة"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.scheduled_tasks = {}
        self.is_running = False
        self.check_interval = 60  # فحص كل دقيقة
    
    async def start(self):
        """بدء خدمة الجدولة"""
        if not self.is_running:
            self.is_running = True
            asyncio.create_task(self.scheduler_loop())
            logger.logger.info("✅ تم بدء خدمة جدولة الرسائل")
    
    async def stop(self):
        """إيقاف خدمة الجدولة"""
        self.is_running = False
        logger.logger.info("⏹️ تم إيقاف خدمة جدولة الرسائل")
    
    async def scheduler_loop(self):
        """حلقة الجدولة الرئيسية"""
        while self.is_running:
            try:
                await self.process_scheduled_messages()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.log_error(e, {'function': 'scheduler_loop'})
                await asyncio.sleep(self.check_interval)
    
    async def process_scheduled_messages(self):
        """معالجة الرسائل المجدولة"""
        try:
            # الحصول على الرسائل المستحقة
            pending_messages = await self.db.get_pending_scheduled_messages()
            
            for message_data in pending_messages:
                await self.send_scheduled_message(message_data)
                
        except Exception as e:
            logger.log_error(e, {'function': 'process_scheduled_messages'})
    
    async def send_scheduled_message(self, message_data: Dict[str, Any]):
        """إرسال رسالة مجدولة"""
        try:
            message_id = message_data['id']
            user_id = message_data['user_id']
            message_text = message_data['message_text']
            target_type = message_data['target_type']
            target_ids = message_data['target_ids']
            interval_minutes = message_data.get('interval_minutes')
            
            # الحصول على بوت المستخدم
            user_bot_token = await self.get_user_bot_token(user_id)
            if not user_bot_token:
                await self.mark_message_failed(message_id, "لا يوجد توكن بوت")
                return
            
            bot = Bot(token=user_bot_token)
            
            # إرسال للأهداف
            sent_count = 0
            failed_count = 0
            
            for target_id in target_ids:
                try:
                    await bot.send_message(
                        chat_id=target_id,
                        text=message_text,
                        parse_mode='HTML'
                    )
                    sent_count += 1
                    await asyncio.sleep(0.1)  # تأخير صغير
                    
                except TelegramError as e:
                    failed_count += 1
                    logger.log_error(e, {
                        'function': 'send_scheduled_message',
                        'target_id': target_id,
                        'message_id': message_id
                    })
            
            # تسجيل النتائج
            await self.log_scheduled_message_result(
                message_id, sent_count, failed_count
            )
            
            # جدولة الرسالة التالية إذا كانت متكررة
            if interval_minutes and interval_minutes > 0:
                next_time = datetime.now() + timedelta(minutes=interval_minutes)
                await self.db.update_scheduled_message_time(message_id, next_time)
            else:
                # إلغاء تفعيل الرسالة غير المتكررة
                await self.db.deactivate_scheduled_message(message_id)
            
            logger.logger.info(
                f"تم إرسال رسالة مجدولة {message_id}: "
                f"نجح {sent_count}, فشل {failed_count}"
            )
            
        except Exception as e:
            await self.mark_message_failed(message_data['id'], str(e))
            logger.log_error(e, {
                'function': 'send_scheduled_message',
                'message_id': message_data['id']
            })
    
    async def schedule_message(self, user_id: int, message_text: str,
                             target_type: str, target_ids: List[int],
                             schedule_time: datetime, 
                             interval_minutes: Optional[int] = None) -> int:
        """جدولة رسالة جديدة"""
        try:
            message_id = await self.db.add_scheduled_message(
                user_id=user_id,
                message_text=message_text,
                target_type=target_type,
                target_ids=target_ids,
                schedule_time=schedule_time,
                interval_minutes=interval_minutes
            )
            
            logger.logger.info(
                f"تم جدولة رسالة جديدة {message_id} للمستخدم {user_id}"
            )
            
            return message_id
            
        except Exception as e:
            logger.log_error(e, {
                'function': 'schedule_message',
                'user_id': user_id
            })
            raise
    
    async def cancel_scheduled_message(self, message_id: int, user_id: int) -> bool:
        """إلغاء رسالة مجدولة"""
        try:
            success = await self.db.cancel_scheduled_message(message_id, user_id)
            
            if success:
                logger.logger.info(
                    f"تم إلغاء الرسالة المجدولة {message_id} للمستخدم {user_id}"
                )
            
            return success
            
        except Exception as e:
            logger.log_error(e, {
                'function': 'cancel_scheduled_message',
                'message_id': message_id,
                'user_id': user_id
            })
            return False
    
    async def get_user_scheduled_messages(self, user_id: int) -> List[Dict[str, Any]]:
        """الحصول على رسائل المستخدم المجدولة"""
        return await self.db.get_user_scheduled_messages(user_id)
    
    async def get_user_bot_token(self, user_id: int) -> Optional[str]:
        """الحصول على توكن بوت المستخدم"""
        # البحث في مهام المستخدم عن توكن البوت
        user_tasks = await self.db.get_user_tasks(user_id)
        
        for task in user_tasks:
            settings = task.get('settings', {})
            bot_token = settings.get('bot_token')
            if bot_token:
                return bot_token
        
        return None
    
    async def mark_message_failed(self, message_id: int, error_reason: str):
        """تمييز الرسالة كفاشلة"""
        await self.db.mark_scheduled_message_failed(message_id, error_reason)
    
    async def log_scheduled_message_result(self, message_id: int, 
                                         sent_count: int, failed_count: int):
        """تسجيل نتيجة الرسالة المجدولة"""
        await self.db.log_scheduled_message_result(
            message_id, sent_count, failed_count
        )

class ScheduleParser:
    """محلل جداول الوقت"""
    
    @staticmethod
    def parse_schedule_expression(expression: str) -> Optional[datetime]:
        """تحليل تعبير الجدولة"""
        expression = expression.strip().lower()
        now = datetime.now()
        
        # أمثلة على التعبيرات المدعومة:
        # "في 15:30"
        # "غداً في 10:00"
        # "بعد 30 دقيقة"
        # "كل يوم في 09:00"
        # "كل أسبوع يوم الأحد في 12:00"
        
        if expression.startswith('في '):
            # "في 15:30"
            time_part = expression[3:].strip()
            return ScheduleParser.parse_time_today(time_part)
        
        elif expression.startswith('غداً في '):
            # "غداً في 10:00"
            time_part = expression[8:].strip()
            tomorrow = now + timedelta(days=1)
            time_obj = ScheduleParser.parse_time_string(time_part)
            if time_obj:
                return datetime.combine(tomorrow.date(), time_obj)
        
        elif expression.startswith('بعد '):
            # "بعد 30 دقيقة"
            return ScheduleParser.parse_relative_time(expression[4:].strip())
        
        elif expression.startswith('كل '):
            # "كل يوم في 09:00" - للرسائل المتكررة
            return ScheduleParser.parse_recurring_schedule(expression[3:].strip())
        
        else:
            # محاولة تحليل مباشر
            return TimeHelper.parse_schedule_time(expression)
        
        return None
    
    @staticmethod
    def parse_time_today(time_str: str) -> Optional[datetime]:
        """تحليل وقت اليوم"""
        time_obj = ScheduleParser.parse_time_string(time_str)
        if time_obj:
            today = datetime.now().date()
            scheduled_time = datetime.combine(today, time_obj)
            
            # إذا كان الوقت قد مضى اليوم، اجعله غداً
            if scheduled_time < datetime.now():
                scheduled_time += timedelta(days=1)
            
            return scheduled_time
        return None
    
    @staticmethod
    def parse_time_string(time_str: str) -> Optional[datetime.time]:
        """تحليل نص الوقت"""
        try:
            # تنسيقات مختلفة للوقت
            formats = ['%H:%M', '%H.%M', '%I:%M %p', '%I.%M %p']
            
            for fmt in formats:
                try:
                    time_obj = datetime.strptime(time_str, fmt).time()
                    return time_obj
                except ValueError:
                    continue
            
            return None
        except Exception:
            return None
    
    @staticmethod
    def parse_relative_time(relative_str: str) -> Optional[datetime]:
        """تحليل الوقت النسبي"""
        now = datetime.now()
        
        if 'دقيقة' in relative_str or 'دقائق' in relative_str:
            minutes = ScheduleParser.extract_number(relative_str)
            if minutes:
                return now + timedelta(minutes=minutes)
        
        elif 'ساعة' in relative_str or 'ساعات' in relative_str:
            hours = ScheduleParser.extract_number(relative_str)
            if hours:
                return now + timedelta(hours=hours)
        
        elif 'يوم' in relative_str or 'أيام' in relative_str:
            days = ScheduleParser.extract_number(relative_str)
            if days:
                return now + timedelta(days=days)
        
        return None
    
    @staticmethod
    def parse_recurring_schedule(schedule_str: str) -> Optional[datetime]:
        """تحليل الجدولة المتكررة"""
        now = datetime.now()
        
        if schedule_str.startswith('يوم في '):
            # "يوم في 09:00"
            time_part = schedule_str[7:].strip()
            time_obj = ScheduleParser.parse_time_string(time_part)
            if time_obj:
                today = now.date()
                scheduled_time = datetime.combine(today, time_obj)
                
                if scheduled_time < now:
                    scheduled_time += timedelta(days=1)
                
                return scheduled_time
        
        elif 'أسبوع' in schedule_str:
            # "أسبوع يوم الأحد في 12:00"
            # تطبيق مبسط - سيتم تطويره
            return now + timedelta(days=7)
        
        return None
    
    @staticmethod
    def extract_number(text: str) -> Optional[int]:
        """استخراج رقم من النص"""
        import re
        numbers = re.findall(r'\d+', text)
        return int(numbers[0]) if numbers else None

class BulkScheduler:
    """جدولة الرسائل المجمعة"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    async def schedule_bulk_messages(self, user_id: int, 
                                   messages: List[Dict[str, Any]],
                                   schedule_config: Dict[str, Any]) -> List[int]:
        """جدولة رسائل متعددة"""
        scheduled_ids = []
        
        base_time = schedule_config.get('start_time', datetime.now())
        interval_minutes = schedule_config.get('interval_minutes', 5)
        
        for i, message_data in enumerate(messages):
            # حساب وقت كل رسالة
            message_time = base_time + timedelta(minutes=i * interval_minutes)
            
            message_id = await self.db.add_scheduled_message(
                user_id=user_id,
                message_text=message_data['text'],
                target_type=message_data['target_type'],
                target_ids=message_data['target_ids'],
                schedule_time=message_time,
                interval_minutes=message_data.get('repeat_interval')
            )
            
            scheduled_ids.append(message_id)
        
        return scheduled_ids
    
    async def schedule_campaign(self, user_id: int, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """جدولة حملة رسائل"""
        campaign_name = campaign_data['name']
        messages = campaign_data['messages']
        targets = campaign_data['targets']
        schedule = campaign_data['schedule']
        
        # إنشاء الحملة
        campaign_id = await self.db.create_message_campaign(
            user_id=user_id,
            name=campaign_name,
            description=campaign_data.get('description', ''),
            schedule_config=schedule
        )
        
        # جدولة الرسائل
        scheduled_ids = []
        
        for message in messages:
            for target_group in targets:
                message_id = await self.db.add_scheduled_message(
                    user_id=user_id,
                    message_text=message['text'],
                    target_type='group',
                    target_ids=target_group['ids'],
                    schedule_time=message['schedule_time'],
                    campaign_id=campaign_id
                )
                scheduled_ids.append(message_id)
        
        return {
            'campaign_id': campaign_id,
            'scheduled_messages': len(scheduled_ids),
            'total_targets': sum(len(group['ids']) for group in targets)
        }
