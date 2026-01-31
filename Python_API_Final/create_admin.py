from app import app
from extensions import db
from models import User

with app.app_context():
    User.query.filter_by(email="admin@example.com").delete()
    db.session.commit()

    u = User(name="Admin", email="admin@example.com", role="admin")
    u.set_password("123456789")
    db.session.add(u)
    db.session.commit()

    print("Admin recreated:", u.email)
