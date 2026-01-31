from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from extensions import db
from models import User, Category, Product, CartItem, Order, OrderDetail

front_bp = Blueprint("front", __name__)


# ---------- PUBLIC READ ----------
@front_bp.get("/category-list")
def category_list():
    """Get all categories"""
    rows = Category.query.order_by(Category.id.desc()).all()
    return jsonify([{"id": c.id, "name": c.name} for c in rows]), 200


@front_bp.get("/category-list/<int:category_id>")
def category_products(category_id):
    """Get all products for a specific category"""
    # Check if category exists
    category = Category.query.get(category_id)
    if not category:
        return jsonify({"message": "category not found"}), 404

    # Get products for this category
    products = Product.query.filter_by(category_id=category_id).order_by(Product.id.desc()).all()

    return jsonify({
        "category": {"id": category.id, "name": category.name},
        "products": [
            {
                "id": p.id,
                "name": p.name,
                "price": p.price,
                "stock": p.stock,
                "category_id": p.category_id
            }
            for p in products
        ]
    }), 200


@front_bp.get("/product-list")
def product_list():
    """Get all products"""
    rows = Product.query.order_by(Product.id.desc()).all()
    return jsonify([
        {
            "id": p.id,
            "name": p.name,
            "price": p.price,
            "stock": p.stock,
            "category_id": p.category_id,
        }
        for p in rows
    ]), 200


# ---------- AUTH ----------
@front_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not name or not email or not password:
        return jsonify({"message": "name, email, password required"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"message": "email already exists"}), 409

    u = User(name=name, email=email, role="customer")
    u.set_password(password)

    db.session.add(u)
    db.session.commit()
    return jsonify({"message": "registered"}), 201


@front_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    u = User.query.filter_by(email=email).first()
    if not u or not u.check_password(password):
        return jsonify({"message": "invalid credentials"}), 401

    # DEBUG PRINT
    print(f"Creating token for identity: {u.id} (type: {type(u.id)})")

    # FORCE STRING CONVERSION
    identity_str = str(u.id)
    print(f"Using identity string: {identity_str} (type: {type(identity_str)})")

    access_token = create_access_token(identity=identity_str)

    return jsonify({
        "access_token": access_token,
        "user": {"id": u.id, "name": u.name, "email": u.email, "role": u.role},
    }), 200


@front_bp.post("/reset-password")
def reset_password():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    new_password = data.get("new_password") or ""

    if not email or not new_password:
        return jsonify({"message": "email and new_password required"}), 400

    u = User.query.filter_by(email=email).first()
    if not u:
        return jsonify({"message": "email not found"}), 404

    u.set_password(new_password)
    db.session.commit()
    return jsonify({"message": "password updated"}), 200


@front_bp.post("/logout")
def logout():
    # Simple version: client deletes token.
    # If you want true logout, use a token blocklist/revoking approach. [web:161]
    return jsonify({"message": "logout successfully"}), 200


@front_bp.get("/me")
@jwt_required()
def me():
    user_id = get_jwt_identity()
    u = User.query.get_or_404(user_id)
    return jsonify({"id": u.id, "name": u.name, "email": u.email, "role": u.role}), 200


# ---------- CART ----------
@front_bp.post("/add-to-cart")
@jwt_required()
def add_to_cart():
    # Already correct
    current_identity = get_jwt_identity()
    try:
        user_id = int(current_identity)  # ✓ Good
    except (ValueError, TypeError):
        return jsonify({"message": "Invalid user identity in token"}), 401

    data = request.get_json(silent=True) or {}

    # 2. Validate product_id and qty
    product_id = data.get("product_id")
    if product_id is None:
        return jsonify({"message": "product_id required"}), 400

    try:
        product_id = int(product_id)
        # Default qty to 1 if missing or invalid
        qty = int(data.get("qty", 1))
    except (TypeError, ValueError):
        return jsonify({"message": "product_id and qty must be numbers"}), 400

    if qty < 1:
        return jsonify({"message": "qty must be >= 1"}), 400

    # 3. Check product existence
    p = Product.query.get(product_id)
    if not p:
        return jsonify({"message": "product not found"}), 404

    # 4. Add to cart logic
    item = CartItem.query.filter_by(user_id=user_id, product_id=product_id).first()
    if item:
        item.qty += qty
    else:
        item = CartItem(user_id=user_id, product_id=product_id, qty=qty)
        db.session.add(item)

    db.session.commit()
    return jsonify({"message": "added to cart"}), 200


@front_bp.delete("/cart/<int:product_id>")
@jwt_required()
def delete_cart_item(product_id):
    """Delete a specific product from the current user's cart"""

    try:
        user_id = int(get_jwt_identity())
    except (ValueError, TypeError):
        return jsonify({"message": "Invalid user identity"}), 401

    try:
        # Find cart item
        item = CartItem.query.filter_by(
            user_id=user_id,
            product_id=product_id
        ).first()

        if not item:
            return jsonify({
                "message": "Item not found in cart",
                "product_id": product_id
            }), 404

        # Optional: product info
        product = Product.query.get(product_id)

        deleted_item = {
            "product_id": product_id,
            "product_name": product.name if product else "Unknown",
            "quantity": item.qty,
            "price": product.price if product else 0
        }

        db.session.delete(item)
        db.session.commit()

        return jsonify({
            "message": "Item removed from cart",
            "deleted_item": deleted_item
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "message": "Failed to remove item from cart",
            "error": str(e)
        }), 500


# ---------- CHECKOUT / ORDERS ----------
@front_bp.post("/checkout")
@jwt_required()
def checkout():
    print("=== CHECKOUT STARTED ===")

    try:
        user_id = int(get_jwt_identity())
        print(f"User ID: {user_id}")
    except (ValueError, TypeError) as e:
        print(f"JWT Error: {e}")
        return jsonify({"message": "Invalid user identity"}), 401

    try:
        # Get cart items
        items = CartItem.query.filter_by(user_id=user_id).all()
        print(f"Found {len(items)} cart items")

        if not items:
            print("Cart is empty")
            return jsonify({"message": "cart empty"}), 400

        # Debug each item
        for i, item in enumerate(items):
            print(f"Item {i + 1}: ID={item.id}, Product={item.product_id}, Qty={item.qty}")
            product = Product.query.get(item.product_id)
            if product:
                print(f"  Product: {product.name}, Stock={product.stock}, Price={product.price}")
            else:
                print(f"  WARNING: Product {item.product_id} not found!")

        total = 0.0
        insufficient_stock_items = []
        available_items = []

        # Validate stock
        for item in items:
            product = Product.query.get(item.product_id)
            if not product:
                print(f"ERROR: Product {item.product_id} not found in database")
                return jsonify({"message": f"product not found: {item.product_id}"}), 404

            print(f"Checking stock: {product.name} - Cart Qty: {item.qty}, Available: {product.stock}")

            if item.qty > product.stock:
                print(f"INSUFFICIENT STOCK: {product.name} - Need {item.qty}, Have {product.stock}")
                insufficient_stock_items.append({
                    "product_id": product.id,
                    "product_name": product.name,
                    "requested": item.qty,
                    "available": product.stock
                })
            else:
                item_total = item.qty * product.price
                total += item_total
                available_items.append({
                    'item': item,
                    'product': product,
                    'subtotal': item_total
                })
                print(f"OK: {product.name} - Added to order, Subtotal: {item_total}")

        print(f"Total calculated: {total}")
        print(f"Available items: {len(available_items)}")
        print(f"Out of stock items: {len(insufficient_stock_items)}")

        if not available_items:
            return jsonify({
                "message": "All items are out of stock",
                "insufficient_items": insufficient_stock_items
            }), 400

        # If no items available after stock check
        if not available_items:
            print("No items available for checkout")
            return jsonify({
                "message": "No items available for checkout (all out of stock)",
                "total": 0
            }), 400

        # Create order
        print("Creating order...")
        order = Order(user_id=user_id, total=total, status="pending")
        db.session.add(order)
        db.session.flush()
        print(f"Order created with ID: {order.id}")

        # Create order details
        print("Creating order details...")
        for data in available_items:
            item = data['item']
            product = data['product']

            print(f"  Processing: {product.name} x {item.qty}")

            # Create order detail
            order_detail = OrderDetail(
                order_id=order.id,
                product_id=product.id,
                qty=item.qty,
                price=product.price,
            )
            db.session.add(order_detail)

            # Update stock
            old_stock = product.stock
            product.stock -= item.qty
            print(f"    Stock: {old_stock} -> {product.stock}")

            # Remove from cart
            db.session.delete(item)
            print(f"    Removed cart item {item.id}")

        # Commit transaction
        print("Committing transaction...")
        db.session.commit()
        print(f"=== CHECKOUT COMPLETE: Order {order.id} ===")

        return jsonify({
            "message": "checkout successful",
            "order_id": order.id,
            "total": total,
            "items_count": len(available_items)
        }), 200

    except Exception as e:
        print(f"=== CHECKOUT ERROR: {str(e)} ===")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({"message": f"Checkout failed: {str(e)}"}), 500


@front_bp.get("/tracking-order")
@jwt_required()
def tracking_order():
    # Convert user_id from string to int
    try:
        user_id = int(get_jwt_identity())
    except (ValueError, TypeError):
        return jsonify({"message": "Invalid user identity"}), 401

    orders = Order.query.filter_by(user_id=user_id).order_by(Order.id.desc()).all()

    return jsonify([
        {
            "id": o.id,
            "total": o.total,
            "status": o.status,
            "created_at": o.created_at.isoformat() if getattr(o, "created_at", None) else None,
        }
        for o in orders
    ]), 200