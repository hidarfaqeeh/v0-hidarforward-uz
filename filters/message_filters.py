"""
مدير فلاتر الرسائل
Message Filters Manager
"""

import re
import json
from typing import Dict, List, Any, Optional
from telegram import Message
from utils.logger import BotLogger

logger = BotLogger()

class MessageFilterManager:
    """مدير فلاتر الرسائل المتقدم"""
    
    def __init__(self):
        self.filter_cache = {}
    
    async def check_message(self, message: Message, filters: Dict[str, Any]) -> bool:
        """فحص الرسالة ضد جميع الفلاتر"""
        if not filters:
            return True
        
        try:
            # فلتر أنواع الوسائط
            if not self.check_media_filter(message, filters.get('media', {})):
                return False
            
            # فلتر النصوص
            if not self.check_text_filter(message, filters.get('text', {})):
                return False
            
            # فلتر المستخدمين
            if not self.check_user_filter(message, filters.get('users', {})):
                return False
            
            # فلتر الروابط
            if not self.check_links_filter(message, filters.get('links', {})):
                return False
            
            # فلتر اللغة
            if not self.check_language_filter(message, filters.get('language', {})):
                return False
            
            # فلتر المشرفين
            if not await self.check_admin_filter(message, filters.get('admins', {})):
                return False
            
            # فلتر الرسائل المُعاد توجيهها
            if not self.check_forwarded_filter(message, filters.get('forwarded', {})):
                return False
            
            return True
            
        except Exception as e:
            logger.log_error(e, {
                'function': 'check_message',
                'message_id': message.message_id,
                'chat_id': message.chat_id
            })
            return True  # في حالة الخطأ، السماح بمرور الرسالة
    
    def check_media_filter(self, message: Message, media_filter: Dict[str, Any]) -> bool:
        """فلتر أنواع الوسائط"""
        if not media_filter.get('enabled', False):
            return True
        
        allowed_types = media_filter.get('allowed_types', [])
        if not allowed_types:
            return True
        
        # تحديد نوع الرسالة
        message_type = self.get_message_type(message)
        
        # فحص إذا كان النوع مسموح
        return message_type in allowed_types
    
    def get_message_type(self, message: Message) -> str:
        """تحديد نوع الرسالة"""
        if message.text:
            return 'text'
        elif message.photo:
            return 'photo'
        elif message.video:
            return 'video'
        elif message.audio:
            return 'audio'
        elif message.voice:
            return 'voice'
        elif message.document:
            return 'document'
        elif message.sticker:
            return 'sticker'
        elif message.animation:
            return 'animation'
        elif message.location:
            return 'location'
        elif message.contact:
            return 'contact'
        elif message.poll:
            return 'poll'
        elif message.game:
            return 'game'
        else:
            return 'other'
    
    def check_text_filter(self, message: Message, text_filter: Dict[str, Any]) -> bool:
        """فلتر النصوص"""
        if not text_filter.get('enabled', False):
            return True
        
        text_content = message.text or message.caption or ""
        if not text_content:
            return True
        
        # فلتر الكلمات المحظورة
        banned_words = text_filter.get('banned_words', [])
        if banned_words:
            text_lower = text_content.lower()
            for word in banned_words:
                if word.lower() in text_lower:
                    return False
        
        # فلتر الكلمات المطلوبة
        required_words = text_filter.get('required_words', [])
        if required_words:
            text_lower = text_content.lower()
            for word in required_words:
                if word.lower() not in text_lower:
                    return False
        
        # فلتر طول النص
        min_length = text_filter.get('min_length', 0)
        max_length = text_filter.get('max_length', 0)
        
        if min_length > 0 and len(text_content) < min_length:
            return False
        
        if max_length > 0 and len(text_content) > max_length:
            return False
        
        # فلتر التعبيرات النمطية
        regex_patterns = text_filter.get('regex_patterns', [])
        for pattern in regex_patterns:
            try:
                if re.search(pattern, text_content):
                    return False
            except re.error:
                continue
        
        return True
    
    def check_user_filter(self, message: Message, user_filter: Dict[str, Any]) -> bool:
        """فلتر المستخدمين"""
        if not user_filter.get('enabled', False):
            return True
        
        user_id = message.from_user.id if message.from_user else None
        username = message.from_user.username if message.from_user else None
        
        # القائمة البيضاء
        whitelist = user_filter.get('whitelist', [])
        if whitelist:
            user_in_whitelist = (
                user_id in whitelist or
                username in whitelist or
                f"@{username}" in whitelist if username else False
            )
            if not user_in_whitelist:
                return False
        
        # القائمة السوداء
        blacklist = user_filter.get('blacklist', [])
        if blacklist:
            user_in_blacklist = (
                user_id in blacklist or
                username in blacklist or
                f"@{username}" in blacklist if username else False
            )
            if user_in_blacklist:
                return False
        
        return True
    
    def check_links_filter(self, message: Message, links_filter: Dict[str, Any]) -> bool:
        """فلتر الروابط"""
        if not links_filter.get('enabled', False):
            return True
        
        text_content = message.text or message.caption or ""
        if not text_content:
            return True
        
        # البحث عن الروابط
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\$$\$$,]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        urls = re.findall(url_pattern, text_content)
        
        # فلتر حظر الروابط
        if links_filter.get('block_all_links', False) and urls:
            return False
        
        # فلتر الدومينات المحظورة
        banned_domains = links_filter.get('banned_domains', [])
        if banned_domains and urls:
            for url in urls:
                for domain in banned_domains:
                    if domain in url:
                        return False
        
        # فلتر الدومينات المسموحة
        allowed_domains = links_filter.get('allowed_domains', [])
        if allowed_domains and urls:
            for url in urls:
                domain_allowed = False
                for domain in allowed_domains:
                    if domain in url:
                        domain_allowed = True
                        break
                if not domain_allowed:
                    return False
        
        return True
    
    def check_language_filter(self, message: Message, language_filter: Dict[str, Any]) -> bool:
        """فلتر اللغة"""
        if not language_filter.get('enabled', False):
            return True
        
        text_content = message.text or message.caption or ""
        if not text_content:
            return True
        
        # فحص اللغة المطلوبة (تطبيق بسيط)
        required_language = language_filter.get('required_language')
        if required_language:
            if required_language == 'arabic':
                # فحص وجود أحرف عربية
                arabic_pattern = r'[\u0600-\u06FF]'
                if not re.search(arabic_pattern, text_content):
                    return False
            elif required_language == 'english':
                # فحص وجود أحرف إنجليزية
                english_pattern = r'[a-zA-Z]'
                if not re.search(english_pattern, text_content):
                    return False
        
        return True
    
    async def check_admin_filter(self, message: Message, admin_filter: Dict[str, Any]) -> bool:
        """فلتر المشرفين"""
        if not admin_filter.get('enabled', False):
            return True
        
        # فحص إذا كان المرسل مشرف (يتطلب API call)
        # سيتم تطوير هذه الوظيفة في المرحلة التالية
        return True
    
    def check_forwarded_filter(self, message: Message, forwarded_filter: Dict[str, Any]) -> bool:
        """فلتر الرسائل المُعاد توجيهها"""
        if not forwarded_filter.get('enabled', False):
            return True
        
        # فحص إذا كانت الرسالة مُعاد توجيهها
        is_forwarded = message.forward_from or message.forward_from_chat
        
        # حظر الرسائل المُعاد توجيهها
        if forwarded_filter.get('block_forwarded', False) and is_forwarded:
            return False
        
        # السماح فقط بالرسائل المُعاد توجيهها
        if forwarded_filter.get('only_forwarded', False) and not is_forwarded:
            return False
        
        return True
    
    def check_duplicate_filter(self, message: Message, duplicate_filter: Dict[str, Any], 
                             recent_messages: List[str]) -> bool:
        """فلتر التكرار"""
        if not duplicate_filter.get('enabled', False):
            return True
        
        text_content = message.text or message.caption or ""
        if not text_content:
            return True
        
        # فحص التكرار الدقيق
        if duplicate_filter.get('exact_match', True):
            return text_content not in recent_messages
        
        # فحص التشابه (تطبيق بسيط)
        similarity_threshold = duplicate_filter.get('similarity_threshold', 0.8)
        for recent_msg in recent_messages:
            similarity = self.calculate_text_similarity(text_content, recent_msg)
            if similarity >= similarity_threshold:
                return False
        
        return True
    
    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """حساب التشابه بين النصوص"""
        # تطبيق بسيط لحساب التشابه
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 and not words2:
            return 1.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0

class MediaFilter:
    """فلتر الوسائط المتخصص"""
    
    SUPPORTED_MEDIA_TYPES = [
        'text', 'photo', 'video', 'audio', 'voice', 
        'document', 'sticker', 'animation', 'location', 
        'contact', 'poll', 'game'
    ]
    
    @staticmethod
    def get_media_info(message: Message) -> Dict[str, Any]:
        """الحصول على معلومات الوسائط"""
        info = {
            'type': 'text',
            'size': 0,
            'duration': 0,
            'dimensions': None
        }
        
        if message.photo:
            info['type'] = 'photo'
            info['size'] = message.photo[-1].file_size or 0
            info['dimensions'] = (message.photo[-1].width, message.photo[-1].height)
        elif message.video:
            info['type'] = 'video'
            info['size'] = message.video.file_size or 0
            info['duration'] = message.video.duration or 0
            info['dimensions'] = (message.video.width, message.video.height)
        elif message.audio:
            info['type'] = 'audio'
            info['size'] = message.audio.file_size or 0
            info['duration'] = message.audio.duration or 0
        elif message.voice:
            info['type'] = 'voice'
            info['size'] = message.voice.file_size or 0
            info['duration'] = message.voice.duration or 0
        elif message.document:
            info['type'] = 'document'
            info['size'] = message.document.file_size or 0
        
        return info
    
    @staticmethod
    def check_file_size_limit(message: Message, max_size_mb: int) -> bool:
        """فحص حد حجم الملف"""
        if max_size_mb <= 0:
            return True
        
        media_info = MediaFilter.get_media_info(message)
        max_size_bytes = max_size_mb * 1024 * 1024
        
        return media_info['size'] <= max_size_bytes
    
    @staticmethod
    def check_duration_limit(message: Message, max_duration_seconds: int) -> bool:
        """فحص حد مدة الوسائط"""
        if max_duration_seconds <= 0:
            return True
        
        media_info = MediaFilter.get_media_info(message)
        return media_info['duration'] <= max_duration_seconds
