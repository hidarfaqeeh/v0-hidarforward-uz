"""
مدير الفلاتر المتقدم
Advanced Filter Manager
"""

import re
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from telegram import Message, User, Chat
from database.db_manager import DatabaseManager
from utils.helpers import TextProcessor
from utils.logger import BotLogger

logger = BotLogger()

class AdvancedFilterManager:
    """مدير الفلاتر المتقدم"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.filter_cache = {}
        self.user_message_history = {}  # تتبع تاريخ رسائل المستخدمين
        self.spam_detection = SpamDetector()
        self.content_analyzer = ContentAnalyzer()
    
    async def apply_filters(self, message: Message, task_filters: Dict[str, Any]) -> Tuple[bool, str]:
        """تطبيق جميع الفلاتر على الرسالة"""
        try:
            # فلتر الحظر العام
            if await self.check_global_ban(message):
                return False, "المستخدم محظور عالمياً"
            
            # فلتر السبام
            if await self.spam_detection.is_spam(message, self.user_message_history):
                return False, "رسالة سبام"
            
            # فلتر المحتوى المحظور
            if await self.content_analyzer.has_forbidden_content(message):
                return False, "محتوى محظور"
            
            # فلاتر المهمة المخصصة
            for filter_name, filter_config in task_filters.items():
                if not filter_config.get('enabled', False):
                    continue
                
                result, reason = await self.apply_single_filter(message, filter_name, filter_config)
                if not result:
                    return False, f"فلتر {filter_name}: {reason}"
            
            # تحديث تاريخ الرسائل
            await self.update_message_history(message)
            
            return True, "تم قبول الرسالة"
            
        except Exception as e:
            logger.log_error(e, {
                'function': 'apply_filters',
                'message_id': message.message_id,
                'chat_id': message.chat_id
            })
            return True, "خطأ في الفلتر - تم قبول الرسالة"
    
    async def apply_single_filter(self, message: Message, filter_name: str, 
                                 filter_config: Dict[str, Any]) -> Tuple[bool, str]:
        """تطبيق فلتر واحد"""
        
        if filter_name == 'media_type':
            return await self.filter_media_type(message, filter_config)
        elif filter_name == 'text_content':
            return await self.filter_text_content(message, filter_config)
        elif filter_name == 'user_restrictions':
            return await self.filter_user_restrictions(message, filter_config)
        elif filter_name == 'time_based':
            return await self.filter_time_based(message, filter_config)
        elif filter_name == 'size_limits':
            return await self.filter_size_limits(message, filter_config)
        elif filter_name == 'language_detection':
            return await self.filter_language(message, filter_config)
        elif filter_name == 'sentiment_analysis':
            return await self.filter_sentiment(message, filter_config)
        elif filter_name == 'duplicate_detection':
            return await self.filter_duplicates(message, filter_config)
        elif filter_name == 'link_analysis':
            return await self.filter_links(message, filter_config)
        elif filter_name == 'forwarded_restrictions':
            return await self.filter_forwarded(message, filter_config)
        else:
            return True, "فلتر غير معروف"
    
    async def filter_media_type(self, message: Message, config: Dict[str, Any]) -> Tuple[bool, str]:
        """فلتر نوع الوسائط"""
        allowed_types = config.get('allowed_types', [])
        blocked_types = config.get('blocked_types', [])
        
        message_type = self.get_message_type(message)
        
        # فحص الأنواع المحظورة
        if blocked_types and message_type in blocked_types:
            return False, f"نوع الوسائط محظور: {message_type}"
        
        # فحص الأنواع المسموحة
        if allowed_types and message_type not in allowed_types:
            return False, f"نوع الوسائط غير مسموح: {message_type}"
        
        # فلتر حجم الملف
        max_file_size = config.get('max_file_size_mb', 0)
        if max_file_size > 0:
            file_size = self.get_file_size(message)
            if file_size > max_file_size * 1024 * 1024:
                return False, f"حجم الملف كبير جداً: {file_size / (1024*1024):.1f}MB"
        
        # فلتر مدة الوسائط
        max_duration = config.get('max_duration_seconds', 0)
        if max_duration > 0:
            duration = self.get_media_duration(message)
            if duration > max_duration:
                return False, f"مدة الوسائط طويلة جداً: {duration}s"
        
        return True, "نوع الوسائط مقبول"
    
    async def filter_text_content(self, message: Message, config: Dict[str, Any]) -> Tuple[bool, str]:
        """فلتر محتوى النص"""
        text = message.text or message.caption or ""
        if not text:
            return True, "لا يوجد نص"
        
        # فلتر الكلمات المحظورة
        banned_words = config.get('banned_words', [])
        if banned_words:
            text_lower = text.lower()
            for word in banned_words:
                if word.lower() in text_lower:
                    return False, f"كلمة محظورة: {word}"
        
        # فلتر الكلمات المطلوبة
        required_words = config.get('required_words', [])
        if required_words:
            text_lower = text.lower()
            found_required = False
            for word in required_words:
                if word.lower() in text_lower:
                    found_required = True
                    break
            if not found_required:
                return False, "لا يحتوي على كلمات مطلوبة"
        
        # فلتر طول النص
        min_length = config.get('min_length', 0)
        max_length = config.get('max_length', 0)
        
        if min_length > 0 and len(text) < min_length:
            return False, f"النص قصير جداً: {len(text)} < {min_length}"
        
        if max_length > 0 and len(text) > max_length:
            return False, f"النص طويل جداً: {len(text)} > {max_length}"
        
        # فلتر التعبيرات النمطية
        regex_patterns = config.get('regex_patterns', [])
        for pattern_config in regex_patterns:
            pattern = pattern_config.get('pattern', '')
            action = pattern_config.get('action', 'block')  # block or require
            
            try:
                match = re.search(pattern, text, re.IGNORECASE)
                if action == 'block' and match:
                    return False, f"نمط محظور: {pattern}"
                elif action == 'require' and not match:
                    return False, f"نمط مطلوب غير موجود: {pattern}"
            except re.error:
                continue
        
        # فلتر تكرار الأحرف
        max_char_repeat = config.get('max_char_repeat', 0)
        if max_char_repeat > 0:
            for char in text:
                if text.count(char) > max_char_repeat:
                    return False, f"تكرار مفرط للحرف: {char}"
        
        return True, "محتوى النص مقبول"
    
    async def filter_user_restrictions(self, message: Message, config: Dict[str, Any]) -> Tuple[bool, str]:
        """فلتر قيود المستخدمين"""
        if not message.from_user:
            return config.get('allow_anonymous', True), "مستخدم مجهول"
        
        user = message.from_user
        user_id = user.id
        
        # القائمة البيضاء
        whitelist = config.get('whitelist', [])
        if whitelist:
            if user_id not in whitelist and user.username not in whitelist:
                return False, "المستخدم ليس في القائمة البيضاء"
        
        # القائمة السوداء
        blacklist = config.get('blacklist', [])
        if blacklist:
            if user_id in blacklist or user.username in blacklist:
                return False, "المستخدم في القائمة السوداء"
        
        # فلتر البوتات
        if config.get('block_bots', False) and user.is_bot:
            return False, "البوتات محظورة"
        
        # فلتر المستخدمين الجدد
        min_account_age_days = config.get('min_account_age_days', 0)
        if min_account_age_days > 0:
            # هذا يتطلب معلومات إضافية عن المستخدم
            # سيتم تطويره في المرحلة التالية
            pass
        
        # فلتر المستخدمين بدون اسم مستخدم
        if config.get('require_username', False) and not user.username:
            return False, "اسم المستخدم مطلوب"
        
        # فلتر المستخدمين المميزين
        if config.get('verified_only', False):
            # فحص إذا كان المستخدم مميز (Premium)
            is_premium = await self.db.check_premium(user_id)
            if not is_premium:
                return False, "مستخدمي Premium فقط"
        
        return True, "المستخدم مقبول"
    
    async def filter_time_based(self, message: Message, config: Dict[str, Any]) -> Tuple[bool, str]:
        """فلتر زمني"""
        now = datetime.now()
        
        # ساعات العمل
        working_hours = config.get('working_hours', {})
        if working_hours.get('enabled', False):
            start_hour = working_hours.get('start_hour', 0)
            end_hour = working_hours.get('end_hour', 23)
            
            current_hour = now.hour
            if not (start_hour <= current_hour <= end_hour):
                return False, f"خارج ساعات العمل: {current_hour}:00"
        
        # أيام العمل
        working_days = config.get('working_days', [])
        if working_days:
            current_day = now.strftime('%A').lower()
            if current_day not in working_days:
                return False, f"يوم غير مسموح: {current_day}"
        
        # فترة التهدئة
        cooldown_seconds = config.get('cooldown_seconds', 0)
        if cooldown_seconds > 0:
            user_id = message.from_user.id if message.from_user else 0
            last_message_time = self.user_message_history.get(user_id, {}).get('last_time')
            
            if last_message_time:
                time_diff = (now - last_message_time).total_seconds()
                if time_diff < cooldown_seconds:
                    return False, f"فترة تهدئة: {cooldown_seconds - time_diff:.0f}s متبقية"
        
        return True, "التوقيت مقبول"
    
    async def filter_size_limits(self, message: Message, config: Dict[str, Any]) -> Tuple[bool, str]:
        """فلتر حدود الحجم"""
        # حد حجم النص
        max_text_length = config.get('max_text_length', 0)
        if max_text_length > 0:
            text = message.text or message.caption or ""
            if len(text) > max_text_length:
                return False, f"النص طويل جداً: {len(text)} > {max_text_length}"
        
        # حد حجم الملف
        max_file_size = config.get('max_file_size_mb', 0)
        if max_file_size > 0:
            file_size = self.get_file_size(message)
            max_size_bytes = max_file_size * 1024 * 1024
            if file_size > max_size_bytes:
                return False, f"الملف كبير جداً: {file_size / (1024*1024):.1f}MB"
        
        # حد أبعاد الصورة/الفيديو
        max_resolution = config.get('max_resolution', {})
        if max_resolution:
            width, height = self.get_media_dimensions(message)
            max_width = max_resolution.get('width', 0)
            max_height = max_resolution.get('height', 0)
            
            if max_width > 0 and width > max_width:
                return False, f"العرض كبير جداً: {width} > {max_width}"
            
            if max_height > 0 and height > max_height:
                return False, f"الارتفاع كبير جداً: {height} > {max_height}"
        
        return True, "الحجم مقبول"
    
    async def filter_language(self, message: Message, config: Dict[str, Any]) -> Tuple[bool, str]:
        """فلتر اللغة"""
        text = message.text or message.caption or ""
        if not text:
            return True, "لا يوجد نص"
        
        required_language = config.get('required_language', '')
        if not required_language:
            return True, "لا يوجد قيد لغوي"
        
        detected_language = self.detect_language(text)
        
        if detected_language != required_language:
            return False, f"لغة غير مطلوبة: {detected_language} != {required_language}"
        
        return True, "اللغة مقبولة"
    
    async def filter_sentiment(self, message: Message, config: Dict[str, Any]) -> Tuple[bool, str]:
        """فلتر المشاعر"""
        text = message.text or message.caption or ""
        if not text:
            return True, "لا يوجد نص"
        
        allowed_sentiments = config.get('allowed_sentiments', [])
        if not allowed_sentiments:
            return True, "لا يوجد قيد مشاعر"
        
        sentiment = self.analyze_sentiment(text)
        
        if sentiment not in allowed_sentiments:
            return False, f"مشاعر غير مرغوبة: {sentiment}"
        
        return True, "المشاعر مقبولة"
    
    async def filter_duplicates(self, message: Message, config: Dict[str, Any]) -> Tuple[bool, str]:
        """فلتر التكرار"""
        if not config.get('enabled', False):
            return True, "فلتر التكرار معطل"
        
        text = message.text or message.caption or ""
        if not text:
            return True, "لا يوجد نص"
        
        user_id = message.from_user.id if message.from_user else 0
        chat_id = message.chat_id
        
        # الحصول على الرسائل الأخيرة
        recent_messages = await self.get_recent_messages(chat_id, user_id, config.get('check_last_n', 10))
        
        similarity_threshold = config.get('similarity_threshold', 0.8)
        
        for recent_msg in recent_messages:
            similarity = self.calculate_similarity(text, recent_msg)
            if similarity >= similarity_threshold:
                return False, f"رسالة مكررة (تشابه: {similarity:.2f})"
        
        return True, "رسالة فريدة"
    
    async def filter_links(self, message: Message, config: Dict[str, Any]) -> Tuple[bool, str]:
        """فلتر الروابط المتقدم"""
        text = message.text or message.caption or ""
        if not text:
            return True, "لا يوجد نص"
        
        # استخراج الروابط
        urls = self.extract_urls(text)
        
        if not urls:
            if config.get('require_links', False):
                return False, "روابط مطلوبة"
            return True, "لا توجد روابط"
        
        # فحص حظر جميع الروابط
        if config.get('block_all_links', False):
            return False, "جميع الروابط محظورة"
        
        # فحص الدومينات المحظورة
        banned_domains = config.get('banned_domains', [])
        for url in urls:
            domain = self.extract_domain(url)
            if domain in banned_domains:
                return False, f"دومين محظور: {domain}"
        
        # فحص الدومينات المسموحة
        allowed_domains = config.get('allowed_domains', [])
        if allowed_domains:
            for url in urls:
                domain = self.extract_domain(url)
                if domain not in allowed_domains:
                    return False, f"دومين غير مسموح: {domain}"
        
        # فحص الروابط المختصرة
        if config.get('block_shortened_urls', False):
            short_url_domains = ['bit.ly', 'tinyurl.com', 't.co', 'goo.gl', 'ow.ly']
            for url in urls:
                domain = self.extract_domain(url)
                if domain in short_url_domains:
                    return False, f"رابط مختصر محظور: {domain}"
        
        # فحص أمان الروابط
        if config.get('check_url_safety', False):
            for url in urls:
                if not await self.is_url_safe(url):
                    return False, f"رابط غير آمن: {url}"
        
        return True, "الروابط مقبولة"
    
    async def filter_forwarded(self, message: Message, config: Dict[str, Any]) -> Tuple[bool, str]:
        """فلتر الرسائل المُعاد توجيهها"""
        is_forwarded = bool(message.forward_from or message.forward_from_chat)
        
        # حظر الرسائل المُعاد توجيهها
        if config.get('block_forwarded', False) and is_forwarded:
            return False, "الرسائل المُعاد توجيهها محظورة"
        
        # السماح فقط بالرسائل المُعاد توجيهها
        if config.get('only_forwarded', False) and not is_forwarded:
            return False, "الرسائل المُعاد توجيهها فقط مسموحة"
        
        # فحص مصدر التوجيه
        if is_forwarded and config.get('check_forward_source', False):
            allowed_sources = config.get('allowed_forward_sources', [])
            blocked_sources = config.get('blocked_forward_sources', [])
            
            source_id = None
            if message.forward_from:
                source_id = message.forward_from.id
            elif message.forward_from_chat:
                source_id = message.forward_from_chat.id
            
            if blocked_sources and source_id in blocked_sources:
                return False, f"مصدر توجيه محظور: {source_id}"
            
            if allowed_sources and source_id not in allowed_sources:
                return False, f"مصدر توجيه غير مسموح: {source_id}"
        
        return True, "حالة التوجيه مقبولة"
    
    # وظائف مساعدة
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
        else:
            return 'other'
    
    def get_file_size(self, message: Message) -> int:
        """الحصول على حجم الملف"""
        if message.photo:
            return message.photo[-1].file_size or 0
        elif message.video:
            return message.video.file_size or 0
        elif message.audio:
            return message.audio.file_size or 0
        elif message.voice:
            return message.voice.file_size or 0
        elif message.document:
            return message.document.file_size or 0
        else:
            return 0
    
    def get_media_duration(self, message: Message) -> int:
        """الحصول على مدة الوسائط"""
        if message.video:
            return message.video.duration or 0
        elif message.audio:
            return message.audio.duration or 0
        elif message.voice:
            return message.voice.duration or 0
        else:
            return 0
    
    def get_media_dimensions(self, message: Message) -> Tuple[int, int]:
        """الحصول على أبعاد الوسائط"""
        if message.photo:
            photo = message.photo[-1]
            return photo.width, photo.height
        elif message.video:
            return message.video.width, message.video.height
        else:
            return 0, 0
    
    def detect_language(self, text: str) -> str:
        """كشف لغة النص"""
        # تطبيق بسيط لكشف اللغة
        arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        
        if arabic_chars > english_chars:
            return 'arabic'
        elif english_chars > arabic_chars:
            return 'english'
        else:
            return 'mixed'
    
    def analyze_sentiment(self, text: str) -> str:
        """تحليل مشاعر النص"""
        # تطبيق بسيط لتحليل المشاعر
        positive_words = ['جيد', 'ممتاز', 'رائع', 'good', 'great', 'excellent']
        negative_words = ['سيء', 'فظيع', 'bad', 'terrible', 'awful']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def extract_urls(self, text: str) -> List[str]:
        """استخراج الروابط من النص"""
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\$$\$$,]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        return re.findall(url_pattern, text)
    
    def extract_domain(self, url: str) -> str:
        """استخراج الدومين من الرابط"""
        import urllib.parse
        parsed = urllib.parse.urlparse(url)
        return parsed.netloc.lower()
    
    async def is_url_safe(self, url: str) -> bool:
        """فحص أمان الرابط"""
        # تطبيق بسيط - يمكن تطويره للاتصال بخدمات فحص الأمان
        dangerous_domains = [
            'malware.com', 'phishing.net', 'spam.org',
            'virus.info', 'scam.biz'
        ]
        
        domain = self.extract_domain(url)
        return domain not in dangerous_domains
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """حساب التشابه بين النصوص"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 and not words2:
            return 1.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    async def get_recent_messages(self, chat_id: int, user_id: int, count: int) -> List[str]:
        """الحصول على الرسائل الأخيرة"""
        # استعلام قاعدة البيانات للحصول على الرسائل الأخيرة
        return await self.db.get_recent_user_messages(chat_id, user_id, count)
    
    async def check_global_ban(self, message: Message) -> bool:
        """فحص الحظر العالمي"""
        if not message.from_user:
            return False
        
        user_id = message.from_user.id
        user_data = await self.db.get_user(user_id)
        
        return user_data and user_data.get('is_banned', False)
    
    async def update_message_history(self, message: Message):
        """تحديث تاريخ الرسائل"""
        if not message.from_user:
            return
        
        user_id = message.from_user.id
        current_time = datetime.now()
        
        if user_id not in self.user_message_history:
            self.user_message_history[user_id] = {
                'messages': [],
                'last_time': current_time,
                'count_today': 0
            }
        
        user_history = self.user_message_history[user_id]
        user_history['last_time'] = current_time
        user_history['messages'].append({
            'text': message.text or message.caption or '',
            'time': current_time,
            'type': self.get_message_type(message)
        })
        
        # الاحتفاظ بآخر 100 رسالة فقط
        if len(user_history['messages']) > 100:
            user_history['messages'] = user_history['messages'][-100:]
        
        # تحديث عداد اليوم
        today = current_time.date()
        if hasattr(user_history, 'last_date') and user_history.get('last_date') != today:
            user_history['count_today'] = 0
        
        user_history['count_today'] += 1
        user_history['last_date'] = today

class SpamDetector:
    """كاشف السبام المتقدم"""
    
    def __init__(self):
        self.spam_patterns = [
            r'(win|won|winner).*(prize|money|cash)',
            r'(click|visit).*(link|url)',
            r'(free|gratis).*(download|gift)',
            r'(urgent|hurry|limited time)',
            r'(\$|\€|\£|USD|EUR)\s*\d+',
        ]
        self.spam_keywords = [
            'spam', 'scam', 'phishing', 'malware',
            'free money', 'easy money', 'get rich quick'
        ]
    
    async def is_spam(self, message: Message, user_history: Dict[int, Dict]) -> bool:
        """فحص إذا كانت الرسالة سبام"""
        text = message.text or message.caption or ""
        if not text:
            return False
        
        user_id = message.from_user.id if message.from_user else 0
        
        # فحص الأنماط المشبوهة
        if self.check_spam_patterns(text):
            return True
        
        # فحص الكلمات المفتاحية
        if self.check_spam_keywords(text):
            return True
        
        # فحص معدل الإرسال
        if await self.check_rate_limit(user_id, user_history):
            return True
        
        # فحص التكرار المفرط
        if await self.check_excessive_repetition(user_id, text, user_history):
            return True
        
        # فحص الروابط المشبوهة
        if self.check_suspicious_links(text):
            return True
        
        return False
    
    def check_spam_patterns(self, text: str) -> bool:
        """فحص أنماط السبام"""
        text_lower = text.lower()
        for pattern in self.spam_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        return False
    
    def check_spam_keywords(self, text: str) -> bool:
        """فحص كلمات السبام"""
        text_lower = text.lower()
        for keyword in self.spam_keywords:
            if keyword in text_lower:
                return True
        return False
    
    async def check_rate_limit(self, user_id: int, user_history: Dict[int, Dict]) -> bool:
        """فحص معدل الإرسال"""
        if user_id not in user_history:
            return False
        
        user_data = user_history[user_id]
        messages_today = user_data.get('count_today', 0)
        
        # حد 100 رسالة في اليوم للمستخدم العادي
        return messages_today > 100
    
    async def check_excessive_repetition(self, user_id: int, text: str, 
                                       user_history: Dict[int, Dict]) -> bool:
        """فحص التكرار المفرط"""
        if user_id not in user_history:
            return False
        
        user_data = user_history[user_id]
        recent_messages = user_data.get('messages', [])
        
        # فحص آخر 10 رسائل
        recent_texts = [msg['text'] for msg in recent_messages[-10:]]
        identical_count = recent_texts.count(text)
        
        return identical_count >= 3  # 3 رسائل متطابقة أو أكثر
    
    def check_suspicious_links(self, text: str) -> bool:
        """فحص الروابط المشبوهة"""
        suspicious_domains = [
            'bit.ly', 'tinyurl.com', 'goo.gl',
            'ow.ly', 't.co', 'short.link'
        ]
        
        urls = re.findall(r'http[s]?://[^\s]+', text)
        for url in urls:
            for domain in suspicious_domains:
                if domain in url:
                    return True
        return False

class ContentAnalyzer:
    """محلل المحتوى المتقدم"""
    
    def __init__(self):
        self.forbidden_content = [
            'violence', 'hate speech', 'adult content',
            'illegal activities', 'harassment'
        ]
        
        self.violence_keywords = [
            'kill', 'murder', 'bomb', 'weapon', 'terror',
            'قتل', 'قنبلة', 'سلاح', 'إرهاب', 'عنف'
        ]
        
        self.hate_keywords = [
            'racist', 'discrimination', 'hate',
            'عنصري', 'كراهية', 'تمييز'
        ]
    
    async def has_forbidden_content(self, message: Message) -> bool:
        """فحص المحتوى المحظور"""
        text = message.text or message.caption or ""
        if not text:
            return False
        
        # فحص العنف
        if self.check_violence_content(text):
            return True
        
        # فحص خطاب الكراهية
        if self.check_hate_speech(text):
            return True
        
        # فحص المحتوى الإباحي
        if self.check_adult_content(text):
            return True
        
        # فحص الأنشطة غير القانونية
        if self.check_illegal_activities(text):
            return True
        
        return False
    
    def check_violence_content(self, text: str) -> bool:
        """فحص محتوى العنف"""
        text_lower = text.lower()
        violence_count = sum(1 for keyword in self.violence_keywords 
                           if keyword in text_lower)
        return violence_count >= 2  # كلمتين أو أكثر من كلمات العنف
    
    def check_hate_speech(self, text: str) -> bool:
        """فحص خطاب الكراهية"""
        text_lower = text.lower()
        hate_count = sum(1 for keyword in self.hate_keywords 
                        if keyword in text_lower)
        return hate_count >= 1
    
    def check_adult_content(self, text: str) -> bool:
        """فحص المحتوى الإباحي"""
        adult_keywords = [
            'porn', 'sex', 'adult', 'xxx',
            'إباحي', 'جنس', 'عاري'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in adult_keywords)
    
    def check_illegal_activities(self, text: str) -> bool:
        """فحص الأنشطة غير القانونية"""
        illegal_keywords = [
            'drugs', 'cocaine', 'heroin', 'marijuana',
            'hack', 'crack', 'piracy', 'counterfeit',
            'مخدرات', 'كوكايين', 'هيروين', 'حشيش',
            'اختراق', 'قرصنة', 'تزوير'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in illegal_keywords)

class FilterPresets:
    """إعدادات الفلاتر المُعدة مسبقاً"""
    
    @staticmethod
    def get_basic_filter() -> Dict[str, Any]:
        """فلتر أساسي"""
        return {
            'media_type': {
                'enabled': True,
                'allowed_types': ['text', 'photo', 'video'],
                'max_file_size_mb': 50
            },
            'text_content': {
                'enabled': True,
                'max_length': 4000,
                'banned_words': ['spam', 'scam']
            },
            'user_restrictions': {
                'enabled': True,
                'block_bots': True
            }
        }
    
    @staticmethod
    def get_strict_filter() -> Dict[str, Any]:
        """فلتر صارم"""
        return {
            'media_type': {
                'enabled': True,
                'allowed_types': ['text', 'photo'],
                'max_file_size_mb': 10
            },
            'text_content': {
                'enabled': True,
                'min_length': 10,
                'max_length': 1000,
                'banned_words': ['spam', 'scam', 'fake', 'virus'],
                'required_words': []
            },
            'user_restrictions': {
                'enabled': True,
                'block_bots': True,
                'require_username': True,
                'verified_only': True
            },
            'link_analysis': {
                'enabled': True,
                'block_shortened_urls': True,
                'check_url_safety': True
            },
            'duplicate_detection': {
                'enabled': True,
                'similarity_threshold': 0.7,
                'check_last_n': 20
            }
        }
    
    @staticmethod
    def get_media_only_filter() -> Dict[str, Any]:
        """فلتر الوسائط فقط"""
        return {
            'media_type': {
                'enabled': True,
                'allowed_types': ['photo', 'video', 'audio'],
                'max_file_size_mb': 100,
                'max_duration_seconds': 300
            },
            'text_content': {
                'enabled': True,
                'max_length': 200  # تعليقات قصيرة فقط
            },
            'size_limits': {
                'enabled': True,
                'max_resolution': {
                    'width': 1920,
                    'height': 1080
                }
            }
        }
    
    @staticmethod
    def get_news_filter() -> Dict[str, Any]:
        """فلتر الأخبار"""
        return {
            'text_content': {
                'enabled': True,
                'min_length': 50,
                'required_words': ['news', 'breaking', 'report', 'أخبار', 'عاجل'],
                'banned_words': ['opinion', 'rumor', 'رأي', 'شائعة']
            },
            'link_analysis': {
                'enabled': True,
                'allowed_domains': [
                    'bbc.com', 'cnn.com', 'reuters.com',
                    'aljazeera.net', 'alarabiya.net'
                ],
                'require_links': True
            },
            'forwarded_restrictions': {
                'enabled': True,
                'check_forward_source': True
            }
        }
