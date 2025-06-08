"""
الوظائف المساعدة
Helper Functions
"""

import re
import json
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import emoji

class TextProcessor:
    """معالج النصوص المتقدم"""
    
    @staticmethod
    def clean_text(text: str, settings: Dict[str, Any]) -> str:
        """تنظيف النص حسب الإعدادات"""
        if not text:
            return text
        
        cleaned_text = text
        
        # إزالة الروابط
        if settings.get('remove_links', False):
            url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\$$\$$,]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
            cleaned_text = re.sub(url_pattern, '', cleaned_text)
        
        # إزالة الهاشتاغ
        if settings.get('remove_hashtags', False):
            cleaned_text = re.sub(r'#\w+', '', cleaned_text)
        
        # إزالة الإيموجي
        if settings.get('remove_emojis', False):
            cleaned_text = emoji.demojize(cleaned_text)
            cleaned_text = re.sub(r':[a-zA-Z_]+:', '', cleaned_text)
        
        # حذف الأسطر التي تحتوي على كلمات معينة
        if settings.get('remove_lines_with_words'):
            words_to_remove = settings['remove_lines_with_words']
            lines = cleaned_text.split('\n')
            filtered_lines = []
            
            for line in lines:
                should_remove = False
                for word in words_to_remove:
                    if word.lower() in line.lower():
                        should_remove = True
                        break
                if not should_remove:
                    filtered_lines.append(line)
            
            cleaned_text = '\n'.join(filtered_lines)
        
        # إزالة الأسطر الفارغة
        if settings.get('remove_empty_lines', False):
            lines = cleaned_text.split('\n')
            cleaned_text = '\n'.join([line for line in lines if line.strip()])
        
        # استبدال النصوص
        if settings.get('text_replacements'):
            for old_text, new_text in settings['text_replacements'].items():
                cleaned_text = cleaned_text.replace(old_text, new_text)
        
        return cleaned_text.strip()
    
    @staticmethod
    def add_header_footer(text: str, header: str = None, footer: str = None) -> str:
        """إضافة رأس وتذييل للنص"""
        result = text
        
        if header:
            result = f"{header}\n\n{result}"
        
        if footer:
            result = f"{result}\n\n{footer}"
        
        return result
    
    @staticmethod
    def limit_text_length(text: str, max_length: int) -> str:
        """تحديد طول النص"""
        if len(text) <= max_length:
            return text
        
        return text[:max_length-3] + "..."
    
    @staticmethod
    def remove_formatting(text: str) -> str:
        """إزالة تنسيق النص"""
        # إزالة تنسيق Markdown
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*(.*?)\*', r'\1', text)      # Italic
        text = re.sub(r'__(.*?)__', r'\1', text)      # Underline
        text = re.sub(r'~~(.*?)~~', r'\1', text)      # Strikethrough
        text = re.sub(r'`(.*?)`', r'\1', text)        # Code
        text = re.sub(r'\|\|(.*?)\|\|', r'\1', text)  # Spoiler
        
        return text

class TimeHelper:
    """مساعد الوقت والتاريخ"""
    
    @staticmethod
    def format_duration(seconds: int) -> str:
        """تنسيق المدة الزمنية"""
        if seconds < 60:
            return f"{seconds} ثانية"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes} دقيقة"
        elif seconds < 86400:
            hours = seconds // 3600
            return f"{hours} ساعة"
        else:
            days = seconds // 86400
            return f"{days} يوم"
    
    @staticmethod
    def is_working_hours(working_hours: Dict[str, Any]) -> bool:
        """فحص ساعات العمل"""
        if not working_hours.get('enabled', False):
            return True
        
        now = datetime.now()
        current_time = now.time()
        current_day = now.strftime('%A').lower()
        
        # فحص اليوم
        if working_hours.get('days') and current_day not in working_hours['days']:
            return False
        
        # فحص الوقت
        start_time = working_hours.get('start_time')
        end_time = working_hours.get('end_time')
        
        if start_time and end_time:
            start = datetime.strptime(start_time, '%H:%M').time()
            end = datetime.strptime(end_time, '%H:%M').time()
            
            if start <= end:
                return start <= current_time <= end
            else:  # يمتد عبر منتصف الليل
                return current_time >= start or current_time <= end
        
        return True
    
    @staticmethod
    def parse_schedule_time(time_str: str) -> Optional[datetime]:
        """تحليل وقت الجدولة"""
        try:
            # تنسيقات مختلفة للوقت
            formats = [
                '%Y-%m-%d %H:%M',
                '%d/%m/%Y %H:%M',
                '%H:%M',
                '%Y-%m-%d',
                '%d/%m/%Y'
            ]
            
            for fmt in formats:
                try:
                    parsed_time = datetime.strptime(time_str, fmt)
                    
                    # إذا كان التنسيق يحتوي على وقت فقط، أضف التاريخ الحالي
                    if fmt == '%H:%M':
                        today = datetime.now().date()
                        parsed_time = datetime.combine(today, parsed_time.time())
                        
                        # إذا كان الوقت قد مضى اليوم، اجعله غداً
                        if parsed_time < datetime.now():
                            parsed_time += timedelta(days=1)
                    
                    return parsed_time
                except ValueError:
                    continue
            
            return None
        except Exception:
            return None

class DataValidator:
    """مدقق البيانات"""
    
    @staticmethod
    def is_valid_chat_id(chat_id: Union[str, int]) -> bool:
        """فحص صحة معرف الدردشة"""
        try:
            chat_id = int(chat_id)
            return abs(chat_id) > 0
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def is_valid_username(username: str) -> bool:
        """فحص صحة اسم المستخدم"""
        if not username:
            return False
        
        # إزالة @ إذا كانت موجودة
        username = username.lstrip('@')
        
        # فحص التنسيق
        pattern = r'^[a-zA-Z][a-zA-Z0-9_]{4,31}$'
        return bool(re.match(pattern, username))
    
    @staticmethod
    def is_valid_bot_token(token: str) -> bool:
        """فحص صحة توكن البوت"""
        if not token:
            return False
        
        # تنسيق توكن البوت: bot_id:token
        pattern = r'^\d+:[a-zA-Z0-9_-]{35}$'
        return bool(re.match(pattern, token))
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """تنظيف اسم الملف"""
        # إزالة الأحرف غير المسموحة
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # تحديد الطول
        if len(filename) > 255:
            filename = filename[:255]
        
        return filename

class KeyboardBuilder:
    """بناء لوحات المفاتيح"""
    
    @staticmethod
    def build_pagination_keyboard(items: List[Dict], page: int, per_page: int, 
                                callback_prefix: str) -> InlineKeyboardMarkup:
        """بناء لوحة مفاتيح مع ترقيم الصفحات"""
        keyboard = []
        
        # حساب الصفحات
        total_pages = (len(items) + per_page - 1) // per_page
        start_idx = page * per_page
        end_idx = min(start_idx + per_page, len(items))
        
        # إضافة العناصر
        for i in range(start_idx, end_idx):
            item = items[i]
            keyboard.append([
                InlineKeyboardButton(
                    item['title'], 
                    callback_data=f"{callback_prefix}_{item['id']}"
                )
            ])
        
        # أزرار التنقل
        nav_buttons = []
        if page > 0:
            nav_buttons.append(
                InlineKeyboardButton("◀️ السابق", callback_data=f"page_{page-1}")
            )
        
        nav_buttons.append(
            InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="current_page")
        )
        
        if page < total_pages - 1:
            nav_buttons.append(
                InlineKeyboardButton("التالي ▶️", callback_data=f"page_{page+1}")
            )
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def build_confirmation_keyboard(confirm_callback: str, cancel_callback: str = "cancel") -> InlineKeyboardMarkup:
        """بناء لوحة تأكيد"""
        keyboard = [
            [
                InlineKeyboardButton("✅ تأكيد", callback_data=confirm_callback),
                InlineKeyboardButton("❌ إلغاء", callback_data=cancel_callback)
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

class SecurityHelper:
    """مساعد الأمان"""
    
    @staticmethod
    def hash_data(data: str) -> str:
        """تشفير البيانات"""
        return hashlib.sha256(data.encode()).hexdigest()
    
    @staticmethod
    def generate_unique_id() -> str:
        """توليد معرف فريد"""
        import uuid
        return str(uuid.uuid4())
    
    @staticmethod
    def is_safe_content(text: str) -> bool:
        """فحص أمان المحتوى"""
        # قائمة الكلمات المحظورة (يمكن توسيعها)
        banned_words = [
            'spam', 'scam', 'hack', 'virus'
        ]
        
        text_lower = text.lower()
        return not any(word in text_lower for word in banned_words)

class FormatHelper:
    """مساعد التنسيق"""
    
    @staticmethod
    def format_number(number: int) -> str:
        """تنسيق الأرقام"""
        if number >= 1000000:
            return f"{number/1000000:.1f}M"
        elif number >= 1000:
            return f"{number/1000:.1f}K"
        else:
            return str(number)
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """تنسيق حجم الملف"""
        if size_bytes >= 1024**3:
            return f"{size_bytes/(1024**3):.1f} GB"
        elif size_bytes >= 1024**2:
            return f"{size_bytes/(1024**2):.1f} MB"
        elif size_bytes >= 1024:
            return f"{size_bytes/1024:.1f} KB"
        else:
            return f"{size_bytes} B"
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 100) -> str:
        """اختصار النص"""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."
