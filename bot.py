import telebot
import json
import os
import gnupg
from dotenv import load_dotenv
from user_bot import setup_user_handlers
from admin_bot import setup_admin_handlers
from notification_system import NotificationManager, setup_notification_handlers
from customer_support import CustomerSupportManager, setup_support_handlers
from recommendation_engine import RecommendationEngine, setup_recommendation_handlers
from fraud_detection import FraudDetectionSystem, setup_fraud_detection_handlers
from smart_auto_response import SmartAutoResponseSystem, setup_smart_auto_response_handlers

# Load environment variables
load_dotenv('config.env')

# Get configuration from environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in environment variables. Please check your config.env file.")

bot = telebot.TeleBot(BOT_TOKEN)

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

# In-memory storage
user_carts = {}  # user_id -> list of {'name': str, 'price': float}
user_states = {}  # user_id -> {'country': str, 'pgp_state': str, 'pgp_challenge': str}

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

print("Setting up notification system...")
notification_manager = NotificationManager(bot, categories, shop_info, user_carts, user_states)
setup_notification_handlers(bot, notification_manager)

print("Setting up customer support system...")
support_manager = CustomerSupportManager(bot, admin_config)
setup_support_handlers(bot, support_manager)

print("Setting up recommendation engine...")
recommendation_engine = RecommendationEngine(bot, categories, shop_info)
setup_recommendation_handlers(bot, recommendation_engine)

print("Setting up fraud detection system...")
fraud_detection = FraudDetectionSystem(bot, admin_config)
setup_fraud_detection_handlers(bot, fraud_detection)

print("Setting up smart auto-response system...")
smart_auto_response = SmartAutoResponseSystem(bot, categories, shop_info, user_carts, user_states)
setup_smart_auto_response_handlers(bot, smart_auto_response)

# Make all managers globally accessible
globals()['support_manager'] = support_manager
globals()['recommendation_engine'] = recommendation_engine
globals()['fraud_detection'] = fraud_detection
globals()['smart_auto_response'] = smart_auto_response

print("Setting up admin handlers...")
setup_admin_handlers(bot, admin_config, categories, shop_info, user_carts, user_states, notification_manager, support_manager, recommendation_engine, fraud_detection, smart_auto_response)

# Run the bot
if __name__ == '__main__':
    print("Bot starting...")
    print(f"Loaded {len(categories)} categories with {sum(len(cat['products']) for cat in categories)} products")
    print(f"Admin users: {len(admin_config['admin_users'])}")
    bot.infinity_polling()
