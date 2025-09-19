import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import os
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import threading
import re

class FraudDetectionSystem:
    """Advanced fraud detection and suspicious activity monitoring system"""
    
    def __init__(self, bot, admin_config):
        self.bot = bot
        self.admin_config = admin_config
        
        # Fraud detection data
        self.suspicious_activities = self.load_suspicious_activities()
        self.user_risk_scores = self.load_user_risk_scores()
        self.fraud_patterns = self.load_fraud_patterns()
        self.blocked_users = self.load_blocked_users()
        self.fraud_alerts = self.load_fraud_alerts()
        
        # Detection thresholds
        self.risk_thresholds = {
            'low': 0.3,
            'medium': 0.6,
            'high': 0.8,
            'critical': 0.9
        }
        
        # Suspicious behavior patterns
        self.suspicious_patterns = {
            'rapid_orders': {'threshold': 5, 'timeframe': 300},  # 5 orders in 5 minutes
            'high_value_orders': {'threshold': 1000, 'currency': 'EUR'},  # Orders over €1000
            'multiple_accounts': {'threshold': 3, 'timeframe': 3600},  # 3 accounts from same IP in 1 hour
            'unusual_timing': {'suspicious_hours': [2, 3, 4, 5]},  # Orders at 2-5 AM
            'repeated_failures': {'threshold': 3, 'timeframe': 1800},  # 3 failed attempts in 30 minutes
            'suspicious_keywords': ['test', 'fake', 'spam', 'bot', 'hack']
        }
        
        # Start monitoring
        self.start_fraud_monitoring()
    
    def load_suspicious_activities(self) -> Dict[str, Any]:
        """Load suspicious activities data"""
        try:
            with open('data/suspicious_activities.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                'activities': [],
                'ip_addresses': {},
                'device_fingerprints': {},
                'behavioral_patterns': {}
            }
    
    def save_suspicious_activities(self):
        """Save suspicious activities data"""
        os.makedirs('data', exist_ok=True)
        with open('data/suspicious_activities.json', 'w', encoding='utf-8') as f:
            json.dump(self.suspicious_activities, f, indent=2, ensure_ascii=False)
    
    def load_user_risk_scores(self) -> Dict[str, float]:
        """Load user risk scores"""
        try:
            with open('data/user_risk_scores.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_user_risk_scores(self):
        """Save user risk scores"""
        os.makedirs('data', exist_ok=True)
        with open('data/user_risk_scores.json', 'w', encoding='utf-8') as f:
            json.dump(self.user_risk_scores, f, indent=2, ensure_ascii=False)
    
    def load_fraud_patterns(self) -> Dict[str, Any]:
        """Load known fraud patterns"""
        try:
            with open('data/fraud_patterns.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                'known_fraud_ips': [],
                'suspicious_keywords': [],
                'fraudulent_orders': [],
                'blocked_patterns': []
            }
    
    def save_fraud_patterns(self):
        """Save fraud patterns"""
        os.makedirs('data', exist_ok=True)
        with open('data/fraud_patterns.json', 'w', encoding='utf-8') as f:
            json.dump(self.fraud_patterns, f, indent=2, ensure_ascii=False)
    
    def load_blocked_users(self) -> Dict[str, Any]:
        """Load blocked users list"""
        try:
            with open('data/blocked_users.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                'permanently_blocked': [],
                'temporarily_blocked': {},
                'warning_users': {}
            }
    
    def save_blocked_users(self):
        """Save blocked users list"""
        os.makedirs('data', exist_ok=True)
        with open('data/blocked_users.json', 'w', encoding='utf-8') as f:
            json.dump(self.blocked_users, f, indent=2, ensure_ascii=False)
    
    def load_fraud_alerts(self) -> List[Dict[str, Any]]:
        """Load fraud alerts"""
        try:
            with open('data/fraud_alerts.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
    
    def save_fraud_alerts(self):
        """Save fraud alerts"""
        os.makedirs('data', exist_ok=True)
        with open('data/fraud_alerts.json', 'w', encoding='utf-8') as f:
            json.dump(self.fraud_alerts, f, indent=2, ensure_ascii=False)
    
    def analyze_user_behavior(self, user_id: int, action: str, data: Dict[str, Any]) -> Tuple[float, List[str]]:
        """Analyze user behavior for suspicious activity"""
        risk_score = 0.0
        alerts = []
        
        # Get user's current risk score
        current_risk = self.user_risk_scores.get(str(user_id), 0.0)
        
        # Analyze different types of actions
        if action == 'order_placed':
            risk_score, alerts = self.analyze_order_behavior(user_id, data)
        elif action == 'payment_attempt':
            risk_score, alerts = self.analyze_payment_behavior(user_id, data)
        elif action == 'account_creation':
            risk_score, alerts = self.analyze_account_creation(user_id, data)
        elif action == 'login_attempt':
            risk_score, alerts = self.analyze_login_behavior(user_id, data)
        elif action == 'message_sent':
            risk_score, alerts = self.analyze_message_behavior(user_id, data)
        
        # Update user's risk score
        new_risk = min(1.0, current_risk + risk_score)
        self.user_risk_scores[str(user_id)] = new_risk
        
        # Log suspicious activity if risk is high
        if new_risk > self.risk_thresholds['medium']:
            self.log_suspicious_activity(user_id, action, data, new_risk, alerts)
        
        # Create alerts for high-risk activities
        if new_risk > self.risk_thresholds['high']:
            self.create_fraud_alert(user_id, action, data, new_risk, alerts)
        
        self.save_user_risk_scores()
        return new_risk, alerts
    
    def analyze_order_behavior(self, user_id: int, order_data: Dict[str, Any]) -> Tuple[float, List[str]]:
        """Analyze order behavior for fraud indicators"""
        risk_score = 0.0
        alerts = []
        
        # Check for rapid orders
        recent_orders = self.get_recent_orders(user_id, 300)  # Last 5 minutes
        if len(recent_orders) >= self.suspicious_patterns['rapid_orders']['threshold']:
            risk_score += 0.4
            alerts.append("Rapid order placement detected")
        
        # Check for high-value orders
        order_value = order_data.get('total_amount', 0)
        if order_value >= self.suspicious_patterns['high_value_orders']['threshold']:
            risk_score += 0.3
            alerts.append("High-value order detected")
        
        # Check for unusual timing
        current_hour = datetime.now().hour
        if current_hour in self.suspicious_patterns['unusual_timing']['suspicious_hours']:
            risk_score += 0.2
            alerts.append("Unusual order timing")
        
        # Check for suspicious shipping addresses
        shipping_address = order_data.get('shipping_address', '')
        if self.is_suspicious_address(shipping_address):
            risk_score += 0.5
            alerts.append("Suspicious shipping address")
        
        # Check for multiple orders to same address
        if self.has_multiple_orders_to_address(user_id, shipping_address):
            risk_score += 0.3
            alerts.append("Multiple orders to same address")
        
        return risk_score, alerts
    
    def analyze_payment_behavior(self, user_id: int, payment_data: Dict[str, Any]) -> Tuple[float, List[str]]:
        """Analyze payment behavior for fraud indicators"""
        risk_score = 0.0
        alerts = []
        
        # Check for repeated payment failures
        recent_failures = self.get_recent_payment_failures(user_id, 1800)  # Last 30 minutes
        if len(recent_failures) >= self.suspicious_patterns['repeated_failures']['threshold']:
            risk_score += 0.6
            alerts.append("Repeated payment failures")
        
        # Check for suspicious payment amounts
        payment_amount = payment_data.get('amount', 0)
        if payment_amount <= 0 or payment_amount > 10000:
            risk_score += 0.4
            alerts.append("Suspicious payment amount")
        
        # Check for unusual payment timing
        current_hour = datetime.now().hour
        if current_hour in self.suspicious_patterns['unusual_timing']['suspicious_hours']:
            risk_score += 0.2
            alerts.append("Unusual payment timing")
        
        return risk_score, alerts
    
    def analyze_account_creation(self, user_id: int, account_data: Dict[str, Any]) -> Tuple[float, List[str]]:
        """Analyze account creation for fraud indicators"""
        risk_score = 0.0
        alerts = []
        
        # Check for multiple accounts from same IP
        ip_address = account_data.get('ip_address', '')
        if ip_address:
            recent_accounts = self.get_recent_accounts_from_ip(ip_address, 3600)  # Last hour
            if len(recent_accounts) >= self.suspicious_patterns['multiple_accounts']['threshold']:
                risk_score += 0.7
                alerts.append("Multiple accounts from same IP")
        
        # Check for suspicious username
        username = account_data.get('username', '')
        if self.is_suspicious_username(username):
            risk_score += 0.3
            alerts.append("Suspicious username pattern")
        
        return risk_score, alerts
    
    def analyze_login_behavior(self, user_id: int, login_data: Dict[str, Any]) -> Tuple[float, List[str]]:
        """Analyze login behavior for fraud indicators"""
        risk_score = 0.0
        alerts = []
        
        # Check for rapid login attempts
        recent_logins = self.get_recent_logins(user_id, 300)  # Last 5 minutes
        if len(recent_logins) >= 5:
            risk_score += 0.4
            alerts.append("Rapid login attempts")
        
        # Check for login from new location
        ip_address = login_data.get('ip_address', '')
        if ip_address and not self.is_known_ip(user_id, ip_address):
            risk_score += 0.2
            alerts.append("Login from new location")
        
        return risk_score, alerts
    
    def analyze_message_behavior(self, user_id: int, message_data: Dict[str, Any]) -> Tuple[float, List[str]]:
        """Analyze message behavior for fraud indicators"""
        risk_score = 0.0
        alerts = []
        
        # Check for suspicious keywords
        message_text = message_data.get('text', '').lower()
        for keyword in self.suspicious_patterns['suspicious_keywords']:
            if keyword in message_text:
                risk_score += 0.3
                alerts.append(f"Suspicious keyword detected: {keyword}")
        
        # Check for spam-like behavior
        recent_messages = self.get_recent_messages(user_id, 60)  # Last minute
        if len(recent_messages) >= 10:
            risk_score += 0.4
            alerts.append("Spam-like message behavior")
        
        return risk_score, alerts
    
    def is_suspicious_address(self, address: str) -> bool:
        """Check if address is suspicious"""
        suspicious_patterns = [
            r'test\s+address',
            r'fake\s+address',
            r'123\s+main\s+st',
            r'no\s+address',
            r'none',
            r'null'
        ]
        
        address_lower = address.lower()
        for pattern in suspicious_patterns:
            if re.search(pattern, address_lower):
                return True
        
        return False
    
    def is_suspicious_username(self, username: str) -> bool:
        """Check if username is suspicious"""
        suspicious_patterns = [
            r'^test\d+$',
            r'^bot\d+$',
            r'^spam\d+$',
            r'^fake\d+$',
            r'^\d{10,}$'  # Only numbers
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, username.lower()):
                return True
        
        return False
    
    def has_multiple_orders_to_address(self, user_id: int, address: str) -> bool:
        """Check if user has multiple orders to same address"""
        # This would check against order history
        # For now, return False as placeholder
        return False
    
    def get_recent_orders(self, user_id: int, timeframe: int) -> List[Dict]:
        """Get recent orders for user"""
        # This would query order history
        # For now, return empty list as placeholder
        return []
    
    def get_recent_payment_failures(self, user_id: int, timeframe: int) -> List[Dict]:
        """Get recent payment failures for user"""
        # This would query payment history
        # For now, return empty list as placeholder
        return []
    
    def get_recent_accounts_from_ip(self, ip_address: str, timeframe: int) -> List[Dict]:
        """Get recent accounts created from IP"""
        # This would query account creation history
        # For now, return empty list as placeholder
        return []
    
    def get_recent_logins(self, user_id: int, timeframe: int) -> List[Dict]:
        """Get recent logins for user"""
        # This would query login history
        # For now, return empty list as placeholder
        return []
    
    def get_recent_messages(self, user_id: int, timeframe: int) -> List[Dict]:
        """Get recent messages from user"""
        # This would query message history
        # For now, return empty list as placeholder
        return []
    
    def is_known_ip(self, user_id: int, ip_address: str) -> bool:
        """Check if IP is known for user"""
        # This would check user's IP history
        # For now, return True as placeholder
        return True
    
    def log_suspicious_activity(self, user_id: int, action: str, data: Dict[str, Any], risk_score: float, alerts: List[str]):
        """Log suspicious activity"""
        activity = {
            'user_id': user_id,
            'action': action,
            'data': data,
            'risk_score': risk_score,
            'alerts': alerts,
            'timestamp': datetime.now().isoformat(),
            'ip_address': data.get('ip_address', 'unknown'),
            'user_agent': data.get('user_agent', 'unknown')
        }
        
        self.suspicious_activities['activities'].append(activity)
        
        # Keep only last 1000 activities
        if len(self.suspicious_activities['activities']) > 1000:
            self.suspicious_activities['activities'] = self.suspicious_activities['activities'][-1000:]
        
        self.save_suspicious_activities()
    
    def create_fraud_alert(self, user_id: int, action: str, data: Dict[str, Any], risk_score: float, alerts: List[str]):
        """Create fraud alert for admins"""
        alert = {
            'id': len(self.fraud_alerts) + 1,
            'user_id': user_id,
            'action': action,
            'risk_score': risk_score,
            'alerts': alerts,
            'timestamp': datetime.now().isoformat(),
            'status': 'active',
            'data': data
        }
        
        self.fraud_alerts.append(alert)
        self.save_fraud_alerts()
        
        # Notify admins
        self.notify_admins_fraud_alert(alert)
    
    def notify_admins_fraud_alert(self, alert: Dict[str, Any]):
        """Notify admins about fraud alert"""
        for admin in self.admin_config['admin_users']:
            try:
                admin_id = admin['user_id']
                
                risk_level = self.get_risk_level(alert['risk_score'])
                risk_emoji = self.get_risk_emoji(risk_level)
                
                alert_text = f"""
{risk_emoji} **FRAUD ALERT**

**Alert ID:** #{alert['id']}
**User ID:** {alert['user_id']}
**Risk Level:** {risk_level.upper()}
**Risk Score:** {alert['risk_score']:.2f}
**Action:** {alert['action']}

**Alerts:**
{chr(10).join(f'• {alert_msg}' for alert_msg in alert['alerts'])}

**Timestamp:** {alert['timestamp']}

**Status:** {alert['status'].title()}
                """.strip()
                
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton('🔍 Investigate', callback_data=f'fraud_investigate_{alert["id"]}'))
                markup.add(InlineKeyboardButton('🚫 Block User', callback_data=f'fraud_block_{alert["user_id"]}'))
                
                self.bot.send_message(admin_id, alert_text, reply_markup=markup)
                
            except Exception as e:
                print(f"Failed to notify admin {admin_id} about fraud alert: {e}")
    
    def get_risk_level(self, risk_score: float) -> str:
        """Get risk level from score"""
        if risk_score >= self.risk_thresholds['critical']:
            return 'critical'
        elif risk_score >= self.risk_thresholds['high']:
            return 'high'
        elif risk_score >= self.risk_thresholds['medium']:
            return 'medium'
        else:
            return 'low'
    
    def get_risk_emoji(self, risk_level: str) -> str:
        """Get emoji for risk level"""
        emojis = {
            'low': '🟢',
            'medium': '🟡',
            'high': '🟠',
            'critical': '🔴'
        }
        return emojis.get(risk_level, '⚪')
    
    def block_user(self, user_id: int, reason: str, duration: Optional[int] = None):
        """Block user temporarily or permanently"""
        if duration:
            # Temporary block
            block_until = datetime.now() + timedelta(seconds=duration)
            self.blocked_users['temporarily_blocked'][str(user_id)] = {
                'reason': reason,
                'blocked_until': block_until.isoformat(),
                'blocked_at': datetime.now().isoformat()
            }
        else:
            # Permanent block
            self.blocked_users['permanently_blocked'].append({
                'user_id': user_id,
                'reason': reason,
                'blocked_at': datetime.now().isoformat()
            })
        
        self.save_blocked_users()
    
    def unblock_user(self, user_id: int):
        """Unblock user"""
        user_id_str = str(user_id)
        
        # Remove from temporary blocks
        if user_id_str in self.blocked_users['temporarily_blocked']:
            del self.blocked_users['temporarily_blocked'][user_id_str]
        
        # Remove from permanent blocks
        self.blocked_users['permanently_blocked'] = [
            block for block in self.blocked_users['permanently_blocked']
            if block['user_id'] != user_id
        ]
        
        self.save_blocked_users()
    
    def is_user_blocked(self, user_id: int) -> Tuple[bool, str]:
        """Check if user is blocked and return reason"""
        user_id_str = str(user_id)
        
        # Check permanent blocks
        for block in self.blocked_users['permanently_blocked']:
            if block['user_id'] == user_id:
                return True, f"Permanently blocked: {block['reason']}"
        
        # Check temporary blocks
        if user_id_str in self.blocked_users['temporarily_blocked']:
            block_info = self.blocked_users['temporarily_blocked'][user_id_str]
            block_until = datetime.fromisoformat(block_info['blocked_until'])
            
            if datetime.now() < block_until:
                return True, f"Temporarily blocked: {block_info['reason']}"
            else:
                # Block expired, remove it
                del self.blocked_users['temporarily_blocked'][user_id_str]
                self.save_blocked_users()
        
        return False, ""
    
    def get_fraud_statistics(self) -> Dict[str, Any]:
        """Get fraud detection statistics"""
        total_alerts = len(self.fraud_alerts)
        active_alerts = len([a for a in self.fraud_alerts if a['status'] == 'active'])
        
        risk_distribution = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        for user_id, risk_score in self.user_risk_scores.items():
            risk_level = self.get_risk_level(risk_score)
            risk_distribution[risk_level] += 1
        
        blocked_users_count = len(self.blocked_users['permanently_blocked']) + len(self.blocked_users['temporarily_blocked'])
        
        return {
            'total_alerts': total_alerts,
            'active_alerts': active_alerts,
            'blocked_users': blocked_users_count,
            'risk_distribution': risk_distribution,
            'suspicious_activities': len(self.suspicious_activities['activities']),
            'monitoring_status': 'active'
        }
    
    def start_fraud_monitoring(self):
        """Start fraud monitoring in background"""
        def monitor_fraud():
            while True:
                try:
                    # Clean up expired temporary blocks
                    current_time = datetime.now()
                    expired_blocks = []
                    
                    for user_id, block_info in self.blocked_users['temporarily_blocked'].items():
                        block_until = datetime.fromisoformat(block_info['blocked_until'])
                        if current_time >= block_until:
                            expired_blocks.append(user_id)
                    
                    for user_id in expired_blocks:
                        del self.blocked_users['temporarily_blocked'][user_id]
                    
                    if expired_blocks:
                        self.save_blocked_users()
                    
                    # Monitor for new suspicious activities
                    self.analyze_system_health()
                    
                    time.sleep(300)  # Check every 5 minutes
                    
                except Exception as e:
                    print(f"Fraud monitoring error: {e}")
                    time.sleep(300)
        
        monitor_thread = threading.Thread(target=monitor_fraud, daemon=True)
        monitor_thread.start()
        print("Fraud monitoring started")
    
    def analyze_system_health(self):
        """Analyze overall system health for fraud patterns"""
        # This would analyze system-wide patterns
        # For now, just a placeholder
        pass
    
    def create_fraud_management_menu(self) -> InlineKeyboardMarkup:
        """Create fraud management menu for admins"""
        markup = InlineKeyboardMarkup(row_width=2)
        
        stats = self.get_fraud_statistics()
        
        markup.add(
            InlineKeyboardButton(f'🚨 Active Alerts ({stats["active_alerts"]})', callback_data='fraud_alerts'),
            InlineKeyboardButton(f'🚫 Blocked Users ({stats["blocked_users"]})', callback_data='fraud_blocked')
        )
        
        markup.add(
            InlineKeyboardButton('📊 Fraud Statistics', callback_data='fraud_stats'),
            InlineKeyboardButton('🔍 Risk Analysis', callback_data='fraud_risk_analysis')
        )
        
        markup.add(
            InlineKeyboardButton('⚙️ Fraud Settings', callback_data='fraud_settings'),
            InlineKeyboardButton('🔙 Back to Admin', callback_data='admin_back_management')
        )
        
        return markup

def setup_fraud_detection_handlers(bot, fraud_detection):
    """Setup fraud detection handlers"""
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('fraud_'))
    def fraud_callback_handler(call):
        user_id = call.from_user.id
        
        # Check if user is admin
        admin_config = fraud_detection.admin_config
        is_admin = any(admin['user_id'] == user_id for admin in admin_config['admin_users'])
        
        if not is_admin:
            bot.answer_callback_query(call.id, "❌ Access denied.")
            return
        
        if call.data == 'fraud_alerts':
            alerts = fraud_detection.fraud_alerts
            active_alerts = [a for a in alerts if a['status'] == 'active']
            
            if not active_alerts:
                alerts_text = """
🚨 **Fraud Alerts**

No active fraud alerts at the moment.

System is monitoring for suspicious activities.
                """.strip()
            else:
                alerts_text = f"""
🚨 **Active Fraud Alerts**

**Total Active:** {len(active_alerts)}

"""
                for alert in active_alerts[-5:]:  # Show last 5 alerts
                    risk_level = fraud_detection.get_risk_level(alert['risk_score'])
                    risk_emoji = fraud_detection.get_risk_emoji(risk_level)
                    alerts_text += f"{risk_emoji} **#{alert['id']}** - User {alert['user_id']} ({risk_level})\n"
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton('🔙 Back to Fraud Management', callback_data='fraud_management'))
            
            bot.edit_message_text(
                alerts_text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup
            )
        
        elif call.data == 'fraud_blocked':
            blocked_users = fraud_detection.blocked_users
            permanent_count = len(blocked_users['permanently_blocked'])
            temporary_count = len(blocked_users['temporarily_blocked'])
            
            blocked_text = f"""
🚫 **Blocked Users**

**Permanently Blocked:** {permanent_count}
**Temporarily Blocked:** {temporary_count}
**Total Blocked:** {permanent_count + temporary_count}

**Recent Blocks:**
"""
            
            # Show recent permanent blocks
            for block in blocked_users['permanently_blocked'][-3:]:
                blocked_text += f"• User {block['user_id']} - {block['reason']}\n"
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton('🔙 Back to Fraud Management', callback_data='fraud_management'))
            
            bot.edit_message_text(
                blocked_text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup
            )
        
        elif call.data == 'fraud_stats':
            stats = fraud_detection.get_fraud_statistics()
            
            stats_text = f"""
📊 **Fraud Detection Statistics**

🚨 **Alerts:**
• Total Alerts: {stats['total_alerts']}
• Active Alerts: {stats['active_alerts']}
• Suspicious Activities: {stats['suspicious_activities']}

🚫 **Blocked Users:**
• Total Blocked: {stats['blocked_users']}

📈 **Risk Distribution:**
• Low Risk: {stats['risk_distribution']['low']}
• Medium Risk: {stats['risk_distribution']['medium']}
• High Risk: {stats['risk_distribution']['high']}
• Critical Risk: {stats['risk_distribution']['critical']}

🔧 **System Status:**
• Monitoring: {stats['monitoring_status'].title()}
            """.strip()
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton('🔙 Back to Fraud Management', callback_data='fraud_management'))
            
            bot.edit_message_text(
                stats_text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup
            )
        
        bot.answer_callback_query(call.id, "Fraud management option selected!")
