import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import datetime
import os
from typing import Dict, List, Any, Optional
import threading
import time

class CustomerSupportManager:
    """Professional customer support system with ticket management"""
    
    def __init__(self, bot, admin_config):
        self.bot = bot
        self.admin_config = admin_config
        
        # Support data storage
        self.support_tickets = self.load_support_tickets()
        self.support_responses = self.load_support_responses()
        self.support_stats = self.load_support_stats()
        
        # Auto-response patterns
        self.auto_responses = {
            'greeting': {
                'keywords': ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening', 'namaste', 'salam', 'assalamu alaikum', 'kemon achen', 'ki obostha'],
                'response': "👋 **Hello! Welcome to our support!**\n\nHow can I help you today?\n\n**Quick Help:**\n• 📦 Order issues\n• 💳 Payment problems\n• 🛍️ Product questions\n• 🔧 Technical support\n\nType your question or use /support for more options!"
            },
            'order_status': {
                'keywords': ['order', 'status', 'tracking', 'delivery', 'shipped', 'where is my order', 'order kothay', 'delivery kobe hobe', 'tracking number'],
                'response': "📦 **Order Status Help**\n\nTo check your order status:\n1. Use /orders command\n2. Or click '📦 Orders' in main menu\n3. Enter your order ID for tracking\n\nNeed more help? Create a support ticket!"
            },
            'payment_help': {
                'keywords': ['payment', 'pay', 'crypto', 'bitcoin', 'xmr', 'wallet', 'how to pay', 'payment kivabe korbo', 'bitcoin address', 'monero address', 'payment method'],
                'response': "💳 **Payment Help**\n\nWe accept:\n• Bitcoin (BTC)\n• Monero (XMR)\n\nPayment process:\n1. Add items to cart\n2. Proceed to checkout\n3. Send exact amount to provided wallet\n4. Confirm payment\n\nNeed help? Create a support ticket!"
            },
            'product_info': {
                'keywords': ['product', 'price', 'stock', 'available', 'quantity', 'product list', 'ki ki ache', 'price koto', 'stock ache ki', 'product details'],
                'response': "🛍️ **Product Information**\n\nTo view products:\n1. Click '🛍️ Products' in main menu\n2. Select your country\n3. Browse categories\n4. View product details\n\nNeed specific info? Create a support ticket!"
            },
            'shipping_delivery': {
                'keywords': ['shipping', 'delivery', 'how long', 'delivery time', 'shipping cost', 'delivery kobe hobe', 'shipping koto taka', 'delivery time koto'],
                'response': "🚚 **Shipping & Delivery**\n\n**Delivery Times:**\n• EU: 3-7 days\n• USA: 5-10 days\n• Worldwide: 7-14 days\n\n**Shipping Costs:**\n• Varies by country\n• Check delivery options at checkout\n\nNeed specific info? Create a support ticket!"
            },
            'refund_return': {
                'keywords': ['refund', 'return', 'money back', 'refund chai', 'return korbo', 'money back chai'],
                'response': "💰 **Refund & Return Policy**\n\n**Refund Policy:**\n• Contact support within 7 days\n• Provide order details\n• Refunds processed within 3-5 business days\n\n**Return Process:**\n• Create support ticket\n• Explain reason for return\n• Follow instructions from support team\n\nNeed help? Create a support ticket!"
            },
            'technical_issues': {
                'keywords': ['error', 'bug', 'not working', 'problem', 'issue', 'broken'],
                'response': "🔧 **Technical Support**\n\nFor technical issues:\n1. Try restarting your session (🔄 Restart Session)\n2. Clear your cart and try again\n3. If problem persists, create a support ticket\n\nWe'll help you resolve it quickly!"
            },
            'general_help': {
                'keywords': ['help', 'how', 'what', 'where', 'when'],
                'response': "❓ **General Help**\n\nQuick help:\n• /start - Main menu\n• /orders - Check orders\n• /notifications - Manage notifications\n• /support - Get help\n\nFor specific questions, create a support ticket!"
            }
        }
        
        # Support categories
        self.support_categories = [
            "Order Issues",
            "Payment Problems", 
            "Product Questions",
            "Technical Support",
            "Account Issues",
            "General Inquiry"
        ]
        
        # Start support monitoring
        self.start_support_monitoring()
    
    def load_support_tickets(self) -> Dict[str, Any]:
        """Load support tickets from file"""
        try:
            with open('data/support_tickets.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                'tickets': [],
                'next_ticket_id': 1,
                'active_tickets': 0,
                'resolved_tickets': 0
            }
    
    def save_support_tickets(self):
        """Save support tickets to file"""
        os.makedirs('data', exist_ok=True)
        with open('data/support_tickets.json', 'w', encoding='utf-8') as f:
            json.dump(self.support_tickets, f, indent=2, ensure_ascii=False)
    
    def load_support_responses(self) -> Dict[str, Any]:
        """Load support responses from file"""
        try:
            with open('data/support_responses.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                'responses': [],
                'auto_responses_enabled': True,
                'response_templates': {
                    'greeting': "Hello! How can I help you today?",
                    'closing': "Thank you for contacting us! Have a great day!",
                    'escalation': "I'm escalating this to our admin team. You'll receive a response soon."
                }
            }
    
    def save_support_responses(self):
        """Save support responses to file"""
        os.makedirs('data', exist_ok=True)
        with open('data/support_responses.json', 'w', encoding='utf-8') as f:
            json.dump(self.support_responses, f, indent=2, ensure_ascii=False)
    
    def load_support_stats(self) -> Dict[str, Any]:
        """Load support statistics"""
        try:
            with open('data/support_stats.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                'total_tickets': 0,
                'resolved_tickets': 0,
                'avg_response_time': 0,
                'customer_satisfaction': 0,
                'daily_tickets': {},
                'category_stats': {}
            }
    
    def save_support_stats(self):
        """Save support statistics"""
        os.makedirs('data', exist_ok=True)
        with open('data/support_stats.json', 'w', encoding='utf-8') as f:
            json.dump(self.support_stats, f, indent=2, ensure_ascii=False)
    
    def create_support_ticket(self, user_id: int, username: str, category: str, message: str) -> int:
        """Create a new support ticket"""
        ticket_id = self.support_tickets['next_ticket_id']
        
        ticket = {
            'id': ticket_id,
            'user_id': user_id,
            'username': username,
            'category': category,
            'message': message,
            'status': 'open',
            'priority': 'medium',
            'created_at': datetime.datetime.now().isoformat(),
            'updated_at': datetime.datetime.now().isoformat(),
            'responses': [],
            'assigned_to': None,
            'resolution': None
        }
        
        self.support_tickets['tickets'].append(ticket)
        self.support_tickets['next_ticket_id'] += 1
        self.support_tickets['active_tickets'] += 1
        self.support_stats['total_tickets'] += 1
        
        # Update daily stats
        today = datetime.datetime.now().date().isoformat()
        if today not in self.support_stats['daily_tickets']:
            self.support_stats['daily_tickets'][today] = 0
        self.support_stats['daily_tickets'][today] += 1
        
        # Update category stats
        if category not in self.support_stats['category_stats']:
            self.support_stats['category_stats'][category] = 0
        self.support_stats['category_stats'][category] += 1
        
        self.save_support_tickets()
        self.save_support_stats()
        
        # Notify admins
        self.notify_admins_new_ticket(ticket)
        
        return ticket_id
    
    def get_user_tickets(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all tickets for a specific user"""
        return [ticket for ticket in self.support_tickets['tickets'] if ticket['user_id'] == user_id]
    
    def get_ticket_by_id(self, ticket_id: int) -> Optional[Dict[str, Any]]:
        """Get ticket by ID"""
        for ticket in self.support_tickets['tickets']:
            if ticket['id'] == ticket_id:
                return ticket
        return None
    
    def add_ticket_response(self, ticket_id: int, responder_id: int, response: str, is_admin: bool = False):
        """Add response to a ticket"""
        ticket = self.get_ticket_by_id(ticket_id)
        if not ticket:
            return False
        
        response_data = {
            'id': len(ticket['responses']) + 1,
            'responder_id': responder_id,
            'response': response,
            'is_admin': is_admin,
            'timestamp': datetime.datetime.now().isoformat()
        }
        
        ticket['responses'].append(response_data)
        ticket['updated_at'] = datetime.datetime.now().isoformat()
        
        self.save_support_tickets()
        
        # Notify user if admin responded
        if is_admin:
            self.notify_user_ticket_response(ticket, response_data)
        
        return True
    
    def resolve_ticket(self, ticket_id: int, resolution: str, admin_id: int):
        """Resolve a support ticket"""
        ticket = self.get_ticket_by_id(ticket_id)
        if not ticket:
            return False
        
        ticket['status'] = 'resolved'
        ticket['resolution'] = resolution
        ticket['updated_at'] = datetime.datetime.now().isoformat()
        ticket['resolved_by'] = admin_id
        
        self.support_tickets['active_tickets'] -= 1
        self.support_tickets['resolved_tickets'] += 1
        self.support_stats['resolved_tickets'] += 1
        
        self.save_support_tickets()
        self.save_support_stats()
        
        # Notify user
        self.notify_user_ticket_resolved(ticket)
        
        return True
    
    def analyze_message_for_auto_response(self, message: str) -> Optional[str]:
        """Analyze message and return auto-response if applicable"""
        message_lower = message.lower()
        
        # Check for human agent requests first
        human_agent_keywords = [
            'human', 'agent', 'person', 'staff', 'representative', 
            'manager', 'supervisor', 'live chat', 'real person',
            'talk to someone', 'speak to', 'connect me', 'transfer me'
        ]
        
        for keyword in human_agent_keywords:
            if keyword in message_lower:
                return None  # Don't auto-respond, escalate to human
        
        # Check for auto-response patterns
        for category, data in self.auto_responses.items():
            for keyword in data['keywords']:
                if keyword in message_lower:
                    return data['response']
        
        return None
    
    def create_support_menu(self, user_id: int) -> InlineKeyboardMarkup:
        """Create support menu for users"""
        markup = InlineKeyboardMarkup(row_width=2)
        
        # Get user's tickets
        user_tickets = self.get_user_tickets(user_id)
        open_tickets = [t for t in user_tickets if t['status'] == 'open']
        
        markup.add(
            InlineKeyboardButton('📝 Create Ticket', callback_data='support_create_ticket'),
            InlineKeyboardButton(f'📋 My Tickets ({len(open_tickets)})', callback_data='support_my_tickets')
        )
        
        markup.add(
            InlineKeyboardButton('❓ FAQ', callback_data='support_faq'),
            InlineKeyboardButton('👤 Speak with Human', callback_data='support_human_agent')
        )
        
        markup.add(
            InlineKeyboardButton('🔙 Back to Menu', callback_data='back')
        )
        
        return markup
    
    def create_support_category_menu(self) -> InlineKeyboardMarkup:
        """Create support category selection menu"""
        markup = InlineKeyboardMarkup(row_width=2)
        
        for category in self.support_categories:
            markup.add(InlineKeyboardButton(category, callback_data=f'support_category_{category}'))
        
        markup.add(InlineKeyboardButton('🔙 Back to Support', callback_data='support_menu'))
        
        return markup
    
    def create_admin_support_menu(self) -> InlineKeyboardMarkup:
        """Create admin support management menu"""
        markup = InlineKeyboardMarkup(row_width=2)
        
        open_tickets = [t for t in self.support_tickets['tickets'] if t['status'] == 'open']
        
        markup.add(
            InlineKeyboardButton(f'📋 Open Tickets ({len(open_tickets)})', callback_data='admin_support_tickets'),
            InlineKeyboardButton('📊 Support Stats', callback_data='admin_support_stats')
        )
        
        markup.add(
            InlineKeyboardButton('⚙️ Support Settings', callback_data='admin_support_settings'),
            InlineKeyboardButton('📝 Response Templates', callback_data='admin_support_templates')
        )
        
        markup.add(
            InlineKeyboardButton('🔙 Back to Admin', callback_data='admin_back_management')
        )
        
        return markup
    
    def notify_admins_new_ticket(self, ticket: Dict[str, Any]):
        """Notify admins about new support ticket"""
        for admin in self.admin_config['admin_users']:
            try:
                admin_id = admin['user_id']
                notification_text = f"""
🚨 **New Support Ticket**

**Ticket ID:** #{ticket['id']}
**User:** @{ticket['username']} ({ticket['user_id']})
**Category:** {ticket['category']}
**Status:** {ticket['status'].title()}

**Message:**
{ticket['message'][:200]}{'...' if len(ticket['message']) > 200 else ''}

**Created:** {ticket['created_at']}
                """.strip()
                
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton('📋 View Ticket', callback_data=f'admin_view_ticket_{ticket["id"]}'))
                
                self.bot.send_message(admin_id, notification_text, reply_markup=markup)
                
            except Exception as e:
                print(f"Failed to notify admin {admin_id} about new ticket: {e}")
    
    def notify_user_ticket_response(self, ticket: Dict[str, Any], response: Dict[str, Any]):
        """Notify user about ticket response"""
        try:
            notification_text = f"""
📨 **Response to Ticket #{ticket['id']}**

**Category:** {ticket['category']}

**Admin Response:**
{response['response']}

**Status:** {ticket['status'].title()}
**Time:** {response['timestamp']}

Thank you for your patience!
            """.strip()
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton('📋 View Full Ticket', callback_data=f'support_view_ticket_{ticket["id"]}'))
            
            self.bot.send_message(ticket['user_id'], notification_text, reply_markup=markup)
            
        except Exception as e:
            print(f"Failed to notify user {ticket['user_id']} about ticket response: {e}")
    
    def notify_user_ticket_resolved(self, ticket: Dict[str, Any]):
        """Notify user about ticket resolution"""
        try:
            # Format the resolution date
            resolved_date = datetime.datetime.fromisoformat(ticket['updated_at']).strftime('%Y-%m-%d %H:%M:%S')
            
            notification_text = f"""
🎉 **Your Issue Has Been Fixed!**

**Ticket ID:** #{ticket['id']}
**Category:** {ticket['category']}

**Resolution:**
{ticket['resolution']}

**Status:** ✅ Resolved
**Resolved On:** {resolved_date}

Your support ticket has been successfully resolved. If you have any other questions or need further assistance, please don't hesitate to create a new ticket.

Thank you for contacting us!
            """.strip()
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton('📝 Create New Ticket', callback_data='support_create_ticket'))
            markup.add(InlineKeyboardButton('🆘 Support', callback_data='support_menu'))
            markup.add(InlineKeyboardButton('🏠 Main Menu', callback_data='back'))
            
            self.bot.send_message(ticket['user_id'], notification_text, reply_markup=markup, parse_mode='Markdown')
            
            print(f"Successfully notified user {ticket['user_id']} about ticket #{ticket['id']} resolution")
            
        except Exception as e:
            print(f"Failed to notify user {ticket['user_id']} about ticket resolution: {e}")
    
    def notify_user_ticket_status_update(self, ticket: Dict[str, Any], status: str, message: str = None):
        """Notify user about ticket status updates"""
        try:
            status_emojis = {
                'open': '📝',
                'in_progress': '🔄',
                'pending': '⏳',
                'resolved': '✅',
                'closed': '🔒'
            }
            
            emoji = status_emojis.get(status, '📋')
            status_text = status.replace('_', ' ').title()
            
            notification_text = f"""
{emoji} **Ticket Status Update**

**Ticket ID:** #{ticket['id']}
**Category:** {ticket['category']}
**New Status:** {status_text}

{f"**Message:** {message}" if message else ""}

Your support ticket status has been updated. We're working on resolving your issue as quickly as possible.

Thank you for your patience!
            """.strip()
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton('🆘 Support', callback_data='support_menu'))
            markup.add(InlineKeyboardButton('🏠 Main Menu', callback_data='back'))
            
            self.bot.send_message(ticket['user_id'], notification_text, reply_markup=markup, parse_mode='Markdown')
            
            print(f"Successfully notified user {ticket['user_id']} about ticket #{ticket['id']} status update to {status}")
            
        except Exception as e:
            print(f"Failed to notify user {ticket['user_id']} about ticket status update: {e}")
    
    def update_ticket_status(self, ticket_id: int, new_status: str, admin_id: int, message: str = None):
        """Update ticket status and notify user"""
        ticket = self.get_ticket_by_id(ticket_id)
        if not ticket:
            return False
        
        old_status = ticket['status']
        ticket['status'] = new_status
        ticket['updated_at'] = datetime.datetime.now().isoformat()
        ticket['updated_by'] = admin_id
        
        # Update statistics based on status change
        if old_status == 'open' and new_status != 'open':
            self.support_tickets['active_tickets'] = max(0, self.support_tickets['active_tickets'] - 1)
        elif old_status != 'open' and new_status == 'open':
            self.support_tickets['active_tickets'] += 1
        
        # Save data
        self.save_support_tickets()
        self.save_support_stats()
        
        # Notify user about status change
        self.notify_user_ticket_status_update(ticket, new_status, message)
        
        return True
    
    def get_support_statistics(self) -> Dict[str, Any]:
        """Get comprehensive support statistics"""
        total_tickets = len(self.support_tickets['tickets'])
        open_tickets = len([t for t in self.support_tickets['tickets'] if t['status'] == 'open'])
        resolved_tickets = len([t for t in self.support_tickets['tickets'] if t['status'] == 'resolved'])
        
        # Calculate average response time
        avg_response_time = 0
        if resolved_tickets > 0:
            total_time = 0
            for ticket in self.support_tickets['tickets']:
                if ticket['status'] == 'resolved' and len(ticket['responses']) > 0:
                    created = datetime.datetime.fromisoformat(ticket['created_at'])
                    resolved = datetime.datetime.fromisoformat(ticket['updated_at'])
                    total_time += (resolved - created).total_seconds()
            avg_response_time = total_time / resolved_tickets / 3600  # Convert to hours
        
        return {
            'total_tickets': total_tickets,
            'open_tickets': open_tickets,
            'resolved_tickets': resolved_tickets,
            'avg_response_time_hours': round(avg_response_time, 2),
            'category_stats': self.support_stats['category_stats'],
            'daily_tickets': self.support_stats['daily_tickets'],
            'auto_responses_enabled': self.support_responses['auto_responses_enabled']
        }
    
    def start_support_monitoring(self):
        """Start support system monitoring"""
        def monitor_support():
            while True:
                try:
                    # Check for tickets that need attention
                    open_tickets = [t for t in self.support_tickets['tickets'] if t['status'] == 'open']
                    
                    for ticket in open_tickets:
                        # Check if ticket is older than 24 hours without response
                        created = datetime.datetime.fromisoformat(ticket['created_at'])
                        if datetime.datetime.now() - created > datetime.timedelta(hours=24):
                            if not ticket.get('escalated', False):
                                self.escalate_ticket(ticket['id'])
                    
                    time.sleep(3600)  # Check every hour
                    
                except Exception as e:
                    print(f"Support monitoring error: {e}")
                    time.sleep(3600)
        
        monitor_thread = threading.Thread(target=monitor_support, daemon=True)
        monitor_thread.start()
        print("Support monitoring started")
    
    def escalate_ticket(self, ticket_id: int):
        """Escalate ticket to high priority"""
        ticket = self.get_ticket_by_id(ticket_id)
        if ticket:
            ticket['priority'] = 'high'
            ticket['escalated'] = True
            ticket['updated_at'] = datetime.datetime.now().isoformat()
            
            # Notify admins about escalation
            for admin in self.admin_config['admin_users']:
                try:
                    admin_id = admin['user_id']
                    escalation_text = f"""
🚨 **TICKET ESCALATED**

**Ticket ID:** #{ticket['id']}
**User:** @{ticket['username']}
**Category:** {ticket['category']}
**Priority:** HIGH
**Age:** 24+ hours

This ticket needs immediate attention!
                    """.strip()
                    
                    markup = InlineKeyboardMarkup()
                    markup.add(InlineKeyboardButton('📋 View Ticket', callback_data=f'admin_view_ticket_{ticket["id"]}'))
                    
                    self.bot.send_message(admin_id, escalation_text, reply_markup=markup)
                    
                except Exception as e:
                    print(f"Failed to notify admin about escalation: {e}")
            
            self.save_support_tickets()
    
    def notify_admins_human_agent_request(self, user_id: int, username: str, message: str):
        """Notify admins when user requests human agent"""
        for admin in self.admin_config['admin_users']:
            try:
                admin_id = admin['user_id']
                
                notification_text = f"""
👤 **HUMAN AGENT REQUEST**

**User:** @{username} ({user_id})
**Message:** {message[:200]}{'...' if len(message) > 200 else ''}

**Request Type:** Human Agent Support
**Priority:** HIGH
**Timestamp:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Action Required:** User wants to speak with a human agent.
Please respond to this user directly.
                """.strip()
                
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton('💬 Respond to User', callback_data=f'admin_respond_user_{user_id}'))
                markup.add(InlineKeyboardButton('📋 Create Support Ticket', callback_data=f'admin_create_ticket_{user_id}'))
                
                self.bot.send_message(admin_id, notification_text, reply_markup=markup)
                
            except Exception as e:
                print(f"Failed to notify admin {admin_id} about human agent request: {e}")

# Support state management
support_states = {}

def setup_support_handlers(bot, support_manager):
    """Setup support-related handlers"""
    
    @bot.message_handler(commands=['support'])
    def support_menu(message):
        user_id = message.from_user.id
        username = message.from_user.username or "Unknown"
        
        support_text = """
🆘 **Customer Support**

How can we help you today?

**Quick Options:**
• 📝 Create a support ticket
• 📋 View your existing tickets
• ❓ Browse frequently asked questions
• 💬 Get live assistance

**Auto-Response System:**
Our smart system can instantly help with common questions about orders, payments, and products.

Choose an option below or just type your question!
        """.strip()
        
        bot.reply_to(message, support_text, reply_markup=support_manager.create_support_menu(user_id))
    
    @bot.message_handler(func=lambda message: message.text and not message.text.startswith('/') and not message.text.startswith('admin'))
    def handle_support_message(message):
        """Handle messages for auto-response and ticket creation"""
        user_id = message.from_user.id
        username = message.from_user.username or "Unknown"
        text = message.text
        
        # Check if user is waiting for address input - if so, skip support handling
        try:
            # Access user_states from global scope
            user_states = globals().get('user_states', {})
            if user_id in user_states and user_states[user_id].get('waiting_for_address'):
                print(f"Support: Skipping support handling for user {user_id} - waiting for address input")
                return  # Let user_bot_clean.py handle the address input
        except Exception as e:
            print(f"Support: Error checking user state: {e}")
        
        # print(f"Support message handler: User {user_id} sent: '{text}'")
        
        # Check if user is in support state
        if user_id in support_states:
            state = support_states[user_id]
            
            if state['action'] == 'creating_ticket':
                if text.lower() in ['cancel', 'stop', 'exit']:
                    del support_states[user_id]
                    bot.reply_to(message, "❌ Ticket creation cancelled.")
                    return
                
                # Create ticket
                ticket_id = support_manager.create_support_ticket(
                    user_id, username, state['category'], text
                )
                
                del support_states[user_id]
                
                success_text = f"""
✅ **Support Ticket Created**

**Ticket ID:** #{ticket_id}
**Category:** {state['category']}
**Status:** Open

Your ticket has been submitted successfully! Our support team will respond within 24 hours.

You can check your ticket status anytime using /support
                """.strip()
                
                bot.reply_to(message, success_text)
                return
        
        # Check for human agent request first
        human_agent_keywords = [
            'human', 'agent', 'person', 'staff', 'representative', 
            'manager', 'supervisor', 'live chat', 'real person',
            'talk to someone', 'speak to', 'connect me', 'transfer me',
            'ami human er sathe kotha bolte chai', 'human agent chai',
            'staff er sathe kotha bolte hobe', 'manager er sathe kotha'
        ]
        
        message_lower = text.lower()
        is_human_request = any(keyword in message_lower for keyword in human_agent_keywords)
        
        if is_human_request:
            # Notify admins about human agent request
            support_manager.notify_admins_human_agent_request(user_id, username, text)
            
            # Send confirmation to user
            human_response = """
👤 **Human Agent Request Received**

Thank you for your request! I've notified our support team that you'd like to speak with a human agent.

**What happens next:**
• Our support team will respond to you directly
• You'll receive a personal message from our staff
• Response time: Usually within 1-2 hours

**In the meantime:**
• You can continue using our bot for other questions
• Browse our FAQ for quick answers
• Create a support ticket for detailed issues

We appreciate your patience!
            """.strip()
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton('📋 Create Support Ticket', callback_data='support_create_ticket'))
            markup.add(InlineKeyboardButton('❓ Browse FAQ', callback_data='support_faq'))
            
            bot.reply_to(message, human_response, reply_markup=markup)
            return
        
        # Check for auto-response
        auto_response = support_manager.analyze_message_for_auto_response(text)
        if auto_response:
            bot.reply_to(message, auto_response)
            return
        
        # If no auto-response and not in support state, suggest creating ticket
        if len(text) > 3:  # Respond to any substantial message
            print(f"Support: No auto-response found for message: '{text}' from user {user_id}")
            
            suggestion_text = f"""
🤖 **I'm here to help!**

I received your message: "{text[:100]}{'...' if len(text) > 100 else ''}"

While I couldn't find an automatic response, I can help you with:

**Common Topics:**
• 📦 Order status and tracking
• 💳 Payment methods and issues  
• 🛍️ Product information
• 🚚 Shipping and delivery
• 💰 Refunds and returns
• 🔧 Technical problems

**What would you like to do?**
            """.strip()
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton('📝 Create Support Ticket', callback_data='support_create_ticket'))
            markup.add(InlineKeyboardButton('👤 Speak with Human', callback_data='support_human_agent'))
            markup.add(InlineKeyboardButton('❓ Browse FAQ', callback_data='support_faq'))
            markup.add(InlineKeyboardButton('🔙 Main Menu', callback_data='back'))
            
            bot.reply_to(message, suggestion_text, reply_markup=markup)
        else:
            # For very short messages, just acknowledge
            bot.reply_to(message, "👋 Hi! How can I help you today? Use /support for more options.")
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('support_'))
    def support_callback_handler(call):
        user_id = call.from_user.id
        username = call.from_user.username or "Unknown"
        
        if call.data == 'support_menu':
            support_text = """
🆘 **Customer Support**

How can we help you today?
            """.strip()
            
            bot.edit_message_text(
                support_text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=support_manager.create_support_menu(user_id)
            )
        
        elif call.data == 'support_create_ticket':
            support_text = """
📝 **Create Support Ticket**

Please select the category that best describes your issue:
            """.strip()
            
            bot.edit_message_text(
                support_text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=support_manager.create_support_category_menu()
            )
        
        elif call.data.startswith('support_category_'):
            category = call.data.replace('support_category_', '')
            
            support_states[user_id] = {
                'action': 'creating_ticket',
                'category': category
            }
            
            category_text = f"""
📝 **Create Ticket - {category}**

Please describe your issue in detail. Be as specific as possible to help us assist you better.

**Category:** {category}

Type your message below, or type 'cancel' to abort.
            """.strip()
            
            bot.edit_message_text(
                category_text,
                call.message.chat.id,
                call.message.message_id
            )
        
        elif call.data == 'support_my_tickets':
            user_tickets = support_manager.get_user_tickets(user_id)
            
            if not user_tickets:
                tickets_text = """
📋 **My Support Tickets**

You don't have any support tickets yet.

Create your first ticket to get help with any issues!
                """.strip()
                
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton('📝 Create Ticket', callback_data='support_create_ticket'))
                markup.add(InlineKeyboardButton('🔙 Back to Support', callback_data='support_menu'))
                
                bot.edit_message_text(
                    tickets_text,
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=markup
                )
            else:
                tickets_text = f"""
📋 **My Support Tickets**

**Total Tickets:** {len(user_tickets)}

"""
                
                for ticket in user_tickets[-5:]:  # Show last 5 tickets
                    status_emoji = "🟢" if ticket['status'] == 'open' else "✅"
                    tickets_text += f"{status_emoji} **#{ticket['id']}** - {ticket['category']} ({ticket['status']})\n"
                
                if len(user_tickets) > 5:
                    tickets_text += f"\n... and {len(user_tickets) - 5} more tickets"
                
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton('📝 Create New Ticket', callback_data='support_create_ticket'))
                markup.add(InlineKeyboardButton('🔙 Back to Support', callback_data='support_menu'))
                
                bot.edit_message_text(
                    tickets_text,
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=markup
                )
        
        elif call.data == 'support_faq':
            faq_text = """
❓ **Frequently Asked Questions**

**Q: How do I check my order status?**
A: Use /orders command or click '📦 Orders' in main menu.

**Q: What payment methods do you accept?**
A: We accept Bitcoin (BTC) and Monero (XMR).

**Q: How long does delivery take?**
A: Delivery times vary by country. Check product details for specific information.

**Q: Can I cancel my order?**
A: Orders can be cancelled before payment is confirmed.

**Q: How do I contact support?**
A: Use /support command or create a support ticket.

**Need more help?** Create a support ticket for personalized assistance!
            """.strip()
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton('📝 Create Support Ticket', callback_data='support_create_ticket'))
            markup.add(InlineKeyboardButton('🔙 Back to Support', callback_data='support_menu'))
            
            bot.edit_message_text(
                faq_text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup
            )
        
        elif call.data == 'support_live_chat':
            live_chat_text = """
💬 **Live Chat**

Our live chat is currently available through support tickets.

**How it works:**
1. Create a support ticket
2. Our team responds within 24 hours
3. Continue the conversation in your ticket

**For urgent issues:**
Create a high-priority ticket and we'll respond faster!

**Average response time:** 2-4 hours
            """.strip()
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton('📝 Create Support Ticket', callback_data='support_create_ticket'))
            markup.add(InlineKeyboardButton('🔙 Back to Support', callback_data='support_menu'))
            
            bot.edit_message_text(
                live_chat_text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup
            )
        
        elif call.data == 'support_human_agent':
            # Notify admins about human agent request
            support_manager.notify_admins_human_agent_request(user_id, username, "User requested human agent via support menu")
            
            human_agent_text = """
👤 **Human Agent Request**

I've notified our support team that you'd like to speak with a human agent.

**What happens next:**
• Our support team will respond to you directly
• You'll receive a personal message from our staff
• Response time: Usually within 1-2 hours

**In the meantime:**
• You can continue using our bot for other questions
• Browse our FAQ for quick answers
• Create a support ticket for detailed issues

We appreciate your patience!
            """.strip()
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton('📋 Create Support Ticket', callback_data='support_create_ticket'))
            markup.add(InlineKeyboardButton('❓ Browse FAQ', callback_data='support_faq'))
            markup.add(InlineKeyboardButton('🔙 Back to Support', callback_data='support_menu'))
            
            bot.edit_message_text(
                human_agent_text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup
            )
        
        bot.answer_callback_query(call.id, "Support option selected!")
