"""
Gemini LLM Handler Module
Handles conversation with Gemini AI and database queries
"""

from google import genai
import json
import sys
import os

# Add parent directory to path to import from modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class GeminiHandler:
    def __init__(self, api_key, database_path='data/products.json'):
        """Initialize Gemini LLM client"""
        
        # Initialize Gemini client
        self.client = genai.Client(api_key=api_key)
        self.model = 'gemini-2.0-flash-exp'
        
        # Load product database
        try:
            with open(database_path, 'r', encoding='utf-8') as f:
                self.database = json.load(f)
            print(f"✓ Gemini Handler initialized with {len(self.database['products'])} products")
        except FileNotFoundError:
            print(f"✗ Error: Database not found at {database_path}")
            self.database = None
        
        # Conversation history
        self.conversation_history = []
        
        # System prompt for sales bot
        self.system_prompt = """You are a friendly and helpful sales assistant for MYG Kerala, an electronics retail store.

Your role:
- Welcome customers warmly
- Ask clarifying questions to understand their needs
- Recommend products from the MYG database
- Provide product details, prices, and stock availability
- Help customers make purchasing decisions

Guidelines:
- Keep responses SHORT and conversational (2-3 sentences max)
- Ask ONE question at a time
- Mention specific product names and prices
- If customer mentions budget, recommend within that range
- Be friendly and natural

You are speaking, not writing, so be concise!"""
    
    
    def get_database_context(self, query):
        """Search database and return relevant products"""
        if not self.database:
            return "Database not available"
        
        query_lower = query.lower()
        context = []
        
        # Find relevant products
        relevant_products = []
        for product in self.database['products']:
            if (query_lower in product['name'].lower() or 
                query_lower in product['brand'].lower() or
                query_lower in product['category'].replace('_', ' ').lower()):
                relevant_products.append(product)
        
        if relevant_products:
            context.append(f"Found {len(relevant_products)} products:")
            for p in relevant_products[:3]:
                savings = p['original_price'] - p['price']
                context.append(f"- {p['name']} (₹{p['price']:,})")
                if p['discount'] > 0:
                    context.append(f"  {p['discount']}% OFF - Save ₹{savings:,}")
        else:
            context.append("Available categories:")
            for cat in self.database['categories'][:4]:
                context.append(f"- {cat.replace('_', ' ').title()}")
        
        # Add offers
        if self.database['active_offers']:
            context.append("\nActive Offers:")
            for offer in self.database['active_offers']:
                context.append(f"- {offer['title']}: {offer['description']}")
        
        return "\n".join(context)
    
    
    def generate_response(self, user_input):
        """Generate response from Gemini"""
        
        # Get database context
        db_context = self.get_database_context(user_input)
        
        # Build prompt
        prompt = f"""{self.system_prompt}

Database Info:
{db_context}

Recent conversation:
{self._format_history()}

User: {user_input}

Assistant (keep response SHORT - you are speaking out loud):"""
        
        try:
            # Generate response
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            
            bot_response = response.text.strip()
            
            # Save to history
            self.conversation_history.append({
                "user": user_input,
                "bot": bot_response
            })
            
            return bot_response
            
        except Exception as e:
            print(f"Error generating response: {e}")
            return "I'm sorry, I encountered an error. Could you please repeat that?"
    
    
    def _format_history(self):
        """Format conversation history for context"""
        if not self.conversation_history:
            return "No previous conversation"
        
        # Get last 3 exchanges
        recent = self.conversation_history[-3:]
        formatted = []
        for exchange in recent:
            formatted.append(f"User: {exchange['user']}")
            formatted.append(f"Bot: {exchange['bot']}")
        
        return "\n".join(formatted)
    
    
    def get_welcome_message(self):
        """Generate welcome message"""
        return "Hello! Welcome to MYG Kerala. I'm your sales assistant. How can I help you today?"
    
    
    def reset_conversation(self):
        """Clear conversation history"""
        self.conversation_history = []


# Test the module
if __name__ == "__main__":
    print("Testing Gemini LLM Handler")
    print("="*60)
    
    # You need to set your API key
    API_KEY = input("Enter your Gemini API key: ")
    
    handler = GeminiHandler(API_KEY)
    
    # Test welcome message
    print("\n1. Welcome Message:")
    print(handler.get_welcome_message())
    
    # Test conversation
    print("\n2. Test Conversation:")
    test_queries = [
        "I'm looking for a laptop under 80000",
        "What about Samsung products?",
    ]
    
    for query in test_queries:
        print(f"\nUser: {query}")
        response = handler.generate_response(query)
        print(f"Bot: {response}")
    
    print("\n" + "="*60)
    print("Gemini Handler test complete!")
