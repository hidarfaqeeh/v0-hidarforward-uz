"""
معالج الأزرار والاستدعاءات
Callback Handler
"""

import logging
from telegram import Update, CallbackQuery
from telegram.ext import ContextTypes
from database.db_manager import DatabaseManager
from config.keyboards import *
from config.messages import Messages
from utils.decorators import user_required, premium_required, error_handler
from utils.logger import BotLogger

logger = BotLogger()

class CallbackHandler:
    """معالج استدعاءات الأزرار"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    @user_required
    @error_handler
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج عام للاستدعاءات"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user_id = update.effective_user.id
        
        # تسجيل النشاط
        logger.log_user_action(user_id, f"callback_{data}")
        
        # توجيه الاستدعاء للمعالج المناسب
        if data == "main_menu":
            await self.show_main_menu(query)
        elif data == "tasks_menu":
            await self.show_tasks_menu(query)
        elif data == "account_status":
            await self.show_account_status(query)
        elif data == "premium_info":
            await self.show_premium_info(query)
        elif data == "help_menu":
            await self.show_help_menu(query)
        elif data == "activate_trial":
            await self.activate_trial(query)
        elif data == "create_task":
            await self.create_task_start(query)
        elif data == "my_tasks":
            await self.show_my_tasks(query)
        elif data.startswith("task_"):
            await self.handle_task_callback(query, data)
        elif data.startswith("admin_"):
            await self.handle_admin_callback(query, data)
        elif data.startswith("filter_"):
            await self.handle_filter_callback(query, data)
        elif data.startswith("setting_"):
            await self.handle_setting_callback(query, data)
        elif data == "close_menu":
            await query.delete_message()
        else:
            await query.edit_message_text("❌ أمر غير معروف")
    
    async def show_main_menu(self, query: CallbackQuery):
        """عرض القائمة الرئيسية"""
        await query.edit_message_text(
            Messages.WELCOME,
            reply_markup=MainKeyboards.main_menu(),
            parse_mode='HTML'
        )
    
    async def show_tasks_menu(self, query: CallbackQuery):
        """عرض قائمة المهام"""
        text = """
📋 <b>إدارة المهام</b>

من هنا يمكنك إنشاء وإدارة مهام التوجيه الخاصة بك.

🎯 الميزات المتاحة:
• إنشاء مهام توجيه جديدة
• تعديل المهام الموجودة
• تفعيل/تعطيل المهام
• إعداد الفلاتر المتقدمة
• مراقبة الإحصائيات
        """
        
        await query.edit_message_text(
            text,
            reply_markup=TaskKeyboards.tasks_menu(),
            parse_mode='HTML'
        )
    
    async def show_account_status(self, query: CallbackQuery):
        """عرض حالة الحساب"""
        user_id = query.from_user.id
        user_data = await self.db.get_user(user_id)
        
        if not user_data:
            await query.edit_message_text("❌ خطأ في الحصول على بيانات المستخدم")
            return
        
        # فحص حالة Premium
        is_premium = await self.db.check_premium(user_id)
        premium_status = "✅ نشط" if is_premium else "❌ غير نشط"
        
        # إحصائيات المستخدم
        tasks = await self.db.get_user_tasks(user_id)
        active_tasks = len([t for t in tasks if t['is_active']])
        
        status_text = f"""
👤 <b>حالة حسابك</b>

🆔 معرف المستخدم: <code>{user_id}</code>
👤 الاسم: {user_data['first_name'] or 'غير محدد'}
📱 اسم المستخدم: @{user_data['username'] or 'غير محدد'}

💎 <b>حالة Premium:</b> {premium_status}
🔄 <b>التجربة المجانية:</b> {'مُستخدمة' if user_data['trial_used'] else 'متاحة'}

📊 <b>الإحصائيات:</b>
📋 إجمالي المهام: {len(tasks)}
✅ المهام النشطة: {active_tasks}
📅 تاريخ التسجيل: {user_data['created_at'][:10]}
        """
        
        keyboard = [
            [InlineKeyboardButton("📋 إدارة المهام", callback_data="tasks_menu")],
            [InlineKeyboardButton("💎 ترقية Premium", callback_data="premium_info")],
            [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            status_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    async def show_premium_info(self, query: CallbackQuery):
        """عرض معلومات Premium"""
        user_id = query.from_user.id
        is_premium = await self.db.check_premium(user_id)
        
        if is_premium:
            text = """
✨ <b>أنت مشترك في Premium!</b>

🎯 الميزات المتاحة لك:
• مهام غير محدودة
• فلاتر متقدمة
• جدولة الرسائل
• نسخ البوت
• دعم فني مميز
• إحصائيات تفصيلية
• أولوية في المعالجة

💎 استمتع بجميع الميزات المتقدمة!
            """
        else:
            text = """
💎 <b>ميزات Premium</b>

🚀 احصل على إمكانيات لا محدودة:
• مهام توجيه غير محدودة
• فلاتر متقدمة ومخصصة
• جدولة الرسائل التلقائية
• إنشاء نسخ من البوت
• دعم فني على مدار الساعة
• إحصائيات وتقارير مفصلة
• أولوية في المعالجة

💰 السعر: اتصل للاستفسار
🎁 تجربة مجانية: 48 ساعة
            """
        
        await query.edit_message_text(
            text,
            reply_markup=PremiumKeyboards.premium_menu(),
            parse_mode='HTML'
        )
    
    async def show_help_menu(self, query: CallbackQuery):
        """عرض قائمة المساعدة"""
        await query.edit_message_text(
            Messages.HELP,
            reply_markup=MainKeyboards.back_to_main(),
            parse_mode='HTML'
        )
    
    async def activate_trial(self, query: CallbackQuery):
        """تفعيل التجربة المجانية"""
        user_id = query.from_user.id
        
        if await self.db.activate_trial(user_id):
            text = """
🎉 <b>تم تفعيل التجربة المجانية!</b>

⏰ المدة: 48 ساعة
✨ جميع ميزات Premium متاحة الآن

استمتع بالتجربة! 🚀
            """
            keyboard = [
                [InlineKeyboardButton("📋 إنشاء مهمة جديدة", callback_data="create_task")],
                [InlineKeyboardButton("🔙 العودة", callback_data="main_menu")]
            ]
        else:
            text = "❌ التجربة المجانية مُستخدمة مسبقاً أو أنت مشترك في Premium"
            keyboard = [
                [InlineKeyboardButton("💎 شراء Premium", url="https://t.me/support")],
                [InlineKeyboardButton("🔙 العودة", callback_data="main_menu")]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    async def create_task_start(self, query: CallbackQuery):
        """بدء إنشاء مهمة جديدة"""
        user_id = query.from_user.id
        
        # فحص حالة Premium للمهام المتعددة
        is_premium = await self.db.check_premium(user_id)
        user_tasks = await self.db.get_user_tasks(user_id)
        
        if not is_premium and len(user_tasks) >= 3:  # حد 3 مهام للمستخدمين العاديين
            text = """
⚠️ <b>وصلت للحد الأقصى من المهام</b>

المستخدمون العاديون يمكنهم إنشاء حتى 3 مهام فقط.

💎 ترقية إلى Premium للحصول على مهام غير محدودة!
            """
            keyboard = [
                [InlineKeyboardButton("💎 ترقية Premium", callback_data="premium_info")],
                [InlineKeyboardButton("🔙 العودة", callback_data="tasks_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            return
        
        text = """
➕ <b>إنشاء مهمة جديدة</b>

اختر نوع البوت الذي تريد استخدامه:

🤖 <b>Bot Token:</b> استخدام توكن البوت العادي
👤 <b>Userbot:</b> استخدام حساب المستخدم (Telethon)

💡 <b>نصيحة:</b> Bot Token أسهل في الإعداد، بينما Userbot يوفر مرونة أكثر.
        """
        
        await query.edit_message_text(
            text,
            reply_markup=TaskKeyboards.task_type_selection(),
            parse_mode='HTML'
        )
    
    async def show_my_tasks(self, query: CallbackQuery):
        """عرض مهام المستخدم"""
        user_id = query.from_user.id
        tasks = await self.db.get_user_tasks(user_id)
        
        if not tasks:
            text = """
📋 <b>مهامك</b>

لا توجد مهام حالياً.

➕ أنشئ مهمة جديدة للبدء في توجيه الرسائل!
            """
            keyboard = [
                [InlineKeyboardButton("➕ إنشاء مهمة جديدة", callback_data="create_task")],
                [InlineKeyboardButton("🔙 العودة", callback_data="tasks_menu")]
            ]
        else:
            text = f"📋 <b>مهامك ({len(tasks)})</b>\n\n"
            
            keyboard = []
            for task in tasks[:10]:  # عرض أول 10 مهام
                status_icon = "✅" if task['is_active'] else "⏸️"
                task_name = task['name'][:20] + "..." if len(task['name']) > 20 else task['name']
                
                keyboard.append([
                    InlineKeyboardButton(
                        f"{status_icon} {task_name}",
                        callback_data=f"task_view_{task['id']}"
                    )
                ])
            
            if len(tasks) > 10:
                keyboard.append([
                    InlineKeyboardButton("📄 عرض المزيد", callback_data="tasks_page_1")
                ])
            
            keyboard.extend([
                [InlineKeyboardButton("➕ إنشاء مهمة جديدة", callback_data="create_task")],
                [InlineKeyboardButton("🔙 العودة", callback_data="tasks_menu")]
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    async def handle_task_callback(self, query: CallbackQuery, data: str):
        """معالجة استدعاءات المهام"""
        parts = data.split('_')
        action = parts[1]
        
        if action == "view":
            task_id = int(parts[2])
            await self.show_task_details(query, task_id)
        elif action == "start":
            task_id = int(parts[2])
            await self.start_task(query, task_id)
        elif action == "stop":
            task_id = int(parts[2])
            await self.stop_task(query, task_id)
        elif action == "edit":
            task_id = int(parts[2])
            await self.edit_task_menu(query, task_id)
        elif action == "delete":
            task_id = int(parts[2])
            await self.confirm_delete_task(query, task_id)
        elif action == "stats":
            task_id = int(parts[2])
            await self.show_task_stats(query, task_id)
    
    async def show_task_details(self, query: CallbackQuery, task_id: int):
        """عرض تفاصيل المهمة"""
        user_id = query.from_user.id
        tasks = await self.db.get_user_tasks(user_id)
        task = next((t for t in tasks if t['id'] == task_id), None)
        
        if not task:
            await query.edit_message_text("❌ المهمة غير موجودة")
            return
        
        status = "✅ نشطة" if task['is_active'] else "⏸️ متوقفة"
        forward_type = "📤 توجيه" if task['forward_type'] == 'forward' else "📋 نسخ"
        
        text = f"""
📋 <b>تفاصيل المهمة</b>

📝 الاسم: {task['name']}
📊 الحالة: {status}
🔄 نوع التوجيه: {forward_type}
📤 المصدر: <code>{task['source_chat_id']}</code>
📥 الأهداف: {len(task['target_chat_ids'])} دردشة
📅 تاريخ الإنشاء: {task['created_at'][:10]}
🔄 آخر تحديث: {task['updated_at'][:10]}
        """
        
        await query.edit_message_text(
            text,
            reply_markup=TaskKeyboards.task_actions(task_id),
            parse_mode='HTML'
        )
    
    async def start_task(self, query: CallbackQuery, task_id: int):
        """تشغيل المهمة"""
        user_id = query.from_user.id
        
        if await self.db.update_task(task_id, is_active=True):
            logger.log_task_action(user_id, task_id, "started")
            await query.answer("✅ تم تشغيل المهمة")
            await self.show_task_details(query, task_id)
        else:
            await query.answer("❌ فشل في تشغيل المهمة")
    
    async def stop_task(self, query: CallbackQuery, task_id: int):
        """إيقاف المهمة"""
        user_id = query.from_user.id
        
        if await self.db.update_task(task_id, is_active=False):
            logger.log_task_action(user_id, task_id, "stopped")
            await query.answer("⏸️ تم إيقاف المهمة")
            await self.show_task_details(query, task_id)
        else:
            await query.answer("❌ فشل في إيقاف المهمة")
    
    async def edit_task_menu(self, query: CallbackQuery, task_id: int):
        """قائمة تعديل المهمة"""
        text = """
⚙️ <b>تعديل المهمة</b>

اختر الإعداد الذي تريد تعديله:
        """
        
        await query.edit_message_text(
            text,
            reply_markup=SettingsKeyboards.task_settings(task_id),
            parse_mode='HTML'
        )
    
    async def confirm_delete_task(self, query: CallbackQuery, task_id: int):
        """تأكيد حذف المهمة"""
        text = """
⚠️ <b>تأكيد الحذف</b>

هل أنت متأكد من حذف هذه المهمة؟

❗ هذا الإجراء لا يمكن التراجع عنه.
        """
        
        await query.edit_message_text(
            text,
            reply_markup=ConfirmationKeyboards.confirm_delete("task", task_id),
            parse_mode='HTML'
        )
    
    async def show_task_stats(self, query: CallbackQuery, task_id: int):
        """عرض إحصائيات المهمة"""
        # هذه الوظيفة ستكتمل في المرحلة التالية
        await query.answer("📊 الإح��ائيات ستكون متاحة قريباً")
    
    async def handle_admin_callback(self, query: CallbackQuery, data: str):
        """معالجة استدعاءات الإدارة"""
        # سيتم تطويرها في المرحلة التالية
        await query.answer("👑 لوحة الإدارة ستكون متاحة قريباً")
    
    async def handle_filter_callback(self, query: CallbackQuery, data: str):
        """معالجة استدعاءات الفلاتر"""
        # سيتم تطويرها في المرحلة التالية
        await query.answer("🔍 الفلاتر ستكون متاحة قريباً")
    
    async def handle_setting_callback(self, query: CallbackQuery, data: str):
        """معالجة استدعاءات الإعدادات"""
        # سيتم تطويرها في المرحلة التالية
        await query.answer("⚙️ الإعدادات ستكون متاحة قريباً")
