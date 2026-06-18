import os
import uuid
from datetime import datetime, timezone
from flask import Flask, request, jsonify
from pymongo import MongoClient

app = Flask(__name__)

# Koneksi ke MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client.orderdb
orders_collection = db.orders

# Helper function: Menerjemahkan tipe data bawaan MongoDB agar bisa dibaca JSON
def sanitize_mongo_data(data):
    if isinstance(data, list):
        return [sanitize_mongo_data(item) for item in data]
    elif isinstance(data, dict):
        for key, value in data.items():
            if type(value).__name__ == 'ObjectId':
                data[key] = str(value)
            elif type(value).__name__ == 'datetime':
                data[key] = value.isoformat()
        return data
    return data

# 1. Create Order
@app.route('/order', methods=['POST'])
def create_order():
    data = request.get_json()
    
    if not data or 'product' not in data or 'quantity' not in data or 'price' not in data:
        return jsonify({"error": "Bad Request: Missing fields"}), 400

    order_id = str(uuid.uuid4())
    total = int(data['quantity']) * float(data['price'])
    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    new_order = {
        "order_id": order_id,
        "product": data['product'],
        "quantity": data['quantity'],
        "price": data['price'],
        "total": total,
        "status": "pending",
        "created_at": created_at
    }

    orders_collection.insert_one(new_order.copy())
    return jsonify(sanitize_mongo_data(new_order)), 201

# 2. Get Order Status
@app.route('/order/<order_id>', methods=['GET'])
def get_order(order_id):
    order = orders_collection.find_one({"order_id": order_id})
    if order:
        return jsonify(sanitize_mongo_data(order)), 200
    return jsonify({"error": "Order not found"}), 404

# 3. Get Order History
@app.route('/orders', methods=['GET'])
def get_orders():
    orders = list(orders_collection.find().sort("created_at", -1))
    return jsonify(sanitize_mongo_data(orders)), 200

# 4. Update Order Status
@app.route('/order/<order_id>', methods=['PUT'])
def update_order(order_id):
    data = request.get_json()
    if not data or 'status' not in data:
        return jsonify({"error": "Bad Request: Status is required"}), 400

    result = orders_collection.update_one(
        {"order_id": order_id},
        {"$set": {"status": data['status']}}
    )

    if result.matched_count > 0:
        return jsonify({
            "order_id": order_id,
            "status": data['status']
        }), 200
        
    return jsonify({"error": "Order not found"}), 404

# Endpoint tambahan untuk memastikan Flask menyala
@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)