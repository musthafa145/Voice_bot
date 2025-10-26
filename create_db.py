# create_db.py
import sqlite3
import random
import csv
from pathlib import Path

DB_PATH = "myg_products.db"
NUM_PRODUCTS = 300

categories = {
    "Mobile": {
        "brands": ["Samsung", "Redmi", "Realme", "OnePlus", "Apple", "Vivo", "Oppo"],
        "features": [
            "8GB RAM, 128GB storage, 50MP camera",
            "12GB RAM, 256GB storage, 200MP camera",
            "6GB RAM, 64GB storage, 5000mAh battery",
            "8GB RAM, 128GB storage, AMOLED display",
            "Snapdragon 7 Gen 1, 80W fast charging",
            "90Hz display, AI camera, long battery life",
        ],
        "price_range": (12000, 90000)
    },
    "Laptop": {
        "brands": ["HP", "Dell", "Lenovo", "Asus", "Acer", "MSI", "Apple"],
        "features": [
            "i5 12th Gen, 8GB RAM, 512GB SSD",
            "i7 13th Gen, 16GB RAM, 1TB SSD, RTX 3050",
            "Ryzen 5, 8GB RAM, 512GB SSD",
            "i3 11th Gen, 8GB RAM, 256GB SSD",
            "i9, 32GB RAM, RTX 4060, 1TB SSD",
            "Touchscreen, Backlit keyboard, Fingerprint sensor",
        ],
        "price_range": (35000, 160000)
    },
    "Tablet": {
        "brands": ["Samsung", "Apple", "Lenovo", "Xiaomi", "Realme"],
        "features": [
            "Snapdragon 8 Gen 2, 11-inch AMOLED display",
            "Apple M2 chip, 12.9-inch Retina display",
            "8GB RAM, 128GB storage, 13MP rear camera",
            "S-Pen support, Dolby Atmos speakers",
            "Helio G99, 10.5-inch LCD, long battery life",
        ],
        "price_range": (15000, 95000)
    },
    "Headphone": {
        "brands": ["JBL", "Sony", "Boat", "Realme", "Zebronics"],
        "features": [
            "Bluetooth 5.2, 40-hour battery",
            "Noise cancellation, Foldable design",
            "Deep bass, Mic support, Fast charging",
            "Lightweight, Sweat resistant",
            "Dual pairing, Voice assistant compatible",
        ],
        "price_range": (999, 9999)
    },
    "Speaker": {
        "brands": ["Boat", "JBL", "Sony", "Zebronics"],
        "features": [
            "Bluetooth 5.0, 10W output, waterproof",
            "Portable, 12-hour playtime, bass boost",
            "Smart assistant enabled, 360° sound",
            "20W stereo output, splash resistant",
        ],
        "price_range": (1499, 14999)
    }
}

def create_db(path=DB_PATH):
    p = Path(path)
    if p.exists():
        p.unlink()
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE product (
        id INTEGER PRIMARY KEY,
        product_name TEXT,
        category TEXT,
        brand TEXT,
        price INTEGER,
        features TEXT,
        highlights TEXT,
        stock_status TEXT
    )
    """)
    conn.commit()
    pid = 1
    for _ in range(NUM_PRODUCTS):
        category = random.choice(list(categories.keys()))
        cat = categories[category]
        brand = random.choice(cat["brands"])
        feature = random.choice(cat["features"])
        price = random.randint(*cat["price_range"])
        stock = "Out of stock" if random.random() < 0.10 else "In stock"
        highlights = random.choice([
            "Best seller", "New arrival", "Value for money", "Customer favorite",
            "High performance", "Limited stock", "Popular model"
        ])
        product_name = f"{brand} {category} {random.randint(100,999)}"
        c.execute("INSERT INTO product VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (pid, product_name, category, brand, price, feature, highlights, stock))
        pid += 1
    conn.commit()
    conn.close()
    print(f"Created {path} with {NUM_PRODUCTS} items.")

if __name__ == "__main__":
    create_db()
