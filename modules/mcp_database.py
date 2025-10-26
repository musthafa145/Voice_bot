"""
MYG Electronics Product Database - FastMCP Server
"""

from fastmcp import FastMCP
import json

# Initialize FastMCP server
mcp = FastMCP("MYG Electronics Database")

# Load product database
def load_database():
    """Load the MYG products database from JSON file"""
    try:
        with open('../data/products.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: products.json not found in data/ directory")
        return None

# Global database variable
DB = load_database()

# ==================== MCP TOOLS ====================

@mcp.tool()
def get_all_products():
    """Get list of all available products in MYG store"""
    if not DB:
        return {"error": "Database not loaded"}
    
    return {
        "store_info": DB["store_info"],
        "total_products": len(DB["products"]),
        "products": DB["products"]
    }


@mcp.tool()
def search_products(query: str = "", category: str = "", min_price: int = 0, max_price: int = 999999, brand: str = ""):
    """
    Search for products by name, category, price range, or brand
    """
    if not DB:
        return {"error": "Database not loaded"}
    
    results = []
    
    for product in DB["products"]:
        # Apply filters
        if category and product["category"] != category:
            continue
        
        if product["price"] < min_price or product["price"] > max_price:
            continue
        
        if brand and product["brand"].lower() != brand.lower():
            continue
        
        if query:
            query_lower = query.lower()
            if (query_lower not in product["name"].lower() and 
                query_lower not in product["description"].lower()):
                continue
        
        results.append(product)
    
    return {
        "count": len(results),
        "products": results
    }


@mcp.tool()
def get_product_by_id(product_id: str):
    """Get detailed information about a specific product by its ID"""
    if not DB:
        return {"error": "Database not loaded"}
    
    for product in DB["products"]:
        if product["id"] == product_id:
            return {"success": True, "product": product}
    
    return {"success": False, "error": f"Product {product_id} not found"}


@mcp.tool()
def check_stock(product_id: str):
    """Check stock availability for a specific product"""
    if not DB:
        return {"error": "Database not loaded"}
    
    for product in DB["products"]:
        if product["id"] == product_id:
            return {
                "product_name": product["name"],
                "stock_quantity": product["stock"],
                "availability": "Available" if product["in_stock"] else "Out of Stock"
            }
    
    return {"error": f"Product {product_id} not found"}


@mcp.tool()
def get_active_offers():
    """Get all active promotional offers and discounts"""
    if not DB:
        return {"error": "Database not loaded"}
    
    return {
        "total_offers": len(DB["active_offers"]),
        "offers": DB["active_offers"]
    }


@mcp.tool()
def recommend_products(budget: int, category: str = ""):
    """Get product recommendations based on budget"""
    if not DB:
        return {"error": "Database not loaded"}
    
    candidates = [p for p in DB["products"] 
                 if p["price"] <= budget and p["in_stock"]]
    
    if category:
        candidates = [p for p in candidates if p["category"] == category]
    
    # Sort by discount (best deals first)
    candidates.sort(key=lambda x: x["discount"], reverse=True)
    
    return {
        "budget": budget,
        "recommendations": candidates[:5]
    }


# ==================== MAIN ====================

if __name__ == "__main__":
    print("MYG Electronics Database Server")
    print(f"Loaded {len(DB['products']) if DB else 0} products")
    mcp.run()
