"""
API wrapper for Inventory System
"""

from flask import Flask, jsonify, request
from inventory import InventoryDB

app = Flask(__name__)
db = InventoryDB()

@app.route('/api/products', methods=['GET'])
def list_products():
    """List all products"""
    db.cursor.execute('SELECT * FROM products')
    products = db.cursor.fetchall()
    return jsonify([{
        'id': p[0],
        'name': p[1],
        'sku': p[2],
        'quantity': p[3],
        'price': p[4]
    } for p in products])

@app.route('/api/products', methods=['POST'])
def create_product():
    """Create new product"""
    data = request.json
    success = db.add_product(data['id'], data['name'], data['sku'], data['price'])
    return jsonify({'success': success}), 201 if success else 400

@app.route('/api/products/<product_id>/stock', methods=['PUT'])
def update_stock(product_id):
    """Update product stock"""
    data = request.json
    success = db.update_stock(product_id, data['quantity'], data['type'])
    return jsonify({'success': success})

@app.route('/api/low-stock', methods=['GET'])
def get_low_stock():
    """Get low stock items"""
    threshold = request.args.get('threshold', 10, type=int)
    items = db.get_low_stock_items(threshold)
    return jsonify([{
        'id': item[0],
        'name': item[1],
        'quantity': item[2]
    } for item in items])

@app.route('/api/inventory-value', methods=['GET'])
def inventory_value():
    """Get total inventory value"""
    return jsonify({'value': db.get_inventory_value()})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
