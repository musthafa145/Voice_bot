import csv
import random

# Define product categories and sample attributes
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

def generate_products(num_products=300, output_file="synthetic_myg_products.csv"):
    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            "product_id",
            "product_name",
            "category",
            "brand",
            "price",
            "features",
            "highlights",
            "stock_status"
        ])

        pid = 1
        for _ in range(num_products):
            category = random.choice(list(categories.keys()))
            cat_data = categories[category]
            brand = random.choice(cat_data["brands"])
            feature = random.choice(cat_data["features"])
            price = random.randint(*cat_data["price_range"])

            # Only 10% chance of being out of stock
            stock = "Out of stock" if random.random() < 0.10 else "In stock"

            highlights = random.choice([
                "Best seller", "New arrival", "Value for money", "Customer favorite",
                "High performance", "Limited stock", "Popular model"
            ])

            product_name = f"{brand} {category} {random.randint(100,999)}"
            writer.writerow([pid, product_name, category, brand, price, feature, highlights, stock])
            pid += 1

    print(f"✅ Generated {num_products} products and saved to {output_file}")

# Run the generator
generate_products()
