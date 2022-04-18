import sqlite3

class BotDB:
    def __init__(self, db_file: str):
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS "categories" (
	"id"	INTEGER NOT NULL UNIQUE,
	"name"	TEXT NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
);''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS "products" (
	"id"	INTEGER NOT NULL UNIQUE,
	"name"	TEXT NOT NULL,
	"category_id"	TEXT NOT NULL,
	"description"	TEXT,
	"price"	REAL NOT NULL,
	"image_path"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("category_id") REFERENCES "categories"("id")
);''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS "orders" (
	"id"	INTEGER NOT NULL UNIQUE,
	"user_id"	INTEGER NOT NULL,
	"product_id"	INTEGER NOT NULL,
	"order_date"	TEXT NOT NULL,
	"delivery_date"	TEXT NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("user_id") REFERENCES "users"("id"),
	FOREIGN KEY("product_id") REFERENCES "products"("id")
);''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS "users" (
	"id"	INTEGER NOT NULL UNIQUE,
	"user_telegram_id"	INTEGER NOT NULL,
	"nickname"	TEXT NOT NULL,
	"phone_number"	INTEGER NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
);''')
    
    def user_exists(self, user_id: int):
        result = self.cursor.execute("SELECT id FROM users WHERE user_telegram_id = ?", (user_id,))
        return bool(len(result.fetchall()))
    
    def add_user(self, user_id: int, nickname: str, phone_number: int):
        self.cursor.execute("INSERT INTO users (user_telegram_id, nickname, phone_number) VALUES(?, ?, ?)", (user_id, nickname, phone_number))
        return self.conn.commit()

    def get_categories(self):
        result = self.cursor.execute("SELECT name FROM categories").fetchall()
        lst = []
        for i in result:
            lst.append(i[0])
        return lst

    def get_category_id(self, category: str):
        result = self.cursor.execute("SELECT id FROM categories WHERE name = ?", (category,)).fetchall()
        return result[0]
    
    def get_products_in_category(self, category_id: int):
        result = self.cursor.execute("SELECT name FROM products WHERE category_id = ?", (category_id)).fetchall()
        lst = []
        for i in result:
            lst.append(i[0])
        return lst
    
    def get_product_id(self, product_name: str):
        return self.cursor.execute("SELECT id FROM products WHERE name = ?", (product_name,)).fetchall()[0]

    def get_product(self, product_id: int):
        return {
            'id': product_id[0],
            'name': self.cursor.execute("SELECT name FROM products WHERE id = ?", (product_id)).fetchall()[0][0],
            'category_id': self.cursor.execute("SELECT category_id FROM products WHERE id = ?", (product_id)).fetchall()[0][0],
            'description': self.cursor.execute("SELECT description FROM products WHERE id = ?", (product_id)).fetchall()[0][0],
            'price': self.cursor.execute("SELECT price FROM products WHERE id = ?", (product_id)).fetchall()[0][0],
            'image_path': self.cursor.execute("SELECT image_path FROM products WHERE id = ?", (product_id)).fetchall()[0][0]
        }

    def add_order(self, user_id: int, product_id: int, order_date: str, delivery_date: str):
        self.cursor.execute("INSERT INTO orders (user_id, product_id, order_date, delivery_date) VALUES(?, ?, ?, ?)", (user_id, product_id, order_date, delivery_date))
        return self.conn.commit()
    
    def close(self):
        self.conn.close()