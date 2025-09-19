import os
import json
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

class ConfigManager:
    """Professional configuration management system"""
    
    def __init__(self, config_file: str = "config.env"):
        self.config_file = config_file
        self.config_data = {}
        self.load_config()
    
    def load_config(self):
        """Load configuration from environment file"""
        if os.path.exists(self.config_file):
            load_dotenv(self.config_file)
        
        # Load all configuration values
        self.config_data = {
            'bot_token': os.getenv('BOT_TOKEN'),
            'admin_user_id': os.getenv('ADMIN_USER_ID'),
            'btc_address': os.getenv('BTC_ADDRESS'),
            'xmr_address': os.getenv('XMR_ADDRESS'),
            'pgp_public_key': os.getenv('PGP_PUBLIC_KEY'),
            'pgp_private_passphrase': os.getenv('PGP_PRIVATE_PASSPHRASE'),
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'backup_retention_days': int(os.getenv('BACKUP_RETENTION_DAYS', '30')),
            'rate_limit_seconds': int(os.getenv('RATE_LIMIT_SECONDS', '1')),
            'max_failed_attempts': int(os.getenv('MAX_FAILED_ATTEMPTS', '5')),
            'session_timeout_hours': int(os.getenv('SESSION_TIMEOUT_HOURS', '24')),
            'enable_pgp': os.getenv('ENABLE_PGP', 'false').lower() == 'true',
            'enable_logging': os.getenv('ENABLE_LOGGING', 'true').lower() == 'true',
            'enable_backups': os.getenv('ENABLE_BACKUPS', 'true').lower() == 'true',
            'shop_name': os.getenv('SHOP_NAME', 'MrZoidbergBot Shop'),
            'currency': os.getenv('CURRENCY', 'EUR'),
            'default_country': os.getenv('DEFAULT_COUNTRY', 'GER'),
            'maintenance_mode': os.getenv('MAINTENANCE_MODE', 'false').lower() == 'true',
            'maintenance_message': os.getenv('MAINTENANCE_MESSAGE', 'Bot is under maintenance. Please try again later.')
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config_data.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value"""
        self.config_data[key] = value
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate configuration and return validation results"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Required configurations
        required_configs = {
            'bot_token': 'Bot token is required',
            'btc_address': 'Bitcoin address is required',
            'xmr_address': 'Monero address is required'
        }
        
        for config_key, error_message in required_configs.items():
            if not self.get(config_key):
                validation_result['valid'] = False
                validation_result['errors'].append(error_message)
        
        # Optional but recommended configurations
        if not self.get('admin_user_id'):
            validation_result['warnings'].append('Admin user ID not set - admin features will be limited')
        
        if self.get('enable_pgp') and not self.get('pgp_public_key'):
            validation_result['warnings'].append('PGP enabled but public key not configured')
        
        # Validate numeric values
        try:
            int(self.get('backup_retention_days', 30))
            int(self.get('rate_limit_seconds', 1))
            int(self.get('max_failed_attempts', 5))
            int(self.get('session_timeout_hours', 24))
        except ValueError:
            validation_result['valid'] = False
            validation_result['errors'].append('Invalid numeric configuration values')
        
        return validation_result
    
    def get_bot_config(self) -> Dict[str, Any]:
        """Get bot-specific configuration"""
        return {
            'token': self.get('bot_token'),
            'admin_user_id': self.get('admin_user_id'),
            'maintenance_mode': self.get('maintenance_mode'),
            'maintenance_message': self.get('maintenance_message')
        }
    
    def get_crypto_config(self) -> Dict[str, Any]:
        """Get cryptocurrency configuration"""
        return {
            'btc_address': self.get('btc_address'),
            'xmr_address': self.get('xmr_address')
        }
    
    def get_pgp_config(self) -> Dict[str, Any]:
        """Get PGP configuration"""
        return {
            'enabled': self.get('enable_pgp'),
            'public_key': self.get('pgp_public_key'),
            'private_passphrase': self.get('pgp_private_passphrase')
        }
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration"""
        return {
            'rate_limit_seconds': self.get('rate_limit_seconds'),
            'max_failed_attempts': self.get('max_failed_attempts'),
            'session_timeout_hours': self.get('session_timeout_hours')
        }
    
    def get_shop_config(self) -> Dict[str, Any]:
        """Get shop configuration"""
        return {
            'name': self.get('shop_name'),
            'currency': self.get('currency'),
            'default_country': self.get('default_country')
        }
    
    def get_system_config(self) -> Dict[str, Any]:
        """Get system configuration"""
        return {
            'log_level': self.get('log_level'),
            'enable_logging': self.get('enable_logging'),
            'enable_backups': self.get('enable_backups'),
            'backup_retention_days': self.get('backup_retention_days')
        }
    
    def create_config_template(self, filename: str = "config.env.template"):
        """Create configuration template file"""
        template_content = """# MrZoidbergBot Configuration Template
# Copy this file to config.env and fill in your values

# Bot Configuration (REQUIRED)
BOT_TOKEN=your_bot_token_here
ADMIN_USER_ID=your_telegram_user_id_here

# Cryptocurrency Addresses (REQUIRED)
BTC_ADDRESS=your_bitcoin_address_here
XMR_ADDRESS=your_monero_address_here

# PGP Configuration (OPTIONAL)
ENABLE_PGP=false
PGP_PUBLIC_KEY=your_pgp_public_key_here
PGP_PRIVATE_PASSPHRASE=your_pgp_passphrase_here

# System Configuration (OPTIONAL)
LOG_LEVEL=INFO
BACKUP_RETENTION_DAYS=30
RATE_LIMIT_SECONDS=1
MAX_FAILED_ATTEMPTS=5
SESSION_TIMEOUT_HOURS=24

# Feature Toggles (OPTIONAL)
ENABLE_LOGGING=true
ENABLE_BACKUPS=true

# Shop Configuration (OPTIONAL)
SHOP_NAME=MrZoidbergBot Shop
CURRENCY=EUR
DEFAULT_COUNTRY=GER

# Maintenance Mode (OPTIONAL)
MAINTENANCE_MODE=false
MAINTENANCE_MESSAGE=Bot is under maintenance. Please try again later.
"""
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        return filename

# Global config manager instance
config_manager = ConfigManager()
