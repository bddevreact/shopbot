import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

class UXManager:
    """Professional user experience management system"""
    
    def __init__(self):
        self.user_sessions = {}  # user_id -> session_data
        self.typing_indicators = {}  # user_id -> last_typing_time
        self.user_preferences = {}  # user_id -> preferences
    
    def start_user_session(self, user_id: int, user_data: Dict[str, Any]):
        """Start a new user session"""
        self.user_sessions[user_id] = {
            'start_time': datetime.now(),
            'last_activity': datetime.now(),
            'actions_count': 0,
            'user_data': user_data,
            'session_id': f"session_{user_id}_{int(time.time())}"
        }
    
    def update_user_activity(self, user_id: int, action: str):
        """Update user activity tracking"""
        if user_id in self.user_sessions:
            self.user_sessions[user_id]['last_activity'] = datetime.now()
            self.user_sessions[user_id]['actions_count'] += 1
            self.user_sessions[user_id]['last_action'] = action
    
    def get_user_session_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user session information"""
        return self.user_sessions.get(user_id)
    
    def cleanup_inactive_sessions(self, hours: int = 24):
        """Clean up inactive sessions"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        inactive_users = []
        
        for user_id, session in self.user_sessions.items():
            if session['last_activity'] < cutoff_time:
                inactive_users.append(user_id)
        
        for user_id in inactive_users:
            del self.user_sessions[user_id]
    
    def create_loading_message(self, text: str = "Processing...") -> str:
        """Create loading message with animation"""
        return f"⏳ {text}"
    
    def create_success_message(self, text: str) -> str:
        """Create success message"""
        return f"✅ {text}"
    
    def create_error_message(self, text: str) -> str:
        """Create error message"""
        return f"❌ {text}"
    
    def create_warning_message(self, text: str) -> str:
        """Create warning message"""
        return f"⚠️ {text}"
    
    def create_info_message(self, text: str) -> str:
        """Create info message"""
        return f"ℹ️ {text}"
    
    def format_currency(self, amount: float, currency: str = "EUR") -> str:
        """Format currency amount"""
        if currency.upper() == "EUR":
            return f"€{amount:.2f}"
        elif currency.upper() == "USD":
            return f"${amount:.2f}"
        else:
            return f"{amount:.2f} {currency}"
    
    def format_timestamp(self, timestamp: datetime) -> str:
        """Format timestamp for display"""
        now = datetime.now()
        diff = now - timestamp
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"
    
    def create_pagination_buttons(self, current_page: int, total_pages: int, 
                                callback_prefix: str) -> InlineKeyboardMarkup:
        """Create pagination buttons"""
        markup = InlineKeyboardMarkup(row_width=5)
        
        # Previous button
        if current_page > 1:
            markup.add(InlineKeyboardButton("⬅️", callback_data=f"{callback_prefix}_page_{current_page-1}"))
        
        # Page numbers (show max 5 pages)
        start_page = max(1, current_page - 2)
        end_page = min(total_pages, current_page + 2)
        
        page_buttons = []
        for page in range(start_page, end_page + 1):
            if page == current_page:
                page_buttons.append(InlineKeyboardButton(f"•{page}•", callback_data=f"{callback_prefix}_page_{page}"))
            else:
                page_buttons.append(InlineKeyboardButton(str(page), callback_data=f"{callback_prefix}_page_{page}"))
        
        if page_buttons:
            markup.add(*page_buttons)
        
        # Next button
        if current_page < total_pages:
            markup.add(InlineKeyboardButton("➡️", callback_data=f"{callback_prefix}_page_{current_page+1}"))
        
        return markup
    
    def create_confirmation_dialog(self, message: str, confirm_callback: str, 
                                 cancel_callback: str) -> InlineKeyboardMarkup:
        """Create confirmation dialog"""
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("✅ Yes", callback_data=confirm_callback),
            InlineKeyboardButton("❌ No", callback_data=cancel_callback)
        )
        return markup
    
    def create_quick_actions_menu(self, actions: List[Dict[str, str]]) -> InlineKeyboardMarkup:
        """Create quick actions menu"""
        markup = InlineKeyboardMarkup(row_width=2)
        
        for action in actions:
            markup.add(InlineKeyboardButton(
                action['text'], 
                callback_data=action['callback']
            ))
        
        return markup
    
    def create_status_indicator(self, status: str) -> str:
        """Create status indicator"""
        status_indicators = {
            'pending': '⏳',
            'processing': '🔄',
            'shipped': '📦',
            'delivered': '✅',
            'cancelled': '❌',
            'active': '🟢',
            'inactive': '🔴',
            'warning': '🟡'
        }
        
        return status_indicators.get(status.lower(), '❓')
    
    def create_progress_bar(self, current: int, total: int, length: int = 10) -> str:
        """Create progress bar"""
        if total == 0:
            return "▱" * length
        
        filled = int((current / total) * length)
        empty = length - filled
        
        return "▰" * filled + "▱" * empty
    
    def get_user_preference(self, user_id: int, preference: str, default: Any = None) -> Any:
        """Get user preference"""
        return self.user_preferences.get(user_id, {}).get(preference, default)
    
    def set_user_preference(self, user_id: int, preference: str, value: Any):
        """Set user preference"""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {}
        self.user_preferences[user_id][preference] = value
    
    def create_help_text(self, command: str, description: str, 
                        usage: str = "", examples: List[str] = None) -> str:
        """Create help text for commands"""
        help_text = f"**{command}**\n{description}\n"
        
        if usage:
            help_text += f"\n**Usage:** `{usage}`"
        
        if examples:
            help_text += "\n**Examples:**"
            for example in examples:
                help_text += f"\n• `{example}`"
        
        return help_text

# Global UX manager instance
ux_manager = UXManager()
