"""
معالج المهام المتقدم
Advanced Task Handler
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from database.db_manager import DatabaseManager
from config.keyboards import TaskKeyboards, ConfirmationKeyboards
from config.messages import Messages  # هذا هو الصحيح
from utils.decorators import user_required, premium_required, error_handler, rate_limit
from utils.helpers import DataValidator, TextProcessor
from utils.logger import BotLogger

logger = BotLogger()

# حالات المحادثة
(TASK_NAME, TASK_SOURCE, TASK_TARGETS, TASK_TYPE, 
 TASK_SETTINGS, CONFIRM_TASK) = range(6)

class TaskHandler:
    """معالج المهام المتقدم"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.user_sessions = {}  # جلسات المستخدمين لإنشاء المهام
    
    @user_required
    @error_handler
    async def list_tasks(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض قائمة المهام"""
        user_id = update.effective_user.id
        tasks = await self.db.get_user_tasks(user_id)
        
        if not tasks:
            text = """
📋 <b>مهامك</b>

لا توجد مهام حالياً.

➕ أنشئ مهمة جديدة للبدء في توجيه الرسائل!

💡 <b>نصائح:</b>
• يمكنك إنشاء حتى 3 مهام مجاناً
• المستخدمون Premium يحصلون على مهام غير محدودة
• كل مهمة يمكنها توجيه من مصدر واحد لعدة أهداف
            """
            
            keyboard = [
                [InlineKeyboardButton("➕ إنشاء مهمة جديدة", callback_data="create_task")],
                [InlineKeyboardButton("💎 ترقية Premium", callback_data="premium_info")],
                [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu")]
            ]
        else:
            text = f"📋 <b>مهامك ({len(tasks)})</b>\n\n"
            
            keyboard = []
            for i, task in enumerate(tasks[:10], 1):
                status_icon = "✅" if task['is_active'] else "⏸️"
                task_name = task['name'][:25] + "..." if len(task['name']) > 25 else task['name']
                
                # إحصائيات سريعة
                targets_count = len(task['target_chat_ids'])
                
                text += f"{i}. {status_icon} <b>{task['name']}</b>\n"
                text += f"   📤 المصدر: <code>{task['source_chat_id']}</code>\n"
                text += f"   📥 الأهداف: {targets_count} دردشة\n"
                text += f"   🔄 النوع: {task['forward_type']}\n\n"
                
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
                [InlineKeyboardButton("⚙️ إعدادات عامة", callback_data="tasks_settings")],
                [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu")]
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    @user_required
    @rate_limit(max_calls=3, window_seconds=300)  # 3 مهام كل 5 دقائق
    async def create_task(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """بدء إنشاء مهمة جديدة"""
        user_id = update.effective_user.id
        
        # فحص حالة Premium للمهام المتعددة
        is_premium = await self.db.check_premium(user_id)
        user_tasks = await self.db.get_user_tasks(user_id)
        
        if not is_premium and len(user_tasks) >= 3:
            await update.message.reply_text(
                """
⚠️ <b>وصلت للحد الأقصى من المهام</b>

المستخدمون العاديون يمكنهم إنشاء حتى 3 مهام فقط.

💎 ترقية إلى Premium للحصول على:
• مهام غير محدودة
• فلاتر متقدمة
• جدولة الرسائل
• دعم فني مميز

💰 اتصل بنا للحصول على Premium!
                """,
                parse_mode='HTML'
            )
            return ConversationHandler.END
        
        # بدء جلسة إنشاء مهمة جديدة
        self.user_sessions[user_id] = {
            'step': 'task_type',
            'data': {},
            'created_at': datetime.now()
        }
        
        text = """
➕ <b>إنشاء مهمة جديدة</b>

اختر نوع البوت الذي تريد استخدامه:

🤖 <b>Bot Token:</b>
• سهل الإعداد
• يتطلب إضافة البوت للقنوات
• مناسب للمبتدئين

👤 <b>Userbot:</b>
• يستخدم حسابك الشخصي
• لا يحتاج إضافة بوت
• مرونة أكثر في الوصول

💡 <b>أيهما تختار؟</b>
        """
        
        keyboard = [
            [InlineKeyboardButton("🤖 Bot Token", callback_data="task_type_bot")],
            [InlineKeyboardButton("👤 Userbot", callback_data="task_type_userbot")],
            [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_task_creation")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
        return TASK_TYPE
    
    async def handle_task_type_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة اختيار نوع المهمة"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        if user_id not in self.user_sessions:
            await query.edit_message_text("❌ انتهت الجلسة. يرجى البدء من جديد.")
            return ConversationHandler.END
        
        if query.data == "task_type_bot":
            task_type = "bot_token"
            type_name = "Bot Token"
        elif query.data == "task_type_userbot":
            task_type = "userbot"
            type_name = "Userbot"
        else:
            await query.edit_message_text("❌ تم إلغاء إنشاء المهمة.")
            return ConversationHandler.END
        
        self.user_sessions[user_id]['data']['task_type'] = task_type
        
        text = f"""
📝 <b>إنشاء مهمة {type_name}</b>

الآن أدخل اسماً للمهمة:

💡 <b>نصائح لاختيار الاسم:</b>
• اختر اسماً وصفياً (مثل: "أخبار التقنية")
• تجنب الأسماء الطويلة جداً
• يمكن تغيير الاسم لاحقاً

✍️ أرسل اسم المهمة:
        """
        
        await query.edit_message_text(text, parse_mode='HTML')
        
        return TASK_NAME
    
    async def handle_task_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة اسم المهمة"""
        user_id = update.effective_user.id
        task_name = update.message.text.strip()
        
        if user_id not in self.user_sessions:
            await update.message.reply_text("❌ انتهت الجلسة. يرجى البدء من جديد.")
            return ConversationHandler.END
        
        # التحقق من صحة الاسم
        if len(task_name) < 3:
            await update.message.reply_text(
                "❌ اسم المهمة قصير جداً. يجب أن يكون 3 أحرف على الأقل."
            )
            return TASK_NAME
        
        if len(task_name) > 50:
            await update.message.reply_text(
                "❌ اسم المهمة طويل جداً. يجب أن يكون 50 حرف كحد أقصى."
            )
            return TASK_NAME
        
        self.user_sessions[user_id]['data']['name'] = task_name
        
        text = f"""
📤 <b>تحديد المصدر</b>

المهمة: <b>{task_name}</b>

الآن أدخل معرف القناة أو المجموعة المصدر:

💡 <b>طرق الحصول على المعرف:</b>
• إعادة توجيه رسالة من القناة للبوت
• استخدام @userinfobot
• نسخ الرابط وأخذ الجزء الأخير

📝 <b>أمثلة على التنسيقات المقبولة:</b>
• <code>-1001234567890</code> (معرف رقمي)
• <code>@channel_username</code> (اسم المستخدم)
• <code>https://t.me/channel_name</code> (رابط)

✍️ أرسل معرف المصدر:
        """
        
        await update.message.reply_text(text, parse_mode='HTML')
        
        return TASK_SOURCE
    
    async def handle_task_source(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة مصدر المهمة"""
        user_id = update.effective_user.id
        source_input = update.message.text.strip()
        
        if user_id not in self.user_sessions:
            await update.message.reply_text("❌ انتهت الجلسة. يرجى البدء من جديد.")
            return ConversationHandler.END
        
        # تحويل المدخل إلى معرف صحيح
        source_chat_id = await self.parse_chat_identifier(source_input)
        
        if not source_chat_id:
            await update.message.reply_text(
                """
❌ معرف القناة غير صحيح.

💡 <b>تأكد من:</b>
• كتابة المعرف بالتنسيق الصحيح
• أن القناة موجودة وعامة
• أن لديك صلاحية الوصول للقناة

✍️ أعد إدخال معرف المصدر:
                """,
                parse_mode='HTML'
            )
            return TASK_SOURCE
        
        self.user_sessions[user_id]['data']['source_chat_id'] = source_chat_id
        
        # إضافة القناة لقاعدة البيانات
        await self.db.add_chat(source_chat_id, "source", f"Source for {self.user_sessions[user_id]['data']['name']}")
        
        text = f"""
📥 <b>تحديد الأهداف</b>

المهمة: <b>{self.user_sessions[user_id]['data']['name']}</b>
المصدر: <code>{source_chat_id}</code>

الآن أدخل معرفات القنوات أو المجموعات الهدف:

💡 <b>يمكنك إدخال:</b>
• معرف واحد في كل رسالة
• عدة معرفات مفصولة بفاصلة
• خليط من المعرفات والأسماء

📝 <b>مثال:</b>
<code>-1001234567890, @target_channel, https://t.me/another_channel</code>

✍️ أرسل معرفات الأهداف:
        """
        
        await update.message.reply_text(text, parse_mode='HTML')
        
        return TASK_TARGETS
    
    async def handle_task_targets(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة أهداف المهمة"""
        user_id = update.effective_user.id
        targets_input = update.message.text.strip()
        
        if user_id not in self.user_sessions:
            await update.message.reply_text("❌ انتهت الجلسة. يرجى البدء من جديد.")
            return ConversationHandler.END
        
        # تحليل معرفات الأهداف
        target_identifiers = [t.strip() for t in targets_input.split(',')]
        target_chat_ids = []
        invalid_targets = []
        
        for identifier in target_identifiers:
            if not identifier:
                continue
                
            chat_id = await self.parse_chat_identifier(identifier)
            if chat_id:
                target_chat_ids.append(chat_id)
                # إضافة القناة لقاعدة البيانات
                await self.db.add_chat(chat_id, "target", f"Target for {self.user_sessions[user_id]['data']['name']}")
            else:
                invalid_targets.append(identifier)
        
        if not target_chat_ids:
            await update.message.reply_text(
                """
❌ لم يتم العثور على أهداف صحيحة.

💡 تأكد من صحة المعرفات وأعد المحاولة.

✍️ أرسل معرفات الأهداف:
                """,
                parse_mode='HTML'
            )
            return TASK_TARGETS
        
        self.user_sessions[user_id]['data']['target_chat_ids'] = target_chat_ids
        
        # رسالة تأكيد مع الأهداف غير الصحيحة إن وجدت
        warning_text = ""
        if invalid_targets:
            warning_text = f"\n⚠️ <b>تم تجاهل:</b> {', '.join(invalid_targets[:3])}"
            if len(invalid_targets) > 3:
                warning_text += f" و {len(invalid_targets) - 3} آخرين"
        
        text = f"""
⚙️ <b>إعدادات التوجيه</b>

المهمة: <b>{self.user_sessions[user_id]['data']['name']}</b>
المصدر: <code>{self.user_sessions[user_id]['data']['source_chat_id']}</code>
الأهداف: {len(target_chat_ids)} دردشة{warning_text}

اختر نوع التوجيه:

📤 <b>توجيه (Forward):</b>
• يظهر "Forwarded from" 
• يحافظ على المصدر الأصلي
• أسرع في المعالجة

📋 <b>نسخ (Copy):</b>
• لا يظهر المصدر الأصلي
• يبدو كرسالة جديدة
• يمكن تعديل المحتوى
        """
        
        keyboard = [
            [InlineKeyboardButton("📤 توجيه (Forward)", callback_data="forward_type_forward")],
            [InlineKeyboardButton("📋 نسخ (Copy)", callback_data="forward_type_copy")],
            [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_task_creation")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
        return TASK_SETTINGS
    
    async def handle_forward_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة نوع التوجيه"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        if user_id not in self.user_sessions:
            await query.edit_message_text("❌ انتهت الجلسة. يرجى البدء من جديد.")
            return ConversationHandler.END
        
        if query.data == "forward_type_forward":
            forward_type = "forward"
            type_name = "توجيه"
        elif query.data == "forward_type_copy":
            forward_type = "copy"
            type_name = "نسخ"
        else:
            await query.edit_message_text("❌ تم إلغاء إنشاء المهمة.")
            return ConversationHandler.END
        
        self.user_sessions[user_id]['data']['forward_type'] = forward_type
        
        # عرض ملخص المهمة للتأكيد
        session_data = self.user_sessions[user_id]['data']
        
        text = f"""
✅ <b>تأكيد إنشاء المهمة</b>

📝 <b>الاسم:</b> {session_data['name']}
🤖 <b>النوع:</b> {session_data['task_type'].replace('_', ' ').title()}
📤 <b>المصدر:</b> <code>{session_data['source_chat_id']}</code>
📥 <b>الأهداف:</b> {len(session_data['target_chat_ids'])} دردشة
🔄 <b>طريقة التوجيه:</b> {type_name}

⚙️ <b>الإعدادات الافتراضية:</b>
• الحالة: نشطة
• الفلاتر: بدون فلاتر
• التأخير: بدون تأخير
• ساعات العمل: 24/7

💡 يمكنك تعديل هذه الإعدادات لاحقاً من قائمة المهام.

هل تريد إنشاء المهمة؟
        """
        
        keyboard = [
            [InlineKeyboardButton("✅ إنشاء المهمة", callback_data="confirm_create_task")],
            [InlineKeyboardButton("⚙️ إعدادات متقدمة", callback_data="advanced_task_settings")],
            [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_task_creation")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
        return CONFIRM_TASK
    
    async def confirm_create_task(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تأكيد إنشاء المهمة"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        if user_id not in self.user_sessions:
            await query.edit_message_text("❌ انتهت الجلسة. يرجى البدء من جديد.")
            return ConversationHandler.END
        
        if query.data == "cancel_task_creation":
            del self.user_sessions[user_id]
            await query.edit_message_text("❌ تم إلغاء إنشاء المهمة.")
            return ConversationHandler.END
        
        session_data = self.user_sessions[user_id]['data']
        
        try:
            # إنشاء المهمة في قاعدة البيانات
            task_id = await self.db.create_task(
                user_id=user_id,
                name=session_data['name'],
                source_chat_id=session_data['source_chat_id'],
                target_chat_ids=session_data['target_chat_ids'],
                settings={
                    'task_type': session_data['task_type'],
                    'forward_type': session_data['forward_type'],
                    'filters': {},
                    'delay_seconds': 0,
                    'working_hours': {'enabled': False},
                    'text_processing': {
                        'add_header': '',
                        'add_footer': '',
                        'remove_links': False,
                        'remove_hashtags': False,
                        'remove_emojis': False,
                        'remove_formatting': False,
                        'text_replacements': {}
                    },
                    'advanced': {
                        'pin_messages': False,
                        'reply_to_message': True,
                        'char_limit': 0,
                        'custom_buttons': []
                    }
                }
            )
            
            # تسجيل العملية
            logger.log_task_action(user_id, task_id, "created", session_data)
            
            # تنظيف الجلسة
            del self.user_sessions[user_id]
            
            text = f"""
🎉 <b>تم إنشاء المهمة بنجاح!</b>

📝 اسم المهمة: <b>{session_data['name']}</b>
🆔 معرف المهمة: <code>{task_id}</code>
✅ الحالة: نشطة

🚀 <b>المهمة تعمل الآن!</b>

💡 <b>الخطوات التالية:</b>
• تأكد من إضافة البوت للقنوات (إذا كنت تستخدم Bot Token)
• راقب الرسائل المُوجهة
• عدّل الإعدادات حسب الحاجة

📊 يمكنك مراقبة أداء المهمة من قائمة "مهامي".
            """
            
            keyboard = [
                [InlineKeyboardButton("📋 عرض المهمة", callback_data=f"task_view_{task_id}")],
                [InlineKeyboardButton("⚙️ تعديل الإعدادات", callback_data=f"task_edit_{task_id}")],
                [InlineKeyboardButton("📊 مهامي", callback_data="my_tasks")],
                [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.log_error(e, {'user_id': user_id, 'session_data': session_data})
            await query.edit_message_text(
                "❌ حدث خطأ أثناء إنشاء المهمة. يرجى المحاولة مرة أخرى."
            )
        
        return ConversationHandler.END
    
    @user_required
    @error_handler
    async def edit_task(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تعديل مهمة موجودة"""
        if not context.args:
            await update.message.reply_text(
                "❌ يرجى تحديد معرف المهمة.\n\nمثال: <code>/edittask 123</code>",
                parse_mode='HTML'
            )
            return
        
        try:
            task_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ معرف المهمة يجب أن يكون رقماً.")
            return
        
        user_id = update.effective_user.id
        tasks = await self.db.get_user_tasks(user_id)
        task = next((t for t in tasks if t['id'] == task_id), None)
        
        if not task:
            await update.message.reply_text("❌ المهمة غير موجودة أو ليس لديك صلاحية للوصول إليها.")
            return
        
        # عرض قائمة التعديل
        await self.show_edit_menu(update, task)
    
    async def show_edit_menu(self, update: Update, task: Dict[str, Any]):
        """عرض قائمة تعديل المهمة"""
        text = f"""
⚙️ <b>تعديل المهمة: {task['name']}</b>

اختر الإعداد الذي تريد تعديله:

📊 <b>الحالة الحالية:</b>
• الحالة: {'✅ نشطة' if task['is_active'] else '⏸️ متوقفة'}
• نوع التوجيه: {task['forward_type']}
• المصدر: <code>{task['source_chat_id']}</code>
• الأهداف: {len(task['target_chat_ids'])} دردشة
        """
        
        keyboard = [
            [
                InlineKeyboardButton("📝 تغيير الاسم", callback_data=f"edit_name_{task['id']}"),
                InlineKeyboardButton("🔄 نوع التوجيه", callback_data=f"edit_forward_type_{task['id']}")
            ],
            [
                InlineKeyboardButton("📤 تغيير المصدر", callback_data=f"edit_source_{task['id']}"),
                InlineKeyboardButton("📥 تعديل الأهداف", callback_data=f"edit_targets_{task['id']}")
            ],
            [
                InlineKeyboardButton("🔍 الفلاتر", callback_data=f"edit_filters_{task['id']}"),
                InlineKeyboardButton("⏱️ التأخير", callback_data=f"edit_delay_{task['id']}")
            ],
            [
                InlineKeyboardButton("📝 معالجة النصوص", callback_data=f"edit_text_processing_{task['id']}"),
                InlineKeyboardButton("🕐 ساعات العمل", callback_data=f"edit_working_hours_{task['id']}")
            ],
            [
                InlineKeyboardButton("⚙️ إعدادات متقدمة", callback_data=f"edit_advanced_{task['id']}"),
                InlineKeyboardButton("📊 الإحصائيات", callback_data=f"task_stats_{task['id']}")
            ],
            [
                InlineKeyboardButton("🗑️ حذف المهمة", callback_data=f"delete_task_{task['id']}"),
                InlineKeyboardButton("🔙 العودة", callback_data="my_tasks")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    @user_required
    @error_handler
    async def delete_task(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """حذف مهمة"""
        if not context.args:
            await update.message.reply_text(
                "❌ يرجى تحديد معرف المهمة.\n\nمثال: <code>/deltask 123</code>",
                parse_mode='HTML'
            )
            return
        
        try:
            task_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ معرف المهمة يجب أن يكون رقماً.")
            return
        
        user_id = update.effective_user.id
        
        # التأكد من وجود المهمة وملكية المستخدم لها
        tasks = await self.db.get_user_tasks(user_id)
        task = next((t for t in tasks if t['id'] == task_id), None)
        
        if not task:
            await update.message.reply_text("❌ المهمة غير موجودة أو ليس لديك صلاحية لحذفها.")
            return
        
        # حذف المهمة
        if await self.db.delete_task(task_id, user_id):
            logger.log_task_action(user_id, task_id, "deleted", {'task_name': task['name']})
            
            await update.message.reply_text(
                f"✅ تم حذف المهمة '{task['name']}' بنجاح.",
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text("❌ فشل في حذف المهمة. يرجى المحاولة مرة أخرى.")
    
    async def parse_chat_identifier(self, identifier: str) -> Optional[int]:
        """تحليل معرف الدردشة من أشكال مختلفة"""
        identifier = identifier.strip()
        
        # إذا كان رقماً مباشراً
        if identifier.lstrip('-').isdigit():
            return int(identifier)
        
        # إذا كان اسم مستخدم
        if identifier.startswith('@'):
            username = identifier[1:]
            try:
                # محاولة الحصول على معرف الدردشة (يحتاج bot instance)
                # سيتم تطويرها لاحقاً مع API calls
                return None
            except Exception:
                return None
        
        # إذا كان رابط تلغرام
        if 't.me/' in identifier:
            username = identifier.split('/')[-1]
            if username.startswith('@'):
                username = username[1:]
            try:
                # محاولة الحصول على معرف الدردشة
                # سيتم تطويرها لاحقاً مع API calls
                return None
            except Exception:
                return None
        
        # محاولة تحويل مباشر للرقم
        try:
            return int(identifier)
        except ValueError:
            return None
    
    async def get_task_statistics(self, task_id: int) -> Dict[str, Any]:
        """الحصول على إحصائيات المهمة"""
        # سيتم تطويرها في المرحلة التالية مع نظام التوجيه
        return {
            'total_messages': 0,
            'successful_forwards': 0,
            'failed_forwards': 0,
            'last_activity': None
        }
    
    def cleanup_expired_sessions(self):
        """تنظيف الجلسات المنتهية الصلاحية"""
        current_time = datetime.now()
        expired_users = []
        
        for user_id, session in self.user_sessions.items():
            if (current_time - session['created_at']).total_seconds() > 1800:  # 30 دقيقة
                expired_users.append(user_id)
        
        for user_id in expired_users:
            del self.user_sessions[user_id]
