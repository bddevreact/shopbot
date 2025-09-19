#!/usr/bin/env python3
"""
Simple script to set admin user ID in config.env and admin_config.json
Usage: python set_admin.py <user_id>
"""

import sys
import json
import os
from dotenv import load_dotenv, set_key

def set_admin_user_id(user_id):
    """Set admin user ID in both config.env and admin_config.json"""
    
    try:
        # Convert to integer to validate
        admin_id = int(user_id)
        
        # Update config.env
        env_file = 'config.env'
        set_key(env_file, 'ADMIN_USER_ID', str(admin_id))
        print(f"✅ Updated ADMIN_USER_ID in {env_file}")
        
        # Update admin_config.json
        config_file = 'admin_config.json'
        with open(config_file, 'r') as f:
            admin_config = json.load(f)
        
        # Check if user already exists
        existing_admin = next((admin for admin in admin_config['admin_users'] if admin['user_id'] == admin_id), None)
        
        if existing_admin:
            print(f"✅ Admin user ID {admin_id} already exists in {config_file}")
        else:
            # Add new admin user
            admin_config['admin_users'].append({
                "user_id": admin_id,
                "username": "admin",
                "role": "super_admin",
                "permissions": ["manage_categories", "manage_products", "view_orders", "manage_users", "edit_shop_info"]
            })
            
            with open(config_file, 'w') as f:
                json.dump(admin_config, f, indent=2)
            print(f"✅ Added admin user ID {admin_id} to {config_file}")
        
        print(f"\n🎉 Admin user ID {admin_id} is now configured!")
        print("Restart the bot to apply changes.")
        
    except ValueError:
        print("❌ Error: User ID must be a number")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False
    
    return True

def main():
    if len(sys.argv) != 2:
        print("Usage: python set_admin.py <user_id>")
        print("Example: python set_admin.py 123456789")
        sys.exit(1)
    
    user_id = sys.argv[1]
    if set_admin_user_id(user_id):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
