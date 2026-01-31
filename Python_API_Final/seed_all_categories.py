# seed_all_categories.py
from app import app
from extensions import db
from models import Category

with app.app_context():
    categories = [
        "Technology",          # ID: 1
        "Programming",         # ID: 2
        "Business",            # ID: 3
        "Design",              # ID: 4
        "AI",                  # ID: 5
        "Cameras",             # ID: 6
        "Tablets & E-readers", # ID: 7
        "Audio",               # ID: 8
        "Drones",              # ID: 9
        "Storage"              # ID: 10
    ]

    for name in categories:
        if not Category.query.filter_by(name=name).first():
            db.session.add(Category(name=name))

    db.session.commit()
    print("All categories added")