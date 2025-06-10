"""
خدمة التحليلات والإحصائيات المتقدمة
Advanced Analytics Service
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from database.db_manager import DatabaseManager
from utils.helpers import FormatHelper
from utils.logger import BotLogger

logger = BotLogger()

class AnalyticsService:
    """خدمة التحليلات الشاملة"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    async def track_event(self, user_id: int, event_type: str, event_name: str, 
                         properties: Dict[str, Any] = None, session_id: str = None):
        """تتبع حدث"""
        query = """
        INSERT INTO analytics_events 
        (user_id, event_type, event_name, properties, session_id, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        
        self.db.execute_update(query, (
            user_id,
            event_type,
            event_name,
            json.dumps(properties or {}),
            session_id,
            datetime.now()
        ))
    
    async def record_metric(self, metric_name: str, metric_value: float, 
                           dimensions: Dict[str, Any] = None):
        """تسجيل مقياس"""
        query = """
        INSERT INTO analytics_metrics 
        (metric_name, metric_value, dimensions, recorded_at)
        VALUES (?, ?, ?, ?)
        """
        
        self.db.execute_update(query, (
            metric_name,
            metric_value,
            json.dumps(dimensions or {}),
            datetime.now()
        ))
    
    async def get_user_analytics(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """الحصول على تحليلات المستخدم"""
        start_date = datetime.now() - timedelta(days=days)
        
        # إحصائيات الأحداث
        events_query = """
        SELECT event_type, event_name, COUNT(*) as count
        FROM analytics_events 
        WHERE user_id = ? AND timestamp >= ?
        GROUP BY event_type, event_name
        ORDER BY count DESC
        """
        events = self.db.execute_query(events_query, (user_id, start_date))
        
        # إحصائيات المهام
        tasks_stats = await self.get_user_task_analytics(user_id, days)
        
        # إحصائيات الاستخدام
        usage_stats = await self.get_user_usage_analytics(user_id, days)
        
        return {
            'user_id': user_id,
            'period_days': days,
            'events': events,
            'tasks': tasks_stats,
            'usage': usage_stats,
            'generated_at': datetime.now().isoformat()
        }
    
    async def get_user_task_analytics(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """تحليلات مهام المستخدم"""
        start_date = datetime.now() - timedelta(days=days)
        
        # إحصائيات المهام
        tasks_query = """
        SELECT 
            COUNT(*) as total_tasks,
            SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_tasks,
            AVG(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as activity_rate
        FROM tasks 
        WHERE user_id = ? AND created_at >= ?
        """
        tasks_result = self.db.execute_query(tasks_query, (user_id, start_date))
        
        # إحصائيات الرسائل
        messages_query = """
        SELECT 
            COUNT(*) as total_messages,
            COUNT(DISTINCT DATE(m.forwarded_at)) as active_days
        FROM messages m
        JOIN tasks t ON m.task_id = t.id
        WHERE t.user_id = ? AND m.forwarded_at >= ?
        """
        messages_result = self.db.execute_query(messages_query, (user_id, start_date))
        
        # أداء المهام
        performance_query = """
        SELECT 
            t.id,
            t.name,
            COUNT(m.id) as message_count,
            MIN(m.forwarded_at) as first_message,
            MAX(m.forwarded_at) as last_message
        FROM tasks t
        LEFT JOIN messages m ON t.id = m.task_id
        WHERE t.user_id = ? AND t.created_at >= ?
        GROUP BY t.id, t.name
        ORDER BY message_count DESC
        """
        performance_result = self.db.execute_query(performance_query, (user_id, start_date))
        
        return {
            'summary': tasks_result[0] if tasks_result else {},
            'messages': messages_result[0] if messages_result else {},
            'performance': performance_result
        }
    
    async def get_user_usage_analytics(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """تحليلات استخدام المستخدم"""
        start_date = datetime.now() - timedelta(days=days)
        
        # أنماط الاستخدام اليومية
        daily_usage_query = """
        SELECT 
            DATE(timestamp) as date,
            COUNT(*) as events_count,
            COUNT(DISTINCT event_type) as unique_event_types
        FROM analytics_events 
        WHERE user_id = ? AND timestamp >= ?
        GROUP BY DATE(timestamp)
        ORDER BY date
        """
        daily_usage = self.db.execute_query(daily_usage_query, (user_id, start_date))
        
        # الميزات الأكثر استخداماً
        features_query = """
        SELECT 
            event_name,
            COUNT(*) as usage_count,
            COUNT(DISTINCT DATE(timestamp)) as days_used
        FROM analytics_events 
        WHERE user_id = ? AND timestamp >= ?
        GROUP BY event_name
        ORDER BY usage_count DESC
        LIMIT 10
        """
        top_features = self.db.execute_query(features_query, (user_id, start_date))
        
        # أوقات النشاط
        activity_hours_query = """
        SELECT 
            strftime('%H', timestamp) as hour,
            COUNT(*) as activity_count
        FROM analytics_events 
        WHERE user_id = ? AND timestamp >= ?
        GROUP BY strftime('%H', timestamp)
        ORDER BY hour
        """
        activity_hours = self.db.execute_query(activity_hours_query, (user_id, start_date))
        
        return {
            'daily_usage': daily_usage,
            'top_features': top_features,
            'activity_hours': activity_hours
        }
    
    async def get_system_analytics(self, days: int = 30) -> Dict[str, Any]:
        """تحليلات النظام العامة"""
        start_date = datetime.now() - timedelta(days=days)
        
        # إحصائيات المستخدمين
        users_stats = await self.get_users_analytics(start_date)
        
        # إحصائيات المهام
        tasks_stats = await self.get_tasks_analytics(start_date)
        
        # إحصائيات الأداء
        performance_stats = await self.get_performance_analytics(start_date)
        
        # إحصائيات الأخطاء
        errors_stats = await self.get_errors_analytics(start_date)
        
        return {
            'period_days': days,
            'users': users_stats,
            'tasks': tasks_stats,
            'performance': performance_stats,
            'errors': errors_stats,
            'generated_at': datetime.now().isoformat()
        }
    
    async def get_users_analytics(self, start_date: datetime) -> Dict[str, Any]:
        """تحليلات المستخدمين"""
        # إجمالي المستخدمين
        total_users_query = "SELECT COUNT(*) as count FROM users"
        total_users = self.db.execute_query(total_users_query)[0]['count']
        
        # مستخدمين جدد
        new_users_query = "SELECT COUNT(*) as count FROM users WHERE created_at >= ?"
        new_users = self.db.execute_query(new_users_query, (start_date,))[0]['count']
        
        # مستخدمين نشطين
        active_users_query = """
        SELECT COUNT(DISTINCT user_id) as count 
        FROM analytics_events 
        WHERE timestamp >= ?
        """
        active_users = self.db.execute_query(active_users_query, (start_date,))[0]['count']
        
        # مستخدمي Premium
        premium_users_query = "SELECT COUNT(*) as count FROM users WHERE is_premium = 1"
        premium_users = self.db.execute_query(premium_users_query)[0]['count']
        
        # معدل الاحتفاظ
        retention_query = """
        SELECT 
            COUNT(CASE WHEN last_active >= ? THEN 1 END) * 100.0 / COUNT(*) as retention_rate
        FROM users 
        WHERE created_at < ?
        """
        week_ago = datetime.now() - timedelta(days=7)
        retention = self.db.execute_query(retention_query, (week_ago, start_date))
        retention_rate = retention[0]['retention_rate'] if retention else 0
        
        return {
            'total_users': total_users,
            'new_users': new_users,
            'active_users': active_users,
            'premium_users': premium_users,
            'retention_rate': round(retention_rate, 2)
        }
    
    async def get_tasks_analytics(self, start_date: datetime) -> Dict[str, Any]:
        """تحليلات المهام"""
        # إجمالي المهام
        total_tasks_query = "SELECT COUNT(*) as count FROM tasks"
        total_tasks = self.db.execute_query(total_tasks_query)[0]['count']
        
        # مهام جديدة
        new_tasks_query = "SELECT COUNT(*) as count FROM tasks WHERE created_at >= ?"
        new_tasks = self.db.execute_query(new_tasks_query, (start_date,))[0]['count']
        
        # مهام نشطة
        active_tasks_query = "SELECT COUNT(*) as count FROM tasks WHERE is_active = 1"
        active_tasks = self.db.execute_query(active_tasks_query)[0]['count']
        
        # إحصائيات الرسائل
        messages_stats_query = """
        SELECT 
            COUNT(*) as total_messages,
            COUNT(DISTINCT task_id) as tasks_with_messages,
            AVG(CASE WHEN task_id IS NOT NULL THEN 1 ELSE 0 END) as avg_messages_per_task
        FROM messages 
        WHERE forwarded_at >= ?
        """
        messages_stats = self.db.execute_query(messages_stats_query, (start_date,))
        
        # أنواع التوجيه
        forward_types_query = """
        SELECT 
            forward_type,
            COUNT(*) as count
        FROM tasks 
        WHERE created_at >= ?
        GROUP BY forward_type
        """
        forward_types = self.db.execute_query(forward_types_query, (start_date,))
        
        return {
            'total_tasks': total_tasks,
            'new_tasks': new_tasks,
            'active_tasks': active_tasks,
            'messages_stats': messages_stats[0] if messages_stats else {},
            'forward_types': forward_types
        }
    
    async def get_performance_analytics(self, start_date: datetime) -> Dict[str, Any]:
        """تحليلات الأداء"""
        # معدل نجاح التوجيه
        success_rate_query = """
        SELECT 
            COUNT(*) as total_attempts,
            SUM(CASE WHEN target_message_ids IS NOT NULL THEN 1 ELSE 0 END) as successful,
            (SUM(CASE WHEN target_message_ids IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as success_rate
        FROM messages 
        WHERE forwarded_at >= ?
        """
        success_stats = self.db.execute_query(success_rate_query, (start_date,))
        
        # أداء المهام الأعلى
        top_performing_tasks_query = """
        SELECT 
            t.id,
            t.name,
            COUNT(m.id) as message_count,
            t.user_id
        FROM tasks t
        LEFT JOIN messages m ON t.id = m.task_id AND m.forwarded_at >= ?
        GROUP BY t.id, t.name, t.user_id
        ORDER BY message_count DESC
        LIMIT 10
        """
        top_tasks = self.db.execute_query(top_performing_tasks_query, (start_date,))
        
        # استخدام الموارد
        resource_usage = await self.get_resource_usage_stats()
        
        return {
            'success_stats': success_stats[0] if success_stats else {},
            'top_performing_tasks': top_tasks,
            'resource_usage': resource_usage
        }
    
    async def get_errors_analytics(self, start_date: datetime) -> Dict[str, Any]:
        """تحليلات الأخطاء"""
        # إحصائيات الأخطاء من السجلات
        # هذا يتطلب تحليل ملفات السجلات أو جدول أخطاء منفصل
        
        return {
            'total_errors': 0,
            'error_types': [],
            'error_trends': [],
            'critical_errors': 0
        }
    
    async def get_resource_usage_stats(self) -> Dict[str, Any]:
        """إحصائيات استخدام الموارد"""
        try:
            import psutil
            import os
            
            # استخدام الذاكرة
            memory = psutil.virtual_memory()
            
            # استخدام المعالج
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # مساحة القرص
            disk = psutil.disk_usage('/')
            
            # حجم قاعدة البيانات
            db_size = os.path.getsize('data/bot.db') if os.path.exists('data/bot.db') else 0
            
            return {
                'memory_usage_percent': memory.percent,
                'memory_used_mb': memory.used // (1024 * 1024),
                'memory_total_mb': memory.total // (1024 * 1024),
                'cpu_usage_percent': cpu_percent,
                'disk_usage_percent': (disk.used / disk.total) * 100,
                'disk_free_gb': disk.free // (1024 * 1024 * 1024),
                'database_size_mb': db_size // (1024 * 1024)
            }
        except ImportError:
            return {
                'memory_usage_percent': 0,
                'cpu_usage_percent': 0,
                'disk_usage_percent': 0,
                'database_size_mb': 0
            }
    
    async def generate_report(self, report_type: str, user_id: Optional[int] = None, 
                            days: int = 30) -> Dict[str, Any]:
        """إنشاء تقرير شامل"""
        if report_type == 'user' and user_id:
            return await self.get_user_analytics(user_id, days)
        elif report_type == 'system':
            return await self.get_system_analytics(days)
        elif report_type == 'performance':
            return await self.get_performance_analytics(
                datetime.now() - timedelta(days=days)
            )
        else:
            raise ValueError(f"نوع تقرير غير مدعوم: {report_type}")
    
    async def export_analytics_data(self, format_type: str = 'json', 
                                  filters: Dict[str, Any] = None) -> str:
        """تصدير بيانات التحليلات"""
        # الحصول على البيانات حسب الفلاتر
        data = await self.get_filtered_analytics_data(filters or {})
        
        if format_type == 'json':
            return json.dumps(data, ensure_ascii=False, indent=2)
        elif format_type == 'csv':
            return self.convert_to_csv(data)
        else:
            raise ValueError(f"تنسيق غير مدعوم: {format_type}")
    
    async def get_filtered_analytics_data(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """الحصول على بيانات التحليلات المفلترة"""
        start_date = filters.get('start_date', datetime.now() - timedelta(days=30))
        end_date = filters.get('end_date', datetime.now())
        user_ids = filters.get('user_ids', [])
        
        # بناء الاستعلامات حسب الفلاتر
        base_conditions = "WHERE timestamp BETWEEN ? AND ?"
        params = [start_date, end_date]
        
        if user_ids:
            base_conditions += f" AND user_id IN ({','.join(['?' for _ in user_ids])})"
            params.extend(user_ids)
        
        # الحصول على البيانات
        events_query = f"""
        SELECT * FROM analytics_events 
        {base_conditions}
        ORDER BY timestamp DESC
        """
        events = self.db.execute_query(events_query, params)
        
        metrics_query = f"""
        SELECT * FROM analytics_metrics 
        WHERE recorded_at BETWEEN ? AND ?
        ORDER BY recorded_at DESC
        """
        metrics = self.db.execute_query(metrics_query, [start_date, end_date])
        
        return {
            'events': events,
            'metrics': metrics,
            'filters_applied': filters,
            'exported_at': datetime.now().isoformat()
        }
    
    def convert_to_csv(self, data: Dict[str, Any]) -> str:
        """تحويل البيانات إلى CSV"""
        import csv
        import io
        
        output = io.StringIO()
        
        # تصدير الأحداث
        if 'events' in data and data['events']:
            writer = csv.DictWriter(output, fieldnames=data['events'][0].keys())
            writer.writeheader()
            writer.writerows(data['events'])
        
        return output.getvalue()

class RealtimeAnalytics:
    """تحليلات في الوقت الفعلي"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.real_time_metrics = {}
        self.subscribers = {}
    
    async def update_metric(self, metric_name: str, value: float):
        """تحديث مقياس في الوقت الفعلي"""
        self.real_time_metrics[metric_name] = {
            'value': value,
            'timestamp': datetime.now().isoformat()
        }
        
        # إشعار المشتركين
        await self.notify_subscribers(metric_name, value)
    
    async def notify_subscribers(self, metric_name: str, value: float):
        """إشعار المشتركين بالتحديثات"""
        notification = {
            'type': 'metric_update',
            'metric_name': metric_name,
            'value': value,
            'timestamp': datetime.now().isoformat()
        }
        
        for user_id, connection in self.subscribers.items():
            try:
                await connection.send_json(notification)
            except Exception as e:
                logger.log_error(e, {
                    'function': 'notify_subscribers',
                    'user_id': user_id,
                    'metric': metric_name
                })
    
    async def subscribe_to_metrics(self, user_id: int, connection):
        """الاشتراك في التحديثات المباشرة"""
        self.subscribers[user_id] = connection
    
    async def unsubscribe_from_metrics(self, user_id: int):
        """إلغاء الاشتراك"""
        if user_id in self.subscribers:
            del self.subscribers[user_id]
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """الحصول على المقاييس الحالية"""
        return self.real_time_metrics.copy()
