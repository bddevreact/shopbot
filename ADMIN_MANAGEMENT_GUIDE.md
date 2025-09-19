# Admin Management System Guide

## Overview
The MrZoidbergBot now includes a comprehensive admin management system that allows admins to add, edit, and delete categories and products directly through the bot interface.

## Getting Started

### 1. Set Up Admin User
First, add your user ID to `admin_config.json`:

```json
{
  "admin_users": [
    {
      "user_id": YOUR_USER_ID_HERE,
      "username": "admin",
      "role": "super_admin",
      "permissions": ["manage_categories", "manage_products", "view_orders", "manage_users", "edit_shop_info"]
    }
  ]
}
```

**To get your user ID:**
- Message @userinfobot on Telegram
- Copy the user ID (numbers only)

### 2. Access Admin Panel
Send `/admin` command to the bot to access the admin management system.

## Admin Management Features

### 📦 Category Management

#### ➕ Add New Category
1. Click "📦 Manage Categories"
2. Click "➕ Add Category"
3. Send category details in this format:
   ```
   Category Name
   Category Description
   ```
   
   **Example:**
   ```
   STIMULANTS
   High-quality stimulant products
   ```

#### 📋 List Categories
- Click "📋 List Categories" to view all categories
- Shows category name, product count, and active status

#### 📝 Edit Category
- Click "📝 Edit Category" (coming soon)
- Will allow modification of category name and description

#### 🗑️ Delete Category
- Click "🗑️ Delete Category" (coming soon)
- Will allow removal of categories and their products

### 🏷️ Product Management

#### ➕ Add New Product
1. Click "🏷️ Manage Products"
2. Click "➕ Add Product"
3. Select the category for the new product
4. Send product details in this format:
   ```
   Product Name
   Product Description
   Price
   ```
   
   **Example:**
   ```
   XTC ★ RED BULL ★ 250mg MDMA
   High-quality XTC pills with red bull design
   15.50
   ```

#### 📋 List Products
- Click "📋 List Products" to view all products
- Shows products grouped by category with price ranges

#### 📝 Edit Product
- Click "📝 Edit Product" (coming soon)
- Will allow modification of product details

#### 🗑️ Delete Product
- Click "🗑️ Delete Product" (coming soon)
- Will allow removal of products

### 🏪 Shop Settings
- Click "🏪 Shop Settings" to view current shop configuration
- Shows shop name, currency, payment methods, countries, and promotion

### 📊 Statistics
- Click "📊 View Stats" to see bot performance
- Shows user count, cart activity, categories, and products

### 💾 Backup & Reload
- **Create Backup**: Creates timestamped backup of all data
- **Reload Data**: Reloads categories and products from files

## Admin Commands

### Available Commands:
- `/admin` - Open admin management panel
- `/reload` - Reload data from files
- `/stats` - Show bot statistics

## Data Management

### Automatic Saving
- All changes are automatically saved to `admin_categories.json`
- No need to restart the bot after making changes
- Changes take effect immediately

### File Structure
```
admin_categories.json
├── shop_info
│   ├── name
│   ├── currency
│   ├── payment_methods
│   ├── countries
│   ├── promotion
│   └── contact
└── categories
    ├── id
    ├── name
    ├── description
    ├── active
    └── products
        ├── id
        ├── name
        ├── price (or quantities)
        ├── description
        ├── stock
        └── active
```

## Best Practices

### Category Management
1. **Use clear, descriptive names** (e.g., "MDMA", "STIMULANTS")
2. **Keep descriptions concise** but informative
3. **Organize logically** by product type or effects

### Product Management
1. **Use consistent naming** with symbols (★) for visual appeal
2. **Include relevant details** in descriptions
3. **Set appropriate prices** based on market rates
4. **Use detailed products** with quantities for premium items

### Security
1. **Keep admin user list minimal**
2. **Regularly backup data**
3. **Monitor admin activities**
4. **Use strong user IDs**

## Troubleshooting

### Common Issues

**"Access denied" error:**
- Check if your user ID is in admin_config.json
- Verify user ID is correct (numbers only)
- Restart bot after adding admin user

**Changes not saving:**
- Check file permissions
- Ensure admin_categories.json is writable
- Use /reload command to refresh data

**Product not appearing:**
- Check if category is active
- Verify product is active
- Use /reload command

### Error Messages
- **"No categories available"**: Create a category first
- **"Category not found"**: Check category name spelling
- **"Price must be valid number"**: Use decimal format (e.g., 15.50)

## Advanced Features

### Product Types
- **Simple Products**: Single price, basic format
- **Detailed Products**: Multiple quantities with different prices
- **Physical Products**: Include shipping information and images

### Quantity Management
For products with multiple quantities:
```json
"quantities": [
  {"amount": "3g", "price": 30.0},
  {"amount": "5g", "price": 45.0},
  {"amount": "10g", "price": 80.0}
]
```

## Support

For technical support or questions about the admin system:
1. Check this guide first
2. Verify your admin permissions
3. Check bot logs for errors
4. Contact the bot developer

## Future Updates

Planned features:
- ✅ Add categories and products
- ✅ List categories and products
- ✅ View statistics and shop settings
- ✅ Create backups
- 🔄 Edit categories and products
- 🔄 Delete categories and products
- 🔄 Advanced product management
- 🔄 Bulk operations
- 🔄 User management
- 🔄 Order management

---

**Note**: This admin system is designed for easy management of your shop without needing to edit JSON files manually. All changes are made through the bot interface and automatically saved.
