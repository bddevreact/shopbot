import logging
import os
import json
from datetime import datetime
from typing import Dict, Any

class BotLogger:
    """Professional logging system for MrZoidbergBot"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        self.setup_logging()
    
    def setup_logging(self):
        """Setup professional logging configuration"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # Main logger
        self.logger = logging.getLogger('MrZoidbergBot')
        self.logger.setLevel(logging.INFO)
        
        # File handler for detailed logs
        file_handler = logging.FileHandler(
            os.path.join(self.log_dir, f'bot_{datetime.now().strftime("%Y%m%d")}.log'),
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(detailed_formatter)
        
        # Console handler for simple logs
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(simple_formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def log_user_action(self, user_id: int, action: str, details: Dict[str, Any] = None):
        """Log user actions for analytics"""
        log_data = {
            'user_id': user_id,
            'action': action,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        self.logger.info(f"USER_ACTION: {json.dumps(log_data, ensure_ascii=False)}")
    
    def log_admin_action(self, admin_id: int, action: str, details: Dict[str, Any] = None):
        """Log admin actions for security"""
        log_data = {
            'admin_id': admin_id,
            'action': action,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        self.logger.info(f"ADMIN_ACTION: {json.dumps(log_data, ensure_ascii=False)}")
    
    def log_order_event(self, order_id: str, event: str, details: Dict[str, Any] = None):
        """Log order-related events"""
        log_data = {
            'order_id': order_id,
            'event': event,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        self.logger.info(f"ORDER_EVENT: {json.dumps(log_data, ensure_ascii=False)}")
    
    def log_error(self, error: Exception, context: str = ""):
        """Log errors with context"""
        self.logger.error(f"ERROR in {context}: {str(error)}", exc_info=True)
    
    def log_security_event(self, event_type: str, user_id: int, details: Dict[str, Any] = None):
        """Log security-related events"""
        log_data = {
            'event_type': event_type,
            'user_id': user_id,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        self.logger.warning(f"SECURITY_EVENT: {json.dumps(log_data, ensure_ascii=False)}")

# Global logger instance
bot_logger = BotLogger()
