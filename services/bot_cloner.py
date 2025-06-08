"""
خدمة نسخ البوت
Bot Cloning Service
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from telegram import Bot
from telegram.error import TelegramError
from database.db_manager import DatabaseManager
from utils.decorators import premium_required
from utils.logger import BotLogger

logger = BotLogger()

class BotCloner:
    """خدمة نسخ البوت المتقدمة"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.active_clones = {}  # البوتات النشطة
        self.clone_handlers = {}  # معالجات النسخ
    
    async def create_bot_clone(self, owner_id: int, bot_token: str, 
                             clone_config: Dict[str, Any]) -> Dict[str, Any]:
        """إنشاء نسخة من البوت"""
        try:
            # التحقق من صحة التوكن
            bot = Bot(token=bot_token)
            bot_info = await bot.get_me()
            
            # حفظ النسخة في قاعدة البيانات
            clone_id = await self.db.add_bot_clone(
                owner_id=owner_id,
                bot_token=bot_token,
                bot_username=bot_info.username
            )
            
            # إعداد النسخة
            clone_data = {
                'id': clone_id,
                'owner_id': owner_id,
                'bot_token': bot_token,
                'bot_username': bot_info.username,
                'bot_info': {
                    'id': bot_info.id,
                    'first_name': bot_info.first_name,
                    'username': bot_info.username,
                    'can_join_groups': bot_info.can_join_groups,
                    'can_read_all_group_messages': bot_info.can_read_all_group_messages,
                    'supports_inline_queries': bot_info.supports_inline_queries
                },
                'config': clone_config,
                'status': 'active',
                'created_at': datetime.now().isoformat()
            }
            
            # بدء تشغيل النسخة
            await self.start_bot_clone(clone_data)
            
            logger.logger.info(f"تم إنشاء نسخة بوت جديدة {clone_id} للمستخدم {owner_id}")
            
            return {
                'clone_id': clone_id,
                'bot_username': bot_info.username,
                'bot_id': bot_info.id,
                'status': 'active'
            }
            
        except TelegramError as e:
            logger.log_error(e, {
                'function': 'create_bot_clone',
                'owner_id': owner_id,
                'error': 'invalid_token'
            })
            raise ValueError("توكن البوت غير صحيح")
        
        except Exception as e:
            logger.log_error(e, {
                'function': 'create_bot_clone',
                'owner_id': owner_id
            })
            raise
    
    async def start_bot_clone(self, clone_data: Dict[str, Any]):
        """بدء تشغيل نسخة البوت"""
        clone_id = clone_data['id']
        bot_token = clone_data['bot_token']
        
        try:
            # إنشاء معالج للنسخة
            clone_handler = BotCloneHandler(clone_data, self.db)
            
            # حفظ المعالج
            self.clone_handlers[clone_id] = clone_handler
            
            # بدء تشغيل النسخة
            await clone_handler.start()
            
            # إضافة للقائمة النشطة
            self.active_clones[clone_id] = {
                'clone_data': clone_data,
                'handler': clone_handler,
                'status': 'running'
            }
            
            logger.logger.info(f"تم بدء تشغيل نسخة البوت {clone_id}")
            
        except Exception as e:
            logger.log_error(e, {
                'function': 'start_bot_clone',
                'clone_id': clone_id
            })
            raise
    
    async def stop_bot_clone(self, clone_id: int, owner_id: int) -> bool:
        """إيقاف نسخة البوت"""
        try:
            # التحقق من الملكية
            clone_data = await self.db.get_bot_clone(clone_id)
            if not clone_data or clone_data['owner_id'] != owner_id:
                return False
            
            # إيقاف المعالج
            if clone_id in self.clone_handlers:
                await self.clone_handlers[clone_id].stop()
                del self.clone_handlers[clone_id]
            
            # إزالة من القائمة النشطة
            if clone_id in self.active_clones:
                del self.active_clones[clone_id]
            
            # تحديث الحالة في قاعدة البيانات
            await self.db.update_bot_clone_status(clone_id, 'stopped')
            
            logger.logger.info(f"تم إيقاف نسخة البوت {clone_id}")
            return True
            
        except Exception as e:
            logger.log_error(e, {
                'function': 'stop_bot_clone',
                'clone_id': clone_id,
                'owner_id': owner_id
            })
            return False
    
    async def delete_bot_clone(self, clone_id: int, owner_id: int) -> bool:
        """حذف نسخة البوت"""
        try:
            # إيقاف النسخة أولاً
            await self.stop_bot_clone(clone_id, owner_id)
            
            # حذف من قاعدة البيانات
            success = await self.db.delete_bot_clone(clone_id, owner_id)
            
            if success:
                logger.logger.info(f"تم حذف نسخة البوت {clone_id}")
            
            return success
            
        except Exception as e:
            logger.log_error(e, {
                'function': 'delete_bot_clone',
                'clone_id': clone_id,
                'owner_id': owner_id
            })
            return False
    
    async def get_user_bot_clones(self, user_id: int) -> List[Dict[str, Any]]:
        """الحصول على نسخ البوت للمستخدم"""
        clones = await self.db.get_user_bot_clones(user_id)
        
        # إضافة معلومات الحالة
        for clone in clones:
            clone_id = clone['id']
            if clone_id in self.active_clones:
                clone['runtime_status'] = 'running'
                clone['runtime_info'] = await self.get_clone_runtime_info(clone_id)
            else:
                clone['runtime_status'] = 'stopped'
                clone['runtime_info'] = None
        
        return clones
    
    async def get_clone_runtime_info(self, clone_id: int) -> Dict[str, Any]:
        """الحصول على معلومات تشغيل النسخة"""
        if clone_id not in self.active_clones:
            return {}
        
        handler = self.active_clones[clone_id]['handler']
        return await handler.get_runtime_stats()
    
    async def update_clone_config(self, clone_id: int, owner_id: int, 
                                new_config: Dict[str, Any]) -> bool:
        """تحديث إعدادات النسخة"""
        try:
            # التحقق من الملكية
            clone_data = await self.db.get_bot_clone(clone_id)
            if not clone_data or clone_data['owner_id'] != owner_id:
                return False
            
            # تحديث الإعدادات
            await self.db.update_bot_clone_config(clone_id, new_config)
            
            # إعادة تشغيل النسخة إذا كانت نشطة
            if clone_id in self.active_clones:
                await self.stop_bot_clone(clone_id, owner_id)
                
                # تحديث البيانات
                clone_data['config'] = new_config
                await self.start_bot_clone(clone_data)
            
            logger.logger.info(f"تم تحديث إعدادات نسخة البوت {clone_id}")
            return True
            
        except Exception as e:
            logger.log_error(e, {
                'function': 'update_clone_config',
                'clone_id': clone_id,
                'owner_id': owner_id
            })
            return False
    
    async def restart_all_clones(self):
        """إعادة تشغيل جميع النسخ"""
        logger.logger.info("بدء إعادة تشغيل جميع نسخ البوت...")
        
        # الحصول على جميع النسخ النشطة
        active_clones = await self.db.get_active_bot_clones()
        
        for clone_data in active_clones:
            try:
                await self.start_bot_clone(clone_data)
            except Exception as e:
                logger.log_error(e, {
                    'function': 'restart_all_clones',
                    'clone_id': clone_data['id']
                })
        
        logger.logger.info(f"تم إعادة تشغيل {len(active_clones)} نسخة بوت")

class BotCloneHandler:
    """معالج نسخة البوت الفردية"""
    
    def __init__(self, clone_data: Dict[str, Any], db: DatabaseManager):
        self.clone_data = clone_data
        self.db = db
        self.bot = Bot(token=clone_data['bot_token'])
        self.is_running = False
        self.stats = {
            'messages_processed': 0,
            'messages_sent': 0,
            'errors': 0,
            'start_time': None
        }
    
    async def start(self):
        """بدء تشغيل النسخة"""
        if self.is_running:
            return
        
        self.is_running = True
        self.stats['start_time'] = datetime.now()
        
        # بدء معالجة الرسائل
        asyncio.create_task(self.message_processor())
        
        logger.logger.info(f"تم بدء نسخة البوت {self.clone_data['id']}")
    
    async def stop(self):
        """إيقاف النسخة"""
        self.is_running = False
        logger.logger.info(f"تم إيقاف نسخة البوت {self.clone_data['id']}")
    
    async def message_processor(self):
        """معالج الرسائل للنسخة"""
        while self.is_running:
            try:
                # الحصول على المهام المخصصة لهذه النسخة
                clone_tasks = await self.get_clone_tasks()
                
                for task in clone_tasks:
                    if not self.is_running:
                        break
                    
                    await self.process_task(task)
                
                await asyncio.sleep(1)  # تأخير قصير
                
            except Exception as e:
                self.stats['errors'] += 1
                logger.log_error(e, {
                    'function': 'message_processor',
                    'clone_id': self.clone_data['id']
                })
                await asyncio.sleep(5)  # تأخير أطول عند الخطأ
    
    async def get_clone_tasks(self) -> List[Dict[str, Any]]:
        """الحصول على مهام النسخة"""
        # البحث عن المهام التي تستخدم توكن هذا البوت
        owner_id = self.clone_data['owner_id']
        bot_token = self.clone_data['bot_token']
        
        user_tasks = await self.db.get_user_tasks(owner_id)
        
        clone_tasks = []
        for task in user_tasks:
            task_settings = task.get('settings', {})
            if task_settings.get('bot_token') == bot_token and task['is_active']:
                clone_tasks.append(task)
        
        return clone_tasks
    
    async def process_task(self, task: Dict[str, Any]):
        """معالجة مهمة محددة"""
        try:
            # هذه الوظيفة ستتكامل مع MessageForwarder
            # لمعالجة الرسائل باستخدام نسخة البوت
            
            self.stats['messages_processed'] += 1
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.log_error(e, {
                'function': 'process_task',
                'clone_id': self.clone_data['id'],
                'task_id': task['id']
            })
    
    async def send_message(self, chat_id: int, text: str, **kwargs) -> bool:
        """إرسال رسالة باستخدام النسخة"""
        try:
            await self.bot.send_message(chat_id=chat_id, text=text, **kwargs)
            self.stats['messages_sent'] += 1
            return True
            
        except TelegramError as e:
            self.stats['errors'] += 1
            logger.log_error(e, {
                'function': 'send_message',
                'clone_id': self.clone_data['id'],
                'chat_id': chat_id
            })
            return False
    
    async def get_runtime_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات التشغيل"""
        uptime = None
        if self.stats['start_time']:
            uptime = (datetime.now() - self.stats['start_time']).total_seconds()
        
        return {
            'is_running': self.is_running,
            'uptime_seconds': uptime,
            'messages_processed': self.stats['messages_processed'],
            'messages_sent': self.stats['messages_sent'],
            'errors': self.stats['errors'],
            'success_rate': (
                self.stats['messages_sent'] / max(self.stats['messages_processed'], 1) * 100
            )
        }

class CloneTemplates:
    """قوالب نسخ البوت المُعدة مسبقاً"""
    
    @staticmethod
    def get_basic_forwarder() -> Dict[str, Any]:
        """قالب موجه أساسي"""
        return {
            'name': 'موجه أساسي',
            'description': 'بوت بسيط لتوجيه الرسائل',
            'features': {
                'message_forwarding': True,
                'text_processing': False,
                'filters': False,
                'scheduling': False
            },
            'settings': {
                'forward_type': 'forward',
                'delay_seconds': 0,
                'max_messages_per_minute': 20
            }
        }
    
    @staticmethod
    def get_advanced_forwarder() -> Dict[str, Any]:
        """قالب موجه متقدم"""
        return {
            'name': 'موجه متقدم',
            'description': 'بوت متقدم مع فلاتر ومعالجة نصوص',
            'features': {
                'message_forwarding': True,
                'text_processing': True,
                'filters': True,
                'scheduling': False
            },
            'settings': {
                'forward_type': 'copy',
                'delay_seconds': 2,
                'max_messages_per_minute': 15,
                'text_processing': {
                    'remove_links': True,
                    'add_footer': 'تم النشر بواسطة البوت'
                }
            }
        }
    
    @staticmethod
    def get_news_bot() -> Dict[str, Any]:
        """قالب بوت الأخبار"""
        return {
            'name': 'بوت الأخبار',
            'description': 'بوت متخصص في نشر الأخبار',
            'features': {
                'message_forwarding': True,
                'text_processing': True,
                'filters': True,
                'scheduling': True
            },
            'settings': {
                'forward_type': 'copy',
                'delay_seconds': 5,
                'filters': {
                    'text_content': {
                        'enabled': True,
                        'required_words': ['news', 'breaking', 'أخبار', 'عاجل'],
                        'min_length': 50
                    }
                },
                'text_processing': {
                    'add_header': '📰 أخبار عاجلة',
                    'add_footer': '📱 تابعونا للمزيد'
                }
            }
        }
    
    @staticmethod
    def get_media_bot() -> Dict[str, Any]:
        """قالب بوت الوسائط"""
        return {
            'name': 'بوت الوسائط',
            'description': 'بوت متخصص في نشر الصور والفيديوهات',
            'features': {
                'message_forwarding': True,
                'text_processing': False,
                'filters': True,
                'scheduling': False
            },
            'settings': {
                'forward_type': 'forward',
                'delay_seconds': 1,
                'filters': {
                    'media_type': {
                        'enabled': True,
                        'allowed_types': ['photo', 'video'],
                        'max_file_size_mb': 50
                    }
                }
            }
        }
