import telebot
import json
import os
import gnupg
<<<<<<< HEAD
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

=======
from dotenv import load_dotenv
from user_bot import setup_user_handlers
from admin_bot import setup_admin_handlers

# Load environment variables
load_dotenv('config.env')

# Get configuration from environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')
>>>>>>> 5f2a61601dd6311cc5b35154e8405aed0090abf1
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in environment variables. Please check your config.env file.")

bot = telebot.TeleBot(BOT_TOKEN)

<<<<<<< HEAD
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
=======
# Load admin configuration
try:
    with open('admin_config.json', 'r', encoding='utf-8') as f:
        content = f.read().strip()
        if not content:
            raise ValueError("admin_config.json is empty")
        admin_config = json.loads(content)
except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
    print(f"Error loading admin_config.json: {e}")
    print("Creating default admin configuration...")
    admin_config = {
        "admin_users": [],
        "settings": {
            "auto_approve_orders": False,
            "notify_on_new_order": True,
            "notify_on_status_change": True
        }
    }
    with open('admin_config.json', 'w', encoding='utf-8') as f:
        json.dump(admin_config, f, indent=2, ensure_ascii=False)

# Get admin user ID from environment variables
ADMIN_USER_ID = os.getenv('ADMIN_USER_ID')
if ADMIN_USER_ID:
    # Update admin_config with the user ID from environment
>>>>>>> 5f2a61601dd6311cc5b35154e8405aed0090abf1
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
<<<<<<< HEAD
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
=======
        with open('admin_config.json', 'w', encoding='utf-8') as f:
            json.dump(admin_config, f, indent=2, ensure_ascii=False)
        print(f"Added admin user ID {admin_user_id} from environment variables")

# Load categories from admin configuration
try:
    with open('admin_categories.json', 'r', encoding='utf-8') as f:
        content = f.read().strip()
        if not content:
            raise ValueError("admin_categories.json is empty")
        admin_data = json.loads(content)
        categories = admin_data['categories']
        shop_info = admin_data['shop_info']
except (FileNotFoundError, json.JSONDecodeError, ValueError, KeyError) as e:
    print(f"Error loading admin_categories.json: {e}")
    print("Creating default categories configuration...")
    categories = []
    shop_info = {
        "shop_name": "MrZoidbergBot Shop",
        "description": "Welcome to our shop!",
        "contact_info": "Contact us for support"
    }
    admin_data = {
        "categories": categories,
        "shop_info": shop_info
    }
    with open('admin_categories.json', 'w', encoding='utf-8') as f:
        json.dump(admin_data, f, indent=2, ensure_ascii=False)
>>>>>>> 5f2a61601dd6311cc5b35154e8405aed0090abf1

# In-memory storage
user_carts = {}  # user_id -> list of {'name': str, 'price': float}
user_states = {}  # user_id -> {'country': str, 'pgp_state': str, 'pgp_challenge': str}

<<<<<<< HEAD
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
=======
# Get crypto wallet addresses from environment variables
BTC_ADDRESS = os.getenv('BTC_ADDRESS')
XMR_ADDRESS = os.getenv('XMR_ADDRESS')

if not BTC_ADDRESS or not XMR_ADDRESS:
    raise ValueError("Cryptocurrency addresses not found in environment variables. Please check your config.env file.")

# PGP Setup - Optional functionality
gpg = None
PUBLIC_KEY = os.getenv('PGP_PUBLIC_KEY')
PRIVATE_PASSPHRASE = os.getenv('PGP_PRIVATE_PASSPHRASE')

# Try to initialize GPG, but don't fail if it's not available
try:
    gpg = gnupg.GPG()  # Uses default GPG home; set gnupghome='/path/to/gpg' if needed
    if PUBLIC_KEY and PRIVATE_PASSPHRASE:
        # Import public key if not already (run once)
        if not gpg.list_keys(keys=['nwwshop@example.com']):
            import_result = gpg.import_keys(PUBLIC_KEY)
            print(f"Imported PGP key: {import_result}")
    else:
        print("Warning: PGP configuration not found in environment variables. PGP features will be disabled.")
        gpg = None
except OSError as e:
    print(f"Warning: GPG not available ({e}). PGP features will be disabled.")
    gpg = None

# Setup all handlers
print("Setting up user handlers...")
setup_user_handlers(bot, categories, shop_info, user_carts, user_states, gpg, PUBLIC_KEY, PRIVATE_PASSPHRASE, BTC_ADDRESS, XMR_ADDRESS, admin_config)

print("Setting up admin handlers...")
>>>>>>> 5f2a61601dd6311cc5b35154e8405aed0090abf1
setup_admin_handlers(bot, admin_config, categories, shop_info, user_carts, user_states)

# Run the bot
if __name__ == '__main__':
<<<<<<< HEAD
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
=======
    print("Bot starting...")
    print(f"Loaded {len(categories)} categories with {sum(len(cat['products']) for cat in categories)} products")
    print(f"Admin users: {len(admin_config['admin_users'])}")
    bot.infinity_polling()
>>>>>>> 5f2a61601dd6311cc5b35154e8405aed0090abf1
