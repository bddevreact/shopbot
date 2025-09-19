import telebot
import json
import os
import gnupg
import signal
import sys
from datetime import datetime
from dotenv import load_dotenv

# Import professional modules
from config_manager import config_manager
from logger import bot_logger
from security import security_manager
from data_manager import data_manager
from ux_manager import ux_manager
from analytics import analytics_manager
from user_bot import setup_user_handlers
from admin_bot import setup_admin_handlers

# Validate configuration
config_validation = config_manager.validate_config()
if not config_validation['valid']:
    print("❌ Configuration validation failed:")
    for error in config_validation['errors']:
        print(f"  - {error}")
    sys.exit(1)

if config_validation['warnings']:
    print("⚠️ Configuration warnings:")
    for warning in config_validation['warnings']:
        print(f"  - {warning}")

# Get bot configuration
bot_config = config_manager.get_bot_config()
BOT_TOKEN = bot_config['token']

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in environment variables. Please check your config.env file.")

bot = telebot.TeleBot(BOT_TOKEN)

# Load admin configuration using data manager
admin_config = data_manager.load_data('admin_config.json', {
    "admin_users": [],
    "settings": {
        "auto_approve_orders": False,
        "notify_on_new_order": True,
        "notify_on_status_change": True
    }
})

# Get admin user ID from configuration
ADMIN_USER_ID = config_manager.get('admin_user_id')
if ADMIN_USER_ID:
    admin_user_id = int(ADMIN_USER_ID)
    # Check if this user ID is already in the admin list
    if not any(admin['user_id'] == admin_user_id for admin in admin_config['admin_users']):
        # Add the admin user if not already present
        admin_config['admin_users'].append({
            "user_id": admin_user_id,
            "username": "admin",
            "role": "super_admin",
            "permissions": ["manage_categories", "manage_products", "view_orders", "manage_users", "edit_shop_info"]
        })
        # Save the updated admin config
        data_manager.save_data('admin_config.json', admin_config)
        bot_logger.log_admin_action(admin_user_id, 'admin_user_added', {'source': 'environment'})
        print(f"Added admin user ID {admin_user_id} from environment variables")

# Load categories using data manager
admin_data = data_manager.load_data('admin_categories.json', {
    "categories": [],
    "shop_info": {
        "name": config_manager.get('shop_name', 'MrZoidbergBot Shop'),
        "currency": config_manager.get('currency', 'EUR'),
        "payment_methods": ["BTC", "XMR"],
        "countries": ["GER", "AUS", "USA"],
        "promotion": "Welcome to our shop!",
        "contact": {
            "telegram_bot": "@MrZoidbergBot",
            "updates_channel": "@NWWupdates",
            "ceo": "@MrWorldwide"
        }
    }
})

categories = admin_data['categories']
shop_info = admin_data['shop_info']

# In-memory storage
user_carts = {}  # user_id -> list of {'name': str, 'price': float}
user_states = {}  # user_id -> {'country': str, 'pgp_state': str, 'pgp_challenge': str}

# Get crypto wallet addresses from configuration
crypto_config = config_manager.get_crypto_config()
BTC_ADDRESS = crypto_config['btc_address']
XMR_ADDRESS = crypto_config['xmr_address']

if not BTC_ADDRESS or not XMR_ADDRESS:
    raise ValueError("Cryptocurrency addresses not found in configuration. Please check your config.env file.")

# PGP Setup - Optional functionality
pgp_config = config_manager.get_pgp_config()
gpg = None
PUBLIC_KEY = pgp_config['public_key']
PRIVATE_PASSPHRASE = pgp_config['private_passphrase']

# Try to initialize GPG, but don't fail if it's not available
if pgp_config['enabled']:
    try:
        gpg = gnupg.GPG()  # Uses default GPG home; set gnupghome='/path/to/gpg' if needed
        if PUBLIC_KEY and PRIVATE_PASSPHRASE:
            # Import public key if not already (run once)
            if not gpg.list_keys(keys=['nwwshop@example.com']):
                import_result = gpg.import_keys(PUBLIC_KEY)
                bot_logger.logger.info(f"Imported PGP key: {import_result}")
        else:
            bot_logger.logger.warning("PGP configuration not found in environment variables. PGP features will be disabled.")
            gpg = None
    except OSError as e:
        bot_logger.logger.warning(f"GPG not available ({e}). PGP features will be disabled.")
        gpg = None
else:
    bot_logger.logger.info("PGP features disabled in configuration")
    gpg = None

# Graceful shutdown handler
def signal_handler(signum, frame):
    bot_logger.logger.info("Received shutdown signal, gracefully stopping bot...")
    analytics_manager.cleanup_old_data()
    data_manager.cleanup_old_backups()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Setup all handlers
bot_logger.logger.info("Setting up user handlers...")
setup_user_handlers(bot, categories, shop_info, user_carts, user_states, gpg, PUBLIC_KEY, PRIVATE_PASSPHRASE, BTC_ADDRESS, XMR_ADDRESS, admin_config)

bot_logger.logger.info("Setting up admin handlers...")
setup_admin_handlers(bot, admin_config, categories, shop_info, user_carts, user_states)

# Run the bot
if __name__ == '__main__':
    bot_logger.logger.info("Bot starting...")
    bot_logger.logger.info(f"Loaded {len(categories)} categories with {sum(len(cat['products']) for cat in categories)} products")
    bot_logger.logger.info(f"Admin users: {len(admin_config['admin_users'])}")
    
    # Log system health
    system_health = analytics_manager.get_system_health()
    bot_logger.logger.info(f"System health: {system_health['health_status']}")
    
    # Create initial backup
    if config_manager.get('enable_backups'):
        backup_path = data_manager.create_manual_backup("startup")
        bot_logger.logger.info(f"Created startup backup: {backup_path}")
    
    try:
        bot.infinity_polling()
    except Exception as e:
        bot_logger.log_error(e, "Bot main loop")
        raise
