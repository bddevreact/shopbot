import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot.apihelper import ApiTelegramException
import json
import os
import qrcode
from PIL import Image
import gnupg
import random
import string
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config.env')

# Get configuration from environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in environment variables. Please check your config.env file.")

bot = telebot.TeleBot(BOT_TOKEN)

# Load admin configuration
with open('admin_config.json', 'r') as f:
    admin_config = json.load(f)

# Load categories from admin configuration
with open('admin_categories.json', 'r') as f:
    admin_data = json.load(f)
    categories = admin_data['categories']
    shop_info = admin_data['shop_info']


# Helper function to check if user is admin
def is_admin(user_id):
    return any(admin['user_id'] == user_id for admin in admin_config['admin_users'])

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

def safe_edit_message(bot, chat_id, message_id, text, reply_markup=None, parse_mode=None):
    """Safely edit a message, handling the 'message not modified' error"""
    try:
        bot.edit_message_text(text, chat_id, message_id, reply_markup=reply_markup, parse_mode=parse_mode)
    except ApiTelegramException as e:
        if "message is not modified" in str(e):
            # Message content is the same, just acknowledge the callback
            pass
        else:
            # Re-raise other API errors
            raise e

def create_main_menu(user_id):
    cart_total = sum(item['price'] for item in user_carts.get(user_id, []))
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton('🛍️ Products', callback_data='products'),
        InlineKeyboardButton('📖 Show About', callback_data='about')
    )
    markup.add(
        InlineKeyboardButton('🔑 Verify PGP Key', callback_data='pgp'),
        InlineKeyboardButton(f'🛒 Cart (€{cart_total:.2f})', callback_data='cart')
    )
    markup.add(
        InlineKeyboardButton('📦 Orders', callback_data='orders'),
        InlineKeyboardButton('📰 NWW Updates', callback_data='updates')
    )
    return markup

def create_country_menu():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton('🇩🇪 GER - WW', callback_data='country_GER'))
    markup.add(InlineKeyboardButton('🇦🇺 AUS - AUS', callback_data='country_AUS'))
    markup.add(InlineKeyboardButton('🇺🇸 USA - USA', callback_data='country_USA'))
    markup.add(InlineKeyboardButton('🔙 Back to main menu', callback_data='back'))
    return markup

def create_categories_menu():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton('↩️ Back to main menu', callback_data='back'))
    for category in categories:
        markup.add(InlineKeyboardButton(category['name'], callback_data=f"category_{category['name']}"))
    return markup

def create_product_menu(category_name):
    markup = InlineKeyboardMarkup(row_width=1)
    # Find the category
    category = next((cat for cat in categories if cat['name'] == category_name), None)
    if category:
        for product in category['products']:
            markup.add(InlineKeyboardButton(f"{product['name']} - €{product['price']}", callback_data=f"add_{product['name'].replace(' ', '_')}_{product['price']}"))
    markup.add(InlineKeyboardButton('🔙 Back to Categories', callback_data='products'))
    return markup

def create_cart_menu(user_id):
    cart = user_carts.get(user_id, [])
    total = sum(item['price'] for item in cart)
    markup = InlineKeyboardMarkup()
    if cart:
        for item in cart:
            markup.add(InlineKeyboardButton(f"Remove {item['name']}", callback_data=f"remove_{item['name'].replace(' ', '_')}_{item['price']}"))
    markup.add(InlineKeyboardButton('💳 Checkout (BTC/XMR)', callback_data='checkout'))
    markup.add(InlineKeyboardButton('🔙 Back to Menu', callback_data='back'))
    return markup, total

def generate_qr(data, filename):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    img.save(filename)
    return filename

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    user_states[user_id] = {'country': None, 'pgp_state': None, 'pgp_challenge': None}
    welcome_text = f"""
🌍 {shop_info['name']} 📦 🌏 ✈️

Currency: {shop_info['currency']}
Payments: {' / '.join(shop_info['payment_methods'])}

Available countries:
🇩🇪 GER - WW
🇦🇺 AUS - AUS
🇺🇸 USA - USA

Powered by Mr Zoidberg

✨ {shop_info['promotion']} ✨
"PLEASE READ 'Show About' BEFORE"

✅ Premium quality & best prices
✅ Ninja packaging
✅ Worldwide shipping

📦 WE SHIP:
[🇪🇺 EUROPE] [🇦🇺 AUS] [🇺🇸 USA]

📞 Telegram for all latest updates
{shop_info['contact']['telegram_bot']} & {shop_info['contact']['updates_channel']}

CEO {shop_info['contact']['ceo']}
    """.strip()
    bot.send_message(message.chat.id, welcome_text, reply_markup=create_main_menu(user_id), parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    if user_id not in user_states:
        user_states[user_id] = {'country': None, 'pgp_state': None, 'pgp_challenge': None}
    
    if call.data == 'products':
        if not user_states[user_id]['country']:
            country_text = "Available countries:\nPlease select your country to view products."
            safe_edit_message(bot, call.message.chat.id, call.message.message_id, country_text, reply_markup=create_country_menu())
        else:
            categories_text = f"Available categories:"
            safe_edit_message(bot, call.message.chat.id, call.message.message_id, categories_text, reply_markup=create_categories_menu())
    elif call.data.startswith('country_'):
        country = call.data.split('_')[1]
        user_states[user_id]['country'] = country
        bot.answer_callback_query(call.id, f"Selected country: {country}")
        # Proceed to categories
        categories_text = f"Available categories:"
        safe_edit_message(bot, call.message.chat.id, call.message.message_id, categories_text, reply_markup=create_categories_menu())
    elif call.data.startswith('category_'):
        category_name = call.data.split('_', 1)[1]
        # Find the category
        category = next((cat for cat in categories if cat['name'] == category_name), None)
        if category:
            product_text = f"🛍️ **{category_name}**\n\n" + "\n".join([f"• {p['name']} - €{p['price']}" for p in category['products']])
            safe_edit_message(bot, call.message.chat.id, call.message.message_id, product_text, reply_markup=create_product_menu(category_name), parse_mode='Markdown')
    elif call.data == 'about':
        about_text = f"""
📖 **Show About**

{shop_info['name']}: Premium quality & best prices
Ninja packaging experience
Worldwide shipping

{shop_info['promotion']}

Currency: {shop_info['currency']} | Payments: {'/'.join(shop_info['payment_methods'])}
Countries: {', '.join(shop_info['countries'])}

Powered by Mr Zoidberg
        """.strip()
        safe_edit_message(bot, call.message.chat.id, call.message.message_id, about_text, reply_markup=create_main_menu(user_id), parse_mode='Markdown')
    elif call.data == 'pgp':
        if gpg is None:
            pgp_text = """
🔑 **Verify PGP Key**

⚠️ PGP functionality is currently disabled.

To enable PGP features:
1. Install GPG for Windows from: https://www.gpg4win.org/
2. Configure your PGP keys in config.env
3. Restart the bot

For now, you can verify our authenticity through our official channels.
            """.strip()
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton('🔙 Back to Menu', callback_data='back'))
            safe_edit_message(bot, call.message.chat.id, call.message.message_id, pgp_text, reply_markup=markup, parse_mode='Markdown')
        else:
            # Sign a test message
            test_message = "Verify NWW Shop authenticity"
            signed_data = gpg.sign(test_message, passphrase=PRIVATE_PASSPHRASE, detach=True)
            signature = str(signed_data)
            
            pgp_text = f"""
🔑 **Verify PGP Key**

Public Key:
{PUBLIC_KEY}

Test Signed Message: "{test_message}"
Signature:
{signature}

Use GPG to verify offline, or test here.
            """.strip()
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton('✅ Test Verify Signature', callback_data='test_verify_pgp'))
            markup.add(InlineKeyboardButton('🔙 Back to Menu', callback_data='back'))
            safe_edit_message(bot, call.message.chat.id, call.message.message_id, pgp_text, reply_markup=markup, parse_mode='Markdown')
    elif call.data == 'test_verify_pgp':
        if gpg is None:
            bot.answer_callback_query(call.id, "PGP functionality is disabled. Please install GPG first.")
        else:
            # Generate challenge for user to sign
            challenge = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
            user_states[user_id]['pgp_challenge'] = challenge
            user_states[user_id]['pgp_state'] = 'waiting_signature'
            bot.answer_callback_query(call.id, "Challenge generated.")
            bot.send_message(call.message.chat.id, f"Sign this challenge with your PGP key and send the detached signature:\n\n{challenge}")
    elif call.data == 'cart':
        cart_markup, total = create_cart_menu(user_id)
        cart_text = f"🛒 **Cart** (Total: €{total:.2f})\n\n" + "\n".join([f"• {item['name']} - €{item['price']}" for item in user_carts.get(user_id, [])]) + "\n\nPayments: BTC / XMR"
        if total == 0:
            cart_text += "\nYour cart is empty."
        safe_edit_message(bot, call.message.chat.id, call.message.message_id, cart_text, reply_markup=cart_markup, parse_mode='Markdown')
    elif call.data == 'checkout':
        total = sum(item['price'] for item in user_carts.get(user_id, []))
        if total > 0:
            # Approximate conversions (use API for real)
            btc_amount = total * 0.000015  # ~1 EUR = 0.000015 BTC (demo rate)
            xmr_amount = total * 0.006     # ~1 EUR = 0.006 XMR (demo rate)
            
            btc_data = f"bitcoin:{BTC_ADDRESS}?amount={btc_amount}"
            xmr_data = f"monero:{XMR_ADDRESS}?tx_amount={xmr_amount}"
            
            btc_qr_file = 'btc_qr.png'
            xmr_qr_file = 'xmr_qr.png'
            generate_qr(btc_data, btc_qr_file)
            generate_qr(xmr_data, xmr_qr_file)
            
            checkout_text = f"💳 **Checkout**\n\nTotal: €{total:.2f} (~{btc_amount:.6f} BTC or ~{xmr_amount:.3f} XMR)\n\nScan QR or send to addresses.\nAfter payment, /upload_proof"
            safe_edit_message(bot,checkout_text, call.message.chat.id, call.message.message_id, parse_mode='Markdown')
            with open(btc_qr_file, 'rb') as btc_photo:
                bot.send_photo(call.message.chat.id, btc_photo, caption="BTC QR Code")
            with open(xmr_qr_file, 'rb') as xmr_photo:
                bot.send_photo(call.message.chat.id, xmr_photo, caption="XMR QR Code")
            
            # Clean up
            os.remove(btc_qr_file)
            os.remove(xmr_qr_file)
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton('✅ Payment Sent', callback_data='payment_sent'))
            markup.add(InlineKeyboardButton('🔙 Back to Cart', callback_data='cart'))
            bot.send_message(call.message.chat.id, "Confirm:", reply_markup=markup)
        else:
            bot.answer_callback_query(call.id, "Cart is empty!")
    elif call.data == 'payment_sent':
        bot.answer_callback_query(call.id, "Thanks! Order confirmed. Shipping soon 🚀")
    elif call.data == 'orders':
        orders_text = """
📦 **Orders**

Your recent orders:
• Order #123 - Delivered (USA)
• Order #456 - In Transit (GER)

Enter order ID to track: /track <ID>
        """.strip()
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton('🔙 Back to Menu', callback_data='back'))
        safe_edit_message(bot,orders_text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')
    elif call.data == 'updates':
        updates_text = """
📰 **NWW Updates**

Latest: 20% promo extended! New products incoming 🚀
Follow @NWWupdates for more.
        """.strip()
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton('🔙 Back to Menu', callback_data='back'))
        safe_edit_message(bot,updates_text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')
    elif call.data == 'back':
        safe_edit_message(bot,"Back to main menu.", call.message.chat.id, call.message.message_id, reply_markup=create_main_menu(user_id))
    elif call.data.startswith('add_'):
        parts = call.data.split('_', 2)
        if len(parts) == 3:
            name = parts[1].replace('_', ' ')
            price = float(parts[2])
            if user_id not in user_carts:
                user_carts[user_id] = []
            user_carts[user_id].append({'name': name, 'price': price})
            bot.answer_callback_query(call.id, f"Added {name} to cart!")
    elif call.data.startswith('remove_'):
        parts = call.data.split('_', 2)
        if len(parts) == 3:
            name = parts[1].replace('_', ' ')
            price = float(parts[2])
            if user_id in user_carts:
                user_carts[user_id] = [item for item in user_carts[user_id] if not (item['name'] == name and item['price'] == price)]
            bot.answer_callback_query(call.id, f"Removed {name} from cart!")
            # Refresh cart
            cart_markup, total = create_cart_menu(user_id)
            cart_text = f"🛒 **Cart** (Total: €{total:.2f})\n\n" + "\n".join([f"• {item['name']} - €{item['price']}" for item in user_carts.get(user_id, [])])
            if total == 0:
                cart_text += "\nYour cart is empty."
            safe_edit_message(bot, call.message.chat.id, call.message.message_id, cart_text, reply_markup=cart_markup, parse_mode='Markdown')
    elif call.data == 'admin_reload':
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ Access denied.")
            return
        try:
            with open('admin_categories.json', 'r') as f:
                admin_data = json.load(f)
                categories.clear()
                categories.extend(admin_data['categories'])
                shop_info.update(admin_data['shop_info'])
            bot.answer_callback_query(call.id, "✅ Categories reloaded!")
        except Exception as e:
            bot.answer_callback_query(call.id, f"❌ Error: {str(e)}")
    elif call.data == 'admin_stats':
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ Access denied.")
            return
        total_users = len(user_states)
        total_carts = len(user_carts)
        active_carts = sum(1 for cart in user_carts.values() if cart)
        total_categories = len(categories)
        total_products = sum(len(cat['products']) for cat in categories)
        
        stats_text = f"""
📊 **Bot Statistics**

👥 Users: {total_users}
🛒 Total Carts: {total_carts}
🛍️ Active Carts: {active_carts}
📦 Categories: {total_categories}
🏷️ Products: {total_products}
        """.strip()
        
        bot.send_message(call.message.chat.id, stats_text, parse_mode='Markdown')
        bot.answer_callback_query(call.id, "📊 Stats sent!")
    elif call.data == 'admin_users':
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ Access denied.")
            return
        users_text = f"""
👥 **User Statistics**

Total Users: {len(user_states)}
Users with Carts: {len(user_carts)}

Recent Users:
{chr(10).join([f"• User {uid}" for uid in list(user_states.keys())[-10:]])}
        """.strip()
        
        bot.send_message(call.message.chat.id, users_text, parse_mode='Markdown')
        bot.answer_callback_query(call.id, "👥 User data sent!")
    elif call.data == 'admin_backup':
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ Access denied.")
            return
        try:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_data = {
                "timestamp": timestamp,
                "user_states": user_states,
                "user_carts": user_carts,
                "categories": categories,
                "shop_info": shop_info
            }
            backup_filename = f"backup_{timestamp}.json"
            with open(backup_filename, 'w') as f:
                json.dump(backup_data, f, indent=2)
            bot.send_message(call.message.chat.id, f"✅ Backup created: {backup_filename}")
            bot.answer_callback_query(call.id, "💾 Backup created!")
        except Exception as e:
            bot.answer_callback_query(call.id, f"❌ Backup failed: {str(e)}")

# Admin Commands
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        bot.reply_to(message, "❌ Access denied. Admin privileges required.")
        return
    
    admin_text = """
🔧 **Admin Panel**

Available commands:
/admin - Show this panel
/reload - Reload categories from admin_categories.json
/stats - Show bot statistics
/users - Show user statistics
/backup - Create backup of current data

📁 Configuration Files:
- admin_categories.json - Manage categories and products
- admin_config.json - Manage admin users and settings
    """.strip()
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton('🔄 Reload Categories', callback_data='admin_reload'))
    markup.add(InlineKeyboardButton('📊 View Stats', callback_data='admin_stats'))
    markup.add(InlineKeyboardButton('👥 View Users', callback_data='admin_users'))
    markup.add(InlineKeyboardButton('💾 Create Backup', callback_data='admin_backup'))
    
    bot.reply_to(message, admin_text, reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(commands=['reload'])
def reload_categories(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        bot.reply_to(message, "❌ Access denied. Admin privileges required.")
        return
    
    try:
        with open('admin_categories.json', 'r') as f:
            admin_data = json.load(f)
            categories.clear()
            categories.extend(admin_data['categories'])
            shop_info.update(admin_data['shop_info'])
        bot.reply_to(message, "✅ Categories reloaded successfully!")
    except Exception as e:
        bot.reply_to(message, f"❌ Error reloading categories: {str(e)}")

@bot.message_handler(commands=['stats'])
def show_stats(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        bot.reply_to(message, "❌ Access denied. Admin privileges required.")
        return
    
    total_users = len(user_states)
    total_carts = len(user_carts)
    active_carts = sum(1 for cart in user_carts.values() if cart)
    total_categories = len(categories)
    total_products = sum(len(cat['products']) for cat in categories)
    
    stats_text = f"""
📊 **Bot Statistics**

👥 Users: {total_users}
🛒 Total Carts: {total_carts}
🛍️ Active Carts: {active_carts}
📦 Categories: {total_categories}
🏷️ Products: {total_products}

💾 Memory Usage:
- User States: {len(user_states)} entries
- User Carts: {len(user_carts)} entries
    """.strip()
    
    bot.reply_to(message, stats_text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    if user_id in user_states and user_states[user_id]['pgp_state'] == 'waiting_signature':
        if gpg is None:
            bot.reply_to(message, "❌ PGP functionality is disabled. Please install GPG first.")
            user_states[user_id]['pgp_state'] = None
            user_states[user_id]['pgp_challenge'] = None
        else:
            signature = message.text
            challenge = user_states[user_id]['pgp_challenge']
            verified = gpg.verify_data(signature, challenge)
            if verified:
                bot.reply_to(message, "✅ Signature verified successfully!")
            else:
                bot.reply_to(message, "❌ Verification failed. Try again.")
            user_states[user_id]['pgp_state'] = None
            user_states[user_id]['pgp_challenge'] = None

# Run the bot
if __name__ == '__main__':
    print("Bot starting...")
    bot.infinity_polling()