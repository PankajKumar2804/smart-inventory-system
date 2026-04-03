"""
Inventory management system
"""

import sqlite3
from datetime import datetime
from typing import List, Optional

class InventoryDB:
    def __init__(self, db_path: str = 'inventory.db'):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._init_db()
    
    def _init_db(self):
        """Initialize database"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                sku TEXT UNIQUE NOT NULL,
                quantity INTEGER DEFAULT 0,
                price REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id TEXT,
                quantity INTEGER,
                type TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(product_id) REFERENCES products(id)
            )
        ''')
        self.conn.commit()
    
    def add_product(self, product_id: str, name: str, sku: str, price: float):
        """Add new product"""
        try:
            self.cursor.execute('''
                INSERT INTO products (id, name, sku, price)
                VALUES (?, ?, ?, ?)
            ''', (product_id, name, sku, price))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def update_stock(self, product_id: str, quantity: int, transaction_type: str):
        """Update product stock"""
        self.cursor.execute('SELECT quantity FROM products WHERE id = ?', (product_id,))
        result = self.cursor.fetchone()
        
        if not result:
            return False
        
        new_quantity = result[0] + quantity
        if new_quantity < 0:
            return False
        
        self.cursor.execute('UPDATE products SET quantity = ? WHERE id = ?', 
                          (new_quantity, product_id))
        
        self.cursor.execute('''
            INSERT INTO transactions (product_id, quantity, type)
            VALUES (?, ?, ?)
        ''', (product_id, quantity, transaction_type))
        
        self.conn.commit()
        return True
    
    def get_product(self, product_id: str):
        """Get product details"""
        self.cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
        return self.cursor.fetchone()
    
    def get_low_stock_items(self, threshold: int = 10):
        """Get items below stock threshold"""
        self.cursor.execute(
            'SELECT id, name, quantity FROM products WHERE quantity < ?',
            (threshold,)
        )
        return self.cursor.fetchall()
    
    def get_inventory_value(self):
        """Calculate total inventory value"""
        self.cursor.execute('SELECT SUM(quantity * price) FROM products')
        result = self.cursor.fetchone()
        return result[0] or 0
    
    def close(self):
        """Close database connection"""
        self.conn.close()


if __name__ == "__main__":
    db = InventoryDB()
    db.add_product("P001", "Laptop", "SKU001", 999.99)
    db.add_product("P002", "Mouse", "SKU002", 29.99)
    db.update_stock("P001", 10, "inbound")
    db.update_stock("P002", 50, "inbound")
    
    print("Low stock items:", db.get_low_stock_items())
    print("Inventory value:", db.get_inventory_value())
    db.close()
