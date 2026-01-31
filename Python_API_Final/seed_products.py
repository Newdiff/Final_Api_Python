# seed_products.py
from app import app
from extensions import db
from models import Product

with app.app_context():
    products = [
        { "name": "Canon EOS R10", "price": 979, "category_id": 6, "stock": 7, "description": "Mirrorless digital camera" },
        { "name": "GoPro Hero 12", "price": 399, "category_id": 6, "stock": 14, "description": "Action camera for adventure" },
        { "name": "iPad Air 5", "price": 599, "category_id": 7, "stock": 16, "description": "Powerful tablet with M1 chip" },
        { "name": "Kindle Paperwhite", "price": 139, "category_id": 7, "stock": 22, "description": "E-reader with glare-free display" },
        { "name": "Bose SoundLink Flex", "price": 149, "category_id": 8, "stock": 19, "description": "Portable Bluetooth speaker" },
        { "name": "DJI Mini 3", "price": 469, "category_id": 9, "stock": 9, "description": "Compact drone with 4K camera" },
        { "name": "Razer BlackWidow V4", "price": 169, "category_id": 4, "stock": 13, "description": "RGB mechanical gaming keyboard" },
        { "name": "SteelSeries Arctis Nova 7", "price": 179, "category_id": 2, "stock": 11, "description": "Wireless gaming headset" },
        { "name": "Samsung T7 Shield SSD", "price": 129, "category_id": 10, "stock": 27, "description": "Portable rugged SSD storage" },
        { "name": "Xiaomi Smart Band 8", "price": 59, "category_id": 5, "stock": 35, "description": "Fitness tracking smart band" }
    ]

    for product_data in products:
        if not Product.query.filter_by(name=product_data["name"]).first():
            db.session.add(Product(**product_data))

    db.session.commit()
    print(f"Added {len(products)} products")