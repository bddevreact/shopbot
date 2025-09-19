# MrZoidbergBot Admin Guide

## Overview
This bot includes a comprehensive admin system for managing categories, products, and shop settings through JSON configuration files.

## Admin Files

### 1. `admin_categories.json`
Main configuration file for managing shop content:

```json
{
  "shop_info": {
    "name": "MrZoidberg Shop",
    "currency": "EUR",
    "payment_methods": ["BTC", "XMR"],
    "countries": ["GER", "AUS", "USA"],
    "promotion": "20% EXTRA on your order promotion now LIVE!",
    "contact": {
      "telegram_bot": "@MrZoidbergBot",
      "updates_channel": "@NWWupdates",
      "ceo": "@MrZoidberg"
    }
  },
  "categories": [
    {
      "id": "mdma",
      "name": "MDMA",
      "description": "High-quality MDMA products",
      "active": true,
      "products": [
        {
          "id": "mdma_crystal",
          "name": "MDMA Crystal",
          "price": 25.99,
          "description": "High-quality crystal form",
          "stock": 100,
          "active": true
        }
      ]
    }
  ]
}
```

### 2. `admin_config.json`
Admin user management:

```json
{
  "admin_users": [
    {
      "user_id": 123456789,
      "username": "admin",
      "role": "super_admin",
      "permissions": ["manage_categories", "manage_products", "view_orders", "manage_users"]
    }
  ],
  "bot_settings": {
    "auto_reload_categories": true,
    "backup_enabled": true,
    "log_level": "INFO"
  }
}
```

## Admin Commands

### Available Commands:
- `/admin` - Show admin panel with interactive buttons
- `/reload` - Reload categories from admin_categories.json
- `/stats` - Show bot statistics (users, carts, products, etc.)

### Admin Panel Features:
- 🔄 **Reload Categories** - Reload shop content without restarting bot
- 📊 **View Stats** - See user statistics and bot performance
- 👥 **View Users** - See user activity and cart information
- 💾 **Create Backup** - Create timestamped backup of all data

## How to Add Admin Users

1. **Get User ID:**
   - Ask user to message @userinfobot on Telegram
   - Copy their user ID (numbers only)

2. **Add to admin_config.json:**
   ```json
   {
     "admin_users": [
       {
         "user_id": YOUR_USER_ID_HERE,
         "username": "your_username",
         "role": "admin",
         "permissions": ["manage_categories", "manage_products", "view_orders"]
       }
     ]
   }
   ```

3. **Restart bot or use /reload command**

## Managing Categories and Products

### Adding New Category:
1. Edit `admin_categories.json`
2. Add new category object in the `categories` array
3. Use `/reload` command or restart bot

### Adding New Product:
1. Find the category in `admin_categories.json`
2. Add new product object in the category's `products` array
3. Use `/reload` command or restart bot

### Updating Prices:
1. Edit the `price` field in `admin_categories.json`
2. Use `/reload` command to apply changes

### Managing Stock:
1. Edit the `stock` field for each product
2. Set `active: false` to hide products temporarily
3. Use `/reload` command to apply changes

## Shop Information Management

### Updating Shop Details:
Edit the `shop_info` section in `admin_categories.json`:

- `name` - Shop name (appears in welcome message)
- `currency` - Currency symbol (EUR, USD, etc.)
- `payment_methods` - Array of accepted payment methods
- `countries` - Array of shipping countries
- `promotion` - Current promotion text
- `contact` - Contact information

## Security Features

### Admin Access Control:
- Only users listed in `admin_config.json` can access admin features
- All admin commands check user permissions
- Access denied messages for unauthorized users

### Data Protection:
- Automatic backup creation with timestamps
- JSON validation for configuration files
- Error handling for malformed configurations

## Backup and Recovery

### Automatic Backups:
- Created when using admin backup feature
- Includes all user data, categories, and shop info
- Timestamped filenames: `backup_YYYYMMDD_HHMMSS.json`

### Manual Backup:
```bash
cp admin_categories.json admin_categories_backup.json
cp admin_config.json admin_config_backup.json
```

## Troubleshooting

### Common Issues:

1. **"Access denied" error:**
   - Check if user ID is in admin_config.json
   - Verify user ID is correct (numbers only)

2. **Categories not updating:**
   - Check JSON syntax in admin_categories.json
   - Use `/reload` command after making changes
   - Restart bot if reload doesn't work

3. **Bot not starting:**
   - Check JSON file syntax
   - Verify all required fields are present
   - Check file permissions

### JSON Validation:
Use online JSON validators to check syntax before saving files.

## Best Practices

1. **Always backup before major changes**
2. **Test changes in a development environment first**
3. **Keep admin user list minimal and secure**
4. **Regularly update product stock levels**
5. **Monitor bot statistics for performance**

## File Structure
```
MrZoidbergBot/
├── bot.py                    # Main bot code
├── admin_categories.json     # Shop content configuration
├── admin_config.json         # Admin user management
├── config.env               # Bot token and sensitive data
├── products.json            # Legacy products file (can be removed)
├── requirements.txt         # Python dependencies
├── .gitignore              # Git ignore rules
├── SETUP.md                # Setup instructions
└── ADMIN_GUIDE.md          # This file
```

## Support
For technical support or questions about the admin system, contact the bot developer.
