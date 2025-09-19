import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import random
import schedule
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import os

class NotificationManager:
    """Professional push notification system for product recommendations"""
    
    def __init__(self, bot, categories, shop_info, user_carts, user_states):
        self.bot = bot
        self.categories = categories
        self.shop_info = shop_info
        self.user_carts = user_carts
        self.user_states = user_states
        
        # Load user notification preferences
        self.user_preferences = self.load_user_preferences()
        
        # Notification settings
        self.notification_times = ["09:00", "15:00", "21:00"]  # 3 times daily
        self.max_products_per_notification = 3
        self.min_products_per_notification = 1
        
        # Start the scheduler
        self.start_scheduler()
    
    def load_user_preferences(self) -> Dict[int, Dict[str, Any]]:
        """Load user notification preferences"""
        try:
            with open('data/user_notification_preferences.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_user_preferences(self):
        """Save user notification preferences"""
        os.makedirs('data', exist_ok=True)
        with open('data/user_notification_preferences.json', 'w', encoding='utf-8') as f:
            json.dump(self.user_preferences, f, indent=2, ensure_ascii=False)
    
    def get_user_preference(self, user_id: int) -> Dict[str, Any]:
        """Get user notification preferences"""
        if user_id not in self.user_preferences:
            # Default preferences
            self.user_preferences[user_id] = {
                'notifications_enabled': True,
                'notification_frequency': 'daily',  # daily, weekly, disabled
                'preferred_categories': [],
                'last_notification': None,
                'notification_count_today': 0,
                'opt_out_until': None
            }
        return self.user_preferences[user_id]
    
    def update_user_preference(self, user_id: int, preference: str, value: Any):
        """Update user notification preference"""
        prefs = self.get_user_preference(user_id)
        prefs[preference] = value
        self.user_preferences[user_id] = prefs
        self.save_user_preferences()
    
    def get_random_products(self, user_id: int, count: int = None) -> List[Dict[str, Any]]:
        """Get random products for notification"""
        if count is None:
            count = random.randint(self.min_products_per_notification, self.max_products_per_notification)
        
        all_products = []
        for category in self.categories:
            if category.get('active', True):
                for product in category.get('products', []):
                    if product.get('active', True):
                        product_with_category = product.copy()
                        product_with_category['category_name'] = category['name']
                        product_with_category['category_id'] = category.get('id', category['name'])
                        all_products.append(product_with_category)
        
        # Filter by user preferences if they have preferred categories
        user_prefs = self.get_user_preference(user_id)
        if user_prefs.get('preferred_categories'):
            preferred_products = [p for p in all_products if p['category_name'] in user_prefs['preferred_categories']]
            if preferred_products:
                all_products = preferred_products
        
        # Return random selection
        return random.sample(all_products, min(count, len(all_products)))
    
    def create_product_notification_card(self, product: Dict[str, Any]) -> tuple:
        """Create a rich product notification card with image, description, and cart button"""
        
        # Product details
        name = product.get('name', 'Unknown Product')
        description = product.get('description', 'No description available')
        category = product.get('category_name', 'Unknown Category')
        
        # Handle different price formats
        if 'quantities' in product and product['quantities']:
            # New format with multiple quantities
            min_price = min(qty['price'] for qty in product['quantities'])
            max_price = max(qty['price'] for qty in product['quantities'])
            if min_price == max_price:
                price_text = f"€{min_price:.2f}"
            else:
                price_text = f"€{min_price:.2f} - €{max_price:.2f}"
        else:
            # Old format with single price
            price = product.get('price', 0)
            price_text = f"€{price:.2f}"
        
        # Create notification text
        notification_text = f"""
🛍️ **{name}**

📂 **Category:** {category}
💰 **Price:** {price_text}

📝 **Description:**
{description}

✨ **Special Offer!** Limited time deal!
        """.strip()
        
        # Create inline keyboard with cart button
        markup = InlineKeyboardMarkup(row_width=2)
        
        # Add to cart button
        product_id = product['name'].replace(' ', '|').replace('_', '|')
        if 'quantities' in product and product['quantities']:
            markup.add(InlineKeyboardButton('🛒 Add to Cart', callback_data=f"add_{product_id}|0"))
        else:
            markup.add(InlineKeyboardButton('🛒 Add to Cart', callback_data=f"add_{product_id}|{product.get('price', 0)}"))
        
        # View details button
        markup.add(InlineKeyboardButton('👁️ View Details', callback_data=f"view_{product_id}"))
        
        # Quick actions
        markup.add(
            InlineKeyboardButton('🛍️ Browse More', callback_data='products'),
            InlineKeyboardButton('🔕 Disable Notifications', callback_data='disable_notifications')
        )
        
        return notification_text, markup
    
    def send_product_notification(self, user_id: int):
        """Send product notification to a specific user"""
        try:
            # Check if user should receive notifications
            user_prefs = self.get_user_preference(user_id)
            
            # Check if notifications are disabled
            if not user_prefs.get('notifications_enabled', True):
                return False
            
            # Check if user opted out temporarily
            if user_prefs.get('opt_out_until'):
                opt_out_until = datetime.fromisoformat(user_prefs['opt_out_until'])
                if datetime.now() < opt_out_until:
                    return False
            
            # Check daily notification limit
            today = datetime.now().date()
            last_notification_date = None
            if user_prefs.get('last_notification'):
                last_notification_date = datetime.fromisoformat(user_prefs['last_notification']).date()
            
            if last_notification_date == today and user_prefs.get('notification_count_today', 0) >= 3:
                return False
            
            # Get random products
            products = self.get_random_products(user_id)
            if not products:
                return False
            
            # Send notification for each product
            for product in products:
                try:
                    notification_text, markup = self.create_product_notification_card(product)
                    
                    # Send the notification
                    self.bot.send_message(
                        user_id,
                        notification_text,
                        reply_markup=markup,
                        parse_mode='Markdown'
                    )
                    
                    # Small delay between products
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"Error sending notification for product {product.get('name', 'Unknown')}: {e}")
                    continue
            
            # Update user preferences
            now = datetime.now()
            user_prefs['last_notification'] = now.isoformat()
            user_prefs['notification_count_today'] = user_prefs.get('notification_count_today', 0) + 1
            
            # Reset daily count if it's a new day
            if last_notification_date != today:
                user_prefs['notification_count_today'] = 1
            
            self.update_user_preference(user_id, 'last_notification', user_prefs['last_notification'])
            self.update_user_preference(user_id, 'notification_count_today', user_prefs['notification_count_today'])
            
            return True
            
        except Exception as e:
            print(f"Error sending notification to user {user_id}: {e}")
            return False
    
    def send_daily_notifications(self):
        """Send daily notifications to all eligible users"""
        print(f"[{datetime.now()}] Sending daily product notifications...")
        
        # Get all users who should receive notifications
        eligible_users = []
        
        # Load users from users.json
        try:
            with open('data/users.json', 'r', encoding='utf-8') as f:
                users_data = json.load(f)
                users = users_data.get('users', [])
                
                for user in users:
                    user_id = user.get('user_id')
                    if user_id:
                        user_prefs = self.get_user_preference(user_id)
                        if user_prefs.get('notifications_enabled', True):
                            eligible_users.append(user_id)
                            
        except FileNotFoundError:
            print("No users.json found, skipping notifications")
            return
        
        # Send notifications to eligible users
        sent_count = 0
        for user_id in eligible_users:
            if self.send_product_notification(user_id):
                sent_count += 1
        
        print(f"[{datetime.now()}] Sent notifications to {sent_count} users")
    
    def start_scheduler(self):
        """Start the notification scheduler"""
        # Schedule notifications at specified times
        for time_str in self.notification_times:
            schedule.every().day.at(time_str).do(self.send_daily_notifications)
        
        # Start scheduler in a separate thread
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        print(f"Notification scheduler started. Times: {', '.join(self.notification_times)}")
    
    def send_immediate_notification(self, user_id: int, product: Dict[str, Any] = None):
        """Send immediate notification (for testing or special offers)"""
        if product:
            products = [product]
        else:
            products = self.get_random_products(user_id, 1)
        
        if products:
            notification_text, markup = self.create_product_notification_card(products[0])
            self.bot.send_message(
                user_id,
                notification_text,
                reply_markup=markup,
                parse_mode='Markdown'
            )
            return True
        return False
    
    def get_notification_stats(self) -> Dict[str, Any]:
        """Get notification statistics"""
        total_users = len(self.user_preferences)
        enabled_users = sum(1 for prefs in self.user_preferences.values() 
                           if prefs.get('notifications_enabled', True))
        
        today_notifications = sum(prefs.get('notification_count_today', 0) 
                                for prefs in self.user_preferences.values())
        
        return {
            'total_users': total_users,
            'notifications_enabled': enabled_users,
            'notifications_disabled': total_users - enabled_users,
            'today_notifications_sent': today_notifications,
            'notification_times': self.notification_times
        }

# Notification preference handlers
def setup_notification_handlers(bot, notification_manager):
    """Setup notification-related callback handlers"""
    
    @bot.callback_query_handler(func=lambda call: call.data == 'disable_notifications')
    def disable_notifications(call):
        user_id = call.from_user.id
        notification_manager.update_user_preference(user_id, 'notifications_enabled', False)
        
        bot.answer_callback_query(call.id, "Notifications disabled! Use /notifications to re-enable.")
        
        # Update the message
        bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            reply_markup=None
        )
    
    @bot.callback_query_handler(func=lambda call: call.data == 'enable_notifications')
    def enable_notifications(call):
        user_id = call.from_user.id
        notification_manager.update_user_preference(user_id, 'notifications_enabled', True)
        
        bot.answer_callback_query(call.id, "Notifications enabled! You'll receive daily product updates.")
    
    @bot.message_handler(commands=['notifications'])
    def notification_settings(message):
        user_id = message.from_user.id
        prefs = notification_manager.get_user_preference(user_id)
        
        status = "✅ Enabled" if prefs.get('notifications_enabled', True) else "❌ Disabled"
        count_today = prefs.get('notification_count_today', 0)
        
        settings_text = f"""
🔔 **Notification Settings**

**Status:** {status}
**Today's notifications:** {count_today}/3
**Schedule:** {', '.join(notification_manager.notification_times)}

**What you'll receive:**
• Daily product recommendations
• Special offers and deals
• New product announcements
• Price updates

Use the buttons below to manage your preferences.
        """.strip()
        
        markup = InlineKeyboardMarkup(row_width=2)
        if prefs.get('notifications_enabled', True):
            markup.add(InlineKeyboardButton('🔕 Disable Notifications', callback_data='disable_notifications'))
        else:
            markup.add(InlineKeyboardButton('🔔 Enable Notifications', callback_data='enable_notifications'))
        
        markup.add(
            InlineKeyboardButton('📊 Notification Stats', callback_data='notification_stats'),
            InlineKeyboardButton('🎯 Test Notification', callback_data='test_notification')
        )
        
        bot.reply_to(message, settings_text, reply_markup=markup, parse_mode='Markdown')
    
    @bot.callback_query_handler(func=lambda call: call.data == 'notification_stats')
    def show_notification_stats(call):
        user_id = call.from_user.id
        prefs = notification_manager.get_user_preference(user_id)
        
        stats_text = f"""
📊 **Your Notification Stats**

**Status:** {'✅ Enabled' if prefs.get('notifications_enabled', True) else '❌ Disabled'}
**Today's notifications:** {prefs.get('notification_count_today', 0)}/3
**Last notification:** {prefs.get('last_notification', 'Never')}

**System Stats:**
{notification_manager.get_notification_stats()}
        """.strip()
        
        bot.answer_callback_query(call.id, "Stats updated!")
        bot.edit_message_text(
            stats_text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode='Markdown'
        )
    
    @bot.callback_query_handler(func=lambda call: call.data == 'test_notification')
    def test_notification(call):
        user_id = call.from_user.id
        
        if notification_manager.send_immediate_notification(user_id):
            bot.answer_callback_query(call.id, "Test notification sent!")
        else:
            bot.answer_callback_query(call.id, "No products available for notification.")
