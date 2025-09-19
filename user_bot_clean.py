import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot.apihelper import ApiTelegramException
import json
import os
import qrcode
from PIL import Image
import gnupg
import datetime
import random
import string

# Helper functions
def save_categories_to_file(categories, shop_info):
    """Save categories and shop_info to admin_categories.json"""
    data = {
        "shop_info": shop_info,
        "categories": categories
    }
    with open('admin_categories.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# User data management functions
def load_users():
    """Load users from users.json"""
    try:
        with open('users.json', 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                # File is empty, return default structure
                return {"users": [], "user_counter": 0, "statistics": {"total_users": 0}}
            return json.loads(content)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading users.json: {e}")
        # Return default structure and try to create a new file
        default_data = {"users": [], "user_counter": 0, "statistics": {"total_users": 0}}
        save_users(default_data)
        return default_data

def save_users(users_data):
    """Save users to users.json"""
    with open('users.json', 'w', encoding='utf-8') as f:
        json.dump(users_data, f, indent=2, ensure_ascii=False)

def get_user_by_id(user_id):
    """Get user by ID without creating new one"""
    users_data = load_users()
    
    for user in users_data.get('users', []):
        if user['user_id'] == user_id:
            return user
    
    return None

def get_or_create_user(user_id, username="", first_name="", last_name=""):
    """Get existing user or create new user entry"""
    users_data = load_users()
    
    # Check if user already exists
    existing_user = None
    for user in users_data.get('users', []):
        if user['user_id'] == user_id:
            existing_user = user
            break
    
    if existing_user:
        # User exists, return existing user data
        print(f"Found existing user: {user_id} - Order #{existing_user['order_number']}")
        return existing_user
    
    # Create new user entry only if user doesn't exist
    users_data['user_counter'] += 1
    full_name = f"{first_name} {last_name}".strip()
    
    user_data = {
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "join_date": datetime.datetime.now().isoformat(),
        "order_number": users_data['user_counter'],
        "phrase_verified": False,
        "personal_phrase_code": None
    }
    
    # Add to users list (not dictionary)
    if 'users' not in users_data:
        users_data['users'] = []
    
    users_data['users'].append(user_data)
    users_data['statistics']['total_users'] = len(users_data['users'])
    save_users(users_data)
    
    print(f"Created new user entry: {user_id} - Order #{users_data['user_counter']}")
    return user_data

# Simplified user data functions - only basic info stored
def save_user_cart(user_id, cart_items):
    """Save user cart to memory only (not permanent)"""
    pass  # No permanent cart storage needed

def save_user_state(user_id, state_data):
    """Save user state to memory only (not permanent)"""
    pass  # No permanent state storage needed

def add_user_order(user_id, order_id, order_data):
    """Order is already saved in orders.json, no need for user history"""
    pass  # Orders are stored in orders.json

# Order management functions
def load_orders():
    """Load orders from orders.json"""
    try:
        with open('orders.json', 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                # File is empty, return default structure
                return {"orders": [], "order_counter": 0, "statistics": {"total_orders": 0, "total_sales": 0.0, "total_users": 0, "orders_by_status": {"pending": 0, "processing": 0, "shipped": 0, "delivered": 0, "cancelled": 0}}}
            return json.loads(content)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading orders.json: {e}")
        # Return default structure and try to create a new file
        default_data = {"orders": [], "order_counter": 0, "statistics": {"total_orders": 0, "total_sales": 0.0, "total_users": 0, "orders_by_status": {"pending": 0, "processing": 0, "shipped": 0, "delivered": 0, "cancelled": 0}}}
        save_orders(default_data)
        return default_data

def save_orders(orders_data):
    """Save orders to orders.json"""
    with open('orders.json', 'w', encoding='utf-8') as f:
        json.dump(orders_data, f, indent=2, ensure_ascii=False)

def create_order(user_id, cart_items, delivery_method, delivery_price, payment_method, delivery_address, total_amount):
    """Create a new order and save it"""
    orders_data = load_orders()
    
    # Generate order ID
    orders_data['order_counter'] += 1
    order_id = f"ORD{orders_data['order_counter']:06d}"
    
    # Create order object
    order = {
        "order_id": order_id,
        "user_id": user_id,
        "timestamp": datetime.datetime.now().isoformat(),
        "status": "pending",
        "items": cart_items,
        "delivery_method": delivery_method,
        "delivery_price": delivery_price,
        "payment_method": payment_method,
        "delivery_address": delivery_address,
        "total_amount": total_amount,
        "crypto_amount": total_amount * (0.000015 if payment_method == 'btc' else 0.006),
        "notes": "",
        "tracking_number": ""
    }
    
    # Add to orders
    orders_data['orders'].append(order)
    
    # Update statistics
    orders_data['statistics']['total_orders'] += 1
    orders_data['statistics']['total_sales'] += total_amount
    orders_data['statistics']['orders_by_status']['pending'] += 1
    
    # Save orders
    save_orders(orders_data)
    
    return order_id

def notify_admin_new_order(bot, admin_config, order_id, user_id, total_amount):
    """Send notification to admin about new order"""
    for admin in admin_config['admin_users']:
        try:
            notification_text = f"""
≡ƒöö **New Order Received!**

**Order ID:** {order_id}
**User ID:** {user_id}
**Total Amount:** Γé¼{total_amount:.2f}
**Status:** Pending

Click /admin to manage orders.
            """.strip()
            bot.send_message(admin['user_id'], notification_text, parse_mode='Markdown')
        except Exception as e:
            print(f"Failed to notify admin {admin['user_id']}: {e}")

def safe_edit_message(bot, chat_id, message_id, text, reply_markup=None, parse_mode=None):
    """Safely edit a message, handling various edit errors"""
    try:
        bot.edit_message_text(text, chat_id, message_id, reply_markup=reply_markup, parse_mode=parse_mode)
    except ApiTelegramException as e:
        if "message is not modified" in str(e):
            # Message content is the same, just acknowledge the callback
            pass
        elif "no text in the message to edit" in str(e):
            # Trying to edit a photo/media message, send new message instead
            try:
                bot.send_message(chat_id, text, reply_markup=reply_markup, parse_mode=parse_mode)
            except Exception as send_error:
                print(f"Failed to send new message: {send_error}")
        else:
            # For other errors, try to send a new message
            try:
                bot.send_message(chat_id, text, reply_markup=reply_markup, parse_mode=parse_mode)
            except Exception as send_error:
                print(f"Failed to send new message: {send_error}")
                # Don't re-raise to prevent crashes

def find_product_by_name(name, categories):
    """Find a product by name in all categories"""
    for category in categories:
        for product in category['products']:
            if product['name'] == name:
                return product
    return None

def validate_discount_code(code, shop_info, order_total):
    """Validate discount code and return discount info"""
    if 'discount_codes' not in shop_info:
        return None
    
    discount_codes = shop_info['discount_codes']
    if code.upper() not in discount_codes:
        return None
    
    discount_info = discount_codes[code.upper()]
    
    # Check if code is active
    if not discount_info.get('active', False):
        return None
    
    # Check usage limit
    if discount_info.get('used_count', 0) >= discount_info.get('usage_limit', 999999):
        return None
    
    # Check minimum order amount
    min_amount = discount_info.get('min_order_amount', 0)
    if order_total < min_amount:
        return None
    
    return discount_info

def apply_discount_code(code, shop_info, order_total, categories):
    """Apply discount code and update usage count"""
    discount_info = validate_discount_code(code, shop_info, order_total)
    if not discount_info:
        return None, "Invalid or expired discount code"
    
    # Calculate discount amount
    discount_percent = discount_info.get('discount_percent', 0)
    discount_amount = (order_total * discount_percent) / 100
    
    # Update usage count
    shop_info['discount_codes'][code.upper()]['used_count'] += 1
    
    # Save updated shop info
    save_categories_to_file(categories, shop_info)
    
    return {
        'code': code.upper(),
        'discount_percent': discount_percent,
        'discount_amount': discount_amount,
        'description': discount_info.get('description', '')
    }, "Discount applied successfully!"

def show_product_detail(bot, call, product, user_carts):
    """Show detailed product page with quantities and prices"""
    user_id = call.from_user.id
    
    # Create product detail text
    product_text = f"""
**{product['name']}**

{product.get('type', 'Product')}

{product.get('description', '')}

{product.get('shipping', '')}

After adding products just click to "≡ƒ¢Æ Cart" button

Product photo link -> {product.get('image_url', 'No image available')}
    """.strip()
    
    # Create quantity buttons
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton('≡ƒöÖ Back to main menu', callback_data='back'))
    
    for qty in product.get('quantities', []):
        button_text = f"{qty['amount']} - {qty['price']:.1f} eur"
        callback_data = f"qty_{product['name'].replace(' ', '|').replace('_', '|')}|{qty['amount']}|{qty['price']}"
        markup.add(InlineKeyboardButton(button_text, callback_data=callback_data))
    
    markup.add(InlineKeyboardButton('≡ƒ¢Æ Cart', callback_data='cart'))
    
    # Send product image if available
    if product.get('image_url'):
        try:
            # Send the image as a photo with caption and buttons
            bot.send_photo(call.message.chat.id, product['image_url'], caption=product_text, reply_markup=markup, parse_mode='Markdown')
            # Delete the original message since we're sending a new one with image
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except:
                pass  # Ignore if can't delete
        except Exception as e:
            print(f"Failed to send product image: {e}")
            # If image fails, send text only with image URL
            product_text += f"\n\n≡ƒû╝∩╕Å **Product Image:**\n{product['image_url']}"
            safe_edit_message(bot, call.message.chat.id, call.message.message_id, product_text, reply_markup=markup, parse_mode='Markdown')
    else:
        safe_edit_message(bot, call.message.chat.id, call.message.message_id, product_text, reply_markup=markup, parse_mode='Markdown')

def create_main_menu(user_id, user_carts, shop_info=None):
    cart_total = sum(item['price'] for item in user_carts.get(user_id, []))
    markup = InlineKeyboardMarkup(row_width=2)
    
    # Determine about button text based on visibility
    about_button_text = '≡ƒôû Show About'
    if shop_info and 'about' in shop_info and shop_info['about'].get('visible', False):
        about_button_text = '≡ƒôû Hide About'
    
    markup.add(
        InlineKeyboardButton('≡ƒ¢ì∩╕Å Products', callback_data='products'),
        InlineKeyboardButton(about_button_text, callback_data='about')
    )
    markup.add(
        InlineKeyboardButton('≡ƒöæ Verify PGP Key', callback_data='pgp'),
        InlineKeyboardButton(f'≡ƒ¢Æ Cart (Γé¼{cart_total:.2f})', callback_data='cart')
    )
    markup.add(
        InlineKeyboardButton('≡ƒôª Orders', callback_data='orders'),
        InlineKeyboardButton('≡ƒô░ NWW Updates', callback_data='updates')
    )
    markup.add(
        InlineKeyboardButton('≡ƒöä Restart Session', callback_data='restart_session')
    )
    return markup

def create_country_menu():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton('≡ƒç⌐≡ƒç¬ GER - WW', callback_data='country_GER'))
    markup.add(InlineKeyboardButton('≡ƒçª≡ƒç║ AUS - AUS', callback_data='country_AUS'))
    markup.add(InlineKeyboardButton('≡ƒç║≡ƒç╕ USA - USA', callback_data='country_USA'))
    markup.add(InlineKeyboardButton('≡ƒöÖ Back to main menu', callback_data='back'))
    return markup

def create_categories_menu(categories):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton('Γå⌐∩╕Å Back to main menu', callback_data='back'))
    for category in categories:
        markup.add(InlineKeyboardButton(category['name'], callback_data=f"category_{category['name']}"))
    return markup

def create_product_menu(category_name, categories):
    markup = InlineKeyboardMarkup(row_width=1)
    # Find the category
    category = next((cat for cat in categories if cat['name'] == category_name), None)
    if category:
        for product in category['products']:
            # Use a different separator to avoid conflicts with underscores in product names
            product_id = product['name'].replace(' ', '|').replace('_', '|')
            # Check if product has quantities (new format) or single price (old format)
            if 'quantities' in product:
                # New format - use a placeholder price since we'll show detail page
                markup.add(InlineKeyboardButton(product['name'], callback_data=f"add_{product_id}|0"))
            else:
                # Old format - use the single price
                markup.add(InlineKeyboardButton(product['name'], callback_data=f"add_{product_id}|{product['price']}"))
    markup.add(InlineKeyboardButton('≡ƒöÖ Back to Categories', callback_data='products'))
    return markup

def create_cart_menu(user_id, user_carts):
    cart = user_carts.get(user_id, [])
    total = sum(item['price'] for item in cart)
    markup = InlineKeyboardMarkup()
    if cart:
        for item in cart:
            # Create remove button with amount only (like in the image)
            amount = item.get('amount', 'item')
            markup.add(InlineKeyboardButton(f"Remove: {amount}", callback_data=f"remove_{item['name']}|{item['price']}"))
    markup.add(InlineKeyboardButton('≡ƒöÖ Back to main menu', callback_data='back'))
    markup.add(InlineKeyboardButton('≡ƒÆ│ Checkout', callback_data='checkout'))
    if cart:  # Only show restart button if cart has items
        markup.add(InlineKeyboardButton('≡ƒöä Clear Cart & Restart', callback_data='restart_session'))
    return markup, total

def create_delivery_menu(user_country):
    """Create delivery method menu based on user's country"""
    markup = InlineKeyboardMarkup(row_width=1)
    
    # Add back to cart button
    markup.add(InlineKeyboardButton('≡ƒöÖ Back to cart', callback_data='cart'))
    
    # Delivery methods based on country - using consistent format: delivery_region_method_price
    if user_country == 'GER' or user_country == 'EU':
        markup.add(InlineKeyboardButton('[EU] UNTRACKED SHIPPING ΓÇó 0.0 eur', callback_data='delivery_eu_untracked_0.0'))
        markup.add(InlineKeyboardButton('[EU] TRACKED SHIPPING ΓÇó 5.0 eur', callback_data='delivery_eu_tracked_5.0'))
    elif user_country == 'AUS':
        markup.add(InlineKeyboardButton('[AUS] EXPRESS SATCHEL ΓÇó 12.0 eur', callback_data='delivery_aus_express_12.0'))
        markup.add(InlineKeyboardButton('[AUS] EXTRA STEALTH ΓÇó 30.0 eur', callback_data='delivery_aus_stealth_30.0'))
    elif user_country == 'USA':
        markup.add(InlineKeyboardButton('[USA] USPS PRIO SHIPPING ΓÇó 15.0 eur', callback_data='delivery_usa_prio_15.0'))
    elif user_country == 'UK':
        markup.add(InlineKeyboardButton('[UK] ROYAL MAIL ΓÇó 8.0 eur', callback_data='delivery_uk_royal_8.0'))
        markup.add(InlineKeyboardButton('[UK] SPECIAL DELIVERY ΓÇó 20.0 eur', callback_data='delivery_uk_special_20.0'))
    elif user_country == 'CAN':
        markup.add(InlineKeyboardButton('[CAN] CANADA POST ΓÇó 10.0 eur', callback_data='delivery_can_post_10.0'))
        markup.add(InlineKeyboardButton('[CAN] EXPRESS ΓÇó 25.0 eur', callback_data='delivery_can_express_25.0'))
    else:
        # Worldwide options for all other countries
        markup.add(InlineKeyboardButton('[WW] UNTRACKED ΓÇó 15.0 eur', callback_data='delivery_ww_untracked_15.0'))
        markup.add(InlineKeyboardButton('[WW] TRACKED ΓÇó 45.0 eur', callback_data='delivery_ww_tracked_45.0'))
    
    return markup

def generate_qr(data, filename):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    img.save(filename)
    return filename

def setup_user_handlers(bot, categories, shop_info, user_carts, user_states, gpg, PUBLIC_KEY, PRIVATE_PASSPHRASE, BTC_ADDRESS, XMR_ADDRESS, admin_config):
    """Setup all user-related handlers"""
    
    @bot.message_handler(commands=['profile'])
    def show_profile(message):
        user_id = message.from_user.id
        users_data = load_users()
        
        # Find all user entries for this user_id
        user_entries = [user for user in users_data['users'] if user['user_id'] == user_id]
        
        if user_entries:
            # Show the most recent entry
            latest_user = user_entries[-1]
            profile_text = f"""
≡ƒæñ **Your Profile**

**Name:** {latest_user['full_name']}
**Username:** @{latest_user['username']}
**User ID:** {latest_user['user_id']}
**Join Date:** {datetime.datetime.fromisoformat(latest_user['join_date']).strftime('%Y-%m-%d %H:%M')}
**Order Number:** #{latest_user['order_number']}

≡ƒôè **Your Orders:**
ΓÇó **Total Orders:** {len(user_entries)}
ΓÇó **Latest Order:** #{latest_user['order_number']}
ΓÇó **First Order:** #{user_entries[0]['order_number']}

≡ƒ¢Æ **Current Cart:** {len(user_carts.get(user_id, []))} items
            """.strip()
        else:
            profile_text = "Γ¥î Profile not found. Please use /start first."
        
        bot.send_message(message.chat.id, profile_text, parse_mode='Markdown')

    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        user_id = message.from_user.id
        username = message.from_user.username or ""
        first_name = message.from_user.first_name or ""
        last_name = message.from_user.last_name or ""
        
        # Get or create user data
        user_data = get_or_create_user(user_id, username, first_name, last_name)
        
        # Check if user has a personal phrase code set
        if user_data.get('personal_phrase_code'):
            # User has personal phrase code, show it
            user_states[user_id] = {'country': None, 'pgp_state': None, 'pgp_challenge': None}
            
            welcome_text = f"""
≡ƒîì {shop_info['name']} ≡ƒôª ≡ƒîÅ Γ£ê∩╕Å

Currency: {shop_info['currency'].lower()}
Payments: {' '.join(shop_info['payment_methods'])}

≡ƒæñ <b>Welcome back, {first_name}!</b>

**Your secret phrase code:** {user_data['personal_phrase_code']}

Available countries:

≡ƒç⌐≡ƒç¬ GER - ≡ƒîì WW

≡ƒçª≡ƒç║ AUS - ≡ƒçª≡ƒç║ AUS

≡ƒç║≡ƒç╕ USA - ≡ƒç║≡ƒç╕ USA

The store owner Mr Worldwide
Powered by The Engineer

Γ£¿ {shop_info['promotion']} Γ£¿
"PLEASE READ 'Show About' BEFORE"

Γ£à Premium quality &amp; best prices
Γ£à Ninja packaging
Γ£à Worldwide shipping

≡ƒôª WE SHIP:
[≡ƒç¬≡ƒç║ EUROPE] [≡ƒçª≡ƒç║ AUS] [≡ƒç║≡ƒç╕ USA]

≡ƒô₧ Telegram for all latest updates
{shop_info['contact']['telegram_bot']} &amp; {shop_info['contact']['updates_channel']}

CEO {shop_info['contact']['ceo']}
            """.strip()
            bot.send_message(message.chat.id, welcome_text, reply_markup=create_main_menu(user_id, user_carts, shop_info), parse_mode='HTML')
        else:
            # User doesn't have personal phrase code, ask them to set one
            user_states[user_id] = {'waiting_for_user_phrase_setup': True}
            save_user_state(user_id, user_states[user_id])
            
            phrase_text = f"""
≡ƒöÉ **Set Your Secret Phrase Code**

Welcome to {shop_info['name']}!

To access our shop, please set your own secret phrase code.

**Your Telegram ID:** {user_id}

**Please create a secret phrase code with 20-40 characters and send it to this chat.**

**Requirements:**
ΓÇó 20-40 characters long
ΓÇó Can include letters, numbers, and symbols
ΓÇó Make it unique and memorable

**Example:** `MySecretCode2024@ShopAccess#123`

Just type your secret phrase code and send it to this chat.
            """.strip()
            
            bot.send_message(message.chat.id, phrase_text, parse_mode='Markdown')

    @bot.callback_query_handler(func=lambda call: call.data in ['products', 'about', 'pgp', 'cart', 'orders', 'updates', 'back', 'checkout', 'payment_sent', 'order_no', 'order_yes', 'order_confirm', 'order_cancel', 'order_paid', 'discount_code', 'select_payment', 'enter_address', 'select_delivery', 'delete_order', 'tracking_info', 'restart_session'] or 
                                call.data.startswith('country_') or call.data.startswith('category_') or 
                                call.data.startswith('add_') or call.data.startswith('remove_') or 
                                call.data.startswith('test_verify_') or call.data.startswith('qty_') or
                                call.data.startswith('delivery_') or call.data.startswith('payment_'))
    def user_callback_handler(call):
        user_id = call.from_user.id
        if user_id not in user_states:
            user_states[user_id] = {'country': None, 'pgp_state': None, 'pgp_challenge': None}
        
        if call.data == 'products':
            if not user_states[user_id]['country']:
                country_text = "Available countries:\nPlease select your country to view products."
                safe_edit_message(bot, call.message.chat.id, call.message.message_id, country_text, reply_markup=create_country_menu())
            else:
                categories_text = f"Available categories:"
                safe_edit_message(bot, call.message.chat.id, call.message.message_id, categories_text, reply_markup=create_categories_menu(categories))
        elif call.data.startswith('country_'):
            country = call.data.split('_')[1]
            user_states[user_id]['country'] = country
            bot.answer_callback_query(call.id, f"Selected country: {country}")
            # Proceed to categories
            categories_text = f"Available categories:"
            safe_edit_message(bot, call.message.chat.id, call.message.message_id, categories_text, reply_markup=create_categories_menu(categories))
        elif call.data.startswith('category_'):
            category_name = call.data.split('_', 1)[1]
            # Find the category
            category = next((cat for cat in categories if cat['name'] == category_name), None)
            if category:
                product_text = f"Available products in {category_name}:"
                safe_edit_message(bot, call.message.chat.id, call.message.message_id, product_text, reply_markup=create_product_menu(category_name, categories))
        elif call.data == 'about':
            # Toggle about visibility
            if 'about' in shop_info and 'visible' in shop_info['about']:
                shop_info['about']['visible'] = not shop_info['about']['visible']
                # Save the updated shop_info back to file
                save_categories_to_file(categories, shop_info)
            
            # Show appropriate content based on visibility
            if 'about' in shop_info and shop_info['about'].get('visible', False):
                # Show full about content
                about_text = f"""
{shop_info['about']['content']}
                """.strip()
                markup = InlineKeyboardMarkup(row_width=2)
                markup.add(
                    InlineKeyboardButton('≡ƒÆè Products', callback_data='products'),
                    InlineKeyboardButton('≡ƒôî Hide About', callback_data='about')
                )
                markup.add(
                    InlineKeyboardButton('≡ƒöæ Verify pgp key', callback_data='pgp'),
                    InlineKeyboardButton('≡ƒôª Orders', callback_data='orders')
                )
                markup.add(
                    InlineKeyboardButton('≡ƒ¢Æ Cart (Γé¼0.00)', callback_data='cart'),
                    InlineKeyboardButton('≡ƒô░ NWW Updates', callback_data='updates')
                )
                markup.add(
                    InlineKeyboardButton('≡ƒöä Restart Session', callback_data='restart_session')
                )
                safe_edit_message(bot, call.message.chat.id, call.message.message_id, about_text, reply_markup=markup, parse_mode='HTML')
            else:
                # Show welcome message (same as /start)
                user_id = call.from_user.id
                username = call.from_user.username or ""
                first_name = call.from_user.first_name or ""
                last_name = call.from_user.last_name or ""
                
                # Get user data for order number
                users_data = load_users()
                user_entries = [u for u in users_data['users'] if u['user_id'] == user_id]
                order_number = user_entries[-1]['order_number'] if user_entries else 1
                
                welcome_text = f"""
≡ƒîì {shop_info['name']} ≡ƒôª ≡ƒîÅ Γ£ê∩╕Å

Currency: {shop_info['currency'].lower()}
Payments: {' '.join(shop_info['payment_methods'])}

≡ƒæñ <b>Welcome back, {first_name}!</b>

Available countries:

≡ƒç⌐≡ƒç¬ GER - ≡ƒîì WW

≡ƒçª≡ƒç║ AUS - ≡ƒçª≡ƒç║ AUS

≡ƒç║≡ƒç╕ USA - ≡ƒç║≡ƒç╕ USA

The store owner Mr Worldwide
Powered by The Engineer

Γ£¿ {shop_info['promotion']} Γ£¿
"PLEASE READ 'Show About' BEFORE"

Γ£à Premium quality &amp; best prices
Γ£à Ninja packaging
Γ£à Worldwide shipping

≡ƒôª WE SHIP:
[≡ƒç¬≡ƒç║ EUROPE] [≡ƒçª≡ƒç║ AUS] [≡ƒç║≡ƒç╕ USA]

≡ƒô₧ Telegram for all latest updates
{shop_info['contact']['telegram_bot']} &amp; {shop_info['contact']['updates_channel']}

CEO {shop_info['contact']['ceo']}
                """.strip()
                safe_edit_message(bot, call.message.chat.id, call.message.message_id, welcome_text, reply_markup=create_main_menu(user_id, user_carts, shop_info), parse_mode='HTML')
        elif call.data == 'pgp':
            if gpg is None:
                pgp_text = """
≡ƒöæ **Verify PGP Key**

ΓÜá∩╕Å PGP functionality is currently disabled.

To enable PGP features:
1. Install GPG for Windows from: https://www.gpg4win.org/
2. Configure your PGP keys in config.env
3. Restart the bot

For now, you can verify our authenticity through our official channels.
                """.strip()
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton('≡ƒöÖ Back to Menu', callback_data='back'))
                markup.add(InlineKeyboardButton('≡ƒöä Restart Session', callback_data='restart_session'))
                safe_edit_message(bot, call.message.chat.id, call.message.message_id, pgp_text, reply_markup=markup, parse_mode='Markdown')
            else:
                # Sign a test message
                test_message = "Verify NWW Shop authenticity"
                signed_data = gpg.sign(test_message, passphrase=PRIVATE_PASSPHRASE, detach=True)
                signature = str(signed_data)
                
                pgp_text = f"""
≡ƒöæ **Verify PGP Key**

Public Key:
{PUBLIC_KEY}

Test Signed Message: "{test_message}"
Signature:
{signature}

Use GPG to verify offline, or test here.
                """.strip()
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton('Γ£à Test Verify Signature', callback_data='test_verify_pgp'))
                markup.add(InlineKeyboardButton('≡ƒöÖ Back to Menu', callback_data='back'))
                markup.add(InlineKeyboardButton('≡ƒöä Restart Session', callback_data='restart_session'))
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
            cart_markup, total = create_cart_menu(user_id, user_carts)
            cart = user_carts.get(user_id, [])
            
            if cart:
                cart_text = "≡ƒ¢Æ **Your cart:**\n\n"
                for i, item in enumerate(cart, 1):
                    cart_text += f"{i} ΓÇó {item['name']} ΓÇó {item['price']:.1f} eur\n"
                cart_text += f"\n≡ƒôï **Total amount: {total:.2f} eur**"
            else:
                cart_text = "≡ƒ¢Æ **Your cart:**\n\nYour cart is empty."
            
            safe_edit_message(bot, call.message.chat.id, call.message.message_id, cart_text, reply_markup=cart_markup, parse_mode='Markdown')
        elif call.data == 'checkout':
            print(f"Checkout callback received from user {user_id}")
            total = sum(item['price'] for item in user_carts.get(user_id, []))
            print(f"Cart total: {total}")
            if total > 0:
                # Show structured checkout invoice
                cart = user_carts.get(user_id, [])
                discount_info = user_states.get(user_id, {}).get('discount_code')
                
                # Get user's personal secret phrase code
                user_data = get_user_by_id(user_id)
                secret_phrase = user_data.get('personal_phrase_code', user_id) if user_data else user_id
                
                invoice_text = f"""
≡ƒÅ¬ **MrZoidbergBot**

Your secret phrase: {secret_phrase}

**Invoice #{user_id}**
Status: ≡ƒòÆ Pending Checkout

Enter the discount code, payment method, address and delivery method. Once your order has been completed, you will be given payment details.

"""
                # Add cart items
                for i, item in enumerate(cart, 1):
                    invoice_text += f"{i}. {item['name']} ΓÇö Γé¼{item['price']:.2f}\n"
                
                # Add discount information if applied
                if discount_info:
                    discount_amount = discount_info['discount_amount']
                    invoice_text += f"\n**Subtotal: Γé¼{total:.2f}**"
                    invoice_text += f"\n**Discount ({discount_info['code']}): -Γé¼{discount_amount:.2f}**"
                    invoice_text += f"\n**Total: Γé¼{total - discount_amount:.2f}**"
                else:
                    invoice_text += f"\n**Total: Γé¼{total:.2f}**"
                
                # Create structured checkout buttons
                markup = InlineKeyboardMarkup(row_width=1)
                markup.add(InlineKeyboardButton('Enter a discount code', callback_data='discount_code'))
                markup.add(InlineKeyboardButton('Select Payment Method', callback_data='select_payment'))
                markup.add(InlineKeyboardButton('Enter Delivery Address', callback_data='enter_address'))
                markup.add(InlineKeyboardButton('Select Delivery Method', callback_data='select_delivery'))
                markup.add(InlineKeyboardButton('≡ƒôª Tracking Information', callback_data='tracking_info'))
                markup.add(InlineKeyboardButton('Delete Order', callback_data='delete_order'))
                markup.add(InlineKeyboardButton('Back', callback_data='back'))
                
                safe_edit_message(bot, call.message.chat.id, call.message.message_id, invoice_text, reply_markup=markup, parse_mode='Markdown')
                print("Structured checkout invoice sent")
            else:
                bot.answer_callback_query(call.id, "Your cart is empty!")
        elif call.data.startswith('delivery_'):
            # Handle delivery method selection
            print(f"Delivery callback received: {call.data}")
            delivery_data = call.data.replace('delivery_', '')
            parts = delivery_data.split('_')
            print(f"Delivery parts: {parts}")
            
            if len(parts) >= 3:
                region = parts[0]
                method = parts[1]
                price = float(parts[2])
                print(f"Delivery selected: {region} {method} {price}")
                
                # Store delivery method in user state
                if user_id not in user_states:
                    user_states[user_id] = {}
                user_states[user_id]['delivery_method'] = f"{region}_{method}"
                user_states[user_id]['delivery_price'] = price
                save_user_state(user_id, user_states[user_id])
                
                # Calculate total with delivery
                cart_total = sum(item['price'] for item in user_carts.get(user_id, []))
                total_with_delivery = cart_total + price
                
                # Show payment method selection
                payment_method_text = f"""
≡ƒÆ│ **Payment Method Selection**

**Cart Total: Γé¼{cart_total:.2f}**
**Delivery: Γé¼{price:.1f}**
**Total: Γé¼{total_with_delivery:.2f}**

Select your payment method:
                """.strip()
                
                markup = InlineKeyboardMarkup(row_width=1)
                markup.add(InlineKeyboardButton('≡ƒöÖ Back to cart', callback_data='cart'))
                markup.add(InlineKeyboardButton('Γé┐ Bitcoin (BTC)', callback_data='payment_btc'))
                markup.add(InlineKeyboardButton('≡ƒöÆ Monero (XMR)', callback_data='payment_xmr'))
                
                safe_edit_message(bot, call.message.chat.id, call.message.message_id, payment_method_text, reply_markup=markup, parse_mode='Markdown')
                bot.answer_callback_query(call.id, f"Delivery method selected: {region} {method}")
                
                # Show tracking information popup after delivery selection
                bot.answer_callback_query(call.id, "Tracking numbers are not given out until 3 working days after purchase.", show_alert=True)
        
        elif call.data == 'payment_btc':
            # Handle Bitcoin payment selection - go to address collection first
            if user_id not in user_states:
                user_states[user_id] = {}
            
            # Store payment method
            user_states[user_id]['payment_method'] = 'btc'
            user_states[user_id]['waiting_for_address'] = True
            save_user_state(user_id, user_states[user_id])
            
            # Get user's personal secret phrase code
            user_data = get_user_by_id(user_id)
            secret_phrase = user_data.get('personal_phrase_code', user_id) if user_data else user_id
            
            # Show address collection message with structured format
            address_text = f"""
≡ƒÅá **Delivery Address Required**

Your secret phrase: {secret_phrase}

You can send a message to the chat either as an encrypted message or as plain text. The bot will handle the encryption of your message and display it to the seller after the order is paid for.

**Please type your address in this format:**

(YOUR NAME) - JAMES HILLS
(STREET NAME + NUMBER) - Victoria St 155
(CITY) - LONDON
(POSTAL CODE) - SW1E 5N
(COUNTRY) - UNITED KINGDOM

**Example for your country:**
(YOUR NAME) - John Smith
(STREET NAME + NUMBER) - Main St 123
(CITY) - Berlin
(POSTAL CODE) - 10115
(COUNTRY) - GERMANY

Just type your address in the format above and send it to this chat.
            """.strip()
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton('≡ƒöÖ Back to cart', callback_data='cart'))
            
            safe_edit_message(bot, call.message.chat.id, call.message.message_id, address_text, reply_markup=markup, parse_mode='Markdown')
            bot.answer_callback_query(call.id, "Please provide your delivery address")
        
        elif call.data == 'payment_xmr':
            # Handle Monero payment selection - go to address collection first
            if user_id not in user_states:
                user_states[user_id] = {}
            
            # Store payment method
            user_states[user_id]['payment_method'] = 'xmr'
            user_states[user_id]['waiting_for_address'] = True
            save_user_state(user_id, user_states[user_id])
            
            # Get user's personal secret phrase code
            user_data = get_user_by_id(user_id)
            secret_phrase = user_data.get('personal_phrase_code', user_id) if user_data else user_id
            
            # Show address collection message with structured format
            address_text = f"""
≡ƒÅá **Delivery Address Required**

Your secret phrase: {secret_phrase}

You can send a message to the chat either as an encrypted message or as plain text. The bot will handle the encryption of your message and display it to the seller after the order is paid for.

**Please type your address in this format:**

(YOUR NAME) - JAMES HILLS
(STREET NAME + NUMBER) - Victoria St 155
(CITY) - LONDON
(POSTAL CODE) - SW1E 5N
(COUNTRY) - UNITED KINGDOM

**Example for your country:**
(YOUR NAME) - John Smith
(STREET NAME + NUMBER) - Main St 123
(CITY) - Berlin
(POSTAL CODE) - 10115
(COUNTRY) - GERMANY

Just type your address in the format above and send it to this chat.
            """.strip()
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton('≡ƒöÖ Back to cart', callback_data='cart'))
            
            safe_edit_message(bot, call.message.chat.id, call.message.message_id, address_text, reply_markup=markup, parse_mode='Markdown')
            bot.answer_callback_query(call.id, "Please provide your delivery address")
        
        elif call.data == 'payment_sent':
            # Go to order summary after payment sent
            cart_total = sum(item['price'] for item in user_carts.get(user_id, []))
            delivery_price = user_states[user_id].get('delivery_price', 0)
            total_amount = cart_total + delivery_price
            payment_method = user_states[user_id].get('payment_method', 'unknown')
            delivery_method = user_states[user_id].get('delivery_method', 'unknown')
            delivery_address = user_states[user_id].get('delivery_address', '')
            
            # Create order summary
            order_summary_text = "**Your order:**\n\n"
            
            # Cart items
            order_summary_text += "≡ƒ¢Æ **Your cart:**\n"
            for i, item in enumerate(user_carts.get(user_id, []), 1):
                order_summary_text += f"≡ƒôª {i} ΓÇó {item['name']} ΓÇó {item['price']:.1f} eur\n"
            
            # Delivery method
            order_summary_text += f"\n≡ƒÜÜ **Your delivery method:**\n"
            order_summary_text += f"≡ƒôï [{delivery_method.upper()}] ΓÇó {delivery_price:.1f} eur\n"
            
            # Payment method
            order_summary_text += f"\n≡ƒÆ│ **Your payment method:**\n"
            order_summary_text += f"≡ƒôï {payment_method.upper()}\n"
            
            # Order note (address)
            order_summary_text += f"\n≡ƒô¥ **Your order note:**\n"
            order_summary_text += f"≡ƒôï {delivery_address}\n\n"
            
            order_summary_text += "**Is this correct?**"
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton('Γ¥î No! Create order again', callback_data='order_no'))
            markup.add(InlineKeyboardButton('Γ£à Yes! Order is correct', callback_data='order_confirm'))
            
            safe_edit_message(bot, call.message.chat.id, call.message.message_id, order_summary_text, reply_markup=markup, parse_mode='Markdown')
            bot.answer_callback_query(call.id, "Order summary shown")
        
        elif call.data == 'order_no':
            # User wants to create order again - clear cart and go back to main menu
            user_carts[user_id] = []
            save_user_cart(user_id, [])
            if user_id in user_states:
                user_states[user_id].clear()
                save_user_state(user_id, {})
            safe_edit_message(bot, call.message.chat.id, call.message.message_id, "Order cancelled. Starting fresh!", reply_markup=create_main_menu(user_id, user_carts, shop_info))
            bot.answer_callback_query(call.id, "Order cancelled")
        
        elif call.data == 'order_yes':
            # User confirmed order - show order summary
            cart_total = sum(item['price'] for item in user_carts.get(user_id, []))
            delivery_price = user_states[user_id].get('delivery_price', 0)
            total_amount = cart_total + delivery_price
            payment_method = user_states[user_id].get('payment_method', 'unknown')
            delivery_method = user_states[user_id].get('delivery_method', 'unknown')
            delivery_address = user_states[user_id].get('delivery_address', '')
            
            # Create order summary
            order_summary_text = "**Your order:**\n\n"
            
            # Cart items
            order_summary_text += "≡ƒ¢Æ **Your cart:**\n"
            for i, item in enumerate(user_carts.get(user_id, []), 1):
                order_summary_text += f"≡ƒôª {i} ΓÇó {item['name']} ΓÇó {item['price']:.1f} eur\n"
            
            # Delivery method
            order_summary_text += f"\n≡ƒÜÜ **Your delivery method:**\n"
            order_summary_text += f"≡ƒôï [{delivery_method.upper()}] ΓÇó {delivery_price:.1f} eur\n"
            
            # Payment method
            order_summary_text += f"\n≡ƒÆ│ **Your payment method:**\n"
            order_summary_text += f"≡ƒôï {payment_method.upper()}\n"
            
            # Order note (address)
            order_summary_text += f"\n≡ƒô¥ **Your order note:**\n"
            order_summary_text += f"≡ƒôï {delivery_address}\n\n"
            
            order_summary_text += "**Is this correct?**"
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton('Γ¥î No! Create order again', callback_data='order_no'))
            markup.add(InlineKeyboardButton('Γ£à Yes! Order is correct', callback_data='order_confirm'))
            
            safe_edit_message(bot, call.message.chat.id, call.message.message_id, order_summary_text, reply_markup=markup, parse_mode='Markdown')
            bot.answer_callback_query(call.id, "Order summary shown")
        
        elif call.data == 'order_confirm':
            # User confirmed order details - show payment details
            cart_total = sum(item['price'] for item in user_carts.get(user_id, []))
            delivery_price = user_states[user_id].get('delivery_price', 0)
            total_amount = cart_total + delivery_price
            payment_method = user_states[user_id].get('payment_method', 'unknown')
            delivery_method = user_states[user_id].get('delivery_method', 'unknown')
            delivery_address = user_states[user_id].get('delivery_address', '')
            
            # Recalculate crypto amounts to ensure consistency
            if payment_method == 'btc':
                crypto_amount = total_amount * 0.000015  # Demo rate: 1 BTC = ~66,667 EUR
                crypto_address = BTC_ADDRESS
            else:  # XMR
                crypto_amount = total_amount * 0.006  # Demo rate: 1 XMR = ~167 EUR
                crypto_address = XMR_ADDRESS
            
            # Store amounts for later use
            user_states[user_id]['crypto_amount'] = crypto_amount
            user_states[user_id]['crypto_address'] = crypto_address
            
            # Generate order ID using proper function
            order_id = create_order(
                user_id=user_id,
                cart_items=user_carts.get(user_id, []),
                delivery_method=delivery_method,
                delivery_price=delivery_price,
                payment_method=payment_method,
                delivery_address=delivery_address,
                total_amount=total_amount
            )
            
            # Store order_id in user state for later use
            user_states[user_id]['order_id'] = order_id
            
            # Show payment details with QR codes
            if payment_method == 'btc':
                # Generate QR code for Bitcoin address
                qr_filename = f"btc_order_qr_{user_id}.png"
                generate_qr(crypto_address, qr_filename)
                
                payment_text = f"""
**Payment for Order #{order_id}**

==========
**Payment method:** {payment_method.upper()}
**Transfer EXACT amount:** {crypto_amount:.8f}
**To next address:** {crypto_address}

**Please send EXACT amount shown above carefully!**

After payment checking you can check your order in the 'orders' section in main menu
                """.strip()
                
                # Send QR code with payment details
                with open(qr_filename, 'rb') as qr_file:
                    bot.send_photo(call.message.chat.id, qr_file, caption=payment_text, reply_markup=InlineKeyboardMarkup().add(
                        InlineKeyboardButton('Γ¥î Cancel', callback_data='order_cancel'),
                        InlineKeyboardButton('Γ£à I paid (starts the checking)', callback_data='order_paid')
                    ), parse_mode='Markdown')
                
                # Clean up QR file
                try:
                    os.remove(qr_filename)
                except:
                    pass
                    
            else:  # XMR
                # Generate QR code for Monero address
                qr_filename = f"xmr_order_qr_{user_id}.png"
                generate_qr(crypto_address, qr_filename)
                
                payment_text = f"""
**Payment for Order #{order_id}**

==========
**Payment method:** {payment_method.upper()}
**Transfer EXACT amount:** {crypto_amount:.6f}
**To next address:** {crypto_address}

**Please send EXACT amount shown above carefully!**

After payment checking you can check your order in the 'orders' section in main menu
                """.strip()
                
                # Send QR code with payment details
                with open(qr_filename, 'rb') as qr_file:
                    bot.send_photo(call.message.chat.id, qr_file, caption=payment_text, reply_markup=InlineKeyboardMarkup().add(
                        InlineKeyboardButton('Γ¥î Cancel', callback_data='order_cancel'),
                        InlineKeyboardButton('Γ£à I paid (starts the checking)', callback_data='order_paid')
                    ), parse_mode='Markdown')
                
                # Clean up QR file
                try:
                    os.remove(qr_filename)
                except:
                    pass
            bot.answer_callback_query(call.id, "Payment details shown")
        
        elif call.data == 'order_cancel':
            # User cancelled payment - clear everything
            user_carts[user_id] = []
            save_user_cart(user_id, [])
            if user_id in user_states:
                user_states[user_id].clear()
                save_user_state(user_id, {})
            safe_edit_message(bot, call.message.chat.id, call.message.message_id, "Payment cancelled. Starting fresh!", reply_markup=create_main_menu(user_id, user_carts, shop_info))
            bot.answer_callback_query(call.id, "Payment cancelled")
        
        elif call.data == 'order_paid':
            # User confirmed payment - create order and show final confirmation
            cart_total = sum(item['price'] for item in user_carts.get(user_id, []))
            delivery_price = user_states[user_id].get('delivery_price', 0)
            total_amount = cart_total + delivery_price
            payment_method = user_states[user_id].get('payment_method', 'unknown')
            delivery_method = user_states[user_id].get('delivery_method', 'unknown')
            delivery_address = user_states[user_id].get('delivery_address', '')
            
            # Order already created above, just get the order_id from user state
            order_id = user_states[user_id].get('order_id', 'UNKNOWN')
            
            # Add order to user's history
            order_data = {
                'total_amount': total_amount,
                'status': 'pending'
            }
            add_user_order(user_id, order_id, order_data)
            
            # User preferences are now session-based only
            
            # Notify admin about new order
            notify_admin_new_order(bot, admin_config, order_id, user_id, total_amount)
            
            # Escape special characters for Markdown
            def escape_markdown(text):
                if text is None:
                    return ""
                return str(text).replace('*', '\\*').replace('_', '\\_').replace('`', '\\`').replace('[', '\\[').replace(']', '\\]')
            
            safe_address = escape_markdown(delivery_address)
            safe_delivery_method = escape_markdown(delivery_method)
            safe_payment_method = escape_markdown(payment_method)
            
            final_confirmation_text = f"""
Γ£à **Order Confirmed!**

**Order Summary:**
ΓÇó **Items**: {len(user_carts.get(user_id, []))} products
ΓÇó **Cart Total**: Γé¼{cart_total:.2f}
ΓÇó **Delivery**: Γé¼{delivery_price:.1f} ({safe_delivery_method})
ΓÇó **Total**: Γé¼{total_amount:.2f}
ΓÇó **Payment**: {safe_payment_method.upper()}
ΓÇó **Address**: {safe_address[:50]}{'...' if len(safe_address) > 50 else ''}

**Next Steps:**
1. Your order has been received
2. Payment verification in progress
3. Package will be shipped within 24-48 hours
4. You will receive tracking information

**Order ID**: {order_id}

Thank you for your order! ≡ƒÜÇ
            """.strip()
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton('≡ƒöÖ Back to main menu', callback_data='back'))
            
            safe_edit_message(bot, call.message.chat.id, call.message.message_id, final_confirmation_text, reply_markup=markup, parse_mode='Markdown')
            bot.answer_callback_query(call.id, "Order confirmed!")
            
            # Clear the cart after successful order
            user_carts[user_id] = []
        
        elif call.data == 'orders':
            orders_text = """
≡ƒôª **Orders**

Your recent orders:
ΓÇó Order #123 - Delivered (USA)
ΓÇó Order #456 - In Transit (GER)

Enter order ID to track: /track <ID>
            """.strip()
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton('≡ƒöÖ Back to Menu', callback_data='back'))
            safe_edit_message(bot, call.message.chat.id, call.message.message_id, orders_text, reply_markup=markup, parse_mode='Markdown')
        elif call.data == 'updates':
            updates_text = """
≡ƒô░ **NWW Updates**

Latest: 20% promo extended! New products incoming ≡ƒÜÇ
Follow @NWWupdates for more.
            """.strip()
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton('≡ƒöÖ Back to Menu', callback_data='back'))
            safe_edit_message(bot, call.message.chat.id, call.message.message_id, updates_text, reply_markup=markup, parse_mode='Markdown')
        elif call.data == 'back':
            safe_edit_message(bot, call.message.chat.id, call.message.message_id, "Back to main menu.", reply_markup=create_main_menu(user_id, user_carts, shop_info))
        elif call.data == 'restart_session':
            # Clear user session data
            if user_id in user_carts:
                user_carts[user_id] = []
            if user_id in user_states:
                user_states[user_id] = {'country': None, 'pgp_state': None, 'pgp_challenge': None}
            
            # Show restart confirmation
            restart_text = """
≡ƒöä **Session Restarted Successfully!**

Γ£à Cart cleared
Γ£à Session data reset
Γ£à Ready for new shopping

Welcome back to the main menu!
            """.strip()
            
            safe_edit_message(bot, call.message.chat.id, call.message.message_id, restart_text, reply_markup=create_main_menu(user_id, user_carts, shop_info), parse_mode='Markdown')
            bot.answer_callback_query(call.id, "Session restarted successfully!")
        elif call.data.startswith('add_'):
            # Parse the new format: add_productname|price
            data_part = call.data[4:]  # Remove 'add_' prefix
            if '|' in data_part:
                parts = data_part.split('|')
                if len(parts) >= 2:
                    # Reconstruct the product name by replacing | with spaces
                    name_parts = parts[:-1]  # All parts except the last one (price)
                    name = ' '.join(name_parts)
                    
                    print(f"Looking for product: '{name}'")
                    
                    # Find the product in categories to get detailed info
                    product = find_product_by_name(name, categories)
                    if product:
                        print(f"Found product: {product['name']}")
                        print(f"Has quantities: {'quantities' in product}")
                        
                        if 'quantities' in product:
                            # Show detailed product page
                            print("Showing product detail page")
                            show_product_detail(bot, call, product, user_carts)
                        else:
                            # Old format - add directly to cart
                            price = float(parts[-1])
                            if user_id not in user_carts:
                                user_carts[user_id] = []
                            user_carts[user_id].append({'name': name, 'price': price})
                            save_user_cart(user_id, user_carts[user_id])
                            bot.answer_callback_query(call.id, f"Added {name} to cart!", show_alert=True)
                    else:
                        print(f"Product not found: '{name}'")
                        bot.answer_callback_query(call.id, f"Γ¥î Product '{name}' not found!")
        elif call.data.startswith('remove_'):
            # Parse the new format: remove_productname|price
            data_part = call.data[7:]  # Remove 'remove_' prefix
            if '|' in data_part:
                parts = data_part.split('|')
                if len(parts) >= 2:
                    name = parts[0].replace('|', ' ')
                    price = float(parts[-1])  # Last part is always the price
                    if user_id in user_carts:
                        user_carts[user_id] = [item for item in user_carts[user_id] if not (item['name'] == name and item['price'] == price)]
                    bot.answer_callback_query(call.id, f"Removed {name} from cart!", show_alert=True)
                    # Refresh cart
                    cart_markup, total = create_cart_menu(user_id, user_carts)
                    cart_text = f"≡ƒ¢Æ **Cart** (Total: Γé¼{total:.2f})\n\n" + "\n".join([f"ΓÇó {item['name']} - Γé¼{item['price']}" for item in user_carts.get(user_id, [])])
                    if total == 0:
                        cart_text += "\nYour cart is empty."
                    safe_edit_message(bot, call.message.chat.id, call.message.message_id, cart_text, reply_markup=cart_markup, parse_mode='Markdown')
        elif call.data.startswith('qty_'):
            # Handle quantity selection: qty_productname|amount|price
            data_part = call.data[4:]  # Remove 'qty_' prefix
            if '|' in data_part:
                parts = data_part.split('|')
                if len(parts) >= 3:
                    # Reconstruct product name from all parts except last two (amount and price)
                    name_parts = parts[:-2]
                    product_name = ' '.join(name_parts)
                    amount = parts[-2]
                    price = float(parts[-1])
                    
                    print(f"Quantity selection: {product_name} - {amount} - {price}")
                    
                    # Add to cart with quantity info
                    if user_id not in user_carts:
                        user_carts[user_id] = []
                    
                    cart_item = {
                        'name': f"{product_name} ΓÇó {amount}",
                        'price': price,
                        'amount': amount,
                        'product_name': product_name
                    }
                    user_carts[user_id].append(cart_item)
                    save_user_cart(user_id, user_carts[user_id])
                    bot.answer_callback_query(call.id, f"Added {product_name} ({amount}) to cart!", show_alert=True)
        
        # New structured checkout handlers
        elif call.data == 'discount_code':
            # Set waiting for discount code state
            if user_id not in user_states:
                user_states[user_id] = {}
            user_states[user_id]['waiting_for_discount_code'] = True
            save_user_state(user_id, user_states[user_id])
            
            # Get user's personal secret phrase code
            user_data = get_user_by_id(user_id)
            secret_phrase = user_data.get('personal_phrase_code', user_id) if user_data else user_id
            
            # Show discount code input message
            discount_text = f"""
≡ƒÄƒ∩╕Å **Enter Discount Code**

Your secret phrase: {secret_phrase}

Enter your discount code below to get a discount on your order.

If you have a discount code, type it and send it to this chat.
            """.strip()
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton('≡ƒöÖ Back to checkout', callback_data='checkout'))
            
            safe_edit_message(bot, call.message.chat.id, call.message.message_id, discount_text, reply_markup=markup, parse_mode='Markdown')
        
        elif call.data == 'select_payment':
            # Show payment method selection
            markup = InlineKeyboardMarkup(row_width=1)
            markup.add(InlineKeyboardButton('≡ƒöÖ Back to checkout', callback_data='checkout'))
            markup.add(InlineKeyboardButton('Γé┐ Bitcoin (BTC)', callback_data='payment_btc'))
            markup.add(InlineKeyboardButton('≡ƒöÆ Monero (XMR)', callback_data='payment_xmr'))
            
            payment_text = "**Select your payment method:**"
            safe_edit_message(bot, call.message.chat.id, call.message.message_id, payment_text, reply_markup=markup, parse_mode='Markdown')
        
        elif call.data == 'enter_address':
            # Set waiting for address state
            if user_id not in user_states:
                user_states[user_id] = {}
            user_states[user_id]['waiting_for_address'] = True
            save_user_state(user_id, user_states[user_id])
            
            # Get user's personal secret phrase code
            user_data = get_user_by_id(user_id)
            secret_phrase = user_data.get('personal_phrase_code', user_id) if user_data else user_id
            
            # Show address collection message with structured format
            address_text = f"""
≡ƒÅá **Delivery Address Required**

Your secret phrase: {secret_phrase}

You can send a message to the chat either as an encrypted message or as plain text. The bot will handle the encryption of your message and display it to the seller after the order is paid for.

**Please type your address in this format:**

(YOUR NAME) - JAMES HILLS
(STREET NAME + NUMBER) - Victoria St 155
(CITY) - LONDON
(POSTAL CODE) - SW1E 5N
(COUNTRY) - UNITED KINGDOM

**Example for your country:**
(YOUR NAME) - John Smith
(STREET NAME + NUMBER) - Main St 123
(CITY) - Berlin
(POSTAL CODE) - 10115
(COUNTRY) - GERMANY

Just type your address in the format above and send it to this chat.
            """.strip()
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton('≡ƒöÖ Back to checkout', callback_data='checkout'))
            
            safe_edit_message(bot, call.message.chat.id, call.message.message_id, address_text, reply_markup=markup, parse_mode='Markdown')
        
        elif call.data == 'select_delivery':
            # Show delivery method selection
            user_country = user_states.get(user_id, {}).get('country', 'WW')
            delivery_markup = create_delivery_menu(user_country)
            
            delivery_text = "**Select delivery method:**"
            safe_edit_message(bot, call.message.chat.id, call.message.message_id, delivery_text, reply_markup=delivery_markup, parse_mode='Markdown')
            
            # Show tracking information popup
            bot.answer_callback_query(call.id, "Tracking numbers are not given out until 3 working days after purchase.", show_alert=True)
        
        elif call.data == 'tracking_info':
            # Show tracking information popup
            bot.answer_callback_query(call.id, "Tracking numbers are not given out until 3 working days after purchase.", show_alert=True)
        
        elif call.data == 'delete_order':
            # Clear cart and go back to main menu
            user_carts[user_id] = []
            save_user_cart(user_id, [])
            if user_id in user_states:
                user_states[user_id].clear()
                save_user_state(user_id, {})
            safe_edit_message(bot, call.message.chat.id, call.message.message_id, "Order deleted. Starting fresh!", reply_markup=create_main_menu(user_id, user_carts, shop_info))
            bot.answer_callback_query(call.id, "Order deleted")

    @bot.message_handler(func=lambda message: message.text and not message.text.startswith('/') and not message.text.startswith('admin'))
    def handle_search_message(message):
        """Handle text-based search queries"""
        user_id = message.from_user.id
        text = message.text.strip()
        
        # Check if user is waiting for address input - if so, skip search handling
        if user_id in user_states and user_states[user_id].get('waiting_for_address'):
            return  # Let the main handler deal with address input
        
        # Check if this looks like a product search
        if len(text) > 2 and len(text) < 100:  # Reasonable search query length
            # Search for products containing the text
            found_products = []
            for category in categories:
                for product in category['products']:
                    if text.lower() in product['name'].lower():
                        found_products.append((product, category))
            
            if found_products:
                # Show search results
                search_text = f"🔍 **Search Results for: '{text}'**\n\n"
                
                for i, (product, category) in enumerate(found_products[:5]):  # Limit to 5 results
                    if 'quantities' in product:
                        min_price = min(qty['price'] for qty in product['quantities'])
                        max_price = max(qty['price'] for qty in product['quantities'])
                        price_text = f"€{min_price:.1f}-€{max_price:.1f}"
                    else:
                        price_text = f"€{product.get('price', 0):.2f}"
                    
                    search_text += f"{i+1}. **{product['name']}**\n"
                    search_text += f"   Category: {category['name']}\n"
                    search_text += f"   Price: {price_text}\n\n"
                
                if len(found_products) > 5:
                    search_text += f"... and {len(found_products) - 5} more results\n\n"
                
                search_text += "Click on a product to view details or use the menu buttons below."
                
                # Create markup with product buttons
                markup = InlineKeyboardMarkup(row_width=1)
                for i, (product, category) in enumerate(found_products[:5]):
                    button_text = f"{i+1}. {product['name']} - {category['name']}"
                    markup.add(InlineKeyboardButton(button_text, callback_data=f"add_{product['name']}|{product.get('price', 0)}"))
                
                markup.add(InlineKeyboardButton('🔙 Back to Menu', callback_data='back'))
                
                bot.reply_to(message, search_text, reply_markup=markup, parse_mode='Markdown')
                return
        
        # If no products found or not a search query, let other handlers deal with it
        return

    @bot.message_handler(func=lambda message: not message.text.startswith('/admin') and not message.text.startswith('/reload') and not message.text.startswith('/stats'))
    def handle_user_message(message):
        user_id = message.from_user.id
        text = message.text.strip()
        
        # Handle user setting their own secret phrase code
        if user_id in user_states and user_states[user_id].get('waiting_for_user_phrase_setup'):
            secret_phrase = text.strip()
            
            # Validate phrase code length (20-40 characters)
            if len(secret_phrase) < 20:
                error_text = f"""
Γ¥î **Secret Phrase Too Short**

Your secret phrase code must be at least 20 characters long.

**Current length:** {len(secret_phrase)} characters
**Required:** 20-40 characters

Please create a longer secret phrase code and try again.

**Example:** `MySecretCode2024@ShopAccess#123`
                """.strip()
                
                bot.reply_to(message, error_text, parse_mode='Markdown')
                return
            elif len(secret_phrase) > 40:
                error_text = f"""
Γ¥î **Secret Phrase Too Long**

Your secret phrase code must be 40 characters or less.

**Current length:** {len(secret_phrase)} characters
**Required:** 20-40 characters

Please create a shorter secret phrase code and try again.

**Example:** `MySecretCode2024@ShopAccess#123`
                """.strip()
                
                bot.reply_to(message, error_text, parse_mode='Markdown')
                return
            
            # Save the user's secret phrase code
            users_data = load_users()
            for user in users_data['users']:
                if user['user_id'] == user_id:
                    user['personal_phrase_code'] = secret_phrase
                    user['phrase_verified'] = True
                    break
            save_users(users_data)
            
            # Clear waiting state and set up user session
            user_states[user_id] = {'country': None, 'pgp_state': None, 'pgp_challenge': None}
            save_user_state(user_id, user_states[user_id])
            
            # Show welcome message with their secret phrase code
            welcome_text = f"""
≡ƒîì {shop_info['name']} ≡ƒôª ≡ƒîÅ Γ£ê∩╕Å

Currency: {shop_info['currency'].lower()}
Payments: {' '.join(shop_info['payment_methods'])}

≡ƒæñ <b>Welcome, {message.from_user.first_name or 'User'}!</b>

**Your secret phrase code:** {secret_phrase}

Available countries:

≡ƒç⌐≡ƒç¬ GER - ≡ƒîì WW

≡ƒçª≡ƒç║ AUS - ≡ƒçª≡ƒç║ AUS

≡ƒç║≡ƒç╕ USA - ≡ƒç║≡ƒç╕ USA

The store owner Mr Worldwide
Powered by The Engineer

Γ£¿ {shop_info['promotion']} Γ£¿
"PLEASE READ 'Show About' BEFORE"

Γ£à Premium quality &amp; best prices
Γ£à Ninja packaging
Γ£à Worldwide shipping

≡ƒôª WE SHIP:
[≡ƒç¬≡ƒç║ EUROPE] [≡ƒçª≡ƒç║ AUS] [≡ƒç║≡ƒç╕ USA]

≡ƒô₧ Telegram for all latest updates
{shop_info['contact']['telegram_bot']} &amp; {shop_info['contact']['updates_channel']}

CEO {shop_info['contact']['ceo']}
            """.strip()
            
            bot.reply_to(message, welcome_text, reply_markup=create_main_menu(user_id, user_carts, shop_info), parse_mode='HTML')
            return
        
        # Handle phrase code submission (legacy - for global phrase codes)
        elif user_id in user_states and user_states[user_id].get('waiting_for_phrase_code'):
            phrase_code = text.upper().strip()
            
            # Get user data to check personal phrase code
            user_data = get_user_by_id(user_id)
            if not user_data:
                user_data = get_or_create_user(user_id, message.from_user.username or "", 
                                             message.from_user.first_name or "", 
                                             message.from_user.last_name or "")
            
            # Check against personal phrase code or global phrase code
            correct_phrase = None
            if user_data.get('personal_phrase_code'):
                correct_phrase = user_data['personal_phrase_code'].upper()
            else:
                correct_phrase = shop_info.get('phrase_code', '').upper()
            
            if phrase_code == correct_phrase:
                # Phrase code is correct, verify user and show welcome
                user_data = get_or_create_user(user_id, message.from_user.username or "", 
                                             message.from_user.first_name or "", 
                                             message.from_user.last_name or "")
                
                # Mark user as phrase verified
                users_data = load_users()
                for user in users_data['users']:
                    if user['user_id'] == user_id:
                        user['phrase_verified'] = True
                        break
                save_users(users_data)
                
                # Clear waiting state and set up user session
                user_states[user_id] = {'country': None, 'pgp_state': None, 'pgp_challenge': None}
                save_user_state(user_id, user_states[user_id])
                
                # Show welcome message with personal phrase code
                personal_code = user_data.get('personal_phrase_code', 'Not set')
                welcome_text = f"""
≡ƒîì {shop_info['name']} ≡ƒôª ≡ƒîÅ Γ£ê∩╕Å

Currency: {shop_info['currency'].lower()}
Payments: {' '.join(shop_info['payment_methods'])}

≡ƒæñ <b>Welcome, {message.from_user.first_name or 'User'}!</b>

**Your secret phrase code:** {personal_code}

Available countries:

≡ƒç⌐≡ƒç¬ GER - ≡ƒîì WW

≡ƒçª≡ƒç║ AUS - ≡ƒçª≡ƒç║ AUS

≡ƒç║≡ƒç╕ USA - ≡ƒç║≡ƒç╕ USA

The store owner Mr Worldwide
Powered by The Engineer

Γ£¿ {shop_info['promotion']} Γ£¿
"PLEASE READ 'Show About' BEFORE"

Γ£à Premium quality &amp; best prices
Γ£à Ninja packaging
Γ£à Worldwide shipping

≡ƒôª WE SHIP:
[≡ƒç¬≡ƒç║ EUROPE] [≡ƒçª≡ƒç║ AUS] [≡ƒç║≡ƒç╕ USA]

≡ƒô₧ Telegram for all latest updates
{shop_info['contact']['telegram_bot']} &amp; {shop_info['contact']['updates_channel']}

CEO {shop_info['contact']['ceo']}
                """.strip()
                
                bot.reply_to(message, welcome_text, reply_markup=create_main_menu(user_id, user_carts, shop_info), parse_mode='HTML')
            else:
                # Phrase code is incorrect
                error_text = f"""
Γ¥î **Invalid Phrase Code**

The phrase code you entered is incorrect.

**Your secret phrase:** {user_id}

**Note:** Enter the phrase code (not your user ID above).

Please try again with the correct phrase code, or contact admin if you don't have it.
                """.strip()
                
                bot.reply_to(message, error_text, parse_mode='Markdown')
            return
        
        # Handle discount code submission
        if user_id in user_states and user_states[user_id].get('waiting_for_discount_code'):
            # Process discount code
            discount_code = text.upper().strip()
            cart_total = sum(item['price'] for item in user_carts.get(user_id, []))
            
            discount_info, error_message = apply_discount_code(discount_code, shop_info, cart_total, categories)
            
            if discount_info:
                # Store discount info in user state
                user_states[user_id]['discount_code'] = discount_info
                user_states[user_id]['waiting_for_discount_code'] = False
                save_user_state(user_id, user_states[user_id])
                
                # Show success message with discount details
                success_text = f"""
Γ£à **Discount Applied Successfully!**

**Code:** {discount_info['code']}
**Discount:** {discount_info['discount_percent']}% off
**Amount Saved:** Γé¼{discount_info['discount_amount']:.2f}
**Description:** {discount_info['description']}

**Cart Total:** Γé¼{cart_total:.2f}
**Discount:** -Γé¼{discount_info['discount_amount']:.2f}
**New Total:** Γé¼{cart_total - discount_info['discount_amount']:.2f}

Continue with your order!
                """.strip()
                
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton('≡ƒöÖ Back to checkout', callback_data='checkout'))
                
                bot.reply_to(message, success_text, reply_markup=markup, parse_mode='Markdown')
            else:
                # Show error message
                error_text = f"""
Γ¥î **Invalid Discount Code**

{error_message}

Please try again with a valid discount code.
                """.strip()
                
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton('≡ƒöÖ Back to checkout', callback_data='checkout'))
                
                bot.reply_to(message, error_text, reply_markup=markup, parse_mode='Markdown')
        
        # Handle address submission
        elif user_id in user_states and user_states[user_id].get('waiting_for_address'):
            # Store the address
            user_states[user_id]['delivery_address'] = text
            user_states[user_id]['waiting_for_address'] = False
            save_user_state(user_id, user_states[user_id])
            
            # Get order details
            cart_total = sum(item['price'] for item in user_carts.get(user_id, []))
            delivery_price = user_states[user_id].get('delivery_price', 0)
            discount_info = user_states[user_id].get('discount_code')
            discount_amount = discount_info['discount_amount'] if discount_info else 0
            total_amount = cart_total + delivery_price - discount_amount
            payment_method = user_states[user_id].get('payment_method', 'unknown')
            delivery_method = user_states[user_id].get('delivery_method', 'unknown')
            
            # Show payment details with QR codes after address is provided
            if payment_method == 'btc':
                crypto_amount = total_amount * 0.000015  # Demo rate: 1 BTC = ~66,667 EUR
                crypto_address = BTC_ADDRESS
                
                # Store amounts for later use
                user_states[user_id]['crypto_amount'] = crypto_amount
                user_states[user_id]['crypto_address'] = crypto_address
                
                # Generate QR code for Bitcoin address
                qr_filename = f"btc_qr_{user_id}.png"
                generate_qr(crypto_address, qr_filename)
                
                payment_text = f"""
≡ƒÆ│ **Bitcoin Payment**

**Cart Total: Γé¼{cart_total:.2f}**
**Delivery: Γé¼{delivery_price:.1f}**"""
                
                if discount_info:
                    payment_text += f"\n**Discount ({discount_info['code']}): -Γé¼{discount_amount:.2f}**"
                
                payment_text += f"""
**Total: Γé¼{total_amount:.2f}**

**Bitcoin Amount: {crypto_amount:.8f} BTC**

**Bitcoin Address:**
`{crypto_address}`

Send exactly {crypto_amount:.8f} BTC to the address above.

After sending, click "Payment Sent" to provide your delivery address.
                """.strip()
                
                # Send QR code with payment details
                with open(qr_filename, 'rb') as qr_file:
                    bot.send_photo(message.chat.id, qr_file, caption=payment_text, reply_markup=InlineKeyboardMarkup().add(
                        InlineKeyboardButton('Γ£à Payment Sent', callback_data='payment_sent'),
                        InlineKeyboardButton('≡ƒöÖ Back to cart', callback_data='cart')
                    ), parse_mode='Markdown')
                
                # Clean up QR file
                try:
                    os.remove(qr_filename)
                except:
                    pass
                
            else:  # XMR
                crypto_amount = total_amount * 0.006  # Demo rate: 1 XMR = ~167 EUR
                crypto_address = XMR_ADDRESS
                
                # Store amounts for later use
                user_states[user_id]['crypto_amount'] = crypto_amount
                user_states[user_id]['crypto_address'] = crypto_address
                
                # Generate QR code for Monero address
                qr_filename = f"xmr_qr_{user_id}.png"
                generate_qr(crypto_address, qr_filename)
                
                payment_text = f"""
≡ƒÆ│ **Monero Payment**

**Cart Total: Γé¼{cart_total:.2f}**
**Delivery: Γé¼{delivery_price:.1f}**"""
                
                if discount_info:
                    payment_text += f"\n**Discount ({discount_info['code']}): -Γé¼{discount_amount:.2f}**"
                
                payment_text += f"""
**Total: Γé¼{total_amount:.2f}**

**Monero Amount: {crypto_amount:.6f} XMR**

**Monero Address:**
`{crypto_address}`

Send exactly {crypto_amount:.6f} XMR to the address above.

After sending, click "Payment Sent" to provide your delivery address.
                """.strip()
                
                # Send QR code with payment details
                with open(qr_filename, 'rb') as qr_file:
                    bot.send_photo(message.chat.id, qr_file, caption=payment_text, reply_markup=InlineKeyboardMarkup().add(
                        InlineKeyboardButton('Γ£à Payment Sent', callback_data='payment_sent'),
                        InlineKeyboardButton('≡ƒöÖ Back to cart', callback_data='cart')
                    ), parse_mode='Markdown')
                
                # Clean up QR file
                try:
                    os.remove(qr_filename)
                except:
                    pass
            
        elif user_id in user_states and user_states[user_id]['pgp_state'] == 'waiting_signature':
            if gpg is None:
                bot.reply_to(message, "Γ¥î PGP functionality is disabled. Please install GPG first.")
                user_states[user_id]['pgp_state'] = None
                user_states[user_id]['pgp_challenge'] = None
            else:
                signature = message.text
                challenge = user_states[user_id]['pgp_challenge']
                try:
                    verified = gpg.verify_data(signature, challenge)
                    if verified:
                        bot.reply_to(message, "Γ£à Signature verified successfully!")
                    else:
                        bot.reply_to(message, "Γ¥î Verification failed. Try again.")
                except Exception as e:
                    bot.reply_to(message, f"Γ¥î Verification error: {str(e)}")
                finally:
                    user_states[user_id]['pgp_state'] = None
                    user_states[user_id]['pgp_challenge'] = None
