"""
معالج المستخدمين
User Handler
"""

import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.db_manager import DatabaseManager
from config.settings import Settings, Messages
from utils.decorators import user_required, premium_required

logger = logging.getLogger(__name__)

class UserHandler:
    """معالج أوامر المستخدمين"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.settings = Settings()
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر البدء"""
        user = update.effective_user
        chat = update.effective_chat
        
        # إضافة المستخدم إلى قاعدة البيانات
        await self.db.add_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # فحص إذا كان المستخدم جديد لتفعيل التجربة المجانية
        user_data = await self.db.get_user(user.id)
        if user_data and not user_data['trial_used'] and not user_data['is_premium']:
            await self.db.activate_trial(user.id)
            trial_msg = "\n🎁 تم تفعيل التجربة المجانية لمدة 48 ساعة!"
        else:
            trial_msg = ""
        
        # إنشاء لوحة المفاتيح
        keyboard = [
            [InlineKeyboardButton("📋 إدارة المهام", callback_data="tasks_menu")],
            [InlineKeyboardButton("📊 حالة الحساب", callback_data="account_status")],
            [InlineKeyboardButton("💎 Premium", callback_data="premium_info")],
            [InlineKeyboardButton("📚 المساعدة", callback_data="help_menu")],
            [InlineKeyboardButton("📞 الدعم الفني", url="https://t.me/support")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            Messages.WELCOME + trial_msg,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر المساعدة"""
        await self.db.update_user_activity(update.effective_user.id)
        
        keyboard = [
            [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            Messages.HELP,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    @user_required
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض حالة المستخدم"""
        user_id = update.effective_user.id
        user_data = await self.db.get_user(user_id)
        
        if not user_data:
            await update.message.reply_text("❌ خطأ في الحصول على بيانات المستخدم")
            return
        
        # فحص حالة Premium
        is_premium = await self.db.check_premium(user_id)
        premium_status = "✅ نشط" if is_premium else "❌ غير نشط"
        
        if is_premium and user_data['premium_expires']:
            expires = datetime.fromisoformat(user_data['premium_expires'])
            premium_status += f"\n📅 ينتهي في: {expires.strftime('%Y-%m-%d %H:%M')}"
        
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
📅 تاريخ التسجيل: {datetime.fromisoformat(user_data['created_at']).strftime('%Y-%m-%d')}
⏰ آخر نشاط: {datetime.fromisoformat(user_data['last_active']).strftime('%Y-%m-%d %H:%M')}
        """
        
        keyboard = [
            [InlineKeyboardButton("📋 إدارة المهام", callback_data="tasks_menu")],
            [InlineKeyboardButton("💎 ترقية Premium", callback_data="premium_upgrade")],
            [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            status_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    async def premium_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معلومات Premium"""
        user_id = update.effective_user.id
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
        
        keyboard = []
        if not is_premium:
            user_data = await self.db.get_user(user_id)
            if user_data and not user_data['trial_used']:
                keyboard.append([InlineKeyboardButton("🎁 تفعيل التجربة المجانية", callback_data="activate_trial")])
            keyboard.append([InlineKeyboardButton("💎 شراء Premium", url="https://t.me/support")])
        
        keyboard.append([InlineKeyboardButton("🔙 العودة", callback_data="main_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    async def activate_trial(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تفعيل التجربة المجانية"""
        user_id = update.effective_user.id
        
        if await self.db.activate_trial(user_id):
            text = """
🎉 <b>تم تفعيل التجربة المجانية!</b>

⏰ المدة: 48 ساعة
✨ جميع ميزات Premium متاحة الآن

استمتع بالتجربة! 🚀
            """
        else:
            text = "❌ التجربة المجانية مُستخدمة مسبقاً أو أنت مشترك في Premium"
        
        keyboard = [
            [InlineKeyboardButton("📋 إنشاء مهمة جديدة", callback_data="create_task")],
            [InlineKeyboardButton("🔙 العودة", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
