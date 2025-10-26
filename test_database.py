"""
Test script to verify MYG database is working
"""

import json

print("="*60)
print("MYG ELECTRONICS DATABASE TEST")
print("="*60)

# Test 1: Load database
print("\n1. Testing: Load Database")
try:
    with open('data/products.json', 'r', encoding='utf-8') as f:
        db = json.load(f)
    print(f"   ✓ Database loaded successfully!")
    print(f"   ✓ Total products: {len(db['products'])}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    exit()

# Test 2: Display store info
print("\n2. Store Information")
print(f"   Name: {db['store_info']['name']}")
print(f"   Type: {db['store_info']['type']}")
print(f"   Location: {db['store_info']['location']}")

# Test 3: List categories
print("\n3. Available Categories")
for i, cat in enumerate(db['categories'], 1):
    print(f"   {i}. {cat.replace('_', ' ').title()}")

# Test 4: Show some products
print("\n4. Sample Products")
for product in db['products'][:3]:
    print(f"\n   - {product['name']}")
    print(f"     Price: ₹{product['price']:,}")
    print(f"     Stock: {product['stock']} units")
    if product['discount'] > 0:
        savings = product['original_price'] - product['price']
        print(f"     Discount: {product['discount']}% (Save ₹{savings:,})")

# Test 5: Active offers
print("\n5. Active Offers")
for offer in db['active_offers']:
    print(f"   - {offer['title']}")
    print(f"     {offer['description']}")
    print(f"     Valid until: {offer['valid_until']}")

print("\n" + "="*60)
print("ALL TESTS PASSED ✓")
print("="*60)
print("\nDatabase is ready to use!")
