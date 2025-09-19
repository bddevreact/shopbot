import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict, Counter
import threading

class AnalyticsManager:
    """Professional analytics and monitoring system"""
    
    def __init__(self):
        self.lock = threading.Lock()
        self.metrics = {
            'user_actions': defaultdict(int),
            'admin_actions': defaultdict(int),
            'order_events': defaultdict(int),
            'error_events': defaultdict(int),
            'daily_stats': defaultdict(lambda: defaultdict(int)),
            'hourly_stats': defaultdict(lambda: defaultdict(int)),
            'user_activity': defaultdict(list),
            'performance_metrics': defaultdict(list)
        }
    
    def track_user_action(self, user_id: int, action: str, metadata: Dict[str, Any] = None):
        """Track user action"""
        with self.lock:
            timestamp = datetime.now()
            self.metrics['user_actions'][action] += 1
            self.metrics['daily_stats'][timestamp.date()]['user_actions'] += 1
            self.metrics['hourly_stats'][timestamp.hour]['user_actions'] += 1
            
            # Track user activity
            self.metrics['user_activity'][user_id].append({
                'action': action,
                'timestamp': timestamp.isoformat(),
                'metadata': metadata or {}
            })
            
            # Keep only last 100 actions per user
            if len(self.metrics['user_activity'][user_id]) > 100:
                self.metrics['user_activity'][user_id] = self.metrics['user_activity'][user_id][-100:]
    
    def track_admin_action(self, admin_id: int, action: str, metadata: Dict[str, Any] = None):
        """Track admin action"""
        with self.lock:
            timestamp = datetime.now()
            self.metrics['admin_actions'][action] += 1
            self.metrics['daily_stats'][timestamp.date()]['admin_actions'] += 1
            self.metrics['hourly_stats'][timestamp.hour]['admin_actions'] += 1
    
    def track_order_event(self, order_id: str, event: str, metadata: Dict[str, Any] = None):
        """Track order event"""
        with self.lock:
            timestamp = datetime.now()
            self.metrics['order_events'][event] += 1
            self.metrics['daily_stats'][timestamp.date()]['order_events'] += 1
            self.metrics['hourly_stats'][timestamp.hour]['order_events'] += 1
    
    def track_error(self, error_type: str, error_message: str, context: str = ""):
        """Track error event"""
        with self.lock:
            timestamp = datetime.now()
            self.metrics['error_events'][error_type] += 1
            self.metrics['daily_stats'][timestamp.date()]['errors'] += 1
            self.metrics['hourly_stats'][timestamp.hour]['errors'] += 1
    
    def track_performance(self, operation: str, duration: float, metadata: Dict[str, Any] = None):
        """Track performance metrics"""
        with self.lock:
            self.metrics['performance_metrics'][operation].append({
                'duration': duration,
                'timestamp': datetime.now().isoformat(),
                'metadata': metadata or {}
            })
            
            # Keep only last 1000 performance records per operation
            if len(self.metrics['performance_metrics'][operation]) > 1000:
                self.metrics['performance_metrics'][operation] = self.metrics['performance_metrics'][operation][-1000:]
    
    def get_user_activity_summary(self, user_id: int, days: int = 7) -> Dict[str, Any]:
        """Get user activity summary"""
        with self.lock:
            if user_id not in self.metrics['user_activity']:
                return {'total_actions': 0, 'actions': [], 'last_activity': None}
            
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_actions = []
            
            for action_data in self.metrics['user_activity'][user_id]:
                action_time = datetime.fromisoformat(action_data['timestamp'])
                if action_time >= cutoff_date:
                    recent_actions.append(action_data)
            
            return {
                'total_actions': len(recent_actions),
                'actions': recent_actions[-10:],  # Last 10 actions
                'last_activity': recent_actions[-1]['timestamp'] if recent_actions else None
            }
    
    def get_daily_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get daily statistics"""
        with self.lock:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days-1)
            
            daily_data = []
            for i in range(days):
                date = start_date + timedelta(days=i)
                date_str = date.isoformat()
                
                if date in self.metrics['daily_stats']:
                    daily_data.append({
                        'date': date_str,
                        'user_actions': self.metrics['daily_stats'][date]['user_actions'],
                        'admin_actions': self.metrics['daily_stats'][date]['admin_actions'],
                        'order_events': self.metrics['daily_stats'][date]['order_events'],
                        'errors': self.metrics['daily_stats'][date]['errors']
                    })
                else:
                    daily_data.append({
                        'date': date_str,
                        'user_actions': 0,
                        'admin_actions': 0,
                        'order_events': 0,
                        'errors': 0
                    })
            
            return {
                'period_days': days,
                'daily_data': daily_data,
                'total_user_actions': sum(day['user_actions'] for day in daily_data),
                'total_admin_actions': sum(day['admin_actions'] for day in daily_data),
                'total_order_events': sum(day['order_events'] for day in daily_data),
                'total_errors': sum(day['errors'] for day in daily_data)
            }
    
    def get_hourly_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get hourly statistics"""
        with self.lock:
            current_hour = datetime.now().hour
            hourly_data = []
            
            for i in range(hours):
                hour = (current_hour - i) % 24
                hour_str = f"{hour:02d}:00"
                
                if hour in self.metrics['hourly_stats']:
                    hourly_data.append({
                        'hour': hour_str,
                        'user_actions': self.metrics['hourly_stats'][hour]['user_actions'],
                        'admin_actions': self.metrics['hourly_stats'][hour]['admin_actions'],
                        'order_events': self.metrics['hourly_stats'][hour]['order_events'],
                        'errors': self.metrics['hourly_stats'][hour]['errors']
                    })
                else:
                    hourly_data.append({
                        'hour': hour_str,
                        'user_actions': 0,
                        'admin_actions': 0,
                        'order_events': 0,
                        'errors': 0
                    })
            
            return {
                'period_hours': hours,
                'hourly_data': list(reversed(hourly_data))  # Chronological order
            }
    
    def get_top_actions(self, action_type: str = 'user_actions', limit: int = 10) -> List[Dict[str, Any]]:
        """Get top actions by frequency"""
        with self.lock:
            if action_type not in self.metrics:
                return []
            
            counter = Counter(self.metrics[action_type])
            return [{'action': action, 'count': count} for action, count in counter.most_common(limit)]
    
    def get_performance_summary(self, operation: str = None) -> Dict[str, Any]:
        """Get performance summary"""
        with self.lock:
            if operation:
                if operation not in self.metrics['performance_metrics']:
                    return {'operation': operation, 'count': 0, 'avg_duration': 0, 'max_duration': 0}
                
                durations = [record['duration'] for record in self.metrics['performance_metrics'][operation]]
                return {
                    'operation': operation,
                    'count': len(durations),
                    'avg_duration': sum(durations) / len(durations) if durations else 0,
                    'max_duration': max(durations) if durations else 0,
                    'min_duration': min(durations) if durations else 0
                }
            else:
                # Summary for all operations
                summary = {}
                for op, records in self.metrics['performance_metrics'].items():
                    durations = [record['duration'] for record in records]
                    summary[op] = {
                        'count': len(durations),
                        'avg_duration': sum(durations) / len(durations) if durations else 0,
                        'max_duration': max(durations) if durations else 0
                    }
                return summary
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get system health metrics"""
        with self.lock:
            now = datetime.now()
            last_hour = now - timedelta(hours=1)
            
            # Calculate error rate
            total_actions = sum(self.metrics['user_actions'].values()) + sum(self.metrics['admin_actions'].values())
            total_errors = sum(self.metrics['error_events'].values())
            error_rate = (total_errors / total_actions * 100) if total_actions > 0 else 0
            
            # Calculate active users (users with activity in last hour)
            active_users = 0
            for user_id, activities in self.metrics['user_activity'].items():
                if activities:
                    last_activity = datetime.fromisoformat(activities[-1]['timestamp'])
                    if last_activity >= last_hour:
                        active_users += 1
            
            return {
                'total_users': len(self.metrics['user_activity']),
                'active_users': active_users,
                'total_actions': total_actions,
                'total_errors': total_errors,
                'error_rate': round(error_rate, 2),
                'health_status': 'healthy' if error_rate < 5 else 'warning' if error_rate < 10 else 'critical'
            }
    
    def export_analytics(self) -> Dict[str, Any]:
        """Export all analytics data"""
        with self.lock:
            return {
                'export_timestamp': datetime.now().isoformat(),
                'metrics': dict(self.metrics),
                'system_health': self.get_system_health()
            }
    
    def cleanup_old_data(self, days: int = 30):
        """Clean up old analytics data"""
        with self.lock:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Clean up daily stats
            old_dates = [date for date in self.metrics['daily_stats'].keys() if date < cutoff_date.date()]
            for date in old_dates:
                del self.metrics['daily_stats'][date]
            
            # Clean up user activity (keep last 30 days)
            for user_id in list(self.metrics['user_activity'].keys()):
                self.metrics['user_activity'][user_id] = [
                    action for action in self.metrics['user_activity'][user_id]
                    if datetime.fromisoformat(action['timestamp']) >= cutoff_date
                ]
                
                # Remove users with no recent activity
                if not self.metrics['user_activity'][user_id]:
                    del self.metrics['user_activity'][user_id]

# Global analytics manager instance
analytics_manager = AnalyticsManager()
