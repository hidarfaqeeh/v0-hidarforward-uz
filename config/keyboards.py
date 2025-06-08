"""
لوحات المفاتيح
Bot Keyboards
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from typing import List, Dict, Any

class MainKeyboards:
    """لوحات المفاتيح الرئيسية"""
    
    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        """القائمة الرئيسية"""
        keyboard = [
            [InlineKeyboardButton("📋 إدارة المهام", callback_data="tasks_menu")],
            [InlineKeyboardButton("📊 حالة الحساب", callback_data="account_status")],
            [
                InlineKeyboardButton("💎 Premium", callback_data="premium_info"),
                InlineKeyboardButton("📚 المساعدة", callback_data="help_menu")
            ],
            [InlineKeyboardButton("📞 الدعم الفني", url="https://t.me/support")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def back_to_main() -> InlineKeyboardMarkup:
        """العودة للقائمة الرئيسية"""
        keyboard = [
            [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)

class TaskKeyboards:
    """لوحات مفاتيح المهام"""
    
    @staticmethod
    def tasks_menu() -> InlineKeyboardMarkup:
        """قائمة المهام"""
        keyboard = [
            [InlineKeyboardButton("➕ إنشاء مهمة جديدة", callback_data="create_task")],
            [InlineKeyboardButton("📋 مهامي", callback_data="my_tasks")],
            [InlineKeyboardButton("⚙️ إعدادات المهام", callback_data="task_settings")],
            [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def task_actions(task_id: int) -> InlineKeyboardMarkup:
        """أحداث المهمة"""
        keyboard = [
            [
                InlineKeyboardButton("▶️ تشغيل", callback_data=f"task_start_{task_id}"),
                InlineKeyboardButton("⏸️ إيقاف", callback_data=f"task_stop_{task_id}")
            ],
            [
                InlineKeyboardButton("⚙️ تعديل", callback_data=f"task_edit_{task_id}"),
                InlineKeyboardButton("📊 إحصائيات", callback_data=f"task_stats_{task_id}")
            ],
            [InlineKeyboardButton("🗑️ حذف", callback_data=f"task_delete_{task_id}")],
            [InlineKeyboardButton("🔙 العودة", callback_data="my_tasks")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def task_type_selection() -> InlineKeyboardMarkup:
        """اختيار نوع المهمة"""
        keyboard = [
            [InlineKeyboardButton("🤖 Bot Token", callback_data="task_type_bot")],
            [InlineKeyboardButton("👤 Userbot", callback_data="task_type_userbot")],
            [InlineKeyboardButton("🔙 العودة", callback_data="tasks_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def forward_type_selection() -> InlineKeyboardMarkup:
        """اختيار نوع التوجيه"""
        keyboard = [
            [InlineKeyboardButton("📤 توجيه (Forward)", callback_data="forward_type_forward")],
            [InlineKeyboardButton("📋 نسخ (Copy)", callback_data="forward_type_copy")],
            [InlineKeyboardButton("🔙 العودة", callback_data="create_task")]
        ]
        return InlineKeyboardMarkup(keyboard)

class FilterKeyboards:
    """لوحات مفاتيح الفلاتر"""
    
    @staticmethod
    def filter_menu(task_id: int) -> InlineKeyboardMarkup:
        """قائمة الفلاتر"""
        keyboard = [
            [InlineKeyboardButton("📱 فلاتر الوسائط", callback_data=f"filter_media_{task_id}")],
            [InlineKeyboardButton("📝 فلاتر النصوص", callback_data=f"filter_text_{task_id}")],
            [InlineKeyboardButton("👥 فلاتر المستخدمين", callback_data=f"filter_users_{task_id}")],
            [InlineKeyboardButton("🔗 فلاتر الروابط", callback_data=f"filter_links_{task_id}")],
            [InlineKeyboardButton("🌐 فلاتر اللغة", callback_data=f"filter_language_{task_id}")],
            [InlineKeyboardButton("🔄 فلتر التكرار", callback_data=f"filter_duplicate_{task_id}")],
            [InlineKeyboardButton("🔙 العودة", callback_data=f"task_edit_{task_id}")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def media_filter_options() -> InlineKeyboardMarkup:
        """خيارات فلتر الوسائط"""
        keyboard = [
            [
                InlineKeyboardButton("📷 صور", callback_data="media_photos"),
                InlineKeyboardButton("🎥 فيديو", callback_data="media_videos")
            ],
            [
                InlineKeyboardButton("🎵 صوت", callback_data="media_audio"),
                InlineKeyboardButton("📄 مستندات", callback_data="media_documents")
            ],
            [
                InlineKeyboardButton("🎮 ألعاب", callback_data="media_games"),
                InlineKeyboardButton("📍 مواقع", callback_data="media_locations")
            ],
            [
                InlineKeyboardButton("👤 جهات اتصال", callback_data="media_contacts"),
                InlineKeyboardButton("🎭 ملصقات", callback_data="media_stickers")
            ],
            [InlineKeyboardButton("✅ حفظ", callback_data="save_media_filter")],
            [InlineKeyboardButton("🔙 العودة", callback_data="filter_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)

class AdminKeyboards:
    """لوحات مفاتيح الإدارة"""
    
    @staticmethod
    def admin_panel() -> InlineKeyboardMarkup:
        """لوحة الإدارة"""
        keyboard = [
            [
                InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats"),
                InlineKeyboardButton("👥 المستخدمين", callback_data="admin_users")
            ],
            [
                InlineKeyboardButton("📋 المهام", callback_data="admin_tasks"),
                InlineKeyboardButton("📢 رسالة جماعية", callback_data="admin_broadcast")
            ],
            [
                InlineKeyboardButton("⚙️ الإعدادات", callback_data="admin_settings"),
                InlineKeyboardButton("🔧 الصيانة", callback_data="admin_maintenance")
            ],
            [
                InlineKeyboardButton("👑 المشرفين", callback_data="admin_admins"),
                InlineKeyboardButton("💎 Premium", callback_data="admin_premium")
            ],
            [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def user_management(user_id: int) -> InlineKeyboardMarkup:
        """إدارة المستخدم"""
        keyboard = [
            [
                InlineKeyboardButton("💎 تفعيل Premium", callback_data=f"admin_premium_activate_{user_id}"),
                InlineKeyboardButton("❌ إلغاء Premium", callback_data=f"admin_premium_deactivate_{user_id}")
            ],
            [
                InlineKeyboardButton("🚫 حظر", callback_data=f"admin_ban_{user_id}"),
                InlineKeyboardButton("✅ إلغاء الحظر", callback_data=f"admin_unban_{user_id}")
            ],
            [
                InlineKeyboardButton("👑 جعل مشرف", callback_data=f"admin_make_admin_{user_id}"),
                InlineKeyboardButton("📊 الإحصائيات", callback_data=f"admin_user_stats_{user_id}")
            ],
            [InlineKeyboardButton("🔙 العودة", callback_data="admin_users")]
        ]
        return InlineKeyboardMarkup(keyboard)

class PremiumKeyboards:
    """لوحات مفاتيح Premium"""
    
    @staticmethod
    def premium_menu() -> InlineKeyboardMarkup:
        """قائمة Premium"""
        keyboard = [
            [InlineKeyboardButton("💎 ميزات Premium", callback_data="premium_features")],
            [InlineKeyboardButton("💰 الأسعار", callback_data="premium_pricing")],
            [InlineKeyboardButton("🎁 تفعيل التجربة المجانية", callback_data="activate_trial")],
            [InlineKeyboardButton("💳 شراء Premium", url="https://t.me/support")],
            [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def premium_plans() -> InlineKeyboardMarkup:
        """خطط Premium"""
        keyboard = [
            [InlineKeyboardButton("📅 شهري - $9.99", callback_data="premium_monthly")],
            [InlineKeyboardButton("📆 سنوي - $99.99", callback_data="premium_yearly")],
            [InlineKeyboardButton("♾️ مدى الحياة - $199.99", callback_data="premium_lifetime")],
            [InlineKeyboardButton("🔙 العودة", callback_data="premium_info")]
        ]
        return InlineKeyboardMarkup(keyboard)

class SettingsKeyboards:
    """لوحات مفاتيح الإعدادات"""
    
    @staticmethod
    def task_settings(task_id: int) -> InlineKeyboardMarkup:
        """إعدادات المهمة"""
        keyboard = [
            [
                InlineKeyboardButton("🔄 نوع التوجيه", callback_data=f"setting_forward_type_{task_id}"),
                InlineKeyboardButton("⏱️ التأخير", callback_data=f"setting_delay_{task_id}")
            ],
            [
                InlineKeyboardButton("📝 تعديل النص", callback_data=f"setting_text_edit_{task_id}"),
                InlineKeyboardButton("🔘 الأزرار", callback_data=f"setting_buttons_{task_id}")
            ],
            [
                InlineKeyboardButton("🕐 ساعات العمل", callback_data=f"setting_work_hours_{task_id}"),
                InlineKeyboardButton("📏 حد الأحرف", callback_data=f"setting_char_limit_{task_id}")
            ],
            [
                InlineKeyboardButton("📌 تثبيت الرسائل", callback_data=f"setting_pin_messages_{task_id}"),
                InlineKeyboardButton("💬 الرد على الرسائل", callback_data=f"setting_reply_{task_id}")
            ],
            [InlineKeyboardButton("🔙 العودة", callback_data=f"task_edit_{task_id}")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def text_cleaning_options(task_id: int) -> InlineKeyboardMarkup:
        """خيارات تنظيف النص"""
        keyboard = [
            [
                InlineKeyboardButton("🔗 إزالة الروابط", callback_data=f"clean_links_{task_id}"),
                InlineKeyboardButton("#️⃣ إزالة الهاشتاغ", callback_data=f"clean_hashtags_{task_id}")
            ],
            [
                InlineKeyboardButton("😀 إزالة الإيموجي", callback_data=f"clean_emojis_{task_id}"),
                InlineKeyboardButton("🔘 إزالة الأزرار", callback_data=f"clean_buttons_{task_id}")
            ],
            [
                InlineKeyboardButton("📝 إزالة التنسيق", callback_data=f"clean_formatting_{task_id}"),
                InlineKeyboardButton("➖ إزالة الأسطر الفارغة", callback_data=f"clean_empty_lines_{task_id}")
            ],
            [InlineKeyboardButton("✅ حفظ", callback_data=f"save_text_cleaning_{task_id}")],
            [InlineKeyboardButton("🔙 العودة", callback_data=f"setting_text_edit_{task_id}")]
        ]
        return InlineKeyboardMarkup(keyboard)

class ConfirmationKeyboards:
    """لوحات مفاتيح التأكيد"""
    
    @staticmethod
    def confirm_delete(item_type: str, item_id: int) -> InlineKeyboardMarkup:
        """تأكيد الحذف"""
        keyboard = [
            [
                InlineKeyboardButton("✅ تأكيد الحذف", callback_data=f"confirm_delete_{item_type}_{item_id}"),
                InlineKeyboardButton("❌ إلغاء", callback_data="cancel_delete")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def confirm_action(action: str, target: str) -> InlineKeyboardMarkup:
        """تأكيد العملية"""
        keyboard = [
            [
                InlineKeyboardButton("✅ تأكيد", callback_data=f"confirm_{action}_{target}"),
                InlineKeyboardButton("❌ إلغاء", callback_data="cancel_action")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

class NavigationKeyboards:
    """لوحات مفاتيح التنقل"""
    
    @staticmethod
    def pagination(current_page: int, total_pages: int, callback_prefix: str) -> InlineKeyboardMarkup:
        """ترقيم الصفحات"""
        keyboard = []
        
        # أزرار التنقل
        nav_buttons = []
        
        if current_page > 0:
            nav_buttons.append(
                InlineKeyboardButton("◀️", callback_data=f"{callback_prefix}_page_{current_page-1}")
            )
        
        nav_buttons.append(
            InlineKeyboardButton(f"{current_page+1}/{total_pages}", callback_data="current_page")
        )
        
        if current_page < total_pages - 1:
            nav_buttons.append(
                InlineKeyboardButton("▶️", callback_data=f"{callback_prefix}_page_{current_page+1}")
            )
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def close_menu() -> InlineKeyboardMarkup:
        """إغلاق القائمة"""
        keyboard = [
            [InlineKeyboardButton("❌ إغلاق", callback_data="close_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
