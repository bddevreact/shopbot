#!/usr/bin/env python3
"""
Script to check which features still need language conversion
"""

import re

def check_language_conversion():
    """Check which features still need language conversion"""
    
    # Read user_bot.py
    with open('user_bot.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all callback handlers
    callback_pattern = r"elif call\.data == '([^']+)':"
    callbacks = re.findall(callback_pattern, content)
    
    # Find all message handlers
    message_pattern = r"@bot\.message_handler\([^)]+\)\s*\n\s*def ([^(]+)"
    messages = re.findall(message_pattern, content)
    
    # Find all hardcoded strings that should be translated
    hardcoded_patterns = [
        r'"[^"]*[A-Za-z]{3,}[^"]*"',  # Strings with 3+ letters
        r"'[^']*[A-Za-z]{3,}[^']*'",  # Single quoted strings
    ]
    
    print("=== CALLBACK HANDLERS ===")
    for callback in callbacks:
        print(f"- {callback}")
    
    print("\n=== MESSAGE HANDLERS ===")
    for message in messages:
        print(f"- {message}")
    
    print("\n=== FEATURES THAT NEED LANGUAGE CONVERSION ===")
    
    # Check specific features
    features_to_check = [
        'payment_btc', 'payment_xmr', 'payment_sent', 'order_confirm',
        'order_cancel', 'order_paid', 'discount_code', 'select_payment',
        'enter_address', 'select_delivery', 'tracking_info', 'delete_order',
        'user_settings', 'security_settings', 'user_analytics', 'user_preferences',
        'search_products', 'search_by_category', 'search_trending', 'search_new',
        'recommendations_trending', 'recommendations_cart', 'recommendations_similar',
        'wishlist', 'order_history', 'advanced_search'
    ]
    
    for feature in features_to_check:
        if feature in callbacks:
            print(f"✅ {feature} - Needs conversion")
        else:
            print(f"❌ {feature} - Not found")
    
    print("\n=== HARDCODED STRINGS TO CONVERT ===")
    
    # Find hardcoded strings in callback handlers
    callback_sections = re.findall(r"elif call\.data == '[^']+':.*?(?=elif call\.data|$)", content, re.DOTALL)
    
    for section in callback_sections[:5]:  # Show first 5 examples
        strings = re.findall(r'"[^"]*[A-Za-z]{3,}[^"]*"', section)
        if strings:
            print(f"Section contains: {strings[:2]}...")  # Show first 2 strings

if __name__ == "__main__":
    check_language_conversion()
