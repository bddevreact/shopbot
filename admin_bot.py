<<<<<<< HEAD
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot.apihelper import ApiTelegramException
import json
import datetime
import os

# User data functions
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

def safe_edit_message(bot, chat_id, message_id, text, reply_markup=None, parse_mode=None):
    """Safely edit a message, handling various edit errors"""
    try:
        bot.edit_message_text(text, chat_id, message_id, reply_markup=reply_markup, parse_mode=parse_mode)
    except ApiTelegramException as e:
        if "message is not modified" in str(e):
            pass  # Ignore this error
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
                print(f"Error editing message: {e}")

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

def update_order_status(order_id, new_status, tracking_number="", notes=""):
    """Update order status and notify user"""
    orders_data = load_orders()
    
    for order in orders_data['orders']:
        if order['order_id'] == order_id:
            old_status = order['status']
            order['status'] = new_status
            if tracking_number:
                order['tracking_number'] = tracking_number
            if notes:
                order['notes'] = notes
            
            # Update statistics
            orders_data['statistics']['orders_by_status'][old_status] -= 1
            orders_data['statistics']['orders_by_status'][new_status] += 1
            
            save_orders(orders_data)
            return order
    
    return None

def notify_user_order_update(bot, user_id, order_id, status, tracking_number="", notes=""):
    """Send notification to user about order status update"""
    try:
        if status == "shipped":
            notification_text = f"""
📦 **Your Order Has Been Shipped!**

**Order ID:** {order_id}
**Status:** Shipped
**Tracking Number:** {tracking_number if tracking_number else "Will be provided soon"}

{notes if notes else "Your package is on its way!"}

Thank you for your order! 🚀
            """.strip()
        elif status == "delivered":
            notification_text = f"""
✅ **Order Delivered!**

**Order ID:** {order_id}
**Status:** Delivered

{notes if notes else "Your order has been successfully delivered!"}

Thank you for choosing us! 🎉
            """.strip()
        else:
            notification_text = f"""
📋 **Order Status Update**

**Order ID:** {order_id}
**Status:** {status.title()}

{notes if notes else "Your order status has been updated."}
            """.strip()
        
        bot.send_message(user_id, notification_text, parse_mode='Markdown')
    except Exception as e:
        print(f"Failed to notify user {user_id}: {e}")

def is_admin(user_id, admin_config):
    """Check if user is admin"""
    return any(admin['user_id'] == user_id for admin in admin_config['admin_users'])

def save_categories_to_file(categories, shop_info):
    """Save categories and shop info to admin_categories.json"""
    data = {
        "shop_info": shop_info,
        "categories": categories
    }
    with open('admin_categories.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def create_admin_management_menu():
    """Create admin management menu"""
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton('📦 Manage Categories', callback_data='admin_categories'),
        InlineKeyboardButton('🏷️ Manage Products', callback_data='admin_products')
    )
    markup.add(
        InlineKeyboardButton('📋 Manage Orders', callback_data='admin_orders'),
        InlineKeyboardButton('📊 View Stats', callback_data='admin_stats')
    )
    markup.add(
        InlineKeyboardButton('🏪 Shop Settings', callback_data='admin_shop'),
        InlineKeyboardButton('💾 Create Backup', callback_data='admin_backup')
    )
    markup.add(
        InlineKeyboardButton('🔄 Reload Data', callback_data='admin_reload'),
        InlineKeyboardButton('🔙 Back to Main', callback_data='admin_back_main')
    )
    return markup

def create_order_management_menu():
    """Create order management menu"""
    orders_data = load_orders()
    orders = orders_data['orders']
    
    markup = InlineKeyboardMarkup(row_width=2)
    
    # Show recent orders (last 10)
    recent_orders = sorted(orders, key=lambda x: x['timestamp'], reverse=True)[:10]
    
    for order in recent_orders:
        status_emoji = {
            'pending': '⏳',
            'processing': '🔄',
            'shipped': '📦',
            'delivered': '✅',
            'cancelled': '❌'
        }.get(order['status'], '❓')
        
        button_text = f"{status_emoji} {order['order_id']} - €{order['total_amount']:.2f}"
        markup.add(InlineKeyboardButton(button_text, callback_data=f'admin_order_{order["order_id"]}'))
    
    markup.add(
        InlineKeyboardButton('📊 All Orders', callback_data='admin_all_orders'),
        InlineKeyboardButton('🔙 Back to Admin', callback_data='admin_back_management')
    )
    return markup

def create_order_detail_menu(order):
    """Create order detail management menu"""
    markup = InlineKeyboardMarkup(row_width=2)
    
    # Status update buttons
    if order['status'] == 'pending':
        markup.add(
            InlineKeyboardButton('🔄 Mark Processing', callback_data=f'admin_status_{order["order_id"]}_processing'),
            InlineKeyboardButton('❌ Cancel Order', callback_data=f'admin_status_{order["order_id"]}_cancelled')
        )
    elif order['status'] == 'processing':
        markup.add(
            InlineKeyboardButton('📦 Mark Shipped', callback_data=f'admin_status_{order["order_id"]}_shipped'),
            InlineKeyboardButton('❌ Cancel Order', callback_data=f'admin_status_{order["order_id"]}_cancelled')
        )
    elif order['status'] == 'shipped':
        markup.add(
            InlineKeyboardButton('✅ Mark Delivered', callback_data=f'admin_status_{order["order_id"]}_delivered')
        )
    
    markup.add(InlineKeyboardButton('🔙 Back to Orders', callback_data='admin_orders'))
    return markup

def create_category_management_menu():
    """Create category management menu"""
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton('➕ Add Category', callback_data='admin_add_category'),
        InlineKeyboardButton('📝 Edit Category', callback_data='admin_edit_category')
    )
    markup.add(
        InlineKeyboardButton('🗑️ Delete Category', callback_data='admin_delete_category'),
        InlineKeyboardButton('📋 List Categories', callback_data='admin_list_categories')
    )
    markup.add(InlineKeyboardButton('🔙 Back to Admin', callback_data='admin_back_management'))
    return markup

def create_product_management_menu():
    """Create product management menu"""
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton('➕ Add Product', callback_data='admin_add_product'),
        InlineKeyboardButton('📝 Edit Product', callback_data='admin_edit_product')
    )
    markup.add(
        InlineKeyboardButton('🗑️ Delete Product', callback_data='admin_delete_product'),
        InlineKeyboardButton('📋 List Products', callback_data='admin_list_products')
    )
    markup.add(InlineKeyboardButton('🔙 Back to Admin', callback_data='admin_back_management'))
    return markup

# Global admin states for multi-step operations
admin_states = {}

def setup_admin_handlers(bot, admin_config, categories, shop_info, user_carts, user_states):
    """Setup all admin-related handlers"""
    
    @bot.message_handler(commands=['test'])
    def test_handler(message):
        bot.reply_to(message, f"Bot is working! Your user ID: {message.from_user.id}")
    
    @bot.message_handler(commands=['admin'])
    def admin_panel(message):
        user_id = message.from_user.id
        print(f"Admin command received from user ID: {user_id}")
        print(f"Admin config: {admin_config}")
        print(f"Is admin: {is_admin(user_id, admin_config)}")
        
        if not is_admin(user_id, admin_config):
            bot.reply_to(message, "❌ Access denied. Admin privileges required.")
            return
        
        admin_text = """
🔧 **Admin Panel**

Welcome to the admin management system!

📋 **Available Management Options:**
• 📦 Manage Categories - Add, edit, delete categories
• 🏷️ Manage Products - Add, edit, delete products  
• 🏪 Shop Settings - Configure shop information
• 📊 View Stats - Bot statistics and user data
• 💾 Create Backup - Backup all data
• 🔄 Reload Data - Reload from files

Use the buttons below to manage your shop!
        """.strip()
        
        bot.reply_to(message, admin_text, reply_markup=create_admin_management_menu(), parse_mode='Markdown')

    @bot.message_handler(commands=['reload'])
    def reload_categories(message):
        user_id = message.from_user.id
        if not is_admin(user_id, admin_config):
            bot.reply_to(message, "❌ Access denied. Admin privileges required.")
            return
        
        try:
            with open('admin_categories.json', 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    raise ValueError("admin_categories.json is empty")
                admin_data = json.loads(content)
                categories.clear()
                categories.extend(admin_data['categories'])
                shop_info.update(admin_data['shop_info'])
            bot.reply_to(message, "✅ Categories reloaded successfully!")
        except Exception as e:
            bot.reply_to(message, f"❌ Error reloading categories: {str(e)}")

    @bot.message_handler(commands=['create_discount'])
    def create_discount_code_command(message):
        user_id = message.from_user.id
        if not is_admin(user_id, admin_config):
            bot.reply_to(message, "❌ Access denied. Admin privileges required.")
            return
        
        admin_states[user_id] = {'action': 'create_discount_code'}
        
        bot.reply_to(message, """🎟️ **Create Discount Code**

Please send the discount code information in this format:

```
DISCOUNT_CODE
DISCOUNT_PERCENT
DESCRIPTION
USAGE_LIMIT
MIN_ORDER_AMOUNT (optional)
```

**Example:**
```
VIP20
20
VIP customer discount
50
100
```

This will create a 20% discount code called "VIP20" with 50 uses and minimum order of €100.""")
    
    @bot.message_handler(commands=['send_discount'])
    def send_discount_code_command(message):
        user_id = message.from_user.id
        if not is_admin(user_id, admin_config):
            bot.reply_to(message, "❌ Access denied. Admin privileges required.")
            return
        
        admin_states[user_id] = {'action': 'send_discount_code'}
        
        bot.reply_to(message, """📤 **Send Discount Code to User**

Please send the user ID and discount code in this format:

```
USER_ID DISCOUNT_CODE
```

**Example:**
```
6251161332 VIP20
```

This will send the discount code "VIP20" to user 6251161332 via DM.""")
    
    @bot.message_handler(commands=['list_discounts'])
    def list_discount_codes_command(message):
        user_id = message.from_user.id
        if not is_admin(user_id, admin_config):
            bot.reply_to(message, "❌ Access denied. Admin privileges required.")
            return
        
        if 'discount_codes' not in shop_info or not shop_info['discount_codes']:
            bot.reply_to(message, "❌ No discount codes found.")
            return
        
        discount_text = "🎟️ **Available Discount Codes**\n\n"
        
        for code, info in shop_info['discount_codes'].items():
            status = "✅ Active" if info.get('active', False) else "❌ Inactive"
            used = info.get('used_count', 0)
            limit = info.get('usage_limit', 0)
            min_order = info.get('min_order_amount', 0)
            
            discount_text += f"""**{code}**
• Discount: {info.get('discount_percent', 0)}%
• Description: {info.get('description', 'N/A')}
• Status: {status}
• Usage: {used}/{limit}
• Min Order: €{min_order}
• Created: {info.get('created_at', 'N/A')}

"""
        
        bot.reply_to(message, discount_text, parse_mode='Markdown')
    
    @bot.message_handler(commands=['set_phrase'])
    def set_phrase_code_command(message):
        user_id = message.from_user.id
        if not is_admin(user_id, admin_config):
            bot.reply_to(message, "❌ Access denied. Admin privileges required.")
            return
        
        admin_states[user_id] = {'action': 'set_phrase_code'}
        
        current_phrase = shop_info.get('phrase_code', 'Not set')
        bot.reply_to(message, f"""🔐 **Set Phrase Code**

Current phrase code: `{current_phrase}`

Please send the new phrase code. This will be required for new users to access the bot.

**Example:**
```
WELCOME2024
```

The phrase code should be easy to remember but secure.""")
    
    @bot.message_handler(commands=['set_user_phrase'])
    def set_user_phrase_code_command(message):
        user_id = message.from_user.id
        if not is_admin(user_id, admin_config):
            bot.reply_to(message, "❌ Access denied. Admin privileges required.")
            return
        
        admin_states[user_id] = {'action': 'set_user_phrase_code'}
        
        bot.reply_to(message, """👤 **Set User Personal Phrase Code**

Please send the user ID and phrase code in this format:

```
USER_ID PHRASE_CODE
```

**Example:**
```
6251161332 USER123
```

This will set a personal phrase code for the specific user.""")
    
    @bot.message_handler(commands=['stats'])
    def show_stats(message):
        user_id = message.from_user.id
        if not is_admin(user_id, admin_config):
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

    @bot.callback_query_handler(func=lambda call: call.data.startswith('admin_') or 
                                call.data.startswith('edit_category_') or 
                                call.data.startswith('delete_category_') or 
                                call.data.startswith('confirm_delete_category_') or
                                call.data.startswith('edit_product_') or
                                call.data.startswith('delete_product_') or
                                call.data.startswith('confirm_delete_product_'))
    def admin_callback_handler(call):
        user_id = call.from_user.id
        if not is_admin(user_id, admin_config):
            bot.answer_callback_query(call.id, "❌ Access denied.")
            return
        
        if call.data == 'admin_categories':
            admin_text = """
📦 **Category Management**

Choose an action to manage categories:
• ➕ Add Category - Create new category
• 📝 Edit Category - Modify existing category
• 🗑️ Delete Category - Remove category
• 📋 List Categories - View all categories
            """.strip()
            safe_edit_message(bot, call.message.chat.id, call.message.message_id, admin_text, 
                                reply_markup=create_category_management_menu(), parse_mode='Markdown')
        
        elif call.data == 'admin_products':
            admin_text = """
🏷️ **Product Management**

Choose an action to manage products:
• ➕ Add Product - Create new product
• 📝 Edit Product - Modify existing product
• 🗑️ Delete Product - Remove product
• 📋 List Products - View all products
            """.strip()
            safe_edit_message(bot, call.message.chat.id, call.message.message_id, admin_text, 
                                reply_markup=create_product_management_menu(), parse_mode='Markdown')
        
        elif call.data == 'admin_shop':
            shop_text = f"""
🏪 **Shop Settings**

Current shop information:
• **Name**: {shop_info.get('name', 'Not set')}
• **Currency**: {shop_info.get('currency', 'Not set')}
• **Payment Methods**: {', '.join(shop_info.get('payment_methods', []))}
• **Countries**: {', '.join(shop_info.get('countries', []))}
• **Promotion**: {shop_info.get('promotion', 'Not set')}

Use /admin_shop_edit to modify shop settings.
            """.strip()
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton('🔙 Back to Admin', callback_data='admin_back_management'))
            safe_edit_message(bot, call.message.chat.id, call.message.message_id, shop_text, 
                                reply_markup=markup, parse_mode='Markdown')
        
        elif call.data == 'admin_list_categories':
            if not categories:
                bot.answer_callback_query(call.id, "📋 No categories found.")
                return
            
            categories_text = "📋 **All Categories:**\n\n"
            for i, category in enumerate(categories, 1):
                products_count = len(category.get('products', []))
                categories_text += f"{i}. **{category['name']}**\n"
                categories_text += f"   - Products: {products_count}\n"
                categories_text += f"   - Active: {'✅' if category.get('active', True) else '❌'}\n\n"
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton('🔙 Back to Categories', callback_data='admin_categories'))
            bot.send_message(call.message.chat.id, categories_text, reply_markup=markup, parse_mode='Markdown')
            bot.answer_callback_query(call.id, "📋 Categories list sent!")
        
        elif call.data == 'admin_list_products':
            if not categories:
                bot.answer_callback_query(call.id, "📋 No products found.")
                return
            
            products_text = "🏷️ **All Products:**\n\n"
            for category in categories:
                products_text += f"**{category['name']}:**\n"
                for product in category.get('products', []):
                    image_status = "🖼️" if product.get('image_url') else "❌"
                    if 'quantities' in product:
                        min_price = min(qty['price'] for qty in product['quantities'])
                        max_price = max(qty['price'] for qty in product['quantities'])
                        products_text += f"  • {product['name']} (€{min_price:.1f}-€{max_price:.1f}) {image_status}\n"
                    else:
                        products_text += f"  • {product['name']} (€{product.get('price', 0):.2f}) {image_status}\n"
                products_text += "\n"
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton('🔙 Back to Products', callback_data='admin_products'))
            bot.send_message(call.message.chat.id, products_text, reply_markup=markup, parse_mode='Markdown')
            bot.answer_callback_query(call.id, "🏷️ Products list sent!")
        
        
        elif call.data == 'admin_edit_category':
            # Show list of categories to edit
            if not categories:
                safe_edit_message(bot, call.message.chat.id, call.message.message_id, 
                                "❌ No categories found to edit.", 
                                reply_markup=create_category_management_menu())
                return
            
            markup = InlineKeyboardMarkup(row_width=1)
            for category in categories:
                category_id = category.get('id', category['name'].lower().replace(' ', '_'))
                markup.add(InlineKeyboardButton(f"📝 {category['name']}", 
                                              callback_data=f"edit_category_{category_id}"))
            markup.add(InlineKeyboardButton('🔙 Back', callback_data='admin_categories'))
            
            safe_edit_message(bot, call.message.chat.id, call.message.message_id, 
                            "📝 **Edit Category**\n\nSelect a category to edit:", 
                            reply_markup=markup, parse_mode='Markdown')
        
        elif call.data == 'admin_delete_category':
            # Show list of categories to delete
            if not categories:
                safe_edit_message(bot, call.message.chat.id, call.message.message_id, 
                                "❌ No categories found to delete.", 
                                reply_markup=create_category_management_menu())
                return
            
            markup = InlineKeyboardMarkup(row_width=1)
            for category in categories:
                category_id = category.get('id', category['name'].lower().replace(' ', '_'))
                markup.add(InlineKeyboardButton(f"🗑️ {category['name']}", 
                                              callback_data=f"delete_category_{category_id}"))
            markup.add(InlineKeyboardButton('🔙 Back', callback_data='admin_categories'))
            
            safe_edit_message(bot, call.message.chat.id, call.message.message_id, 
                            "🗑️ **Delete Category**\n\n⚠️ **Warning**: This will permanently delete the category and all its products!\n\nSelect a category to delete:", 
                            reply_markup=markup, parse_mode='Markdown')
        
        elif call.data == 'admin_add_product':
            if not categories:
                bot.answer_callback_query(call.id, "❌ No categories available. Create a category first.")
                return
            
            # Create category selection menu
            markup = InlineKeyboardMarkup(row_width=1)
            for category in categories:
                markup.add(InlineKeyboardButton(category['name'], callback_data=f"admin_add_product_to_{category['name']}"))
            markup.add(InlineKeyboardButton('🔙 Back to Products', callback_data='admin_products'))
            
            safe_edit_message(bot, call.message.chat.id, call.message.message_id, "🏷️ **Add New Product**\n\nSelect the category for the new product:", 
                                reply_markup=markup, parse_mode='Markdown')
        
        elif call.data == 'admin_edit_product':
            # Show list of products to edit
            if not categories:
                safe_edit_message(bot, call.message.chat.id, call.message.message_id, 
                                "❌ No products found to edit.", 
                                reply_markup=create_product_management_menu())
                return
            
            markup = InlineKeyboardMarkup(row_width=1)
            for category in categories:
                category_id = category.get('id', category['name'].lower().replace(' ', '_'))
                for product in category.get('products', []):
                    product_id = product.get('id', product['name'].lower().replace(' ', '_').replace('★', '').replace('*', ''))
                    button_text = f"📝 {product['name']} ({category['name']})"
                    markup.add(InlineKeyboardButton(button_text, 
                                                  callback_data=f"edit_product_{category_id}|{product_id}"))
            markup.add(InlineKeyboardButton('🔙 Back', callback_data='admin_products'))
            
            safe_edit_message(bot, call.message.chat.id, call.message.message_id, 
                            "📝 **Edit Product**\n\nSelect a product to edit:", 
                            reply_markup=markup, parse_mode='Markdown')
        
        elif call.data == 'admin_delete_product':
            # Show list of products to delete
            if not categories:
                safe_edit_message(bot, call.message.chat.id, call.message.message_id, 
                                "❌ No products found to delete.", 
                                reply_markup=create_product_management_menu())
                return
            
            markup = InlineKeyboardMarkup(row_width=1)
            for category in categories:
                category_id = category.get('id', category['name'].lower().replace(' ', '_'))
                for product in category.get('products', []):
                    product_id = product.get('id', product['name'].lower().replace(' ', '_').replace('★', '').replace('*', ''))
                    button_text = f"🗑️ {product['name']} ({category['name']})"
                    markup.add(InlineKeyboardButton(button_text, 
                                                  callback_data=f"delete_product_{category_id}|{product_id}"))
            markup.add(InlineKeyboardButton('🔙 Back', callback_data='admin_products'))
            
            safe_edit_message(bot, call.message.chat.id, call.message.message_id, 
                            "🗑️ **Delete Product**\n\n⚠️ **Warning**: This will permanently delete the product!\n\nSelect a product to delete:", 
                            reply_markup=markup, parse_mode='Markdown')
        
        elif call.data == 'admin_back_management':
            admin_text = """
🔧 **Admin Panel**

Welcome to the admin management system!

📋 **Available Management Options:**
• 📦 Manage Categories - Add, edit, delete categories
• 🏷️ Manage Products - Add, edit, delete products  
• 🏪 Shop Settings - Configure shop information
• 📊 View Stats - Bot statistics and user data
• 💾 Create Backup - Backup all data
• 🔄 Reload Data - Reload from files

Use the buttons below to manage your shop!
            """.strip()
            safe_edit_message(bot, call.message.chat.id, call.message.message_id, admin_text, 
                                reply_markup=create_admin_management_menu(), parse_mode='Markdown')
        
        elif call.data == 'admin_reload':
            try:
                with open('admin_categories.json', 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        raise ValueError("admin_categories.json is empty")
                    admin_data = json.loads(content)
                    categories.clear()
                    categories.extend(admin_data['categories'])
                    shop_info.update(admin_data['shop_info'])
                bot.answer_callback_query(call.id, "✅ Data reloaded!")
            except Exception as e:
                bot.answer_callback_query(call.id, f"❌ Error: {str(e)}")
        
        elif call.data == 'admin_orders':
            orders_data = load_orders()
            orders = orders_data['orders']
            
            if not orders:
                orders_text = "📋 **Order Management**\n\nNo orders found."
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton('🔙 Back to Admin', callback_data='admin_back_management'))
            else:
                orders_text = f"📋 **Order Management**\n\n**Total Orders:** {len(orders)}\n**Recent Orders:**"
                markup = create_order_management_menu()
            
            safe_edit_message(bot, call.message.chat.id, call.message.message_id, orders_text, reply_markup=markup, parse_mode='Markdown')
            bot.answer_callback_query(call.id, "Order management")
        
        elif call.data.startswith('admin_order_'):
            order_id = call.data.replace('admin_order_', '')
            orders_data = load_orders()
            order = None
            
            for o in orders_data['orders']:
                if o['order_id'] == order_id:
                    order = o
                    break
            
            if order:
                # Format order details
                items_text = ""
                for item in order['items']:
                    items_text += f"• {item['name']} - €{item['price']:.2f}\n"
                
                # Use HTML parsing mode for better reliability
                def escape_html(text):
                    if text is None:
                        return ""
                    text = str(text)
                    text = text.replace('&', '&amp;')
                    text = text.replace('<', '&lt;')
                    text = text.replace('>', '&gt;')
                    return text
                
                safe_address = escape_html(order['delivery_address'][:100])
                safe_items = escape_html(items_text)
                safe_tracking = escape_html(order.get('tracking_number', 'Not provided'))
                safe_notes = escape_html(order.get('notes', 'None'))
                
                order_text = f"""
📋 <b>Order Details</b>

<b>Order ID:</b> {order['order_id']}
<b>User ID:</b> {order['user_id']}
<b>Status:</b> {order['status'].title()}
<b>Date:</b> {datetime.datetime.fromisoformat(order['timestamp']).strftime('%Y-%m-%d %H:%M')}

<b>Items:</b>
{safe_items}

<b>Delivery:</b> {order['delivery_method']} - €{order['delivery_price']:.2f}
<b>Payment:</b> {order['payment_method'].upper()}
<b>Total:</b> €{order['total_amount']:.2f}

<b>Address:</b> {safe_address}{'...' if len(order['delivery_address']) > 100 else ''}

<b>Tracking:</b> {safe_tracking}
<b>Notes:</b> {safe_notes}
                """.strip()
                
                markup = create_order_detail_menu(order)
                safe_edit_message(bot, call.message.chat.id, call.message.message_id, order_text, reply_markup=markup, parse_mode='HTML')
                bot.answer_callback_query(call.id, f"Order {order_id}")
            else:
                bot.answer_callback_query(call.id, "Order not found!")
        
        elif call.data.startswith('admin_status_'):
            # Handle order status updates
            parts = call.data.replace('admin_status_', '').split('_')
            if len(parts) >= 2:
                order_id = parts[0]
                new_status = parts[1]
                
                # Update order status
                order = update_order_status(order_id, new_status)
                
                if order:
                    # Notify user
                    notify_user_order_update(bot, order['user_id'], order_id, new_status)
                    
                    # Update admin message
                    bot.answer_callback_query(call.id, f"Order {order_id} marked as {new_status}")
                    
                    # Refresh order list
                    orders_data = load_orders()
                    orders = orders_data['orders']
                    
                    if not orders:
                        orders_text = "📋 **Order Management**\n\nNo orders found."
                        markup = InlineKeyboardMarkup()
                        markup.add(InlineKeyboardButton('🔙 Back to Admin', callback_data='admin_back_management'))
                    else:
                        orders_text = f"📋 **Order Management**\n\n**Total Orders:** {len(orders)}\n**Recent Orders:**"
                        markup = create_order_management_menu()
                    
                    safe_edit_message(bot, call.message.chat.id, call.message.message_id, orders_text, reply_markup=markup, parse_mode='Markdown')
                else:
                    bot.answer_callback_query(call.id, "Failed to update order!")
        
        elif call.data == 'admin_all_orders':
            orders_data = load_orders()
            orders = orders_data['orders']
            
            if not orders:
                all_orders_text = "📊 **All Orders**\n\nNo orders found."
            else:
                all_orders_text = f"📊 **All Orders** ({len(orders)} total)\n\n"
                
                # Group by status
                status_groups = {}
                for order in orders:
                    status = order['status']
                    if status not in status_groups:
                        status_groups[status] = []
                    status_groups[status].append(order)
                
                for status, status_orders in status_groups.items():
                    status_emoji = {
                        'pending': '⏳',
                        'processing': '🔄',
                        'shipped': '📦',
                        'delivered': '✅',
                        'cancelled': '❌'
                    }.get(status, '❓')
                    
                    all_orders_text += f"{status_emoji} **{status.title()}** ({len(status_orders)})\n"
                    for order in status_orders[:5]:  # Show max 5 per status
                        all_orders_text += f"• {order['order_id']} - €{order['total_amount']:.2f}\n"
                    if len(status_orders) > 5:
                        all_orders_text += f"• ... and {len(status_orders) - 5} more\n"
                    all_orders_text += "\n"
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton('🔙 Back to Orders', callback_data='admin_orders'))
            
            safe_edit_message(bot, call.message.chat.id, call.message.message_id, all_orders_text, reply_markup=markup, parse_mode='Markdown')
            bot.answer_callback_query(call.id, "All orders view")
        
        elif call.data == 'admin_stats':
            orders_data = load_orders()
            
            # Load user statistics
            try:
                with open('users.json', 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        users_data = {"users": [], "statistics": {"total_users": 0}}
                    else:
                        users_data = json.loads(content)
                total_registered_users = users_data['statistics']['total_users']
                # Count unique users (by user_id)
                unique_users = len(set(user['user_id'] for user in users_data['users']))
            except:
                total_registered_users = 0
                unique_users = 0
            
            total_users = len(user_states)
            total_carts = len(user_carts)
            active_carts = sum(1 for cart in user_carts.values() if cart)
            total_categories = len(categories)
            total_products = sum(len(cat['products']) for cat in categories)
            
            # Order statistics
            total_orders = orders_data['statistics']['total_orders']
            total_sales = orders_data['statistics']['total_sales']
            orders_by_status = orders_data['statistics']['orders_by_status']
            
            stats_text = f"""
📊 **Bot Statistics**

👥 **User Statistics:**
• **Active Sessions:** {total_users}
• **Total User Entries:** {total_registered_users}
• **Unique Users:** {unique_users}
• **Active Carts:** {active_carts}

📦 **Product Statistics:**
• **Categories:** {total_categories}
• **Products:** {total_products}

📋 **Order Statistics:**
• **Total Orders:** {total_orders}
• **Total Sales:** €{total_sales:.2f}
• **Pending:** {orders_by_status['pending']}
• **Processing:** {orders_by_status['processing']}
• **Shipped:** {orders_by_status['shipped']}
• **Delivered:** {orders_by_status['delivered']}
• **Cancelled:** {orders_by_status['cancelled']}
            """.strip()
            
            bot.send_message(call.message.chat.id, stats_text, parse_mode='Markdown')
            bot.answer_callback_query(call.id, "📊 Stats sent!")
        
        elif call.data == 'admin_backup':
            try:
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
        
        # Handle edit category selection
        elif call.data.startswith('edit_category_'):
            category_id = call.data.split('_', 2)[2]
            category = next((cat for cat in categories if cat['id'] == category_id), None)
            
            if category:
                admin_states[user_id] = {
                    'action': 'edit_category',
                    'category_id': category_id,
                    'category_name': category['name']
                }
                
                bot.send_message(call.message.chat.id, f"""
📝 **Edit Category: {category['name']}**

Current information:
**Name**: {category['name']}
**Description**: {category.get('description', 'No description')}
**Active**: {'Yes' if category.get('active', True) else 'No'}
**Products**: {len(category.get('products', []))} products

Please send the updated category information in this format:

```
New Category Name
New Category Description
```

Example:
```
UPDATED STIMULANTS
Updated high-quality stimulant products
```

Type 'cancel' to abort editing.
                """.strip())
                bot.answer_callback_query(call.id, f"📝 Editing {category['name']}")
            else:
                bot.answer_callback_query(call.id, "❌ Category not found!")
        
        # Handle delete category selection
        elif call.data.startswith('delete_category_'):
            category_id = call.data.split('_', 2)[2]
            category = next((cat for cat in categories if cat['id'] == category_id), None)
            
            if category:
                # Show confirmation dialog
                markup = InlineKeyboardMarkup(row_width=2)
                markup.add(
                    InlineKeyboardButton('✅ Yes, Delete', callback_data=f'confirm_delete_category_{category_id}'),
                    InlineKeyboardButton('❌ Cancel', callback_data='admin_categories')
                )
                
                safe_edit_message(bot, call.message.chat.id, call.message.message_id, 
                                f"🗑️ **Confirm Delete Category**\n\n"
                                f"**Category**: {category['name']}\n"
                                f"**Description**: {category.get('description', 'No description')}\n"
                                f"**Products**: {len(category.get('products', []))} products\n\n"
                                f"⚠️ **This action cannot be undone!**\n"
                                f"All products in this category will also be deleted.\n\n"
                                f"Are you sure you want to delete this category?",
                                reply_markup=markup, parse_mode='Markdown')
                bot.answer_callback_query(call.id, f"🗑️ Confirm delete {category['name']}")
            else:
                bot.answer_callback_query(call.id, "❌ Category not found!")
        
        # Handle confirmed category deletion
        elif call.data.startswith('confirm_delete_category_'):
            category_id = call.data.split('_', 3)[3]
            
            # Find and remove the category
            category_to_delete = None
            for i, category in enumerate(categories):
                if category['id'] == category_id:
                    category_to_delete = category
                    categories.pop(i)
                    break
            
            if category_to_delete:
                # Save the updated categories
                save_categories_to_file(categories, shop_info)
                
                safe_edit_message(bot, call.message.chat.id, call.message.message_id, 
                                f"✅ **Category Deleted**\n\n"
                                f"Successfully deleted category: **{category_to_delete['name']}**\n"
                                f"Products deleted: {len(category_to_delete.get('products', []))}",
                                reply_markup=create_category_management_menu(), parse_mode='Markdown')
                bot.answer_callback_query(call.id, f"✅ Deleted {category_to_delete['name']}")
            else:
                bot.answer_callback_query(call.id, "❌ Category not found!")
        
        # Handle edit product selection
        elif call.data.startswith('edit_product_'):
            # Parse format: edit_product_category_id|product_id
            data_part = call.data.replace('edit_product_', '')
            if '|' in data_part:
                category_id, product_id = data_part.split('|', 1)
                
                # Find the product
                product = None
                category = None
                for cat in categories:
                    if cat['id'] == category_id:
                        category = cat
                        for prod in cat.get('products', []):
                            if prod['id'] == product_id:
                                product = prod
                                break
                        break
                
                if product and category:
                    admin_states[user_id] = {
                        'action': 'edit_product',
                        'category_id': category_id,
                        'product_id': product_id,
                        'product_name': product['name']
                    }
                    
                    # Send product information with large image if available
                    if product.get('image_url'):
                        try:
                            edit_text = f"""
📝 **Edit Product: {product['name']}**

Current information:
**Name**: {product['name']}
**Description**: {product.get('description', 'No description')}
**Price**: €{product.get('price', 0):.2f}
**Stock**: {product.get('stock', 0)}
**Active**: {'Yes' if product.get('active', True) else 'No'}
**Image**: ✅ Available

Please send the updated product information in this format:

```
New Product Name
New Product Description
New Price
New Stock
```

Example:
```
UPDATED XTC PILLS
Updated high-quality XTC pills
18.50
150
```

Type 'cancel' to abort editing.
                            """.strip()
                            bot.send_photo(call.message.chat.id, product['image_url'], caption=edit_text, parse_mode='Markdown')
                        except Exception as e:
                            print(f"Failed to send product image in admin: {e}")
                            # Fall back to text only
                            edit_text = f"""
📝 **Edit Product: {product['name']}**

Current information:
**Name**: {product['name']}
**Description**: {product.get('description', 'No description')}
**Price**: €{product.get('price', 0):.2f}
**Stock**: {product.get('stock', 0)}
**Active**: {'Yes' if product.get('active', True) else 'No'}
**Image**: ❌ Failed to load

Please send the updated product information in this format:

```
New Product Name
New Product Description
New Price
New Stock
```

Example:
```
UPDATED XTC PILLS
Updated high-quality XTC pills
18.50
150
```

Type 'cancel' to abort editing.
                            """.strip()
                            bot.send_message(call.message.chat.id, edit_text, parse_mode='Markdown')
                    else:
                        edit_text = f"""
📝 **Edit Product: {product['name']}**

Current information:
**Name**: {product['name']}
**Description**: {product.get('description', 'No description')}
**Price**: €{product.get('price', 0):.2f}
**Stock**: {product.get('stock', 0)}
**Active**: {'Yes' if product.get('active', True) else 'No'}
**Image**: ❌ No image available

Please send the updated product information in this format:

```
New Product Name
New Product Description
New Price
New Stock
```

Example:
```
UPDATED XTC PILLS
Updated high-quality XTC pills
18.50
150
```

Type 'cancel' to abort editing.
                        """.strip()
                        bot.send_message(call.message.chat.id, edit_text, parse_mode='Markdown')
                    bot.answer_callback_query(call.id, f"📝 Editing {product['name']}")
                else:
                    bot.answer_callback_query(call.id, "❌ Product not found!")
        
        # Handle delete product selection
        elif call.data.startswith('delete_product_'):
            # Parse format: delete_product_category_id|product_id
            data_part = call.data.replace('delete_product_', '')
            if '|' in data_part:
                category_id, product_id = data_part.split('|', 1)
                
                # Find the product
                product = None
                category = None
                for cat in categories:
                    if cat['id'] == category_id:
                        category = cat
                        for prod in cat.get('products', []):
                            if prod['id'] == product_id:
                                product = prod
                                break
                        break
                
                if product and category:
                    # Show confirmation dialog
                    markup = InlineKeyboardMarkup(row_width=2)
                    markup.add(
                        InlineKeyboardButton('✅ Yes, Delete', callback_data=f'confirm_delete_product_{category_id}|{product_id}'),
                        InlineKeyboardButton('❌ Cancel', callback_data='admin_products')
                    )
                    
                    safe_edit_message(bot, call.message.chat.id, call.message.message_id, 
                                    f"🗑️ **Confirm Delete Product**\n\n"
                                    f"**Product**: {product['name']}\n"
                                    f"**Category**: {category['name']}\n"
                                    f"**Price**: €{product.get('price', 0):.2f}\n"
                                    f"**Stock**: {product.get('stock', 0)}\n\n"
                                    f"⚠️ **This action cannot be undone!**\n\n"
                                    f"Are you sure you want to delete this product?",
                                    reply_markup=markup, parse_mode='Markdown')
                    bot.answer_callback_query(call.id, f"🗑️ Confirm delete {product['name']}")
                else:
                    bot.answer_callback_query(call.id, "❌ Product not found!")
        
        # Handle confirmed product deletion
        elif call.data.startswith('confirm_delete_product_'):
            # Parse format: confirm_delete_product_category_id|product_id
            data_part = call.data.replace('confirm_delete_product_', '')
            if '|' in data_part:
                category_id, product_id = data_part.split('|', 1)
                
                # Find and remove the product
                product_to_delete = None
                category = None
                for cat in categories:
                    if cat['id'] == category_id:
                        category = cat
                        for i, prod in enumerate(cat.get('products', [])):
                            if prod['id'] == product_id:
                                product_to_delete = prod
                                cat['products'].pop(i)
                                break
                        break
                
                if product_to_delete and category:
                    # Save the updated categories
                    save_categories_to_file(categories, shop_info)
                    
                    safe_edit_message(bot, call.message.chat.id, call.message.message_id, 
                                    f"✅ **Product Deleted**\n\n"
                                    f"Successfully deleted product: **{product_to_delete['name']}**\n"
                                    f"From category: **{category['name']}**",
                                    reply_markup=create_product_management_menu(), parse_mode='Markdown')
                    bot.answer_callback_query(call.id, f"✅ Deleted {product_to_delete['name']}")
                else:
                    bot.answer_callback_query(call.id, "❌ Product not found!")
    
    @bot.message_handler(func=lambda message: is_admin(message.from_user.id, admin_config))
    def admin_message_handler(message):
        user_id = message.from_user.id
        text = message.text.strip()
        
        print(f"Admin message received from user {user_id}: {text}")
        print(f"Current admin states: {admin_states}")
        print(f"User state: {admin_states.get(user_id, 'No state')}")
        
        # Handle category creation
        if user_id in admin_states and admin_states[user_id].get('action') == 'add_category':
            try:
                lines = text.split('\n')
                if len(lines) >= 2:
                    name = lines[0].strip()
                    description = lines[1].strip()
                    
                    # Create new category
                    new_category = {
                        "id": name.lower().replace(' ', '_'),
                        "name": name,
                        "description": description,
                        "active": True,
                        "products": []
                    }
                    
                    categories.append(new_category)
                    save_categories_to_file(categories, shop_info)
                    
                    bot.reply_to(message, f"✅ Category '{name}' created successfully!")
                    del admin_states[user_id]
                else:
                    bot.reply_to(message, "❌ Please provide both name and description on separate lines.")
            except Exception as e:
                bot.reply_to(message, f"❌ Error creating category: {str(e)}")
                del admin_states[user_id]
        
        # Handle category editing
        elif user_id in admin_states and admin_states[user_id].get('action') == 'edit_category':
            try:
                if text.lower() == 'cancel':
                    bot.reply_to(message, "❌ Category editing cancelled.")
                    del admin_states[user_id]
                    return
                
                lines = text.split('\n')
                if len(lines) >= 2:
                    new_name = lines[0].strip()
                    new_description = lines[1].strip()
                    category_id = admin_states[user_id]['category_id']
                    old_name = admin_states[user_id]['category_name']
                    
                    # Find and update the category
                    category_found = False
                    for category in categories:
                        if category['id'] == category_id:
                            category['name'] = new_name
                            category['description'] = new_description
                            category_found = True
                            break
                    
                    if category_found:
                        save_categories_to_file(categories, shop_info)
                        bot.reply_to(message, f"✅ Category '{old_name}' updated to '{new_name}' successfully!")
                    else:
                        bot.reply_to(message, "❌ Category not found!")
                    
                    del admin_states[user_id]
                else:
                    bot.reply_to(message, "❌ Please provide both name and description on separate lines.")
            except Exception as e:
                bot.reply_to(message, f"❌ Error editing category: {str(e)}")
                del admin_states[user_id]
        
        # Handle product creation
        elif user_id in admin_states and admin_states[user_id].get('action') == 'add_product':
            try:
                lines = text.split('\n')
                if len(lines) >= 3:
                    name = lines[0].strip()
                    description = lines[1].strip()
                    price = float(lines[2].strip())
                    
                    category_name = admin_states[user_id].get('category')
                    category = next((cat for cat in categories if cat['name'] == category_name), None)
                    
                    if category:
                        new_product = {
                            "id": name.lower().replace(' ', '_').replace('★', '').replace('*', ''),
                            "name": name,
                            "price": price,
                            "description": description,
                            "stock": 100,
                            "active": True
                        }
                        
                        category['products'].append(new_product)
                        save_categories_to_file(categories, shop_info)
                        
                        bot.reply_to(message, f"✅ Product '{name}' added to category '{category_name}' successfully!")
                        del admin_states[user_id]
                    else:
                        bot.reply_to(message, f"❌ Category '{category_name}' not found.")
                        del admin_states[user_id]
                else:
                    bot.reply_to(message, "❌ Please provide name, description, and price on separate lines.")
            except ValueError:
                bot.reply_to(message, "❌ Price must be a valid number.")
            except Exception as e:
                bot.reply_to(message, f"❌ Error creating product: {str(e)}")
                del admin_states[user_id]
        
        # Handle product editing
        elif user_id in admin_states and admin_states[user_id].get('action') == 'edit_product':
            try:
                if text.lower() == 'cancel':
                    bot.reply_to(message, "❌ Product editing cancelled.")
                    del admin_states[user_id]
                    return
                
                lines = text.split('\n')
                if len(lines) >= 4:
                    new_name = lines[0].strip()
                    new_description = lines[1].strip()
                    new_price = float(lines[2].strip())
                    new_stock = int(lines[3].strip())
                    
                    category_id = admin_states[user_id]['category_id']
                    product_id = admin_states[user_id]['product_id']
                    old_name = admin_states[user_id]['product_name']
                    
                    # Find and update the product
                    product_found = False
                    for category in categories:
                        if category['id'] == category_id:
                            for product in category.get('products', []):
                                if product['id'] == product_id:
                                    product['name'] = new_name
                                    product['description'] = new_description
                                    product['price'] = new_price
                                    product['stock'] = new_stock
                                    product_found = True
                                    break
                            break
                    
                    if product_found:
                        save_categories_to_file(categories, shop_info)
                        bot.reply_to(message, f"✅ Product '{old_name}' updated to '{new_name}' successfully!")
                    else:
                        bot.reply_to(message, "❌ Product not found!")
                    
                    del admin_states[user_id]
                else:
                    bot.reply_to(message, "❌ Please provide name, description, price, and stock on separate lines.")
            except ValueError:
                bot.reply_to(message, "❌ Price and stock must be valid numbers.")
            except Exception as e:
                bot.reply_to(message, f"❌ Error editing product: {str(e)}")
                del admin_states[user_id]
        
        # Handle discount code creation
        elif user_id in admin_states and admin_states[user_id].get('action') == 'create_discount_code':
            try:
                lines = text.split('\n')
                if len(lines) >= 4:
                    code = lines[0].strip().upper()
                    discount_percent = float(lines[1].strip())
                    description = lines[2].strip()
                    usage_limit = int(lines[3].strip())
                    min_order_amount = float(lines[4].strip()) if len(lines) > 4 else 0
                    
                    # Initialize discount codes if not exists
                    if 'discount_codes' not in shop_info:
                        shop_info['discount_codes'] = {}
                    
                    # Create new discount code
                    shop_info['discount_codes'][code] = {
                        'discount_percent': discount_percent,
                        'description': description,
                        'active': True,
                        'usage_limit': usage_limit,
                        'used_count': 0,
                        'min_order_amount': min_order_amount,
                        'created_by': user_id,
                        'created_at': datetime.datetime.now().isoformat()
                    }
                    
                    save_categories_to_file(categories, shop_info)
                    
                    bot.reply_to(message, f"""✅ **Discount Code Created Successfully!**

**Code:** {code}
**Discount:** {discount_percent}% off
**Description:** {description}
**Usage Limit:** {usage_limit}
**Min Order:** €{min_order_amount}

You can now send this code to users via DM.""")
                    del admin_states[user_id]
                else:
                    bot.reply_to(message, """❌ Please provide all required information:

```
DISCOUNT_CODE
DISCOUNT_PERCENT
DESCRIPTION
USAGE_LIMIT
MIN_ORDER_AMOUNT (optional)
```

Example:
```
VIP20
20
VIP customer discount
50
100
```""")
            except ValueError:
                bot.reply_to(message, "❌ Discount percent, usage limit, and min order amount must be valid numbers.")
            except Exception as e:
                bot.reply_to(message, f"❌ Error creating discount code: {str(e)}")
                del admin_states[user_id]
        
        # Handle sending discount code to user
        elif user_id in admin_states and admin_states[user_id].get('action') == 'send_discount_code':
            try:
                parts = text.split(' ', 1)
                if len(parts) >= 2:
                    target_user_id = int(parts[0])
                    discount_code = parts[1].strip().upper()
                    
                    # Check if discount code exists
                    if 'discount_codes' not in shop_info or discount_code not in shop_info['discount_codes']:
                        bot.reply_to(message, f"❌ Discount code '{discount_code}' does not exist!")
                        del admin_states[user_id]
                        return
                    
                    # Send discount code to user
                    discount_info = shop_info['discount_codes'][discount_code]
                    message_text = f"""🎟️ **Special Discount Code for You!**

**Code:** `{discount_code}`
**Discount:** {discount_info['discount_percent']}% off
**Description:** {discount_info['description']}

Use this code during checkout to get your discount!

*This code was sent personally by our admin team.*"""
                    
                    try:
                        bot.send_message(target_user_id, message_text, parse_mode='Markdown')
                        bot.reply_to(message, f"✅ Discount code '{discount_code}' sent successfully to user {target_user_id}!")
                    except Exception as send_error:
                        bot.reply_to(message, f"❌ Failed to send message to user {target_user_id}: {str(send_error)}")
                    
                    del admin_states[user_id]
                else:
                    bot.reply_to(message, """❌ Please provide user ID and discount code:

```
USER_ID DISCOUNT_CODE
```

Example:
```
6251161332 VIP20
```""")
            except ValueError:
                bot.reply_to(message, "❌ User ID must be a valid number.")
            except Exception as e:
                bot.reply_to(message, f"❌ Error sending discount code: {str(e)}")
                del admin_states[user_id]
        
        # Handle setting phrase code
        elif user_id in admin_states and admin_states[user_id].get('action') == 'set_phrase_code':
            try:
                new_phrase = text.strip().upper()
                
                if len(new_phrase) < 3:
                    bot.reply_to(message, "❌ Phrase code must be at least 3 characters long.")
                    del admin_states[user_id]
                    return
                
                # Update phrase code in shop info
                shop_info['phrase_code'] = new_phrase
                save_categories_to_file(categories, shop_info)
                
                bot.reply_to(message, f"""✅ **Phrase Code Updated Successfully!**

**New phrase code:** `{new_phrase}`

This phrase code will now be required for new users to access the bot.

**Note:** Existing verified users will not be affected.""")
                del admin_states[user_id]
            except Exception as e:
                bot.reply_to(message, f"❌ Error setting phrase code: {str(e)}")
                del admin_states[user_id]
        
        # Handle setting user personal phrase code
        elif user_id in admin_states and admin_states[user_id].get('action') == 'set_user_phrase_code':
            try:
                parts = text.split(' ', 1)
                if len(parts) >= 2:
                    target_user_id = int(parts[0])
                    personal_phrase = parts[1].strip().upper()
                    
                    if len(personal_phrase) < 3:
                        bot.reply_to(message, "❌ Phrase code must be at least 3 characters long.")
                        del admin_states[user_id]
                        return
                    
                    # Load users data
                    users_data = load_users()
                    user_found = False
                    
                    for user in users_data['users']:
                        if user['user_id'] == target_user_id:
                            user['personal_phrase_code'] = personal_phrase
                            user_found = True
                            break
                    
                    if user_found:
                        save_users(users_data)
                        bot.reply_to(message, f"""✅ **User Personal Phrase Code Set Successfully!**

**User ID:** {target_user_id}
**Personal Phrase Code:** `{personal_phrase}`

This user will now see their personal phrase code when they use /start.""")
                    else:
                        bot.reply_to(message, f"❌ User with ID {target_user_id} not found.")
                    
                    del admin_states[user_id]
                else:
                    bot.reply_to(message, """❌ Please provide user ID and phrase code:

```
USER_ID PHRASE_CODE
```

Example:
```
6251161332 USER123
```""")
            except ValueError:
                bot.reply_to(message, "❌ User ID must be a valid number.")
            except Exception as e:
                bot.reply_to(message, f"❌ Error setting user phrase code: {str(e)}")
                del admin_states[user_id]
    
    # Handle category selection for product addition
    @bot.callback_query_handler(func=lambda call: call.data.startswith('admin_add_product_to_'))
    def handle_category_selection(call):
        user_id = call.from_user.id
        if not is_admin(user_id, admin_config):
            bot.answer_callback_query(call.id, "❌ Access denied.")
            return
        
        category_name = call.data.replace('admin_add_product_to_', '')
        admin_states[user_id] = {'action': 'add_product', 'category': category_name}
        print(f"Category selection: User {user_id} selected category '{category_name}'")
        print(f"Admin states: {admin_states}")
        
        bot.send_message(call.message.chat.id, f"""
🏷️ **Add Product to {category_name}**

Please send the product information in this format:

```
Product Name
Product Description
Price
```

Example:
```
XTC ★ RED BULL ★ 250mg MDMA
High-quality XTC pills with red bull design
15.50
```

The product will be added to the {category_name} category.
        """.strip())
        
        bot.answer_callback_query(call.id, f"📝 Please send product details for {category_name}!")
    
    # Handle category addition
    @bot.callback_query_handler(func=lambda call: call.data == 'admin_add_category')
    def handle_add_category(call):
        user_id = call.from_user.id
        print(f"Add category callback received from user {user_id}")
        if not is_admin(user_id, admin_config):
            print(f"User {user_id} is not admin")
            bot.answer_callback_query(call.id, "❌ Access denied.")
            return
        
        print(f"Setting admin state for user {user_id}: add_category")
        admin_states[user_id] = {'action': 'add_category'}
        
        bot.send_message(call.message.chat.id, """
➕ **Add New Category**

Please send the category information in this format:

```
Category Name
Category Description
```

Example:
```
STIMULANTS
High-quality stimulant products
```

The category will be created with no products initially.
        """.strip())
        bot.answer_callback_query(call.id, "📝 Please send category details!")
=======
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot.apihelper import ApiTelegramException
import json
import datetime
import os

# User data functions
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

def safe_edit_message(bot, chat_id, message_id, text, reply_markup=None, parse_mode=None):
    """Safely edit a message, handling various edit errors"""
    try:
        bot.edit_message_text(text, chat_id, message_id, reply_markup=reply_markup, parse_mode=parse_mode)
    except ApiTelegramException as e:
        if "message is not modified" in str(e):
            pass  # Ignore this error
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
                print(f"Error editing message: {e}")

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

def update_order_status(order_id, new_status, tracking_number="", notes=""):
    """Update order status and notify user"""
    orders_data = load_orders()
    
    for order in orders_data['orders']:
        if order['order_id'] == order_id:
            old_status = order['status']
            order['status'] = new_status
            if tracking_number:
                order['tracking_number'] = tracking_number
            if notes:
                order['notes'] = notes
            
            # Update statistics
            orders_data['statistics']['orders_by_status'][old_status] -= 1
            orders_data['statistics']['orders_by_status'][new_status] += 1
            
            save_orders(orders_data)
            return order
    
    return None

def notify_user_order_update(bot, user_id, order_id, status, tracking_number="", notes=""):
    """Send notification to user about order status update"""
    try:
        if status == "shipped":
            notification_text = f"""
📦 **Your Order Has Been Shipped!**

**Order ID:** {order_id}
**Status:** Shipped
**Tracking Number:** {tracking_number if tracking_number else "Will be provided soon"}

{notes if notes else "Your package is on its way!"}

Thank you for your order! 🚀
            """.strip()
        elif status == "delivered":
            notification_text = f"""
✅ **Order Delivered!**

**Order ID:** {order_id}
**Status:** Delivered

{notes if notes else "Your order has been successfully delivered!"}

Thank you for choosing us! 🎉
            """.strip()
        else:
            notification_text = f"""
📋 **Order Status Update**

**Order ID:** {order_id}
**Status:** {status.title()}

{notes if notes else "Your order status has been updated."}
            """.strip()
        
        bot.send_message(user_id, notification_text, parse_mode='Markdown')
    except Exception as e:
        print(f"Failed to notify user {user_id}: {e}")

def is_admin(user_id, admin_config):
    """Check if user is admin"""
    return any(admin['user_id'] == user_id for admin in admin_config['admin_users'])

def save_categories_to_file(categories, shop_info):
    """Save categories and shop info to admin_categories.json"""
    data = {
        "shop_info": shop_info,
        "categories": categories
    }
    with open('admin_categories.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def create_admin_management_menu():
    """Create admin management menu"""
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton('📦 Manage Categories', callback_data='admin_categories'),
        InlineKeyboardButton('🏷️ Manage Products', callback_data='admin_products')
    )
    markup.add(
        InlineKeyboardButton('📋 Manage Orders', callback_data='admin_orders'),
        InlineKeyboardButton('📊 View Stats', callback_data='admin_stats')
    )
    markup.add(
        InlineKeyboardButton('🏪 Shop Settings', callback_data='admin_shop'),
        InlineKeyboardButton('💾 Create Backup', callback_data='admin_backup')
    )
    markup.add(
        InlineKeyboardButton('🔄 Reload Data', callback_data='admin_reload'),
        InlineKeyboardButton('🔙 Back to Main', callback_data='admin_back_main')
    )
    return markup

def create_order_management_menu():
    """Create order management menu"""
    orders_data = load_orders()
    orders = orders_data['orders']
    
    markup = InlineKeyboardMarkup(row_width=2)
    
    # Show recent orders (last 10)
    recent_orders = sorted(orders, key=lambda x: x['timestamp'], reverse=True)[:10]
    
    for order in recent_orders:
        status_emoji = {
            'pending': '⏳',
            'processing': '🔄',
            'shipped': '📦',
            'delivered': '✅',
            'cancelled': '❌'
        }.get(order['status'], '❓')
        
        button_text = f"{status_emoji} {order['order_id']} - €{order['total_amount']:.2f}"
        markup.add(InlineKeyboardButton(button_text, callback_data=f'admin_order_{order["order_id"]}'))
    
    markup.add(
        InlineKeyboardButton('📊 All Orders', callback_data='admin_all_orders'),
        InlineKeyboardButton('🔙 Back to Admin', callback_data='admin_back_management')
    )
    return markup

def create_order_detail_menu(order):
    """Create order detail management menu"""
    markup = InlineKeyboardMarkup(row_width=2)
    
    # Status update buttons
    if order['status'] == 'pending':
        markup.add(
            InlineKeyboardButton('🔄 Mark Processing', callback_data=f'admin_status_{order["order_id"]}_processing'),
            InlineKeyboardButton('❌ Cancel Order', callback_data=f'admin_status_{order["order_id"]}_cancelled')
        )
    elif order['status'] == 'processing':
        markup.add(
            InlineKeyboardButton('📦 Mark Shipped', callback_data=f'admin_status_{order["order_id"]}_shipped'),
            InlineKeyboardButton('❌ Cancel Order', callback_data=f'admin_status_{order["order_id"]}_cancelled')
        )
    elif order['status'] == 'shipped':
        markup.add(
            InlineKeyboardButton('✅ Mark Delivered', callback_data=f'admin_status_{order["order_id"]}_delivered')
        )
    
    markup.add(InlineKeyboardButton('🔙 Back to Orders', callback_data='admin_orders'))
    return markup

def create_category_management_menu():
    """Create category management menu"""
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton('➕ Add Category', callback_data='admin_add_category'),
        InlineKeyboardButton('📝 Edit Category', callback_data='admin_edit_category')
    )
    markup.add(
        InlineKeyboardButton('🗑️ Delete Category', callback_data='admin_delete_category'),
        InlineKeyboardButton('📋 List Categories', callback_data='admin_list_categories')
    )
    markup.add(InlineKeyboardButton('🔙 Back to Admin', callback_data='admin_back_management'))
    return markup

def create_product_management_menu():
    """Create product management menu"""
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton('➕ Add Product', callback_data='admin_add_product'),
        InlineKeyboardButton('📝 Edit Product', callback_data='admin_edit_product')
    )
    markup.add(
        InlineKeyboardButton('🗑️ Delete Product', callback_data='admin_delete_product'),
        InlineKeyboardButton('📋 List Products', callback_data='admin_list_products')
    )
    markup.add(InlineKeyboardButton('🔙 Back to Admin', callback_data='admin_back_management'))
    return markup

# Global admin states for multi-step operations
admin_states = {}

def setup_admin_handlers(bot, admin_config, categories, shop_info, user_carts, user_states):
    """Setup all admin-related handlers"""
    
    @bot.message_handler(commands=['test'])
    def test_handler(message):
        bot.reply_to(message, f"Bot is working! Your user ID: {message.from_user.id}")
    
    @bot.message_handler(commands=['admin'])
    def admin_panel(message):
        user_id = message.from_user.id
        print(f"Admin command received from user ID: {user_id}")
        print(f"Admin config: {admin_config}")
        print(f"Is admin: {is_admin(user_id, admin_config)}")
        
        if not is_admin(user_id, admin_config):
            bot.reply_to(message, "❌ Access denied. Admin privileges required.")
            return
        
        admin_text = """
🔧 **Admin Panel**

Welcome to the admin management system!

📋 **Available Management Options:**
• 📦 Manage Categories - Add, edit, delete categories
• 🏷️ Manage Products - Add, edit, delete products  
• 🏪 Shop Settings - Configure shop information
• 📊 View Stats - Bot statistics and user data
• 💾 Create Backup - Backup all data
• 🔄 Reload Data - Reload from files

Use the buttons below to manage your shop!
        """.strip()
        
        bot.reply_to(message, admin_text, reply_markup=create_admin_management_menu(), parse_mode='Markdown')

    @bot.message_handler(commands=['reload'])
    def reload_categories(message):
        user_id = message.from_user.id
        if not is_admin(user_id, admin_config):
            bot.reply_to(message, "❌ Access denied. Admin privileges required.")
            return
        
        try:
            with open('admin_categories.json', 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    raise ValueError("admin_categories.json is empty")
                admin_data = json.loads(content)
                categories.clear()
                categories.extend(admin_data['categories'])
                shop_info.update(admin_data['shop_info'])
            bot.reply_to(message, "✅ Categories reloaded successfully!")
        except Exception as e:
            bot.reply_to(message, f"❌ Error reloading categories: {str(e)}")

    @bot.message_handler(commands=['create_discount'])
    def create_discount_code_command(message):
        user_id = message.from_user.id
        if not is_admin(user_id, admin_config):
            bot.reply_to(message, "❌ Access denied. Admin privileges required.")
            return
        
        admin_states[user_id] = {'action': 'create_discount_code'}
        
        bot.reply_to(message, """🎟️ **Create Discount Code**

Please send the discount code information in this format:

```
DISCOUNT_CODE
DISCOUNT_PERCENT
DESCRIPTION
USAGE_LIMIT
MIN_ORDER_AMOUNT (optional)
```

**Example:**
```
VIP20
20
VIP customer discount
50
100
```

This will create a 20% discount code called "VIP20" with 50 uses and minimum order of €100.""")
    
    @bot.message_handler(commands=['send_discount'])
    def send_discount_code_command(message):
        user_id = message.from_user.id
        if not is_admin(user_id, admin_config):
            bot.reply_to(message, "❌ Access denied. Admin privileges required.")
            return
        
        admin_states[user_id] = {'action': 'send_discount_code'}
        
        bot.reply_to(message, """📤 **Send Discount Code to User**

Please send the user ID and discount code in this format:

```
USER_ID DISCOUNT_CODE
```

**Example:**
```
6251161332 VIP20
```

This will send the discount code "VIP20" to user 6251161332 via DM.""")
    
    @bot.message_handler(commands=['list_discounts'])
    def list_discount_codes_command(message):
        user_id = message.from_user.id
        if not is_admin(user_id, admin_config):
            bot.reply_to(message, "❌ Access denied. Admin privileges required.")
            return
        
        if 'discount_codes' not in shop_info or not shop_info['discount_codes']:
            bot.reply_to(message, "❌ No discount codes found.")
            return
        
        discount_text = "🎟️ **Available Discount Codes**\n\n"
        
        for code, info in shop_info['discount_codes'].items():
            status = "✅ Active" if info.get('active', False) else "❌ Inactive"
            used = info.get('used_count', 0)
            limit = info.get('usage_limit', 0)
            min_order = info.get('min_order_amount', 0)
            
            discount_text += f"""**{code}**
• Discount: {info.get('discount_percent', 0)}%
• Description: {info.get('description', 'N/A')}
• Status: {status}
• Usage: {used}/{limit}
• Min Order: €{min_order}
• Created: {info.get('created_at', 'N/A')}

"""
        
        bot.reply_to(message, discount_text, parse_mode='Markdown')
    
    @bot.message_handler(commands=['set_phrase'])
    def set_phrase_code_command(message):
        user_id = message.from_user.id
        if not is_admin(user_id, admin_config):
            bot.reply_to(message, "❌ Access denied. Admin privileges required.")
            return
        
        admin_states[user_id] = {'action': 'set_phrase_code'}
        
        current_phrase = shop_info.get('phrase_code', 'Not set')
        bot.reply_to(message, f"""🔐 **Set Phrase Code**

Current phrase code: `{current_phrase}`

Please send the new phrase code. This will be required for new users to access the bot.

**Example:**
```
WELCOME2024
```

The phrase code should be easy to remember but secure.""")
    
    @bot.message_handler(commands=['set_user_phrase'])
    def set_user_phrase_code_command(message):
        user_id = message.from_user.id
        if not is_admin(user_id, admin_config):
            bot.reply_to(message, "❌ Access denied. Admin privileges required.")
            return
        
        admin_states[user_id] = {'action': 'set_user_phrase_code'}
        
        bot.reply_to(message, """👤 **Set User Personal Phrase Code**

Please send the user ID and phrase code in this format:

```
USER_ID PHRASE_CODE
```

**Example:**
```
6251161332 USER123
```

This will set a personal phrase code for the specific user.""")
    
    @bot.message_handler(commands=['stats'])
    def show_stats(message):
        user_id = message.from_user.id
        if not is_admin(user_id, admin_config):
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

    @bot.callback_query_handler(func=lambda call: call.data.startswith('admin_') or 
                                call.data.startswith('edit_category_') or 
                                call.data.startswith('delete_category_') or 
                                call.data.startswith('confirm_delete_category_') or
                                call.data.startswith('edit_product_') or
                                call.data.startswith('delete_product_') or
                                call.data.startswith('confirm_delete_product_'))
    def admin_callback_handler(call):
        user_id = call.from_user.id
        if not is_admin(user_id, admin_config):
            bot.answer_callback_query(call.id, "❌ Access denied.")
            return
        
        if call.data == 'admin_categories':
            admin_text = """
📦 **Category Management**

Choose an action to manage categories:
• ➕ Add Category - Create new category
• 📝 Edit Category - Modify existing category
• 🗑️ Delete Category - Remove category
• 📋 List Categories - View all categories
            """.strip()
            safe_edit_message(bot, call.message.chat.id, call.message.message_id, admin_text, 
                                reply_markup=create_category_management_menu(), parse_mode='Markdown')
        
        elif call.data == 'admin_products':
            admin_text = """
🏷️ **Product Management**

Choose an action to manage products:
• ➕ Add Product - Create new product
• 📝 Edit Product - Modify existing product
• 🗑️ Delete Product - Remove product
• 📋 List Products - View all products
            """.strip()
            safe_edit_message(bot, call.message.chat.id, call.message.message_id, admin_text, 
                                reply_markup=create_product_management_menu(), parse_mode='Markdown')
        
        elif call.data == 'admin_shop':
            shop_text = f"""
🏪 **Shop Settings**

Current shop information:
• **Name**: {shop_info.get('name', 'Not set')}
• **Currency**: {shop_info.get('currency', 'Not set')}
• **Payment Methods**: {', '.join(shop_info.get('payment_methods', []))}
• **Countries**: {', '.join(shop_info.get('countries', []))}
• **Promotion**: {shop_info.get('promotion', 'Not set')}

Use /admin_shop_edit to modify shop settings.
            """.strip()
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton('🔙 Back to Admin', callback_data='admin_back_management'))
            safe_edit_message(bot, call.message.chat.id, call.message.message_id, shop_text, 
                                reply_markup=markup, parse_mode='Markdown')
        
        elif call.data == 'admin_list_categories':
            if not categories:
                bot.answer_callback_query(call.id, "📋 No categories found.")
                return
            
            categories_text = "📋 **All Categories:**\n\n"
            for i, category in enumerate(categories, 1):
                products_count = len(category.get('products', []))
                categories_text += f"{i}. **{category['name']}**\n"
                categories_text += f"   - Products: {products_count}\n"
                categories_text += f"   - Active: {'✅' if category.get('active', True) else '❌'}\n\n"
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton('🔙 Back to Categories', callback_data='admin_categories'))
            bot.send_message(call.message.chat.id, categories_text, reply_markup=markup, parse_mode='Markdown')
            bot.answer_callback_query(call.id, "📋 Categories list sent!")
        
        elif call.data == 'admin_list_products':
            if not categories:
                bot.answer_callback_query(call.id, "📋 No products found.")
                return
            
            products_text = "🏷️ **All Products:**\n\n"
            for category in categories:
                products_text += f"**{category['name']}:**\n"
                for product in category.get('products', []):
                    image_status = "🖼️" if product.get('image_url') else "❌"
                    if 'quantities' in product:
                        min_price = min(qty['price'] for qty in product['quantities'])
                        max_price = max(qty['price'] for qty in product['quantities'])
                        products_text += f"  • {product['name']} (€{min_price:.1f}-€{max_price:.1f}) {image_status}\n"
                    else:
                        products_text += f"  • {product['name']} (€{product.get('price', 0):.2f}) {image_status}\n"
                products_text += "\n"
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton('🔙 Back to Products', callback_data='admin_products'))
            bot.send_message(call.message.chat.id, products_text, reply_markup=markup, parse_mode='Markdown')
            bot.answer_callback_query(call.id, "🏷️ Products list sent!")
        
        
        elif call.data == 'admin_edit_category':
            # Show list of categories to edit
            if not categories:
                safe_edit_message(bot, call.message.chat.id, call.message.message_id, 
                                "❌ No categories found to edit.", 
                                reply_markup=create_category_management_menu())
                return
            
            markup = InlineKeyboardMarkup(row_width=1)
            for category in categories:
                category_id = category.get('id', category['name'].lower().replace(' ', '_'))
                markup.add(InlineKeyboardButton(f"📝 {category['name']}", 
                                              callback_data=f"edit_category_{category_id}"))
            markup.add(InlineKeyboardButton('🔙 Back', callback_data='admin_categories'))
            
            safe_edit_message(bot, call.message.chat.id, call.message.message_id, 
                            "📝 **Edit Category**\n\nSelect a category to edit:", 
                            reply_markup=markup, parse_mode='Markdown')
        
        elif call.data == 'admin_delete_category':
            # Show list of categories to delete
            if not categories:
                safe_edit_message(bot, call.message.chat.id, call.message.message_id, 
                                "❌ No categories found to delete.", 
                                reply_markup=create_category_management_menu())
                return
            
            markup = InlineKeyboardMarkup(row_width=1)
            for category in categories:
                category_id = category.get('id', category['name'].lower().replace(' ', '_'))
                markup.add(InlineKeyboardButton(f"🗑️ {category['name']}", 
                                              callback_data=f"delete_category_{category_id}"))
            markup.add(InlineKeyboardButton('🔙 Back', callback_data='admin_categories'))
            
            safe_edit_message(bot, call.message.chat.id, call.message.message_id, 
                            "🗑️ **Delete Category**\n\n⚠️ **Warning**: This will permanently delete the category and all its products!\n\nSelect a category to delete:", 
                            reply_markup=markup, parse_mode='Markdown')
        
        elif call.data == 'admin_add_product':
            if not categories:
                bot.answer_callback_query(call.id, "❌ No categories available. Create a category first.")
                return
            
            # Create category selection menu
            markup = InlineKeyboardMarkup(row_width=1)
            for category in categories:
                markup.add(InlineKeyboardButton(category['name'], callback_data=f"admin_add_product_to_{category['name']}"))
            markup.add(InlineKeyboardButton('🔙 Back to Products', callback_data='admin_products'))
            
            safe_edit_message(bot, call.message.chat.id, call.message.message_id, "🏷️ **Add New Product**\n\nSelect the category for the new product:", 
                                reply_markup=markup, parse_mode='Markdown')
        
        elif call.data == 'admin_edit_product':
            # Show list of products to edit
            if not categories:
                safe_edit_message(bot, call.message.chat.id, call.message.message_id, 
                                "❌ No products found to edit.", 
                                reply_markup=create_product_management_menu())
                return
            
            markup = InlineKeyboardMarkup(row_width=1)
            for category in categories:
                category_id = category.get('id', category['name'].lower().replace(' ', '_'))
                for product in category.get('products', []):
                    product_id = product.get('id', product['name'].lower().replace(' ', '_').replace('★', '').replace('*', ''))
                    button_text = f"📝 {product['name']} ({category['name']})"
                    markup.add(InlineKeyboardButton(button_text, 
                                                  callback_data=f"edit_product_{category_id}|{product_id}"))
            markup.add(InlineKeyboardButton('🔙 Back', callback_data='admin_products'))
            
            safe_edit_message(bot, call.message.chat.id, call.message.message_id, 
                            "📝 **Edit Product**\n\nSelect a product to edit:", 
                            reply_markup=markup, parse_mode='Markdown')
        
        elif call.data == 'admin_delete_product':
            # Show list of products to delete
            if not categories:
                safe_edit_message(bot, call.message.chat.id, call.message.message_id, 
                                "❌ No products found to delete.", 
                                reply_markup=create_product_management_menu())
                return
            
            markup = InlineKeyboardMarkup(row_width=1)
            for category in categories:
                category_id = category.get('id', category['name'].lower().replace(' ', '_'))
                for product in category.get('products', []):
                    product_id = product.get('id', product['name'].lower().replace(' ', '_').replace('★', '').replace('*', ''))
                    button_text = f"🗑️ {product['name']} ({category['name']})"
                    markup.add(InlineKeyboardButton(button_text, 
                                                  callback_data=f"delete_product_{category_id}|{product_id}"))
            markup.add(InlineKeyboardButton('🔙 Back', callback_data='admin_products'))
            
            safe_edit_message(bot, call.message.chat.id, call.message.message_id, 
                            "🗑️ **Delete Product**\n\n⚠️ **Warning**: This will permanently delete the product!\n\nSelect a product to delete:", 
                            reply_markup=markup, parse_mode='Markdown')
        
        elif call.data == 'admin_back_management':
            admin_text = """
🔧 **Admin Panel**

Welcome to the admin management system!

📋 **Available Management Options:**
• 📦 Manage Categories - Add, edit, delete categories
• 🏷️ Manage Products - Add, edit, delete products  
• 🏪 Shop Settings - Configure shop information
• 📊 View Stats - Bot statistics and user data
• 💾 Create Backup - Backup all data
• 🔄 Reload Data - Reload from files

Use the buttons below to manage your shop!
            """.strip()
            safe_edit_message(bot, call.message.chat.id, call.message.message_id, admin_text, 
                                reply_markup=create_admin_management_menu(), parse_mode='Markdown')
        
        elif call.data == 'admin_reload':
            try:
                with open('admin_categories.json', 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        raise ValueError("admin_categories.json is empty")
                    admin_data = json.loads(content)
                    categories.clear()
                    categories.extend(admin_data['categories'])
                    shop_info.update(admin_data['shop_info'])
                bot.answer_callback_query(call.id, "✅ Data reloaded!")
            except Exception as e:
                bot.answer_callback_query(call.id, f"❌ Error: {str(e)}")
        
        elif call.data == 'admin_orders':
            orders_data = load_orders()
            orders = orders_data['orders']
            
            if not orders:
                orders_text = "📋 **Order Management**\n\nNo orders found."
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton('🔙 Back to Admin', callback_data='admin_back_management'))
            else:
                orders_text = f"📋 **Order Management**\n\n**Total Orders:** {len(orders)}\n**Recent Orders:**"
                markup = create_order_management_menu()
            
            safe_edit_message(bot, call.message.chat.id, call.message.message_id, orders_text, reply_markup=markup, parse_mode='Markdown')
            bot.answer_callback_query(call.id, "Order management")
        
        elif call.data.startswith('admin_order_'):
            order_id = call.data.replace('admin_order_', '')
            orders_data = load_orders()
            order = None
            
            for o in orders_data['orders']:
                if o['order_id'] == order_id:
                    order = o
                    break
            
            if order:
                # Format order details
                items_text = ""
                for item in order['items']:
                    items_text += f"• {item['name']} - €{item['price']:.2f}\n"
                
                # Use HTML parsing mode for better reliability
                def escape_html(text):
                    if text is None:
                        return ""
                    text = str(text)
                    text = text.replace('&', '&amp;')
                    text = text.replace('<', '&lt;')
                    text = text.replace('>', '&gt;')
                    return text
                
                safe_address = escape_html(order['delivery_address'][:100])
                safe_items = escape_html(items_text)
                safe_tracking = escape_html(order.get('tracking_number', 'Not provided'))
                safe_notes = escape_html(order.get('notes', 'None'))
                
                order_text = f"""
📋 <b>Order Details</b>

<b>Order ID:</b> {order['order_id']}
<b>User ID:</b> {order['user_id']}
<b>Status:</b> {order['status'].title()}
<b>Date:</b> {datetime.datetime.fromisoformat(order['timestamp']).strftime('%Y-%m-%d %H:%M')}

<b>Items:</b>
{safe_items}

<b>Delivery:</b> {order['delivery_method']} - €{order['delivery_price']:.2f}
<b>Payment:</b> {order['payment_method'].upper()}
<b>Total:</b> €{order['total_amount']:.2f}

<b>Address:</b> {safe_address}{'...' if len(order['delivery_address']) > 100 else ''}

<b>Tracking:</b> {safe_tracking}
<b>Notes:</b> {safe_notes}
                """.strip()
                
                markup = create_order_detail_menu(order)
                safe_edit_message(bot, call.message.chat.id, call.message.message_id, order_text, reply_markup=markup, parse_mode='HTML')
                bot.answer_callback_query(call.id, f"Order {order_id}")
            else:
                bot.answer_callback_query(call.id, "Order not found!")
        
        elif call.data.startswith('admin_status_'):
            # Handle order status updates
            parts = call.data.replace('admin_status_', '').split('_')
            if len(parts) >= 2:
                order_id = parts[0]
                new_status = parts[1]
                
                # Update order status
                order = update_order_status(order_id, new_status)
                
                if order:
                    # Notify user
                    notify_user_order_update(bot, order['user_id'], order_id, new_status)
                    
                    # Update admin message
                    bot.answer_callback_query(call.id, f"Order {order_id} marked as {new_status}")
                    
                    # Refresh order list
                    orders_data = load_orders()
                    orders = orders_data['orders']
                    
                    if not orders:
                        orders_text = "📋 **Order Management**\n\nNo orders found."
                        markup = InlineKeyboardMarkup()
                        markup.add(InlineKeyboardButton('🔙 Back to Admin', callback_data='admin_back_management'))
                    else:
                        orders_text = f"📋 **Order Management**\n\n**Total Orders:** {len(orders)}\n**Recent Orders:**"
                        markup = create_order_management_menu()
                    
                    safe_edit_message(bot, call.message.chat.id, call.message.message_id, orders_text, reply_markup=markup, parse_mode='Markdown')
                else:
                    bot.answer_callback_query(call.id, "Failed to update order!")
        
        elif call.data == 'admin_all_orders':
            orders_data = load_orders()
            orders = orders_data['orders']
            
            if not orders:
                all_orders_text = "📊 **All Orders**\n\nNo orders found."
            else:
                all_orders_text = f"📊 **All Orders** ({len(orders)} total)\n\n"
                
                # Group by status
                status_groups = {}
                for order in orders:
                    status = order['status']
                    if status not in status_groups:
                        status_groups[status] = []
                    status_groups[status].append(order)
                
                for status, status_orders in status_groups.items():
                    status_emoji = {
                        'pending': '⏳',
                        'processing': '🔄',
                        'shipped': '📦',
                        'delivered': '✅',
                        'cancelled': '❌'
                    }.get(status, '❓')
                    
                    all_orders_text += f"{status_emoji} **{status.title()}** ({len(status_orders)})\n"
                    for order in status_orders[:5]:  # Show max 5 per status
                        all_orders_text += f"• {order['order_id']} - €{order['total_amount']:.2f}\n"
                    if len(status_orders) > 5:
                        all_orders_text += f"• ... and {len(status_orders) - 5} more\n"
                    all_orders_text += "\n"
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton('🔙 Back to Orders', callback_data='admin_orders'))
            
            safe_edit_message(bot, call.message.chat.id, call.message.message_id, all_orders_text, reply_markup=markup, parse_mode='Markdown')
            bot.answer_callback_query(call.id, "All orders view")
        
        elif call.data == 'admin_stats':
            orders_data = load_orders()
            
            # Load user statistics
            try:
                with open('users.json', 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        users_data = {"users": [], "statistics": {"total_users": 0}}
                    else:
                        users_data = json.loads(content)
                total_registered_users = users_data['statistics']['total_users']
                # Count unique users (by user_id)
                unique_users = len(set(user['user_id'] for user in users_data['users']))
            except:
                total_registered_users = 0
                unique_users = 0
            
            total_users = len(user_states)
            total_carts = len(user_carts)
            active_carts = sum(1 for cart in user_carts.values() if cart)
            total_categories = len(categories)
            total_products = sum(len(cat['products']) for cat in categories)
            
            # Order statistics
            total_orders = orders_data['statistics']['total_orders']
            total_sales = orders_data['statistics']['total_sales']
            orders_by_status = orders_data['statistics']['orders_by_status']
            
            stats_text = f"""
📊 **Bot Statistics**

👥 **User Statistics:**
• **Active Sessions:** {total_users}
• **Total User Entries:** {total_registered_users}
• **Unique Users:** {unique_users}
• **Active Carts:** {active_carts}

📦 **Product Statistics:**
• **Categories:** {total_categories}
• **Products:** {total_products}

📋 **Order Statistics:**
• **Total Orders:** {total_orders}
• **Total Sales:** €{total_sales:.2f}
• **Pending:** {orders_by_status['pending']}
• **Processing:** {orders_by_status['processing']}
• **Shipped:** {orders_by_status['shipped']}
• **Delivered:** {orders_by_status['delivered']}
• **Cancelled:** {orders_by_status['cancelled']}
            """.strip()
            
            bot.send_message(call.message.chat.id, stats_text, parse_mode='Markdown')
            bot.answer_callback_query(call.id, "📊 Stats sent!")
        
        elif call.data == 'admin_backup':
            try:
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
        
        # Handle edit category selection
        elif call.data.startswith('edit_category_'):
            category_id = call.data.split('_', 2)[2]
            category = next((cat for cat in categories if cat['id'] == category_id), None)
            
            if category:
                admin_states[user_id] = {
                    'action': 'edit_category',
                    'category_id': category_id,
                    'category_name': category['name']
                }
                
                bot.send_message(call.message.chat.id, f"""
📝 **Edit Category: {category['name']}**

Current information:
**Name**: {category['name']}
**Description**: {category.get('description', 'No description')}
**Active**: {'Yes' if category.get('active', True) else 'No'}
**Products**: {len(category.get('products', []))} products

Please send the updated category information in this format:

```
New Category Name
New Category Description
```

Example:
```
UPDATED STIMULANTS
Updated high-quality stimulant products
```

Type 'cancel' to abort editing.
                """.strip())
                bot.answer_callback_query(call.id, f"📝 Editing {category['name']}")
            else:
                bot.answer_callback_query(call.id, "❌ Category not found!")
        
        # Handle delete category selection
        elif call.data.startswith('delete_category_'):
            category_id = call.data.split('_', 2)[2]
            category = next((cat for cat in categories if cat['id'] == category_id), None)
            
            if category:
                # Show confirmation dialog
                markup = InlineKeyboardMarkup(row_width=2)
                markup.add(
                    InlineKeyboardButton('✅ Yes, Delete', callback_data=f'confirm_delete_category_{category_id}'),
                    InlineKeyboardButton('❌ Cancel', callback_data='admin_categories')
                )
                
                safe_edit_message(bot, call.message.chat.id, call.message.message_id, 
                                f"🗑️ **Confirm Delete Category**\n\n"
                                f"**Category**: {category['name']}\n"
                                f"**Description**: {category.get('description', 'No description')}\n"
                                f"**Products**: {len(category.get('products', []))} products\n\n"
                                f"⚠️ **This action cannot be undone!**\n"
                                f"All products in this category will also be deleted.\n\n"
                                f"Are you sure you want to delete this category?",
                                reply_markup=markup, parse_mode='Markdown')
                bot.answer_callback_query(call.id, f"🗑️ Confirm delete {category['name']}")
            else:
                bot.answer_callback_query(call.id, "❌ Category not found!")
        
        # Handle confirmed category deletion
        elif call.data.startswith('confirm_delete_category_'):
            category_id = call.data.split('_', 3)[3]
            
            # Find and remove the category
            category_to_delete = None
            for i, category in enumerate(categories):
                if category['id'] == category_id:
                    category_to_delete = category
                    categories.pop(i)
                    break
            
            if category_to_delete:
                # Save the updated categories
                save_categories_to_file(categories, shop_info)
                
                safe_edit_message(bot, call.message.chat.id, call.message.message_id, 
                                f"✅ **Category Deleted**\n\n"
                                f"Successfully deleted category: **{category_to_delete['name']}**\n"
                                f"Products deleted: {len(category_to_delete.get('products', []))}",
                                reply_markup=create_category_management_menu(), parse_mode='Markdown')
                bot.answer_callback_query(call.id, f"✅ Deleted {category_to_delete['name']}")
            else:
                bot.answer_callback_query(call.id, "❌ Category not found!")
        
        # Handle edit product selection
        elif call.data.startswith('edit_product_'):
            # Parse format: edit_product_category_id|product_id
            data_part = call.data.replace('edit_product_', '')
            if '|' in data_part:
                category_id, product_id = data_part.split('|', 1)
                
                # Find the product
                product = None
                category = None
                for cat in categories:
                    if cat['id'] == category_id:
                        category = cat
                        for prod in cat.get('products', []):
                            if prod['id'] == product_id:
                                product = prod
                                break
                        break
                
                if product and category:
                    admin_states[user_id] = {
                        'action': 'edit_product',
                        'category_id': category_id,
                        'product_id': product_id,
                        'product_name': product['name']
                    }
                    
                    # Send product information with large image if available
                    if product.get('image_url'):
                        try:
                            edit_text = f"""
📝 **Edit Product: {product['name']}**

Current information:
**Name**: {product['name']}
**Description**: {product.get('description', 'No description')}
**Price**: €{product.get('price', 0):.2f}
**Stock**: {product.get('stock', 0)}
**Active**: {'Yes' if product.get('active', True) else 'No'}
**Image**: ✅ Available

Please send the updated product information in this format:

```
New Product Name
New Product Description
New Price
New Stock
```

Example:
```
UPDATED XTC PILLS
Updated high-quality XTC pills
18.50
150
```

Type 'cancel' to abort editing.
                            """.strip()
                            bot.send_photo(call.message.chat.id, product['image_url'], caption=edit_text, parse_mode='Markdown')
                        except Exception as e:
                            print(f"Failed to send product image in admin: {e}")
                            # Fall back to text only
                            edit_text = f"""
📝 **Edit Product: {product['name']}**

Current information:
**Name**: {product['name']}
**Description**: {product.get('description', 'No description')}
**Price**: €{product.get('price', 0):.2f}
**Stock**: {product.get('stock', 0)}
**Active**: {'Yes' if product.get('active', True) else 'No'}
**Image**: ❌ Failed to load

Please send the updated product information in this format:

```
New Product Name
New Product Description
New Price
New Stock
```

Example:
```
UPDATED XTC PILLS
Updated high-quality XTC pills
18.50
150
```

Type 'cancel' to abort editing.
                            """.strip()
                            bot.send_message(call.message.chat.id, edit_text, parse_mode='Markdown')
                    else:
                        edit_text = f"""
📝 **Edit Product: {product['name']}**

Current information:
**Name**: {product['name']}
**Description**: {product.get('description', 'No description')}
**Price**: €{product.get('price', 0):.2f}
**Stock**: {product.get('stock', 0)}
**Active**: {'Yes' if product.get('active', True) else 'No'}
**Image**: ❌ No image available

Please send the updated product information in this format:

```
New Product Name
New Product Description
New Price
New Stock
```

Example:
```
UPDATED XTC PILLS
Updated high-quality XTC pills
18.50
150
```

Type 'cancel' to abort editing.
                        """.strip()
                        bot.send_message(call.message.chat.id, edit_text, parse_mode='Markdown')
                    bot.answer_callback_query(call.id, f"📝 Editing {product['name']}")
                else:
                    bot.answer_callback_query(call.id, "❌ Product not found!")
        
        # Handle delete product selection
        elif call.data.startswith('delete_product_'):
            # Parse format: delete_product_category_id|product_id
            data_part = call.data.replace('delete_product_', '')
            if '|' in data_part:
                category_id, product_id = data_part.split('|', 1)
                
                # Find the product
                product = None
                category = None
                for cat in categories:
                    if cat['id'] == category_id:
                        category = cat
                        for prod in cat.get('products', []):
                            if prod['id'] == product_id:
                                product = prod
                                break
                        break
                
                if product and category:
                    # Show confirmation dialog
                    markup = InlineKeyboardMarkup(row_width=2)
                    markup.add(
                        InlineKeyboardButton('✅ Yes, Delete', callback_data=f'confirm_delete_product_{category_id}|{product_id}'),
                        InlineKeyboardButton('❌ Cancel', callback_data='admin_products')
                    )
                    
                    safe_edit_message(bot, call.message.chat.id, call.message.message_id, 
                                    f"🗑️ **Confirm Delete Product**\n\n"
                                    f"**Product**: {product['name']}\n"
                                    f"**Category**: {category['name']}\n"
                                    f"**Price**: €{product.get('price', 0):.2f}\n"
                                    f"**Stock**: {product.get('stock', 0)}\n\n"
                                    f"⚠️ **This action cannot be undone!**\n\n"
                                    f"Are you sure you want to delete this product?",
                                    reply_markup=markup, parse_mode='Markdown')
                    bot.answer_callback_query(call.id, f"🗑️ Confirm delete {product['name']}")
                else:
                    bot.answer_callback_query(call.id, "❌ Product not found!")
        
        # Handle confirmed product deletion
        elif call.data.startswith('confirm_delete_product_'):
            # Parse format: confirm_delete_product_category_id|product_id
            data_part = call.data.replace('confirm_delete_product_', '')
            if '|' in data_part:
                category_id, product_id = data_part.split('|', 1)
                
                # Find and remove the product
                product_to_delete = None
                category = None
                for cat in categories:
                    if cat['id'] == category_id:
                        category = cat
                        for i, prod in enumerate(cat.get('products', [])):
                            if prod['id'] == product_id:
                                product_to_delete = prod
                                cat['products'].pop(i)
                                break
                        break
                
                if product_to_delete and category:
                    # Save the updated categories
                    save_categories_to_file(categories, shop_info)
                    
                    safe_edit_message(bot, call.message.chat.id, call.message.message_id, 
                                    f"✅ **Product Deleted**\n\n"
                                    f"Successfully deleted product: **{product_to_delete['name']}**\n"
                                    f"From category: **{category['name']}**",
                                    reply_markup=create_product_management_menu(), parse_mode='Markdown')
                    bot.answer_callback_query(call.id, f"✅ Deleted {product_to_delete['name']}")
                else:
                    bot.answer_callback_query(call.id, "❌ Product not found!")
    
    @bot.message_handler(func=lambda message: is_admin(message.from_user.id, admin_config))
    def admin_message_handler(message):
        user_id = message.from_user.id
        text = message.text.strip()
        
        print(f"Admin message received from user {user_id}: {text}")
        print(f"Current admin states: {admin_states}")
        print(f"User state: {admin_states.get(user_id, 'No state')}")
        
        # Handle category creation
        if user_id in admin_states and admin_states[user_id].get('action') == 'add_category':
            try:
                lines = text.split('\n')
                if len(lines) >= 2:
                    name = lines[0].strip()
                    description = lines[1].strip()
                    
                    # Create new category
                    new_category = {
                        "id": name.lower().replace(' ', '_'),
                        "name": name,
                        "description": description,
                        "active": True,
                        "products": []
                    }
                    
                    categories.append(new_category)
                    save_categories_to_file(categories, shop_info)
                    
                    bot.reply_to(message, f"✅ Category '{name}' created successfully!")
                    del admin_states[user_id]
                else:
                    bot.reply_to(message, "❌ Please provide both name and description on separate lines.")
            except Exception as e:
                bot.reply_to(message, f"❌ Error creating category: {str(e)}")
                del admin_states[user_id]
        
        # Handle category editing
        elif user_id in admin_states and admin_states[user_id].get('action') == 'edit_category':
            try:
                if text.lower() == 'cancel':
                    bot.reply_to(message, "❌ Category editing cancelled.")
                    del admin_states[user_id]
                    return
                
                lines = text.split('\n')
                if len(lines) >= 2:
                    new_name = lines[0].strip()
                    new_description = lines[1].strip()
                    category_id = admin_states[user_id]['category_id']
                    old_name = admin_states[user_id]['category_name']
                    
                    # Find and update the category
                    category_found = False
                    for category in categories:
                        if category['id'] == category_id:
                            category['name'] = new_name
                            category['description'] = new_description
                            category_found = True
                            break
                    
                    if category_found:
                        save_categories_to_file(categories, shop_info)
                        bot.reply_to(message, f"✅ Category '{old_name}' updated to '{new_name}' successfully!")
                    else:
                        bot.reply_to(message, "❌ Category not found!")
                    
                    del admin_states[user_id]
                else:
                    bot.reply_to(message, "❌ Please provide both name and description on separate lines.")
            except Exception as e:
                bot.reply_to(message, f"❌ Error editing category: {str(e)}")
                del admin_states[user_id]
        
        # Handle product creation
        elif user_id in admin_states and admin_states[user_id].get('action') == 'add_product':
            try:
                lines = text.split('\n')
                if len(lines) >= 3:
                    name = lines[0].strip()
                    description = lines[1].strip()
                    price = float(lines[2].strip())
                    
                    category_name = admin_states[user_id].get('category')
                    category = next((cat for cat in categories if cat['name'] == category_name), None)
                    
                    if category:
                        new_product = {
                            "id": name.lower().replace(' ', '_').replace('★', '').replace('*', ''),
                            "name": name,
                            "price": price,
                            "description": description,
                            "stock": 100,
                            "active": True
                        }
                        
                        category['products'].append(new_product)
                        save_categories_to_file(categories, shop_info)
                        
                        bot.reply_to(message, f"✅ Product '{name}' added to category '{category_name}' successfully!")
                        del admin_states[user_id]
                    else:
                        bot.reply_to(message, f"❌ Category '{category_name}' not found.")
                        del admin_states[user_id]
                else:
                    bot.reply_to(message, "❌ Please provide name, description, and price on separate lines.")
            except ValueError:
                bot.reply_to(message, "❌ Price must be a valid number.")
            except Exception as e:
                bot.reply_to(message, f"❌ Error creating product: {str(e)}")
                del admin_states[user_id]
        
        # Handle product editing
        elif user_id in admin_states and admin_states[user_id].get('action') == 'edit_product':
            try:
                if text.lower() == 'cancel':
                    bot.reply_to(message, "❌ Product editing cancelled.")
                    del admin_states[user_id]
                    return
                
                lines = text.split('\n')
                if len(lines) >= 4:
                    new_name = lines[0].strip()
                    new_description = lines[1].strip()
                    new_price = float(lines[2].strip())
                    new_stock = int(lines[3].strip())
                    
                    category_id = admin_states[user_id]['category_id']
                    product_id = admin_states[user_id]['product_id']
                    old_name = admin_states[user_id]['product_name']
                    
                    # Find and update the product
                    product_found = False
                    for category in categories:
                        if category['id'] == category_id:
                            for product in category.get('products', []):
                                if product['id'] == product_id:
                                    product['name'] = new_name
                                    product['description'] = new_description
                                    product['price'] = new_price
                                    product['stock'] = new_stock
                                    product_found = True
                                    break
                            break
                    
                    if product_found:
                        save_categories_to_file(categories, shop_info)
                        bot.reply_to(message, f"✅ Product '{old_name}' updated to '{new_name}' successfully!")
                    else:
                        bot.reply_to(message, "❌ Product not found!")
                    
                    del admin_states[user_id]
                else:
                    bot.reply_to(message, "❌ Please provide name, description, price, and stock on separate lines.")
            except ValueError:
                bot.reply_to(message, "❌ Price and stock must be valid numbers.")
            except Exception as e:
                bot.reply_to(message, f"❌ Error editing product: {str(e)}")
                del admin_states[user_id]
        
        # Handle discount code creation
        elif user_id in admin_states and admin_states[user_id].get('action') == 'create_discount_code':
            try:
                lines = text.split('\n')
                if len(lines) >= 4:
                    code = lines[0].strip().upper()
                    discount_percent = float(lines[1].strip())
                    description = lines[2].strip()
                    usage_limit = int(lines[3].strip())
                    min_order_amount = float(lines[4].strip()) if len(lines) > 4 else 0
                    
                    # Initialize discount codes if not exists
                    if 'discount_codes' not in shop_info:
                        shop_info['discount_codes'] = {}
                    
                    # Create new discount code
                    shop_info['discount_codes'][code] = {
                        'discount_percent': discount_percent,
                        'description': description,
                        'active': True,
                        'usage_limit': usage_limit,
                        'used_count': 0,
                        'min_order_amount': min_order_amount,
                        'created_by': user_id,
                        'created_at': datetime.datetime.now().isoformat()
                    }
                    
                    save_categories_to_file(categories, shop_info)
                    
                    bot.reply_to(message, f"""✅ **Discount Code Created Successfully!**

**Code:** {code}
**Discount:** {discount_percent}% off
**Description:** {description}
**Usage Limit:** {usage_limit}
**Min Order:** €{min_order_amount}

You can now send this code to users via DM.""")
                    del admin_states[user_id]
                else:
                    bot.reply_to(message, """❌ Please provide all required information:

```
DISCOUNT_CODE
DISCOUNT_PERCENT
DESCRIPTION
USAGE_LIMIT
MIN_ORDER_AMOUNT (optional)
```

Example:
```
VIP20
20
VIP customer discount
50
100
```""")
            except ValueError:
                bot.reply_to(message, "❌ Discount percent, usage limit, and min order amount must be valid numbers.")
            except Exception as e:
                bot.reply_to(message, f"❌ Error creating discount code: {str(e)}")
                del admin_states[user_id]
        
        # Handle sending discount code to user
        elif user_id in admin_states and admin_states[user_id].get('action') == 'send_discount_code':
            try:
                parts = text.split(' ', 1)
                if len(parts) >= 2:
                    target_user_id = int(parts[0])
                    discount_code = parts[1].strip().upper()
                    
                    # Check if discount code exists
                    if 'discount_codes' not in shop_info or discount_code not in shop_info['discount_codes']:
                        bot.reply_to(message, f"❌ Discount code '{discount_code}' does not exist!")
                        del admin_states[user_id]
                        return
                    
                    # Send discount code to user
                    discount_info = shop_info['discount_codes'][discount_code]
                    message_text = f"""🎟️ **Special Discount Code for You!**

**Code:** `{discount_code}`
**Discount:** {discount_info['discount_percent']}% off
**Description:** {discount_info['description']}

Use this code during checkout to get your discount!

*This code was sent personally by our admin team.*"""
                    
                    try:
                        bot.send_message(target_user_id, message_text, parse_mode='Markdown')
                        bot.reply_to(message, f"✅ Discount code '{discount_code}' sent successfully to user {target_user_id}!")
                    except Exception as send_error:
                        bot.reply_to(message, f"❌ Failed to send message to user {target_user_id}: {str(send_error)}")
                    
                    del admin_states[user_id]
                else:
                    bot.reply_to(message, """❌ Please provide user ID and discount code:

```
USER_ID DISCOUNT_CODE
```

Example:
```
6251161332 VIP20
```""")
            except ValueError:
                bot.reply_to(message, "❌ User ID must be a valid number.")
            except Exception as e:
                bot.reply_to(message, f"❌ Error sending discount code: {str(e)}")
                del admin_states[user_id]
        
        # Handle setting phrase code
        elif user_id in admin_states and admin_states[user_id].get('action') == 'set_phrase_code':
            try:
                new_phrase = text.strip().upper()
                
                if len(new_phrase) < 3:
                    bot.reply_to(message, "❌ Phrase code must be at least 3 characters long.")
                    del admin_states[user_id]
                    return
                
                # Update phrase code in shop info
                shop_info['phrase_code'] = new_phrase
                save_categories_to_file(categories, shop_info)
                
                bot.reply_to(message, f"""✅ **Phrase Code Updated Successfully!**

**New phrase code:** `{new_phrase}`

This phrase code will now be required for new users to access the bot.

**Note:** Existing verified users will not be affected.""")
                del admin_states[user_id]
            except Exception as e:
                bot.reply_to(message, f"❌ Error setting phrase code: {str(e)}")
                del admin_states[user_id]
        
        # Handle setting user personal phrase code
        elif user_id in admin_states and admin_states[user_id].get('action') == 'set_user_phrase_code':
            try:
                parts = text.split(' ', 1)
                if len(parts) >= 2:
                    target_user_id = int(parts[0])
                    personal_phrase = parts[1].strip().upper()
                    
                    if len(personal_phrase) < 3:
                        bot.reply_to(message, "❌ Phrase code must be at least 3 characters long.")
                        del admin_states[user_id]
                        return
                    
                    # Load users data
                    users_data = load_users()
                    user_found = False
                    
                    for user in users_data['users']:
                        if user['user_id'] == target_user_id:
                            user['personal_phrase_code'] = personal_phrase
                            user_found = True
                            break
                    
                    if user_found:
                        save_users(users_data)
                        bot.reply_to(message, f"""✅ **User Personal Phrase Code Set Successfully!**

**User ID:** {target_user_id}
**Personal Phrase Code:** `{personal_phrase}`

This user will now see their personal phrase code when they use /start.""")
                    else:
                        bot.reply_to(message, f"❌ User with ID {target_user_id} not found.")
                    
                    del admin_states[user_id]
                else:
                    bot.reply_to(message, """❌ Please provide user ID and phrase code:

```
USER_ID PHRASE_CODE
```

Example:
```
6251161332 USER123
```""")
            except ValueError:
                bot.reply_to(message, "❌ User ID must be a valid number.")
            except Exception as e:
                bot.reply_to(message, f"❌ Error setting user phrase code: {str(e)}")
                del admin_states[user_id]
    
    # Handle category selection for product addition
    @bot.callback_query_handler(func=lambda call: call.data.startswith('admin_add_product_to_'))
    def handle_category_selection(call):
        user_id = call.from_user.id
        if not is_admin(user_id, admin_config):
            bot.answer_callback_query(call.id, "❌ Access denied.")
            return
        
        category_name = call.data.replace('admin_add_product_to_', '')
        admin_states[user_id] = {'action': 'add_product', 'category': category_name}
        print(f"Category selection: User {user_id} selected category '{category_name}'")
        print(f"Admin states: {admin_states}")
        
        bot.send_message(call.message.chat.id, f"""
🏷️ **Add Product to {category_name}**

Please send the product information in this format:

```
Product Name
Product Description
Price
```

Example:
```
XTC ★ RED BULL ★ 250mg MDMA
High-quality XTC pills with red bull design
15.50
```

The product will be added to the {category_name} category.
        """.strip())
        
        bot.answer_callback_query(call.id, f"📝 Please send product details for {category_name}!")
    
    # Handle category addition
    @bot.callback_query_handler(func=lambda call: call.data == 'admin_add_category')
    def handle_add_category(call):
        user_id = call.from_user.id
        print(f"Add category callback received from user {user_id}")
        if not is_admin(user_id, admin_config):
            print(f"User {user_id} is not admin")
            bot.answer_callback_query(call.id, "❌ Access denied.")
            return
        
        print(f"Setting admin state for user {user_id}: add_category")
        admin_states[user_id] = {'action': 'add_category'}
        
        bot.send_message(call.message.chat.id, """
➕ **Add New Category**

Please send the category information in this format:

```
Category Name
Category Description
```

Example:
```
STIMULANTS
High-quality stimulant products
```

The category will be created with no products initially.
        """.strip())
        bot.answer_callback_query(call.id, "📝 Please send category details!")
>>>>>>> 5f2a61601dd6311cc5b35154e8405aed0090abf1
