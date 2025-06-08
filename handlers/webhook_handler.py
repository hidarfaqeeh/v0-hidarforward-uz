"""
معالج الويب هوك
Webhook Handler
"""

import os
import logging
from typing import Optional
from telegram import Bot
from telegram.error import TelegramError
from database.db_manager import DatabaseManager
from config.settings import Settings
from utils.logger import BotLogger

logger = BotLogger()

class WebhookHandler:
    """معالج الويب هوك المتقدم"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.settings = Settings()
        self.webhook_url = None
        self.webhook_secret = None
        
    async def setup_webhook(self):
        """إعداد الويب هوك"""
        try:
            if not self.settings.USE_WEBHOOK:
                logger.logger.info("🔄 وضع Polling مفعل - تم تخطي إعداد الويب هوك")
                return True
            
            if not self.settings.WEBHOOK_URL:
                logger.logger.warning("⚠️ WEBHOOK_URL غير محدد")
                return False
            
            self.webhook_url = self.settings.WEBHOOK_URL
            self.webhook_secret = self.settings.WEBHOOK_SECRET or "webhook_secret_key"
            
            # إنشاء البوت للإعداد
            bot = Bot(token=self.settings.BOT_TOKEN)
            
            # تعيين الويب هوك
            await bot.set_webhook(
                url=self.webhook_url,
                secret_token=self.webhook_secret,
                allowed_updates=[
                    "message",
                    "edited_message", 
                    "channel_post",
                    "edited_channel_post",
                    "callback_query"
                ]
            )
            
            logger.logger.info(f"✅ تم إعداد الويب هوك: {self.webhook_url}")
            return True
            
        except TelegramError as e:
            logger.log_error(e, {
                'function': 'setup_webhook',
                'webhook_url': self.webhook_url
            })
            return False
        except Exception as e:
            logger.log_error(e, {
                'function': 'setup_webhook',
                'webhook_url': self.webhook_url
            })
            return False
    
    async def remove_webhook(self):
        """إزالة الويب هوك"""
        try:
            bot = Bot(token=self.settings.BOT_TOKEN)
            await bot.delete_webhook()
            logger.logger.info("🗑️ تم حذف الويب هوك")
            return True
            
        except Exception as e:
            logger.log_error(e, {'function': 'remove_webhook'})
            return False
    
    async def get_webhook_info(self) -> Optional[dict]:
        """الحصول على معلومات الويب هوك"""
        try:
            bot = Bot(token=self.settings.BOT_TOKEN)
            webhook_info = await bot.get_webhook_info()
            
            return {
                'url': webhook_info.url,
                'has_custom_certificate': webhook_info.has_custom_certificate,
                'pending_update_count': webhook_info.pending_update_count,
                'last_error_date': webhook_info.last_error_date,
                'last_error_message': webhook_info.last_error_message,
                'max_connections': webhook_info.max_connections,
                'allowed_updates': webhook_info.allowed_updates
            }
            
        except Exception as e:
            logger.log_error(e, {'function': 'get_webhook_info'})
            return None
    
    async def validate_webhook_request(self, request_data: dict, secret_token: str) -> bool:
        """التحقق من صحة طلب الويب هوك"""
        try:
            # التحقق من التوكن السري
            if secret_token != self.webhook_secret:
                logger.logger.warning("⚠️ توكن ويب هوك غير صحيح")
                return False
            
            # التحقق من وجود البيانات المطلوبة
            if 'update_id' not in request_data:
                logger.logger.warning("⚠️ بيانات ويب هوك غير صحيحة")
                return False
            
            return True
            
        except Exception as e:
            logger.log_error(e, {
                'function': 'validate_webhook_request',
                'request_data': str(request_data)[:100]
            })
            return False
    
    def get_webhook_config(self) -> dict:
        """الحصول على إعدادات الويب هوك"""
        return {
            'enabled': self.settings.USE_WEBHOOK,
            'url': self.webhook_url,
            'secret_configured': bool(self.webhook_secret),
            'port': int(os.environ.get("PORT", 8443))
        }
    
    async def test_webhook_connection(self) -> bool:
        """اختبار اتصال الويب هوك"""
        try:
            if not self.settings.USE_WEBHOOK:
                return True
            
            webhook_info = await self.get_webhook_info()
            if not webhook_info:
                return False
            
            # فحص إذا كان الويب هوك مُعد بشكل صحيح
            if webhook_info['url'] != self.webhook_url:
                logger.logger.error(f"❌ عنوان الويب هوك غير متطابق: {webhook_info['url']} != {self.webhook_url}")
                return False
            
            # فحص الأخطاء الأخيرة
            if webhook_info['last_error_message']:
                logger.logger.warning(f"⚠️ آخر خطأ في الويب هوك: {webhook_info['last_error_message']}")
            
            # فحص عدد التحديثات المعلقة
            if webhook_info['pending_update_count'] > 100:
                logger.logger.warning(f"⚠️ عدد كبير من التحديثات المعلقة: {webhook_info['pending_update_count']}")
            
            logger.logger.info("✅ اختبار الويب هوك نجح")
            return True
            
        except Exception as e:
            logger.log_error(e, {'function': 'test_webhook_connection'})
            return False
    
    async def switch_to_polling(self):
        """التبديل إلى وضع Polling"""
        try:
            await self.remove_webhook()
            logger.logger.info("🔄 تم التبديل إلى وضع Polling")
            return True
            
        except Exception as e:
            logger.log_error(e, {'function': 'switch_to_polling'})
            return False
    
    async def switch_to_webhook(self, webhook_url: str):
        """التبديل إلى وضع Webhook"""
        try:
            self.webhook_url = webhook_url
            success = await self.setup_webhook()
            
            if success:
                logger.logger.info(f"🔄 تم التبديل إلى وضع Webhook: {webhook_url}")
            
            return success
            
        except Exception as e:
            logger.log_error(e, {
                'function': 'switch_to_webhook',
                'webhook_url': webhook_url
            })
            return False
    
    def get_webhook_stats(self) -> dict:
        """الحصول على إحصائيات الويب هوك"""
        return {
            'mode': 'webhook' if self.settings.USE_WEBHOOK else 'polling',
            'url': self.webhook_url if self.settings.USE_WEBHOOK else None,
            'configured': bool(self.webhook_url and self.webhook_secret),
            'last_check': None  # سيتم إضافة هذا لاحقاً
        }

class WebhookServer:
    """خادم الويب هوك المدمج"""
    
    def __init__(self, webhook_handler: WebhookHandler):
        self.webhook_handler = webhook_handler
        self.app = None
        
    async def create_app(self):
        """إنشاء تطبيق الويب"""
        try:
            from aiohttp import web
            
            app = web.Application()
            
            # إضافة المسارات
            app.router.add_post('/webhook', self.handle_webhook)
            app.router.add_get('/health', self.health_check)
            app.router.add_get('/webhook/info', self.webhook_info)
            
            self.app = app
            return app
            
        except ImportError:
            logger.logger.error("❌ aiohttp غير مثبت - مطلوب للويب هوك")
            return None
        except Exception as e:
            logger.log_error(e, {'function': 'create_app'})
            return None
    
    async def handle_webhook(self, request):
        """معالجة طلبات الويب هوك"""
        try:
            from aiohttp import web
            
            # الحصول على البيانات
            data = await request.json()
            
            # الحصول على التوكن السري من الهيدر
            secret_token = request.headers.get('X-Telegram-Bot-Api-Secret-Token', '')
            
            # التحقق من صحة الطلب
            if not await self.webhook_handler.validate_webhook_request(data, secret_token):
                return web.Response(status=403, text="Forbidden")
            
            # معالجة التحديث
            # هنا سيتم تمرير البيانات لمعالج التحديثات
            logger.logger.debug(f"تم استلام تحديث ويب هوك: {data.get('update_id')}")
            
            return web.Response(status=200, text="OK")
            
        except Exception as e:
            logger.log_error(e, {'function': 'handle_webhook'})
            return web.Response(status=500, text="Internal Server Error")
    
    async def health_check(self, request):
        """فحص صحة الخادم"""
        try:
            from aiohttp import web
            
            health_data = {
                'status': 'healthy',
                'webhook_configured': self.webhook_handler.settings.USE_WEBHOOK,
                'timestamp': str(datetime.now())
            }
            
            return web.json_response(health_data)
            
        except Exception as e:
            logger.log_error(e, {'function': 'health_check'})
            return web.Response(status=500, text="Internal Server Error")
    
    async def webhook_info(self, request):
        """معلومات الويب هوك"""
        try:
            from aiohttp import web
            
            webhook_info = await self.webhook_handler.get_webhook_info()
            webhook_stats = self.webhook_handler.get_webhook_stats()
            
            info_data = {
                'webhook_info': webhook_info,
                'webhook_stats': webhook_stats,
                'timestamp': str(datetime.now())
            }
            
            return web.json_response(info_data)
            
        except Exception as e:
            logger.log_error(e, {'function': 'webhook_info'})
            return web.Response(status=500, text="Internal Server Error")
    
    async def start_server(self, host='0.0.0.0', port=8443):
        """بدء تشغيل الخادم"""
        try:
            from aiohttp import web
            
            if not self.app:
                await self.create_app()
            
            if not self.app:
                return False
            
            runner = web.AppRunner(self.app)
            await runner.setup()
            
            site = web.TCPSite(runner, host, port)
            await site.start()
            
            logger.logger.info(f"🌐 خادم الويب هوك يعمل على {host}:{port}")
            return True
            
        except Exception as e:
            logger.log_error(e, {
                'function': 'start_server',
                'host': host,
                'port': port
            })
            return False
