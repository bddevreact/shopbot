# MrZoidbergBot File Structure

## Main Files

### `bot.py` - Main Bot File
- **Purpose**: Main entry point that runs everything
- **What it does**: 
  - Loads configuration files
  - Sets up the bot
  - Imports and runs both user and admin functionality
  - Starts the bot

### `user_bot.py` - User Features
- **Purpose**: All regular user functionality
- **Contains**:
  - Product browsing and categories
  - Shopping cart management
  - Checkout and payment
  - PGP verification
  - User interface and menus

### `admin_bot.py` - Admin Features
- **Purpose**: All admin functionality
- **Contains**:
  - Admin commands (/admin, /reload, /stats)
  - Admin panel with buttons
  - User statistics
  - Backup creation
  - Category management

## Configuration Files

### `admin_categories.json` - Shop Content
- **Purpose**: Manage all shop content
- **Contains**:
  - Shop information (name, currency, etc.)
  - All categories and products
  - Prices and stock levels
  - Product descriptions

### `admin_config.json` - Admin Settings
- **Purpose**: Manage admin users and bot settings
- **Contains**:
  - Admin user list
  - User permissions
  - Bot configuration

### `config.env` - Sensitive Data
- **Purpose**: Store sensitive information
- **Contains**:
  - Bot token
  - Crypto wallet addresses
  - PGP keys and passphrases

## How It Works

1. **Run `bot.py`** - This is the only file you need to run
2. **bot.py loads**:
   - Configuration files (admin_categories.json, admin_config.json, config.env)
   - User bot functionality (user_bot.py)
   - Admin bot functionality (admin_bot.py)
3. **Everything works together** - Users get normal features, admins get admin features

## File Separation Benefits

✅ **Clean Organization** - User and admin code are separate
✅ **Easy Maintenance** - Edit user features without touching admin code
✅ **Modular Design** - Add new features easily
✅ **Single Entry Point** - Just run `bot.py` and everything works
✅ **Easy Updates** - Update specific functionality without affecting others

## Quick Start

```bash
# Just run this one command:
python bot.py
```

That's it! The bot will:
- Load all configurations
- Set up user features
- Set up admin features
- Start running

## File Overview

```
MrZoidbergBot/
├── bot.py                    # 🚀 MAIN FILE - Run this!
├── user_bot.py              # 👥 User features
├── admin_bot.py             # 🔧 Admin features
├── admin_categories.json    # 📦 Shop content
├── admin_config.json        # ⚙️ Admin settings
├── config.env              # 🔐 Sensitive data
├── requirements.txt        # 📋 Dependencies
├── .gitignore             # 🚫 Git ignore rules
├── SETUP.md               # 📖 Setup guide
├── ADMIN_GUIDE.md         # 📚 Admin guide
└── FILE_STRUCTURE.md      # 📁 This file
```

## Backup Files

- `bot_old.py` - Backup of original bot.py
- `bot_new.py` - Temporary file (can be deleted)

## Summary

**For Users**: Just run `python bot.py` - everything works automatically!

**For Admins**: Edit JSON files and use `/reload` command to update shop content.

**For Developers**: User and admin code are cleanly separated but work together seamlessly.
