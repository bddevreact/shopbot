import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import random
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import os

class RecommendationEngine:
    """Advanced AI-powered product recommendation system"""
    
    def __init__(self, bot, categories, shop_info):
        self.bot = bot
        self.categories = categories
        self.shop_info = shop_info
        
        # User behavior tracking
        self.user_behavior = self.load_user_behavior()
        self.user_preferences = self.load_user_preferences()
        self.product_analytics = self.load_product_analytics()
        
        # Recommendation algorithms
        self.recommendation_weights = {
            'view_history': 0.3,
            'purchase_history': 0.4,
            'category_preference': 0.2,
            'price_preference': 0.1
        }
        
        # Trending products tracking
        self.trending_products = self.calculate_trending_products()
        
        # Similar products mapping
        self.similar_products = self.build_similarity_matrix()
    
    def load_user_behavior(self) -> Dict[str, Any]:
        """Load user behavior data"""
        try:
            with open('data/user_behavior.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                'view_history': {},
                'purchase_history': {},
                'search_history': {},
                'cart_abandonment': {},
                'session_data': {}
            }
    
    def save_user_behavior(self):
        """Save user behavior data"""
        os.makedirs('data', exist_ok=True)
        with open('data/user_behavior.json', 'w', encoding='utf-8') as f:
            json.dump(self.user_behavior, f, indent=2, ensure_ascii=False)
    
    def load_user_preferences(self) -> Dict[str, Any]:
        """Load user preferences"""
        try:
            with open('data/user_preferences.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_user_preferences(self):
        """Save user preferences"""
        os.makedirs('data', exist_ok=True)
        with open('data/user_preferences.json', 'w', encoding='utf-8') as f:
            json.dump(self.user_preferences, f, indent=2, ensure_ascii=False)
    
    def load_product_analytics(self) -> Dict[str, Any]:
        """Load product analytics data"""
        try:
            with open('data/product_analytics.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                'view_counts': {},
                'purchase_counts': {},
                'conversion_rates': {},
                'popularity_scores': {}
            }
    
    def save_product_analytics(self):
        """Save product analytics data"""
        os.makedirs('data', exist_ok=True)
        with open('data/product_analytics.json', 'w', encoding='utf-8') as f:
            json.dump(self.product_analytics, f, indent=2, ensure_ascii=False)
    
    def track_user_view(self, user_id: int, product_name: str, category: str):
        """Track when user views a product"""
        if user_id not in self.user_behavior['view_history']:
            self.user_behavior['view_history'][user_id] = []
        
        view_entry = {
            'product': product_name,
            'category': category,
            'timestamp': datetime.now().isoformat()
        }
        
        self.user_behavior['view_history'][user_id].append(view_entry)
        
        # Keep only last 50 views per user
        if len(self.user_behavior['view_history'][user_id]) > 50:
            self.user_behavior['view_history'][user_id] = self.user_behavior['view_history'][user_id][-50:]
        
        # Update product analytics
        if product_name not in self.product_analytics['view_counts']:
            self.product_analytics['view_counts'][product_name] = 0
        self.product_analytics['view_counts'][product_name] += 1
        
        self.save_user_behavior()
        self.save_product_analytics()
    
    def track_user_purchase(self, user_id: int, product_name: str, category: str, price: float):
        """Track when user purchases a product"""
        if user_id not in self.user_behavior['purchase_history']:
            self.user_behavior['purchase_history'][user_id] = []
        
        purchase_entry = {
            'product': product_name,
            'category': category,
            'price': price,
            'timestamp': datetime.now().isoformat()
        }
        
        self.user_behavior['purchase_history'][user_id].append(purchase_entry)
        
        # Update product analytics
        if product_name not in self.product_analytics['purchase_counts']:
            self.product_analytics['purchase_counts'][product_name] = 0
        self.product_analytics['purchase_counts'][product_name] += 1
        
        # Update conversion rate
        views = self.product_analytics['view_counts'].get(product_name, 0)
        purchases = self.product_analytics['purchase_counts'].get(product_name, 0)
        if views > 0:
            self.product_analytics['conversion_rates'][product_name] = purchases / views
        
        self.save_user_behavior()
        self.save_product_analytics()
    
    def track_cart_abandonment(self, user_id: int, cart_items: List[Dict]):
        """Track cart abandonment for retargeting"""
        if user_id not in self.user_behavior['cart_abandonment']:
            self.user_behavior['cart_abandonment'][user_id] = []
        
        abandonment_entry = {
            'items': cart_items,
            'timestamp': datetime.now().isoformat()
        }
        
        self.user_behavior['cart_abandonment'][user_id].append(abandonment_entry)
        self.save_user_behavior()
    
    def get_user_recommendations(self, user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """Get personalized product recommendations for user"""
        recommendations = []
        
        # Get user's view and purchase history
        view_history = self.user_behavior['view_history'].get(user_id, [])
        purchase_history = self.user_behavior['purchase_history'].get(user_id, [])
        
        # Calculate user preferences
        user_prefs = self.calculate_user_preferences(user_id)
        
        # Get all products with scores
        product_scores = {}
        
        for category in self.categories:
            for product in category['products']:
                product_name = product['name']
                score = self.calculate_product_score(user_id, product_name, category['name'], user_prefs)
                product_scores[product_name] = {
                    'product': product,
                    'category': category['name'],
                    'score': score
                }
        
        # Sort by score and return top recommendations
        sorted_products = sorted(product_scores.items(), key=lambda x: x[1]['score'], reverse=True)
        
        for product_name, data in sorted_products[:limit]:
            # Get price from product data
            product_price = self.get_product_price(product_name)
            
            recommendations.append({
                'name': product_name,
                'category': data['category'],
                'price': product_price or 0.0,
                'description': data['product'].get('description', ''),
                'score': data['score'],
                'reason': self.get_recommendation_reason(user_id, product_name, data['category'])
            })
        
        return recommendations
    
    def track_product_view(self, user_id: int, product_name: str, category: str):
        """Track when user views a product for recommendation analysis"""
        try:
            # Initialize user's view history if not exists
            if user_id not in self.user_behavior['view_history']:
                self.user_behavior['view_history'][user_id] = []
            
            # Add view record with timestamp
            view_record = {
                'product': product_name,
                'category': category,
                'timestamp': datetime.now().isoformat(),
                'session_id': self.get_or_create_session_id(user_id)
            }
            
            # Add to view history (keep last 50 views per user)
            self.user_behavior['view_history'][user_id].append(view_record)
            if len(self.user_behavior['view_history'][user_id]) > 50:
                self.user_behavior['view_history'][user_id] = self.user_behavior['view_history'][user_id][-50:]
            
            # Update product analytics
            self.update_product_analytics(product_name, category, 'view')
            
            # Save updated behavior data
            self.save_user_behavior()
            
            print(f"Tracked product view: User {user_id} viewed {product_name} in {category}")
            
        except Exception as e:
            print(f"Error tracking product view: {e}")
    
    def track_product_purchase(self, user_id: int, product_name: str, category: str, price: float):
        """Track when user purchases a product"""
        try:
            # Initialize user's purchase history if not exists
            if user_id not in self.user_behavior['purchase_history']:
                self.user_behavior['purchase_history'][user_id] = []
            
            # Add purchase record
            purchase_record = {
                'product': product_name,
                'category': category,
                'price': price,
                'timestamp': datetime.now().isoformat(),
                'session_id': self.get_or_create_session_id(user_id)
            }
            
            # Add to purchase history
            self.user_behavior['purchase_history'][user_id].append(purchase_record)
            
            # Update product analytics
            self.update_product_analytics(product_name, category, 'purchase', price)
            
            # Save updated behavior data
            self.save_user_behavior()
            
            print(f"Tracked product purchase: User {user_id} purchased {product_name} for {price}")
            
        except Exception as e:
            print(f"Error tracking product purchase: {e}")
    
    def get_or_create_session_id(self, user_id: int) -> str:
        """Get or create session ID for user"""
        if user_id not in self.user_behavior['session_data']:
            self.user_behavior['session_data'][user_id] = {
                'current_session': datetime.now().isoformat(),
                'session_count': 1
            }
        return self.user_behavior['session_data'][user_id]['current_session']
    
    def update_product_analytics(self, product_name: str, category: str, action: str, price: float = None):
        """Update product analytics for trending calculations"""
        if product_name not in self.product_analytics:
            self.product_analytics[product_name] = {
                'views': 0,
                'purchases': 0,
                'total_revenue': 0,
                'category': category,
                'last_updated': datetime.now().isoformat()
            }
        
        if action == 'view':
            self.product_analytics[product_name]['views'] += 1
        elif action == 'purchase':
            self.product_analytics[product_name]['purchases'] += 1
            if price:
                self.product_analytics[product_name]['total_revenue'] += price
        
        self.product_analytics[product_name]['last_updated'] = datetime.now().isoformat()
        self.save_product_analytics()
    
    def calculate_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """Calculate user preferences based on behavior"""
        preferences = {
            'favorite_categories': {},
            'price_range': {'min': 0, 'max': float('inf')},
            'purchase_frequency': 0,
            'avg_order_value': 0
        }
        
        # Analyze purchase history
        purchase_history = self.user_behavior['purchase_history'].get(user_id, [])
        if purchase_history:
            # Category preferences
            for purchase in purchase_history:
                category = purchase['category']
                if category not in preferences['favorite_categories']:
                    preferences['favorite_categories'][category] = 0
                preferences['favorite_categories'][category] += 1
            
            # Price range
            prices = [p['price'] for p in purchase_history]
            preferences['price_range']['min'] = min(prices) * 0.5
            preferences['price_range']['max'] = max(prices) * 2.0
            
            # Purchase frequency
            if len(purchase_history) > 1:
                first_purchase = datetime.fromisoformat(purchase_history[0]['timestamp'])
                last_purchase = datetime.fromisoformat(purchase_history[-1]['timestamp'])
                days_diff = (last_purchase - first_purchase).days
                preferences['purchase_frequency'] = len(purchase_history) / max(days_diff, 1)
            
            # Average order value
            preferences['avg_order_value'] = sum(prices) / len(prices)
        
        return preferences
    
    def calculate_product_score(self, user_id: int, product_name: str, category: str, user_prefs: Dict) -> float:
        """Calculate recommendation score for a product based on browsing history"""
        score = 0.0
        
        # Enhanced view history analysis with time weighting
        view_history = self.user_behavior['view_history'].get(user_id, [])
        recent_views = [v for v in view_history if self.is_recent_view(v)]
        
        # Direct product views with time-based weighting
        for view in view_history:
            if view['product'] == product_name:
                time_weight = self.get_time_weight(view['timestamp'])
                score += self.recommendation_weights['view_history'] * time_weight * 1.5
        
        # Category interest from browsing patterns
        category_views = [v for v in view_history if v['category'] == category]
        if category_views:
            recent_category_views = [v for v in category_views if self.is_recent_view(v)]
            category_interest = len(recent_category_views) / max(len(recent_views), 1)
            score += self.recommendation_weights['view_history'] * category_interest * 0.8
        
        # Similar product analysis based on browsing
        similar_products = self.get_similar_products_by_browsing(user_id, product_name)
        if similar_products:
            score += self.recommendation_weights['view_history'] * 0.6
        
        # Purchase history score (negative - don't recommend already purchased)
        purchase_history = self.user_behavior['purchase_history'].get(user_id, [])
        purchase_count = sum(1 for purchase in purchase_history if purchase['product'] == product_name)
        score -= purchase_count * 0.5  # Penalty for already purchased
        
        # Category preference score
        if category in user_prefs['favorite_categories']:
            category_score = user_prefs['favorite_categories'][category]
            score += category_score * self.recommendation_weights['category_preference']
        
        # Price preference score
        product_price = self.get_product_price(product_name)
        if product_price:
            if user_prefs['price_range']['min'] <= product_price <= user_prefs['price_range']['max']:
                score += self.recommendation_weights['price_preference']
        
        # Enhanced trending products boost
        if product_name in self.trending_products:
            trending_rank = self.trending_products.index(product_name)
            trending_boost = max(0, (10 - trending_rank) / 10) * 0.3
            score += trending_boost
        
        # Popularity score
        popularity = self.product_analytics['popularity_scores'].get(product_name, 0)
        score += popularity * 0.1
        
        return max(0, score)  # Ensure non-negative score
    
    def get_product_price(self, product_name: str) -> Optional[float]:
        """Get product price by name"""
        for category in self.categories:
            for product in category['products']:
                if product['name'] == product_name:
                    # Check if product has quantities (new format) or single price (old format)
                    if 'quantities' in product and product['quantities']:
                        # Use the first quantity's price as the base price
                        return product['quantities'][0]['price']
                    elif 'price' in product:
                        # Old format with single price
                        return product['price']
        return None
    
    def is_recent_view(self, view_record: Dict[str, Any], days: int = 7) -> bool:
        """Check if view is recent (within specified days)"""
        try:
            view_time = datetime.fromisoformat(view_record['timestamp'])
            return (datetime.now() - view_time).days <= days
        except:
            return False
    
    def get_time_weight(self, timestamp: str) -> float:
        """Get time-based weight for views (recent views have higher weight)"""
        try:
            view_time = datetime.fromisoformat(timestamp)
            days_ago = (datetime.now() - view_time).days
            # Exponential decay: recent views have higher weight
            return max(0.1, math.exp(-days_ago / 7))
        except:
            return 0.1
    
    def get_similar_products_by_browsing(self, user_id: int, product_name: str) -> List[str]:
        """Get similar products based on user's browsing patterns"""
        similar_products = []
        view_history = self.user_behavior['view_history'].get(user_id, [])
        
        # Find products viewed in same category
        target_category = None
        for view in view_history:
            if view['product'] == product_name:
                target_category = view['category']
                break
        
        if target_category:
            # Find other products in same category that user has viewed
            for view in view_history:
                if (view['category'] == target_category and 
                    view['product'] != product_name and 
                    self.is_recent_view(view)):
                    similar_products.append(view['product'])
        
        return similar_products[:3]  # Return top 3 similar products
    
    def get_recommendation_reason(self, user_id: int, product_name: str, category: str) -> str:
        """Get human-readable reason for recommendation based on browsing history"""
        reasons = []
        
        # Check recent browsing history
        view_history = self.user_behavior['view_history'].get(user_id, [])
        recent_views = [v for v in view_history if self.is_recent_view(v)]
        
        # Check if user viewed this specific product recently
        direct_views = [v for v in recent_views if v['product'] == product_name]
        if direct_views:
            reasons.append("You viewed this recently")
        
        # Check if user viewed similar products in same category
        category_views = [v for v in recent_views if v['category'] == category and v['product'] != product_name]
        if category_views:
            reasons.append(f"Based on your {category} browsing")
        
        # Check if it's trending
        if product_name in self.trending_products:
            trending_rank = self.trending_products.index(product_name) + 1
            reasons.append(f"Trending #{trending_rank}")
        
        # Check if it's popular
        popularity = self.product_analytics['popularity_scores'].get(product_name, 0)
        if popularity > 0.7:
            reasons.append("Popular choice")
        
        # Check browsing patterns
        similar_products = self.get_similar_products_by_browsing(user_id, product_name)
        if similar_products:
            reasons.append("Similar to your interests")
        
        # Check price range
        user_prefs = self.calculate_user_preferences(user_id)
        product_price = self.get_product_price(product_name)
        if product_price and user_prefs['price_range']['min'] <= product_price <= user_prefs['price_range']['max']:
            reasons.append("Matches your price range")
        
        return ", ".join(reasons) if reasons else "Recommended for you"
    
    def calculate_trending_products(self) -> List[str]:
        """Calculate trending products based on recent activity"""
        trending = []
        
        # Get products with high recent view counts
        recent_views = {}
        cutoff_time = datetime.now() - timedelta(days=7)
        
        for user_id, views in self.user_behavior['view_history'].items():
            for view in views:
                view_time = datetime.fromisoformat(view['timestamp'])
                if view_time > cutoff_time:
                    product = view['product']
                    if product not in recent_views:
                        recent_views[product] = 0
                    recent_views[product] += 1
        
        # Sort by recent view count
        sorted_products = sorted(recent_views.items(), key=lambda x: x[1], reverse=True)
        trending = [product for product, count in sorted_products[:10]]
        
        return trending
    
    def build_similarity_matrix(self) -> Dict[str, List[str]]:
        """Build product similarity matrix based on co-purchases"""
        similarity = {}
        
        # Analyze co-purchases
        co_purchases = {}
        for user_id, purchases in self.user_behavior['purchase_history'].items():
            user_products = [p['product'] for p in purchases]
            for i, product1 in enumerate(user_products):
                for j, product2 in enumerate(user_products):
                    if i != j:
                        if product1 not in co_purchases:
                            co_purchases[product1] = {}
                        if product2 not in co_purchases[product1]:
                            co_purchases[product1][product2] = 0
                        co_purchases[product1][product2] += 1
        
        # Build similarity matrix
        for product, co_products in co_purchases.items():
            sorted_similar = sorted(co_products.items(), key=lambda x: x[1], reverse=True)
            similarity[product] = [p for p, count in sorted_similar[:5]]
        
        return similarity
    
    def get_similar_products(self, product_name: str) -> List[str]:
        """Get products similar to the given product"""
        return self.similar_products.get(product_name, [])
    
    def get_trending_products(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get trending products"""
        trending = []
        
        for product_name in self.trending_products[:limit]:
            product_data = self.get_product_data(product_name)
            if product_data:
                trending.append({
                    'name': product_name,
                    'category': product_data['category'],
                    'price': product_data['price'],
                    'description': product_data.get('description', ''),
                    'trend_score': self.product_analytics['view_counts'].get(product_name, 0)
                })
        
        return trending
    
    def get_product_data(self, product_name: str) -> Optional[Dict[str, Any]]:
        """Get product data by name"""
        for category in self.categories:
            for product in category['products']:
                if product['name'] == product_name:
                    # Get price from quantities or single price
                    price = None
                    if 'quantities' in product and product['quantities']:
                        price = product['quantities'][0]['price']
                    elif 'price' in product:
                        price = product['price']
                    
                    return {
                        'name': product_name,
                        'category': category['name'],
                        'price': price,
                        'description': product.get('description', '')
                    }
        return None
    
    def create_recommendation_menu(self, user_id: int) -> InlineKeyboardMarkup:
        """Create recommendation menu for user"""
        markup = InlineKeyboardMarkup(row_width=2)
        
        markup.add(
            InlineKeyboardButton('✨ For You', callback_data='recommendations_personal'),
            InlineKeyboardButton('🔥 Trending', callback_data='recommendations_trending')
        )
        
        markup.add(
            InlineKeyboardButton('🛒 Cart Recovery', callback_data='recommendations_cart'),
            InlineKeyboardButton('💡 Similar Products', callback_data='recommendations_similar')
        )
        
        markup.add(
            InlineKeyboardButton('🔙 Back to Menu', callback_data='back')
        )
        
        return markup
    
    def create_recommendation_display(self, recommendations: List[Dict], title: str) -> str:
        """Create formatted recommendation display"""
        if not recommendations:
            return f"**{title}**\n\nNo recommendations available at the moment."
        
        text = f"**{title}**\n\n"
        
        for i, rec in enumerate(recommendations, 1):
            text += f"**{i}. {rec['name']}**\n"
            text += f"💰 €{rec['price']:.2f}\n"
            text += f"📂 {rec['category']}\n"
            if rec.get('reason'):
                text += f"💡 {rec['reason']}\n"
            text += "\n"
        
        return text
    
    def update_popularity_scores(self):
        """Update product popularity scores"""
        for product_name in self.product_analytics['view_counts']:
            views = self.product_analytics['view_counts'][product_name]
            purchases = self.product_analytics['purchase_counts'].get(product_name, 0)
            
            # Calculate popularity score (0-1)
            if views > 0:
                conversion_rate = purchases / views
                popularity_score = min(1.0, (views * 0.1 + conversion_rate * 10) / 2)
                self.product_analytics['popularity_scores'][product_name] = popularity_score
        
        self.save_product_analytics()
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """Get recommendation engine statistics"""
        total_interactions = len(self.user_behavior['view_history']) + len(self.user_behavior['purchase_history'])
        
        active_users = len(self.user_behavior['view_history'])
        
        return {
            'total_interactions': total_interactions,
            'active_users': active_users,
            'recommendation_accuracy': 85.5,  # Placeholder
            'user_satisfaction': 4.2,  # Placeholder
            'response_time': 150,  # Placeholder
            'cache_hit_rate': 78.3,  # Placeholder
            'learning_enabled': True
        }

def setup_recommendation_handlers(bot, recommendation_engine):
    """Setup recommendation-related handlers"""
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('recommendations_'))
    def recommendation_callback_handler(call):
        user_id = call.from_user.id
        
        if call.data == 'recommendations_personal':
            recommendations = recommendation_engine.get_user_recommendations(user_id, 5)
            title = "🎯 Personalized Recommendations"
            text = recommendation_engine.create_recommendation_display(recommendations, title)
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton('🔙 Back to Recommendations', callback_data='recommendations_menu'))
            
            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup,
                parse_mode='Markdown'
            )
        
        elif call.data == 'recommendations_trending':
            trending = recommendation_engine.get_trending_products(5)
            title = "🔥 Trending Products"
            text = recommendation_engine.create_recommendation_display(trending, title)
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton('🔙 Back to Recommendations', callback_data='recommendations_menu'))
            
            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup,
                parse_mode='Markdown'
            )
        
        elif call.data == 'recommendations_cart':
            # Get cart abandonment recommendations
            cart_abandonments = recommendation_engine.user_behavior['cart_abandonment'].get(user_id, [])
            
            if cart_abandonments:
                latest_abandonment = cart_abandonments[-1]
                abandoned_items = latest_abandonment['items']
                
                text = "🛒 **Cart Recovery Recommendations**\n\n"
                text += "You left these items in your cart:\n\n"
                
                for item in abandoned_items:
                    text += f"• {item['name']} - €{item['price']:.2f}\n"
                
                text += "\nComplete your purchase or browse similar products!"
            else:
                text = "🛒 **Cart Recovery**\n\nNo abandoned carts found. Keep shopping!"
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton('🔙 Back to Recommendations', callback_data='recommendations_menu'))
            
            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup,
                parse_mode='Markdown'
            )
        
        elif call.data == 'recommendations_similar':
            # Get similar products based on recent views
            view_history = recommendation_engine.user_behavior['view_history'].get(user_id, [])
            
            if view_history:
                recent_view = view_history[-1]
                similar_products = recommendation_engine.get_similar_products(recent_view['product'])
                
                if similar_products:
                    text = f"💡 **Similar to {recent_view['product']}**\n\n"
                    for product_name in similar_products[:5]:
                        product_data = recommendation_engine.get_product_data(product_name)
                        if product_data:
                            text += f"• {product_name} - €{product_data['price']:.2f}\n"
                else:
                    text = "💡 **Similar Products**\n\nNo similar products found at the moment."
            else:
                text = "💡 **Similar Products**\n\nView some products first to get similar recommendations!"
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton('🔙 Back to Recommendations', callback_data='recommendations_menu'))
            
            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup,
                parse_mode='Markdown'
            )
        
        bot.answer_callback_query(call.id, "Recommendations loaded!")
