import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import pandas as pd
import unittest
import matplotlib.pyplot as plt
import seaborn as sns
import re

# --- Класс для работы с базой данных ---
class Database:
    @staticmethod
    def init_db():
        try:
            conn = sqlite3.connect('shop.db')
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS clients (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            fio TEXT, phone TEXT, email TEXT, address TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS products (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT, price REAL, unit TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS orders (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            client_id INTEGER,
                            FOREIGN KEY(client_id) REFERENCES clients(id))''')
            c.execute('''CREATE TABLE IF NOT EXISTS order_items (
                            order_id INTEGER,
                            product_id INTEGER,
                            quantity INTEGER,
                            FOREIGN KEY(order_id) REFERENCES orders(id),
                            FOREIGN KEY(product_id) REFERENCES products(id))''')
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка базы данных", f"Ошибка при инициализации базы данных: {e}")

    @staticmethod
    def execute_query(query, params=()):
        try:
            conn = sqlite3.connect('shop.db')
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            result = cursor.lastrowid
            conn.close()
            return result
        except sqlite3.Error as e:
            raise Exception(f"Ошибка базы данных: {e}")

    @staticmethod
    def fetch_all(query, params=()):
        try:
            conn = sqlite3.connect('shop.db')
            cursor = conn.cursor()
            cursor.execute(query, params)
            result = cursor.fetchall()
            conn.close()
            return result
        except sqlite3.Error as e:
            raise Exception(f"Ошибка базы данных: {e}")

# --- Класс Клиента ---
class Client:
    def __init__(self, fio="", phone="", email="", address=""):
        self.fio = fio
        self.phone = phone
        self.email = email
        self.address = address
    
    def validate(self):
        if not all([self.fio, self.phone, self.email, self.address]):
            raise ValueError("Заполните все поля")
        if not re.match(r'^9\d{9}$', self.phone):
            raise ValueError("Телефон должен начинаться на 9 и содержать 10 цифр (без +7 и 8)")
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', self.email):
            raise ValueError("Некорректный формат почты")
        return True
    
    def save(self):
        self.validate()
        Database.execute_query(
            "INSERT INTO clients (fio, phone, email, address) VALUES (?, ?, ?, ?)",
            (self.fio, self.phone, self.email, self.address)
        )

# --- Класс Товара ---
class Product:
    def __init__(self, name="", price=0.0, unit=""):
        self.name = name
        self.price = price
        self.unit = unit
    
    def validate(self):
        if not all([self.name, self.unit]):
            raise ValueError("необходим заполнить все значения товара")
        if self.price < 0:
            raise ValueError("Стоимость должна быть числом >= 0")
        return True
    
    def save(self):
        self.validate()
        Database.execute_query(
            "INSERT INTO products (name, price, unit) VALUES (?, ?, ?)",
            (self.name, self.price, self.unit)
        )

# --- Класс Заказа ---
class Order:
    def __init__(self):
        self.client_id = None
        self.items = []
    
    def add_item(self, product_id, quantity):
        self.items.append((product_id, quantity))
    
    def save(self):
        if not self.client_id:
            raise ValueError("Не выбран клиент")
        if not self.items:
            raise ValueError("Нет товаров в заказе")
        
        # Создаем заказ
        order_id = Database.execute_query(
            "INSERT INTO orders (client_id) VALUES (?)",
            (self.client_id,)
        )
        
        # Добавляем товары в заказ
        for product_id, quantity in self.items:
            Database.execute_query(
                "INSERT INTO order_items (order_id, product_id, quantity) VALUES (?, ?, ?)",
                (order_id, product_id, quantity)
            )

# --- Главное окно ---
class App:
    def __init__(self, root):
        try:
            self.root = root
            self.root.title("Интернет-магазин")
            self.notebook = ttk.Notebook(root)
            self.notebook.pack(fill='both', expand=True)
            
            # Переменная для отслеживания порядка сортировки
            self.sort_direction = {}

            self.init_clients_tab()
            self.init_products_tab()
            self.init_orders_tab()
            self.init_statistics_tab()
        except Exception as e:
            messagebox.showerror("Ошибка инициализации", f"Ошибка при создании интерфейса: {e}")

    # --- Вкладка "Клиенты" ---
    def init_clients_tab(self):
        self.clients_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.clients_frame, text='Клиенты')
        input_frame = ttk.Frame(self.clients_frame)
        input_frame.pack(padx=10, pady=10, fill='x')
        ttk.Label(input_frame, text="ФИО:").grid(row=0, column=0)
        self.entry_fio = ttk.Entry(input_frame)
        self.entry_fio.grid(row=0, column=1)
        ttk.Label(input_frame, text="Телефон:").grid(row=0, column=2)
        self.entry_phone = ttk.Entry(input_frame)
        self.entry_phone.grid(row=0, column=3)
        ttk.Label(input_frame, text="Почта:").grid(row=1, column=0)
        self.entry_email = ttk.Entry(input_frame)
        self.entry_email.grid(row=1, column=1)
        ttk.Label(input_frame, text="Адрес:").grid(row=1, column=2)
        self.entry_address = ttk.Entry(input_frame)
        self.entry_address.grid(row=1, column=3)
        ttk.Button(input_frame, text="Добавить клиента", command=self.add_client).grid(row=2, column=0, columnspan=4, pady=5)
        self.tree_clients = ttk.Treeview(self.clients_frame, columns=('FIO', 'Phone', 'Email', 'Address'), show='headings')
        for col in ('FIO', 'Phone', 'Email', 'Address'):
            self.tree_clients.heading(col, text=col)
        self.tree_clients.pack(padx=10, pady=10, fill='both', expand=True)
        self.load_clients()

    def load_clients(self):
        try:
            for row in self.tree_clients.get_children():
                self.tree_clients.delete(row)
            rows = Database.fetch_all("SELECT fio, phone, email, address FROM clients")
            for row in rows:
                self.tree_clients.insert('', 'end', values=row)
        except Exception as e:
            messagebox.showerror("Ошибка базы данных", f"Ошибка при загрузке клиентов: {e}")

    def add_client(self):
        fio = self.entry_fio.get().strip()
        phone = self.entry_phone.get().strip()
        email = self.entry_email.get().strip()
        address = self.entry_address.get().strip()
        
        try:
            client = Client(fio, phone, email, address)
            client.save()
            self.load_clients()
            # Очищаем поля после добавления
            self.entry_fio.delete(0, tk.END)
            self.entry_phone.delete(0, tk.END)
            self.entry_email.delete(0, tk.END)
            self.entry_address.delete(0, tk.END)
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e))
        except Exception as e:
            messagebox.showerror("Ошибка базы данных", f"Ошибка при добавлении клиента: {e}")

    # --- Вкладка "Товары" ---
    def init_products_tab(self):
        self.products_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.products_frame, text='Товары')

        input_frame = ttk.Frame(self.products_frame)
        input_frame.pack(padx=10, pady=10, fill='x')

        # Ввод названия
        ttk.Label(input_frame, text="Наименование:").grid(row=0, column=0, sticky='w')
        self.entry_product_name = ttk.Entry(input_frame)
        self.entry_product_name.grid(row=0, column=1)
        # Ввод единицы
        ttk.Label(input_frame, text="Ед. измерения:").grid(row=1, column=0, sticky='w')
        self.entry_unit = ttk.Entry(input_frame)
        self.entry_unit.grid(row=1, column=1)
        # Ввод стоимости
        ttk.Label(input_frame, text="Стоимость:").grid(row=2, column=0, sticky='w')
        self.entry_product_price = ttk.Entry(input_frame)
        self.entry_product_price.grid(row=2, column=1)
        # Кнопка
        ttk.Button(input_frame, text="Добавить товар", command=self.add_product).grid(row=3, column=0, columnspan=2, pady=5)

        # Таблица товаров
        self.tree_products = ttk.Treeview(self.products_frame, columns=('Name', 'Price', 'Unit'), show='headings')
        self.tree_products.heading('Name', text='Наименование')
        self.tree_products.heading('Price', text='Стоимость')
        self.tree_products.heading('Unit', text='Ед.изм.')
        self.tree_products.pack(padx=10, pady=10, fill='both', expand=True)
        self.load_products()

    def load_products(self):
        try:
            for row in self.tree_products.get_children():
                self.tree_products.delete(row)
            rows = Database.fetch_all("SELECT name, price, unit FROM products")
            for row in rows:
                self.tree_products.insert('', 'end', values=row)
        except Exception as e:
            messagebox.showerror("Ошибка базы данных", f"Ошибка при загрузке товаров: {e}")

    def add_product(self):
        name = self.entry_product_name.get().strip()
        unit = self.entry_unit.get().strip()
        price_str = self.entry_product_price.get().strip()
        
        try:
            price = float(price_str)
            product = Product(name, price, unit)
            product.save()
            # очистить поля
            self.entry_product_name.delete(0, tk.END)
            self.entry_unit.delete(0, tk.END)
            self.entry_product_price.delete(0, tk.END)
            self.load_products()
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e))
        except Exception as e:
            messagebox.showerror("Ошибка базы данных", f"Ошибка при добавлении товара: {e}")

    # --- Вкладка "Заказы" ---
    def init_orders_tab(self):
        self.orders_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.orders_frame, text='Заказы')
        frame_order = ttk.Frame(self.orders_frame)
        frame_order.pack(padx=10, pady=10, fill='x')

        # Клиент + Обновление списка
        ttk.Label(frame_order, text="Клиент:").grid(row=0, column=0)
        self.combo_clients = ttk.Combobox(frame_order, state='readonly', width=30)
        ttk.Button(frame_order, text="Обновить клиентов", command=self.load_clients_for_order).grid(row=0, column=2, padx=5)
        self.combo_clients.grid(row=0, column=1)

        # Товары + Обновление
        ttk.Label(frame_order, text="Товары:").grid(row=1, column=0, sticky='ne')
        self.list_products = tk.Listbox(frame_order, selectmode='multiple', height=6)
        self.list_products.grid(row=1, column=1)
        ttk.Button(frame_order, text="Обновить список товаров", command=self.load_products_for_order).grid(row=2, column=1, pady=5)

        # Количество
        ttk.Label(frame_order, text="Количество:").grid(row=3, column=0, sticky='e')
        self.entry_qty = ttk.Entry(frame_order, width=5)
        self.entry_qty.grid(row=3, column=1, sticky='w')

        # Создать заказ
        ttk.Button(frame_order, text="Создать заказ", command=self.create_order).grid(row=4, column=0, columnspan=3, pady=5)

        # Таблица заказов
        self.tree_orders = ttk.Treeview(self.orders_frame, columns=('Client', 'Items', 'Total'), show='headings')
        self.tree_orders.heading('Client', text='Клиент')
        self.tree_orders.heading('Items', text='Товары (кол-во)')
        self.tree_orders.heading('Total', text='Общая стоимость', command=lambda: self.sort_orders('Total'))
        self.tree_orders.pack(padx=10, pady=10, fill='both', expand=True)
        
        # Инициализация направления сортировки
        self.sort_direction['orders'] = {'Client': False, 'Items': False, 'Total': False}

        # Начальная загрузка данных
        self.load_clients_for_order()
        self.load_products_for_order()
        self.load_orders()

    def sort_orders(self, column):
        """Сортировка таблицы заказов по выбранному столбцу"""
        try:           
            items = [(self.tree_orders.set(item, column), item) for item in self.tree_orders.get_children('')]            
            
            if column == 'Total':               
                items = [(float(item[0].replace(' руб.', '')), item[1]) for item in items]
            else:                
                items = [(item[0].lower(), item[1]) for item in items]            
            
            items.sort(reverse=self.sort_direction['orders'][column])            
           
            for index, (_, item) in enumerate(items):
                self.tree_orders.move(item, '', index)            
            
            self.sort_direction['orders'][column] = not self.sort_direction['orders'][column]
        except Exception as e:
            messagebox.showerror("Ошибка сортировки", f"Ошибка при сортировке данных: {e}")

    def load_clients_for_order(self):
        try:
            rows = Database.fetch_all("SELECT fio FROM clients")
            self.combo_clients['values'] = [row[0] for row in rows]
        except Exception as e:
            messagebox.showerror("Ошибка базы данных", f"Ошибка при загрузке клиентов: {e}")

    def load_products_for_order(self):
        try:
            self.list_products.delete(0, tk.END)
            rows = Database.fetch_all("SELECT name FROM products")
            for row in rows:
                self.list_products.insert(tk.END, row[0])
        except Exception as e:
            messagebox.showerror("Ошибка базы данных", f"Ошибка при загрузке товаров: {e}")

    def create_order(self):
        client_name = self.combo_clients.get()
        qty_str = self.entry_qty.get().strip()
        
        try:
            if not client_name:
                raise ValueError("Выберите клиента")
            if not qty_str:
                raise ValueError("Введите количество")
            
            qty = int(qty_str)
            if qty <= 0:
                raise ValueError("Количество должно быть целым числом >0")
            
            selected = self.list_products.curselection()
            if not selected:
                raise ValueError("Выберите товары")            
            
            client_rows = Database.fetch_all("SELECT id FROM clients WHERE fio=?", (client_name,))
            if not client_rows:
                raise ValueError("Клиент не найден")
            client_id = client_rows[0][0]            
            
            order = Order()
            order.client_id = client_id            
           
            for idx in selected:
                product_name = self.list_products.get(idx)
                product_rows = Database.fetch_all("SELECT id FROM products WHERE name=?", (product_name,))
                if product_rows:
                    product_id = product_rows[0][0]
                    order.add_item(product_id, qty)
            
            # Сохраняем заказ
            order.save()
            self.load_orders()
            
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e))
        except Exception as e:
            messagebox.showerror("Ошибка базы данных", f"Ошибка при создании заказа: {e}")

    def load_orders(self):
        try:
            for row in self.tree_orders.get_children():
                self.tree_orders.delete(row)
            
            rows = Database.fetch_all('''
                SELECT 
                    c.fio, 
                    GROUP_CONCAT(p.name || ' x' || oi.quantity, ', '),
                    SUM(oi.quantity * p.price) as total_sum
                FROM orders o
                JOIN clients c ON o.client_id=c.id
                JOIN order_items oi ON o.id=oi.order_id
                JOIN products p ON oi.product_id=p.id
                GROUP BY o.id, c.fio
            ''')
            
            for row in rows:
                total_formatted = f"{row[2]:.2f} руб." if row[2] else "0.00 руб."
                self.tree_orders.insert('', 'end', values=(row[0], row[1], total_formatted))
                
        except Exception as e:
            messagebox.showerror("Ошибка базы данных", f"Ошибка при загрузке заказов: {e}")

    # --- Вкладка "Статистика" ---
    def init_statistics_tab(self):
        self.stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.stats_frame, text='Статистика и Анализ')
        ttk.Button(self.stats_frame, text="Топ 5 клиентов", command=self.plot_top_clients).pack(pady=10)
        ttk.Button(self.stats_frame, text="География клиентов", command=self.plot_geo_clients).pack(pady=10)
        self.fig = plt.Figure(figsize=(6,4))
        self.ax1 = self.fig.add_subplot(121)
        self.ax2 = self.fig.add_subplot(122)
        self.canvas = None

    def plot_top_clients(self):
        try:
            df = pd.read_sql_query('''
                SELECT c.fio, SUM(oi.quantity * p.price) as total
                FROM orders o
                JOIN clients c ON o.client_id=c.id
                JOIN order_items oi ON o.id=oi.order_id
                JOIN products p ON oi.product_id=p.id
                GROUP BY c.fio
                ORDER BY total DESC
            ''', sqlite3.connect('shop.db'))
            
            plt.clf()
            plt.bar(df['fio'].head(5), df['total'].head(5))
            plt.title('Топ 5 клиентов по сумме заказов')
            plt.ylabel('Общая сумма')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.show()
        except Exception as e:
            messagebox.showerror("Ошибка построения графика", f"Ошибка при построении топа клиентов: {e}")

    def plot_geo_clients(self):
        try:
            df = pd.read_sql_query('SELECT address FROM clients', sqlite3.connect('shop.db'))
            # Предположим, что в адресе есть город - возьмем первое слово
            df['city'] = df['address'].apply(lambda x: x.split()[0] if x else 'Не определен')
            city_counts = df['city'].value_counts()
            plt.figure()
            sns.barplot(x=city_counts.index, y=city_counts.values, color='red')
            plt.title('География клиентов по городам')
            plt.ylabel('Количество клиентов')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.show()
        except Exception as e:
            messagebox.showerror("Ошибка построения графика", f"Ошибка при построении географии клиентов: {e}")

#--- тесты ---
class Tests(unittest.TestCase):
    
    def test_client_validation_success(self):        
        client = Client("Иванов Иван", "9123456789", "test@example.com", "Москва")
        self.assertTrue(client.validate())
    
    def test_client_validation_failure(self):       
        client = Client("", "123", "invalid-email", "")
        with self.assertRaises(ValueError):
            client.validate()
    
    def test_product_validation_success(self):        
        product = Product("Телефон", 1000.0, "шт")
        self.assertTrue(product.validate())
    
    def test_product_validation_failure(self):        
        product = Product("", -100, "")
        with self.assertRaises(ValueError):
            product.validate()
    
    def test_order_validation_failure_no_client(self):       
        order = Order()
        with self.assertRaises(ValueError):
            order.save()
    
    def test_order_validation_failure_no_items(self):        
        order = Order()
        order.client_id = 1
        with self.assertRaises(ValueError):
            order.save()

# --- запуск ---
if __name__ == "__main__":
    try:
        test_loader = unittest.TestLoader()
        test_suite = test_loader.loadTestsFromTestCase(Tests)
        unittest.TextTestRunner().run(test_suite)
        Database.init_db()
        root = tk.Tk()
        app = App(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Критическая ошибка", f"Программа завершена с ошибкой: {e}")