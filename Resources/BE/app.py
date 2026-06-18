import os
import uuid
from datetime import datetime, timezone
from flask import Flask, request, Response
from pymongo import MongoClient
from bson import json_util

app = Flask(__name__)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client.orderdb
orders_collection = db.orders

def mongo_jsonify(data, status=200):
    return Response(json_util.dumps(data), mimetype='application/json', status=status)

@app.route('/order', methods=['POST'])
def create_order():
    data = request.get_json()
    if not data or 'product' not in data or 'quantity' not in data or 'price' not in data:
        return mongo_jsonify({"error": "Bad Request: Missing fields"}, 400)

    order_id = str(uuid.uuid4())
    total = int(data['quantity']) * float(data['price'])
    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    new_order = {
        "order_id": order_id, "product": data['product'],
        "quantity": data['quantity'], "price": data['price'],
        "total": total, "status": "pending", "created_at": created_at
    }

    orders_collection.insert_one(new_order.copy())
    return mongo_jsonify(new_order, 201)

@app.route('/order/<order_id>', methods=['GET'])
def get_order(order_id):
    order = orders_collection.find_one({"order_id": order_id}, {"_id": 0})
    if order:
        return mongo_jsonify(order, 200)
    return mongo_jsonify({"error": "Order not found"}, 404)

@app.route('/orders', methods=['GET'])
def get_orders():
    # Batasi 50 data agar tidak nge-lag!
    orders = list(orders_collection.find({}, {"_id": 0}).sort("created_at", -1).limit(50))
    return mongo_jsonify(orders, 200)

@app.route('/order/<order_id>', methods=['PUT'])
def update_order(order_id):
    data = request.get_json()
    if not data or 'status' not in data:
        return mongo_jsonify({"error": "Bad Request: Status is required"}, 400)

    result = orders_collection.update_one(
        {"order_id": order_id},
        {"$set": {"status": data['status']}}
    )

    if result.matched_count > 0:
        return mongo_jsonify({"order_id": order_id, "status": data['status']}, 200)
    return mongo_jsonify({"error": "Order not found"}, 404)

@app.route('/health', methods=['GET'])
def health():
    return mongo_jsonify({"status": "healthy"}, 200)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)