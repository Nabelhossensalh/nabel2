import sqlite3
import flet as ft
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple
import json
import os
import shutil
import time
import hashlib
import threading

# =============================================================================
# نماذج البيانات (Models)
# =============================================================================

@dataclass
class User:
    """نموذج المستخدم"""
    id: Optional[int] = None
    username: str = ""
    password_hash: str = ""
    full_name: str = ""
    role: str = "cashier"  # admin, manager, cashier, inventory
    is_active: bool = True
    created_at: str = ""
    last_login: str = ""

@dataclass
class Product:
    """نموذج المنتج"""
    id: Optional[int] = None
    name: str = ""
    barcode: str = ""
    category: str = "عام"
    purchase_price: float = 0.0
    selling_price: float = 0.0
    quantity: int = 0
    created_at: str = ""
    updated_at: str = ""
    min_stock_threshold: int = 5
    unit: str = "حبة"

@dataclass
class Sale:
    """نموذج الفاتورة (Header)"""
    id: Optional[int] = None
    invoice_no: str = ""
    customer_id: Optional[int] = None
    customer_name: str = "نقدي"
    total_amount: float = 0.0
    discount: float = 0.0
    paid_amount: float = 0.0
    remaining_amount: float = 0.0
    payment_type: str = "نقدي"
    profit: float = 0.0
    sale_date: str = ""
    created_at: str = ""
    user_id: Optional[int] = None

@dataclass
class SaleItem:
    """نموذج تفاصيل الفاتورة (Line Items)"""
    id: Optional[int] = None
    sale_id: int = 0
    product_id: int = 0
    product_name: str = ""
    quantity: int = 0
    price: float = 0.0
    purchase_price: float = 0.0
    subtotal: float = 0.0
    profit: float = 0.0

@dataclass
class StockHistory:
    """نموذج سجل الحركات"""
    id: Optional[int] = None
    product_id: int = 0
    product_name: str = ""
    operation_type: str = ""
    quantity_change: int = 0
    old_quantity: int = 0
    new_quantity: int = 0
    profit_change: float = 0.0
    note: str = ""
    created_at: str = ""
    user_id: Optional[int] = None

@dataclass
class Customer:
    """نموذج العميل"""
    id: Optional[int] = None
    name: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""
    created_at: str = ""
    total_debt: float = 0.0
    total_paid: float = 0.0
    notes: str = ""

@dataclass
class Debt:
    """نموذج الدين"""
    id: Optional[int] = None
    customer_id: int = 0
    customer_name: str = ""
    sale_id: int = 0
    amount: float = 0.0
    remaining: float = 0.0
    status: str = "pending"
    created_at: str = ""
    note: str = ""
    due_date: str = ""

@dataclass
class Payment:
    """نموذج السداد"""
    id: Optional[int] = None
    customer_id: int = 0
    customer_name: str = ""
    debt_id: int = 0
    amount: float = 0.0
    payment_date: str = ""
    payment_type: str = "cash"
    note: str = ""
    user_id: Optional[int] = None

@dataclass
class Expense:
    """نموذج المصروف"""
    id: Optional[int] = None
    title: str = ""
    amount: float = 0.0
    category: str = "عام"
    expense_date: str = ""
    note: str = ""
    user_id: Optional[int] = None

@dataclass
class Notification:
    """نموذج الإشعار"""
    id: Optional[int] = None
    title: str = ""
    message: str = ""
    type: str = "info"  # info, warning, error, success
    is_read: bool = False
    created_at: str = ""
    user_id: Optional[int] = None
@dataclass
class Supplier:
    """نموذج المورد"""
    id: Optional[int] = None
    name: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""
    company: str = ""
    tax_number: str = ""
    total_debt: float = 0.0
    total_paid: float = 0.0
    balance: float = 0.0
    notes: str = ""
    created_at: str = ""

@dataclass
class PurchaseInvoice:
    """نموذج فاتورة الشراء"""
    id: Optional[int] = None
    invoice_no: str = ""
    supplier_id: int = 0
    supplier_name: str = ""
    invoice_date: str = ""
    total_amount: float = 0.0
    discount: float = 0.0
    transport_cost: float = 0.0
    loading_cost: float = 0.0
    unloading_cost: float = 0.0
    tax: float = 0.0
    customs: float = 0.0
    other_costs: float = 0.0
    net_total: float = 0.0
    paid_amount: float = 0.0
    remaining_amount: float = 0.0
    payment_status: str = "pending"  # pending, partial, paid
    due_date: str = ""
    notes: str = ""
    created_at: str = ""
    user_id: Optional[int] = None

@dataclass
class PurchaseItem:
    """نموذج تفاصيل فاتورة الشراء"""
    id: Optional[int] = None
    purchase_id: int = 0
    product_id: int = 0
    product_name: str = ""
    quantity: int = 0
    unit_price: float = 0.0
    discount_percent: float = 0.0
    subtotal: float = 0.0
    warehouse: str = "رئيسي"

@dataclass
class SupplierPayment:
    """نموذج سداد للمورد"""
    id: Optional[int] = None
    supplier_id: int = 0
    supplier_name: str = ""
    purchase_id: int = 0
    amount: float = 0.0
    payment_date: str = ""
    payment_type: str = "cash"  # cash, bank, cheque
    cheque_number: str = ""
    note: str = ""
    user_id: Optional[int] = None

@dataclass
class ReturnToSupplier:
    """نموذج مرتجع للمورد"""
    id: Optional[int] = None
    return_no: str = ""
    supplier_id: int = 0
    supplier_name: str = ""
    purchase_id: int = 0
    product_id: int = 0
    product_name: str = ""
    quantity: int = 0
    unit_price: float = 0.0
    total_amount: float = 0.0
    reason: str = ""
    return_date: str = ""
    created_at: str = ""
    user_id: Optional[int] = None

@dataclass
class PriceHistory:
    """نموذج سجل أسعار الشراء"""
    id: Optional[int] = None
    product_id: int = 0
    product_name: str = ""
    old_price: float = 0.0
    new_price: float = 0.0
    supplier_id: int = 0
    supplier_name: str = ""
    purchase_id: int = 0
    changed_at: str = ""

# =============================================================================
# نظام المراسلة والتنبيهات (Messaging System)
# =============================================================================

import urllib.parse
import webbrowser

class MessagingSystem:
    """نظام إرسال الرسائل وتنبيهات الديون للعملاء"""
    
    @staticmethod
    def generate_debt_reminder(customer_name: str, total_amount: float) -> str:
        return f"عزيزي العميل {customer_name}، نود تذكيركم بوجود مستحقات مالية متبقية بقيمة {total_amount:.2f} ج.م. يرجى التكرم بالسداد في أقرب وقت. شاكرين تعاونكم."
        
    @staticmethod
    def generate_payment_receipt(customer_name: str, paid_amount: float) -> str:
        return f"سعادة العميل {customer_name}، تم استلام دفعة مالية بقيمة {paid_amount:.2f} ج.م بنجاح. شكراً لكم ولدعمكم المستمر."
        
    @staticmethod
    def send_sms(phone: str, message: str) -> Tuple[bool, str]:
        try:
            clean_phone = ''.join(c for c in phone if c.isdigit() or c == '+')
            encoded_message = urllib.parse.quote(message)
            sms_url = f"sms:{clean_phone}?body={encoded_message}"
            webbrowser.open(sms_url)
            return True, "تم فتح تطبيق الرسائل بنجاح"
        except Exception as e:
            return False, f"فشل فتح تطبيق الرسائل: {str(e)}"
            
    @staticmethod
    def send_whatsapp(phone: str, message: str) -> Tuple[bool, str]:
        try:
            clean_phone = ''.join(c for c in phone if c.isdigit())
            if len(clean_phone) == 11 and clean_phone.startswith("01"):
                clean_phone = "2" + clean_phone
            encoded_message = urllib.parse.quote(message)
            whatsapp_url = f"https://api.whatsapp.com/send?phone={clean_phone}&text={encoded_message}"
            webbrowser.open(whatsapp_url)
            return True, "تم فتح واتساب بنجاح"
        except Exception as e:
            return False, f"فشل فتح واتساب: {str(e)}"

# =============================================================================
# إدارة قاعدة البيانات (Database)
# =============================================================================

class Database:
    """إدارة اتصال قاعدة البيانات والعمليات الأساسية"""
    
    def __init__(self, storage_path=""):
        if storage_path:
            db_path = os.path.join(storage_path, "grocery_store.db")
        else:
            db_path = "grocery_store.db"
        self.lock = threading.Lock()
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.create_tables()
        self.create_default_admin()
        # في __init__ بعد create_tables()
        self.create_default_accounts()
     



    def hash_password(self, password: str) -> str:
        """تشفير كلمة المرور"""
        return hashlib.sha256(password.encode()).hexdigest()

    def create_default_admin(self):
        """إنشاء مدير افتراضي إذا لم يوجد"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        if cursor.fetchone()[0] == 0:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO users (username, password_hash, full_name, role, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ("admin", self.hash_password("admin123"), "مدير النظام", "admin", True, now))
            self.conn.commit()

    def create_tables(self):
        """إنشاء جميع الجداول"""
        cursor = self.conn.cursor()  # ← أضف هذا السطر
                # جدول المسودات
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS draft_invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cart_data TEXT NOT NULL,
                customer_name TEXT DEFAULT 'نقدي',
                customer_id INTEGER,
                total_amount REAL DEFAULT 0,
                created_at TEXT NOT NULL,
                user_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)


                # 12. جدول الموردين
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                phone TEXT DEFAULT '',
                email TEXT DEFAULT '',
                address TEXT DEFAULT '',
                company TEXT DEFAULT '',
                tax_number TEXT DEFAULT '',
                total_debt REAL DEFAULT 0,
                total_paid REAL DEFAULT 0,
                balance REAL DEFAULT 0,
                notes TEXT DEFAULT '',
                created_at TEXT NOT NULL
            )
        """)
        
        # 13. جدول فواتير الشراء
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS purchase_invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_no TEXT,
                supplier_id INTEGER NOT NULL,
                supplier_name TEXT DEFAULT '',
                invoice_date TEXT NOT NULL,
                total_amount REAL DEFAULT 0,
                discount REAL DEFAULT 0,
                transport_cost REAL DEFAULT 0,
                loading_cost REAL DEFAULT 0,
                unloading_cost REAL DEFAULT 0,
                tax REAL DEFAULT 0,
                customs REAL DEFAULT 0,
                other_costs REAL DEFAULT 0,
                net_total REAL DEFAULT 0,
                paid_amount REAL DEFAULT 0,
                remaining_amount REAL DEFAULT 0,
                payment_status TEXT DEFAULT 'pending',
                due_date TEXT,
                notes TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                user_id INTEGER,
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # 14. جدول تفاصيل فاتورة الشراء
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS purchase_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                purchase_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                discount_percent REAL DEFAULT 0,
                subtotal REAL NOT NULL,
                warehouse TEXT DEFAULT 'رئيسي',
                FOREIGN KEY (purchase_id) REFERENCES purchase_invoices(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)
        
        # 15. جدول سداد الموردين
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS supplier_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier_id INTEGER NOT NULL,
                supplier_name TEXT DEFAULT '',
                purchase_id INTEGER,
                amount REAL NOT NULL,
                payment_date TEXT NOT NULL,
                payment_type TEXT DEFAULT 'cash',
                cheque_number TEXT DEFAULT '',
                note TEXT DEFAULT '',
                user_id INTEGER,
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
                FOREIGN KEY (purchase_id) REFERENCES purchase_invoices(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # 16. جدول مرتجعات الموردين
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS returns_to_supplier (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                return_no TEXT,
                supplier_id INTEGER NOT NULL,
                supplier_name TEXT DEFAULT '',
                purchase_id INTEGER,
                product_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                total_amount REAL NOT NULL,
                reason TEXT DEFAULT '',
                return_date TEXT NOT NULL,
                created_at TEXT NOT NULL,
                user_id INTEGER,
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
                FOREIGN KEY (purchase_id) REFERENCES purchase_invoices(id),
                FOREIGN KEY (product_id) REFERENCES products(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # 17. جدول سجل أسعار الشراء
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                old_price REAL DEFAULT 0,
                new_price REAL NOT NULL,
                supplier_id INTEGER,
                supplier_name TEXT DEFAULT '',
                purchase_id INTEGER,
                changed_at TEXT NOT NULL
            )
        """)
        
        # 18. جدول حركات الموردين (ledger)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS supplier_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier_id INTEGER NOT NULL,
                purchase_id INTEGER,
                transaction_date TEXT NOT NULL,
                debit REAL DEFAULT 0,
                credit REAL DEFAULT 0,
                description TEXT,
                balance_after REAL DEFAULT 0,
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
                FOREIGN KEY (purchase_id) REFERENCES purchase_invoices(id)
            )
        """)
        
        # فهارس إضافية
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_purchase_invoices_supplier ON purchase_invoices(supplier_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_purchase_items_purchase ON purchase_items(purchase_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_supplier_payments_supplier ON supplier_payments(supplier_id)")
        



                # 19. جدول دليل الحسابات
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chart_of_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_code TEXT NOT NULL UNIQUE,
                account_name TEXT NOT NULL,
                account_type TEXT NOT NULL,  -- asset, liability, income, expense
                parent_id INTEGER,
                is_active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL
            )
        """)
        
        # 20. جدول القيود اليومية
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS journal_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_no TEXT NOT NULL,
                entry_date TEXT NOT NULL,
                description TEXT,
                reference_type TEXT,  -- sale, purchase, payment, receipt, expense
                reference_id INTEGER,
                is_posted INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                user_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # 21. جدول تفاصيل القيد
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS journal_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_id INTEGER NOT NULL,
                account_id INTEGER NOT NULL,
                description TEXT,
                debit REAL DEFAULT 0,
                credit REAL DEFAULT 0,
                FOREIGN KEY (entry_id) REFERENCES journal_entries(id),
                FOREIGN KEY (account_id) REFERENCES chart_of_accounts(id)
            )
        """)
                # أضف في create_tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS warehouses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                location TEXT DEFAULT '',
                is_active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS warehouse_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                warehouse_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER DEFAULT 0,
                FOREIGN KEY (warehouse_id) REFERENCES warehouses(id),
                FOREIGN KEY (product_id) REFERENCES products(id),
                UNIQUE(warehouse_id, product_id)
            )
        """)
        # 0. جدول المستخدمين
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT DEFAULT 'cashier',
                is_active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                last_login TEXT
            )
        """)
        
        # 1. جدول المنتجات
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                barcode TEXT DEFAULT '',
                category TEXT DEFAULT 'عام',
                purchase_price REAL NOT NULL,
                selling_price REAL NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                min_stock_threshold INTEGER DEFAULT 5,
                unit TEXT DEFAULT 'حبة'
            )
        """)
        
        # 2. جدول العملاء
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                phone TEXT,
                email TEXT DEFAULT '',
                address TEXT DEFAULT '',
                balance REAL DEFAULT 0,
                total_debt REAL DEFAULT 0,
                total_paid REAL DEFAULT 0,
                notes TEXT DEFAULT '',
                created_at TEXT NOT NULL
            )
        """)
        
        # 3. جدول المبيعات
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_no TEXT,
                customer_id INTEGER,
                customer_name TEXT DEFAULT 'نقدي',
                total_amount REAL DEFAULT 0,
                discount REAL DEFAULT 0,
                paid_amount REAL DEFAULT 0,
                remaining_amount REAL DEFAULT 0,
                payment_type TEXT DEFAULT 'نقدي',
                profit REAL DEFAULT 0,
                sale_date TEXT NOT NULL,
                created_at TEXT NOT NULL,
                user_id INTEGER,
                FOREIGN KEY (customer_id) REFERENCES customers(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # 4. جدول تفاصيل المبيعات
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sale_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                purchase_price REAL NOT NULL,
                subtotal REAL NOT NULL,
                profit REAL NOT NULL,
                FOREIGN KEY (sale_id) REFERENCES sales(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)
        
        # 5. حركة الديون / دفتر الأستاذ
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customer_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                sale_id INTEGER,
                transaction_date TEXT NOT NULL,
                debit REAL DEFAULT 0,
                credit REAL DEFAULT 0,
                description TEXT,
                balance_after REAL DEFAULT 0,
                FOREIGN KEY (customer_id) REFERENCES customers(id),
                FOREIGN KEY (sale_id) REFERENCES sales(id)
            )
        """)

        # 6. جدول المصروفات
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT DEFAULT 'عام',
                expense_date TEXT NOT NULL,
                note TEXT,
                user_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # 7. جدول سجل الحركات
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                operation_type TEXT NOT NULL,
                quantity_change INTEGER NOT NULL,
                old_quantity INTEGER NOT NULL,
                new_quantity INTEGER NOT NULL,
                profit_change REAL DEFAULT 0,
                note TEXT,
                created_at TEXT NOT NULL,
                user_id INTEGER
            )
        """)

        # 8. جدول الديون
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS debts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                customer_name TEXT,
                sale_id INTEGER,
                amount REAL DEFAULT 0,
                remaining REAL DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_at TEXT NOT NULL,
                note TEXT,
                due_date TEXT,
                FOREIGN KEY (customer_id) REFERENCES customers(id),
                FOREIGN KEY (sale_id) REFERENCES sales(id)
            )
        """)

        # 9. جدول السداد
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                customer_name TEXT,
                debt_id INTEGER,
                amount REAL DEFAULT 0,
                payment_date TEXT NOT NULL,
                payment_type TEXT DEFAULT 'cash',
                note TEXT,
                user_id INTEGER,
                FOREIGN KEY (customer_id) REFERENCES customers(id),
                FOREIGN KEY (debt_id) REFERENCES debts(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # 10. جدول الإشعارات
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                type TEXT DEFAULT 'info',
                is_read INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                user_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # 11. جدول إعدادات النظام
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)


        # الفهارس
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(sale_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sale_items_sale ON sale_items(sale_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_customer ON customer_transactions(customer_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id, is_read)")
        
        self.conn.commit()


   
    # ========== عمليات المستخدمين ==========
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """توثيق المستخدم"""
        cursor = self.conn.cursor()
        password_hash = self.hash_password(password)
        cursor.execute("""
            SELECT * FROM users WHERE username = ? AND password_hash = ? AND is_active = 1
        """, (username, password_hash))
        row = cursor.fetchone()
        if row:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("UPDATE users SET last_login = ? WHERE id = ?", (now, row["id"]))
            self.conn.commit()
            return dict(row)
        return None
    
    def add_user(self, username: str, password: str, full_name: str, role: str = "cashier") -> Tuple[bool, str]:
        """إضافة مستخدم جديد"""
        cursor = self.conn.cursor()
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO users (username, password_hash, full_name, role, is_active, created_at)
                VALUES (?, ?, ?, ?, 1, ?)
            """, (username, self.hash_password(password), full_name, role, now))
            self.conn.commit()
            return True, "تم إضافة المستخدم بنجاح"
        except sqlite3.IntegrityError:
            return False, "اسم المستخدم موجود مسبقاً"
    
    def get_all_users(self) -> List[Dict]:
        """الحصول على جميع المستخدمين"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, username, full_name, role, is_active, created_at, last_login FROM users ORDER BY role, username")
        return [dict(row) for row in cursor.fetchall()]
    
    def update_user(self, user_id: int, **kwargs) -> Tuple[bool, str]:
        """تحديث بيانات مستخدم"""
        cursor = self.conn.cursor()
        try:
            updates = []
            values = []
            for key, value in kwargs.items():
                if key == "password":
                    updates.append("password_hash = ?")
                    values.append(self.hash_password(value))
                elif key in ["full_name", "role", "is_active"]:
                    updates.append(f"{key} = ?")
                    values.append(value)
            
            if updates:
                values.append(user_id)
                cursor.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", values)
                self.conn.commit()
            return True, "تم تحديث المستخدم بنجاح"
        except Exception as e:
            return False, f"خطأ: {str(e)}"
    
    def delete_user(self, user_id: int) -> Tuple[bool, str]:
        """حذف مستخدم"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT role FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if row and row["role"] == "admin":
                cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin' AND id != ?", (user_id,))
                if cursor.fetchone()[0] == 0:
                    return False, "لا يمكن حذف آخر مدير في النظام"
            
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            self.conn.commit()
            return True, "تم حذف المستخدم بنجاح"
        except Exception as e:
            return False, f"خطأ: {str(e)}"
    
    # ========== عمليات الإشعارات ==========
    
    def add_notification(self, title: str, message: str, type: str = "info", user_id: int = None):
        """إضافة إشعار"""
        cursor = self.conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO notifications (title, message, type, is_read, created_at, user_id)
            VALUES (?, ?, ?, 0, ?, ?)
        """, (title, message, type, now, user_id))
        self.conn.commit()
    
    def get_notifications(self, user_id: int = None, unread_only: bool = False, limit: int = 50) -> List[Dict]:
        """الحصول على الإشعارات"""
        cursor = self.conn.cursor()
        query = "SELECT * FROM notifications WHERE 1=1"
        params = []
        if user_id:
            query += " AND (user_id = ? OR user_id IS NULL)"
            params.append(user_id)
        if unread_only:
            query += " AND is_read = 0"
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def mark_notification_read(self, notification_id: int):
        """تعليم إشعار كمقروء"""
        cursor = self.conn.cursor()
        cursor.execute("UPDATE notifications SET is_read = 1 WHERE id = ?", (notification_id,))
        self.conn.commit()
    
    def get_unread_notifications_count(self, user_id: int = None) -> int:
        """عدد الإشعارات غير المقروءة"""
        cursor = self.conn.cursor()
        if user_id:
            cursor.execute("""
                SELECT COUNT(*) FROM notifications 
                WHERE is_read = 0 AND (user_id = ? OR user_id IS NULL)
            """, (user_id,))
        else:
            cursor.execute("SELECT COUNT(*) FROM notifications WHERE is_read = 0")
        return cursor.fetchone()[0]
    
    def check_low_stock_notifications(self):
        """فحص المنتجات المنخفضة وإرسال إشعارات"""
        low_products = self.get_low_stock_products()
        if low_products:
            for product in low_products:
                self.add_notification(
                    "⚠️ مخزون منخفض",
                    f"المنتج '{product.name}' منخفض المخزون (المتبقي: {product.quantity})",
                    "warning"
                )
    
    # ========== عمليات الإعدادات ==========
    
    def get_setting(self, key: str, default: str = "") -> str:
        """الحصول على إعداد"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row["value"] if row else default
    
    def set_setting(self, key: str, value: str):
        """حفظ إعداد"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
        """, (key, value))
        self.conn.commit()
    
    def get_all_settings(self) -> Dict:
        """الحصول على جميع الإعدادات"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM settings")
        return {row["key"]: row["value"] for row in cursor.fetchall()}
    
    # ========== النسخ الاحتياطي ==========
    
    def backup_database(self, backup_dir: str = "backups") -> Tuple[bool, str]:
        """عمل نسخة احتياطية"""
        try:
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}.db"
            backup_path = os.path.join(backup_dir, backup_name)
            
            # عمل نسخة من قاعدة البيانات
            source_db = "grocery_store.db"
            if os.path.exists(source_db):
                shutil.copy2(source_db, backup_path)
                
                # حذف النسخ القديمة (الاحتفاظ بآخر 10 نسخ)
                backups = sorted([f for f in os.listdir(backup_dir) if f.endswith('.db')])
                while len(backups) > 10:
                    old_backup = os.path.join(backup_dir, backups[0])
                    os.remove(old_backup)
                    backups.pop(0)
                
                self.set_setting("last_backup", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                self.set_setting("last_backup_file", backup_name)
                
                self.add_notification(
                    "✅ نسخ احتياطي",
                    f"تم إنشاء نسخة احتياطية بنجاح: {backup_name}",
                    "success"
                )
                
                return True, f"تم النسخ الاحتياطي: {backup_name}"
            else:
                return False, "قاعدة البيانات غير موجودة"
        except Exception as e:
            return False, f"فشل النسخ: {str(e)}"
    
    def restore_backup(self, backup_file: str) -> Tuple[bool, str]:
        """استعادة نسخة احتياطية"""
        try:
            backup_path = os.path.join("backups", backup_file)
            if not os.path.exists(backup_path):
                return False, "ملف النسخة غير موجود"
            
            # نسخ احتياطي للقاعدة الحالية أولاً
            shutil.copy2("grocery_store.db", "grocery_store.db.before_restore")
            
            # استعادة النسخة
            shutil.copy2(backup_path, "grocery_store.db")
            
            # إعادة تحميل الاتصال
            self.conn.close()
            self.conn = sqlite3.connect("grocery_store.db", check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            
            return True, "تمت الاستعادة بنجاح. يرجى إعادة تشغيل التطبيق"
        except Exception as e:
            return False, f"فشل الاستعادة: {str(e)}"
    
    def get_backup_list(self) -> List[Dict]:
        """قائمة النسخ الاحتياطية"""
        backup_dir = "backups"
        if not os.path.exists(backup_dir):
            return []
        
        backups = []
        for f in sorted(os.listdir(backup_dir), reverse=True):
            if f.endswith('.db'):
                path = os.path.join(backup_dir, f)
                size = os.path.getsize(path)
                mtime = datetime.fromtimestamp(os.path.getmtime(path))
                backups.append({
                    "name": f,
                    "size": f"{size / 1024:.1f} KB",
                    "date": mtime.strftime("%Y-%m-%d %H:%M:%S")
                })
        return backups
    






    # ============================================================
    # النظام المحاسبي
    # ============================================================
    
    def create_default_accounts(self):
        """إنشاء دليل الحسابات الافتراضي"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM chart_of_accounts")
        if cursor.fetchone()[0] > 0:
            return
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        accounts = [
            ("1001", "الصندوق", "asset", None),
            ("1002", "البنك", "asset", None),
            ("1100", "العملاء", "asset", None),
            ("1200", "المخزون", "asset", None),
            ("1300", "الموردين", "liability", None),
            ("2000", "رأس المال", "liability", None),
            ("2100", "الأرباح المحتجزة", "liability", None),
            ("3001", "المبيعات", "income", None),
            ("3002", "مردودات المبيعات", "income", None),
            ("4001", "المشتريات", "expense", None),
            ("4002", "مردودات المشتريات", "expense", None),
            ("5001", "المصاريف الإدارية", "expense", None),
            ("5002", "الإيجار", "expense", None),
            ("5003", "الرواتب", "expense", None),
            ("5004", "النقل", "expense", None),
            ("5005", "الكهرباء والماء", "expense", None),
        ]
        for code, name, acc_type, parent in accounts:
            cursor.execute("INSERT INTO chart_of_accounts (account_code, account_name, account_type, parent_id, created_at) VALUES (?, ?, ?, ?, ?)",
                           (code, name, acc_type, parent, now))
        self.conn.commit()
    
    def post_journal_entry(self, entry_date: str, description: str, details: List[Dict],
                           reference_type: str = "", reference_id: int = None,
                           user_id: int = None) -> Tuple[bool, str, int]:
        """تسجيل قيد يومي"""
        cursor = self.conn.cursor()
        try:
            self.conn.execute("BEGIN TRANSACTION")
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            entry_no = f"JRN-{datetime.now().strftime('%y%m%d%H%M%S')}"
            
            # التحقق من توازن القيد
            total_debit = sum(d.get('debit', 0) for d in details)
            total_credit = sum(d.get('credit', 0) for d in details)
            if abs(total_debit - total_credit) > 0.01:
                raise Exception(f"القيد غير متوازن: مدين {total_debit} ≠ دائن {total_credit}")
            
            cursor.execute("""
                INSERT INTO journal_entries (entry_no, entry_date, description, reference_type, reference_id, is_posted, created_at, user_id)
                VALUES (?, ?, ?, ?, ?, 1, ?, ?)
            """, (entry_no, entry_date, description, reference_type, reference_id, now, user_id))
            entry_id = cursor.lastrowid
            
            for detail in details:
                cursor.execute("""
                    INSERT INTO journal_details (entry_id, account_id, description, debit, credit)
                    VALUES (?, ?, ?, ?, ?)
                """, (entry_id, detail['account_id'], detail.get('description', ''), detail.get('debit', 0), detail.get('credit', 0)))
            
            self.conn.commit()
            return True, f"تم تسجيل القيد {entry_no}", entry_id
        except Exception as e:
            self.conn.rollback()
            return False, str(e), 0
    
    def get_account_balance(self, account_id: int, start_date: str = None, end_date: str = None) -> float:
        """رصيد حساب"""
        cursor = self.conn.cursor()
        query = "SELECT COALESCE(SUM(debit), 0) - COALESCE(SUM(credit), 0) FROM journal_details WHERE account_id = ?"
        params = [account_id]
        
        if start_date and end_date:
            query += " AND entry_id IN (SELECT id FROM journal_entries WHERE entry_date BETWEEN ? AND ?)"
            params.extend([start_date, end_date])
        
        cursor.execute(query, params)
        return cursor.fetchone()[0]
    
    def get_trial_balance(self, date: str = None) -> List[Dict]:
        """ميزان المراجعة"""
        cursor = self.conn.cursor()
        if date:
            cursor.execute("""
                SELECT a.account_code, a.account_name, a.account_type,
                       COALESCE(SUM(jd.debit), 0) as total_debit,
                       COALESCE(SUM(jd.credit), 0) as total_credit
                FROM chart_of_accounts a
                LEFT JOIN journal_details jd ON a.id = jd.account_id
                LEFT JOIN journal_entries je ON jd.entry_id = je.id
                WHERE je.entry_date <= ? OR je.entry_date IS NULL
                GROUP BY a.id
                ORDER BY a.account_code
            """, (date,))
        else:
            cursor.execute("""
                SELECT a.account_code, a.account_name, a.account_type,
                       COALESCE(SUM(jd.debit), 0) as total_debit,
                       COALESCE(SUM(jd.credit), 0) as total_credit
                FROM chart_of_accounts a
                LEFT JOIN journal_details jd ON a.id = jd.account_id
                GROUP BY a.id
                ORDER BY a.account_code
            """)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_profit_loss(self, start_date: str, end_date: str) -> Dict:
        """قائمة الأرباح والخسائر"""
        cursor = self.conn.cursor()
        
        # الإيرادات
        cursor.execute("""
            SELECT COALESCE(SUM(jd.credit - jd.debit), 0)
            FROM journal_details jd
            JOIN journal_entries je ON jd.entry_id = je.id
            JOIN chart_of_accounts a ON jd.account_id = a.id
            WHERE a.account_type = 'income' AND je.entry_date BETWEEN ? AND ?
        """, (start_date, end_date))
        total_income = cursor.fetchone()[0]
        
        # المصروفات
        cursor.execute("""
            SELECT COALESCE(SUM(jd.debit - jd.credit), 0)
            FROM journal_details jd
            JOIN journal_entries je ON jd.entry_id = je.id
            JOIN chart_of_accounts a ON jd.account_id = a.id
            WHERE a.account_type = 'expense' AND je.entry_date BETWEEN ? AND ?
        """, (start_date, end_date))
        total_expenses = cursor.fetchone()[0]
        
        return {
            "total_income": total_income,
            "total_expenses": total_expenses,
            "net_profit": total_income - total_expenses
        }
    
    def get_account_id_by_code(self, code: str) -> Optional[int]:
        """الحصول على معرف الحساب بالكود"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM chart_of_accounts WHERE account_code = ?", (code,))
        row = cursor.fetchone()
        return row['id'] if row else None
    
    def save_draft(self, cart_items: List[Dict], customer_name: str = "نقدي", 
                   customer_id: int = None, user_id: int = None) -> Tuple[bool, str]:
        """حفظ مسودة فاتورة"""
        cursor = self.conn.cursor()
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            total = sum((item.get('price', item['product'].selling_price) - item.get('discount', 0)) * item['quantity'] for item in cart_items)
            
            cart_data = json.dumps([{
                'product_id': item['product_id'],
                'product_name': item['product'].name,
                'quantity': item['quantity'],
                'price': item.get('selling_price', item['product'].selling_price),
                'discount': item.get('discount', 0),
            } for item in cart_items])
            
            cursor.execute("""
                INSERT INTO draft_invoices (cart_data, customer_name, customer_id, total_amount, created_at, user_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (cart_data, customer_name, customer_id, total, now, user_id))
            self.conn.commit()
            return True, f"✅ تم حفظ المسودة (إجمالي: {total:.2f})"
        except Exception as e:
            return False, f"خطأ: {str(e)}"
    
    def get_drafts(self, user_id: int = None) -> List[Dict]:
        """الحصول على المسودات"""
        cursor = self.conn.cursor()
        if user_id:
            cursor.execute("SELECT * FROM draft_invoices WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        else:
            cursor.execute("SELECT * FROM draft_invoices ORDER BY created_at DESC")
        return [dict(row) for row in cursor.fetchall()]
    
    def get_draft_by_id(self, draft_id: int) -> Optional[Dict]:
        """الحصول على مسودة محددة"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM draft_invoices WHERE id = ?", (draft_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def delete_draft(self, draft_id: int) -> Tuple[bool, str]:
        """حذف مسودة"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("DELETE FROM draft_invoices WHERE id = ?", (draft_id,))
            self.conn.commit()
            return True, "تم حذف المسودة"
        except Exception as e:
            return False, f"خطأ: {str(e)}"

    # ============================================================
    # عمليات الموردين
    # ============================================================
    
    def add_supplier(self, name: str, phone: str = "", email: str = "", address: str = "",
                     company: str = "", tax_number: str = "", notes: str = "") -> Tuple[bool, str, int]:
        """إضافة مورد جديد"""
        cursor = self.conn.cursor()
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO suppliers (name, phone, email, address, company, tax_number, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, phone, email, address, company, tax_number, notes, now))
            self.conn.commit()
            return True, "تم إضافة المورد بنجاح", cursor.lastrowid
        except sqlite3.IntegrityError:
            return False, "المورد موجود مسبقاً", 0
    
    def get_all_suppliers(self) -> List[Dict]:
        """الحصول على جميع الموردين"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM suppliers ORDER BY name")
        return [dict(row) for row in cursor.fetchall()]
    
    def get_supplier_by_id(self, supplier_id: int) -> Optional[Dict]:
        """الحصول على مورد حسب المعرف"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM suppliers WHERE id = ?", (supplier_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_supplier_by_name(self, name: str) -> Optional[Dict]:
        """البحث عن مورد حسب الاسم"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM suppliers WHERE name = ?", (name,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def search_suppliers(self, query: str) -> List[Dict]:
        """البحث عن الموردين"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM suppliers 
            WHERE name LIKE ? OR phone LIKE ? OR company LIKE ?
            ORDER BY name
        """, (f"%{query}%", f"%{query}%", f"%{query}%"))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_supplier_summary(self, supplier_id: int = None) -> Dict:
        """ملخص حساب المورد"""
        cursor = self.conn.cursor()
        if supplier_id:
            cursor.execute("""
                SELECT name, phone, total_debt, total_paid, balance
                FROM suppliers WHERE id = ?
            """, (supplier_id,))
            row = cursor.fetchone()
            if row:
                return {
                    "name": row["name"], "phone": row["phone"],
                    "total_debt": row["total_debt"] or 0,
                    "total_paid": row["total_paid"] or 0,
                    "balance": row["balance"] or 0
                }
        return {"total_debt": 0, "total_paid": 0, "balance": 0}
    
    def get_supplier_ledger(self, supplier_id: int) -> List[Dict]:
        """كشف حساب المورد"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, transaction_date as date, debit, credit, description, balance_after
            FROM supplier_transactions 
            WHERE supplier_id = ? 
            ORDER BY transaction_date DESC, id DESC
        """, (supplier_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def delete_supplier(self, supplier_id: int) -> Tuple[bool, str]:
        """حذف مورد"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("DELETE FROM supplier_payments WHERE supplier_id = ?", (supplier_id,))
            cursor.execute("DELETE FROM supplier_transactions WHERE supplier_id = ?", (supplier_id,))
            cursor.execute("DELETE FROM purchase_items WHERE purchase_id IN (SELECT id FROM purchase_invoices WHERE supplier_id = ?)", (supplier_id,))
            cursor.execute("DELETE FROM purchase_invoices WHERE supplier_id = ?", (supplier_id,))
            cursor.execute("DELETE FROM suppliers WHERE id = ?", (supplier_id,))
            self.conn.commit()
            return True, "تم حذف المورد بنجاح"
        except Exception as e:
            return False, f"خطأ: {str(e)}"
    
    # ============================================================
    # عمليات فواتير الشراء
    # ============================================================
    
    def process_purchase_invoice(self, supplier_id: int, items: List[Dict], 
                                  invoice_date: str, transport_cost: float = 0,
                                  loading_cost: float = 0, unloading_cost: float = 0,
                                  tax: float = 0, customs: float = 0, other_costs: float = 0,
                                  discount: float = 0, paid_amount: float = 0,
                                  due_date: str = "", notes: str = "",
                                  user_id: int = None) -> Tuple[bool, str, Optional[int]]:
                                  
        """معالجة فاتورة الشراء"""
        cursor = self.conn.cursor()
        try:
            self.conn.execute("BEGIN TRANSACTION")
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            supplier = self.get_supplier_by_id(supplier_id)
            if not supplier:
                raise Exception("المورد غير موجود")
            
            # حساب إجمالي المنتجات
            items_total = 0
            for item in items:
                item_subtotal = item['unit_price'] * item['quantity'] * (1 - item.get('discount_percent', 0) / 100)
                items_total += item_subtotal
            
            # حساب الإجمالي النهائي
            total_amount = items_total
            net_total = total_amount - discount + transport_cost + loading_cost + unloading_cost + tax + customs + other_costs
            remaining = net_total - paid_amount
            
            invoice_no = f"PUR-{datetime.now().strftime('%y%m%d%H%M%S')}"
            
            cursor.execute("""
                INSERT INTO purchase_invoices (
                    invoice_no, supplier_id, supplier_name, invoice_date, total_amount,
                    discount, transport_cost, loading_cost, unloading_cost, tax, customs,
                    other_costs, net_total, paid_amount, remaining_amount, payment_status,
                    due_date, notes, created_at, user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                invoice_no, supplier_id, supplier['name'], invoice_date, total_amount,
                discount, transport_cost, loading_cost, unloading_cost, tax, customs,
                other_costs, net_total, paid_amount, remaining,
                'paid' if remaining <= 0 else ('partial' if paid_amount > 0 else 'pending'),
                due_date, notes, now, user_id
            ))
            
            purchase_id = cursor.lastrowid
            
            # إدخال تفاصيل الفاتورة وتحديث المخزون
            for item in items:
                cursor.execute("""
                    INSERT INTO purchase_items (
                        purchase_id, product_id, product_name, quantity, unit_price,
                        discount_percent, subtotal, warehouse
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    purchase_id, item['product_id'], item['product_name'],
                    item['quantity'], item['unit_price'],
                    item.get('discount_percent', 0),
                    item['unit_price'] * item['quantity'] * (1 - item.get('discount_percent', 0) / 100),
                    item.get('warehouse', 'رئيسي')
                ))
                
                # تحديث المخزون
                cursor.execute("""
                    UPDATE products SET quantity = quantity + ?, updated_at = ? WHERE id = ?
                """, (item['quantity'], now, item['product_id']))
                                # ✅ تسجيل الحركة في stock_history
                cursor.execute("""
                    INSERT INTO stock_history (
                        product_id, product_name, operation_type, quantity_change,
                        old_quantity, new_quantity, profit_change, note, created_at, user_id
                    ) VALUES (?, ?, 'add_stock', ?, ?, ?, 0, ?, ?, ?)
                """, (
                    item['product_id'],
                    item['product_name'],
                    item['quantity'],
                    int(item['quantity']) - int(item['quantity']),  # old_quantity
                    int(item['quantity']),  # new_quantity بعد التحديث (تقريبي)
                    f"شراء من {supplier['name']} - فاتورة {invoice_no}",
                    now,
                    user_id
                ))
                # تحديث سعر الشراء في المنتج
                cursor.execute("""
                    UPDATE products SET purchase_price = ? WHERE id = ?
                """, (item['unit_price'], item['product_id']))
                
                # سجل تغير السعر
                cursor.execute("""
                    INSERT INTO price_history (product_id, product_name, old_price, new_price, 
                        supplier_id, supplier_name, purchase_id, changed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (item['product_id'], item['product_name'], 0, item['unit_price'],
                      supplier_id, supplier['name'], purchase_id, now))
            
            # معالجة حساب المورد
            old_balance = 0
            if net_total > 0:
                cursor.execute("SELECT balance FROM suppliers WHERE id = ?", (supplier_id,))
                row = cursor.fetchone()
                old_balance = float(row['balance'] if row and row['balance'] else 0)
                new_balance = old_balance + net_total
                
                # تسجيل الفاتورة كدين
                cursor.execute("""
                    INSERT INTO supplier_transactions (
                        supplier_id, purchase_id, transaction_date, debit, credit, description, balance_after
                    ) VALUES (?, ?, ?, ?, 0, ?, ?)
                """, (supplier_id, purchase_id, invoice_date, net_total,
                      f"فاتورة شراء {invoice_no}", new_balance))
            
            # إذا فيه دفعة
            if paid_amount > 0:
                cursor.execute("SELECT balance FROM suppliers WHERE id = ?", (supplier_id,))
                row = cursor.fetchone()
                old_balance = float(row['balance'] if row and row['balance'] else 0)
                new_balance = old_balance - paid_amount
                
                cursor.execute("""
                    INSERT INTO supplier_transactions (
                        supplier_id, purchase_id, transaction_date, debit, credit, description, balance_after
                    ) VALUES (?, ?, ?, 0, ?, ?, ?)
                """, (supplier_id, purchase_id, invoice_date, paid_amount,
                      f"دفعة للفاتورة {invoice_no}", new_balance))
                
                cursor.execute("""
                    INSERT INTO supplier_payments (supplier_id, supplier_name, purchase_id, amount, payment_date, payment_type, user_id)
                    VALUES (?, ?, ?, ?, ?, 'cash', ?)
                """, (supplier_id, supplier['name'], purchase_id, paid_amount, invoice_date, user_id))
            
            # تحديث رصيد المورد
            final_balance = old_balance + remaining if paid_amount <= 0 else old_balance + net_total - paid_amount
            cursor.execute("""
                UPDATE suppliers SET total_debt = total_debt + ?, total_paid = total_paid + ?, balance = ?
                WHERE id = ?
            """, (net_total, paid_amount, final_balance, supplier_id))

            # ====== تسجيل القيد المحاسبي ======
            purchase_account_id = self.get_account_id_by_code("4001")  # المشتريات
            cash_account_id = self.get_account_id_by_code("1001")      # الصندوق
            supplier_account_id = self.get_account_id_by_code("1300")  # الموردين
            
            if purchase_account_id and supplier_account_id:
                entry_details = []
                
                # المشتريات مدين
                entry_details.append({
                    'account_id': purchase_account_id,
                    'debit': net_total,
                    'credit': 0,
                    'description': f"فاتورة شراء {invoice_no} من {supplier['name']}"
                })
                
                # إذا فيه دفعة، الصندوق دائن
                if paid_amount > 0 and cash_account_id:
                    entry_details.append({
                        'account_id': cash_account_id,
                        'debit': 0,
                        'credit': paid_amount,
                        'description': f"دفعة للمورد {supplier['name']}"
                    })
                
                # المتبقي للمورد (دائن)
                if remaining > 0:
                    entry_details.append({
                        'account_id': supplier_account_id,
                        'debit': 0,
                        'credit': remaining,
                        'description': f"مستحق للمورد {supplier['name']}"
                    })
                
                if entry_details:
                    self.post_journal_entry(invoice_date, f"فاتورة شراء {invoice_no} - {supplier['name']}",
                                           entry_details, "purchase", purchase_id, user_id)

            self.conn.commit()
            self.add_notification("📦 فاتورة شراء", f"تم تسجيل فاتورة الشراء {invoice_no}", "info")
            return True, f"تم حفظ فاتورة الشراء {invoice_no}", purchase_id
            
        except Exception as e:
            try:
                self.conn.rollback()
            except:
                pass
            return False, f"خطأ: {str(e)}", None
        


    def get_low_stock_products(self) -> List[Product]:
        """الحصول على المنتجات المنخفضة المخزون"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM products 
            WHERE quantity <= min_stock_threshold 
            ORDER BY quantity
        """)
        return [self._row_to_product(row) for row in cursor.fetchall()]
    
    def get_purchase_invoices(self, supplier_id: int = None) -> List[Dict]:
        """الحصول على فواتير الشراء"""
        cursor = self.conn.cursor()
        if supplier_id:
            cursor.execute("SELECT * FROM purchase_invoices WHERE supplier_id = ? ORDER BY invoice_date DESC", (supplier_id,))
        else:
            cursor.execute("SELECT * FROM purchase_invoices ORDER BY invoice_date DESC")
        return [dict(row) for row in cursor.fetchall()]
    
    def get_purchase_items(self, purchase_id: int) -> List[Dict]:
        """الحصول على تفاصيل فاتورة الشراء"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM purchase_items WHERE purchase_id = ?", (purchase_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    # ============================================================
    # عمليات سداد الموردين
    # ============================================================
    
    def pay_supplier(self, supplier_id: int, amount: float, payment_type: str = "cash",
                     cheque_number: str = "", note: str = "", purchase_id: int = None,
                     user_id: int = None) -> Tuple[bool, str]:
        """سداد للمورد"""
        cursor = self.conn.cursor()
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            payment_date = datetime.now().strftime("%Y-%m-%d")
            
            supplier = self.get_supplier_by_id(supplier_id)
            if not supplier:
                return False, "المورد غير موجود"
            
            # إذا حدد فاتورة، سددها
            if purchase_id:
                cursor.execute("SELECT * FROM purchase_invoices WHERE id = ?", (purchase_id,))
                invoice = dict(cursor.fetchone())
                if not invoice:
                    return False, "الفاتورة غير موجودة"
                
                new_remaining = invoice['remaining_amount'] - amount
                if new_remaining <= 0:
                    status = 'paid'
                    new_remaining = 0
                else:
                    status = 'partial'
                
                cursor.execute("""
                    UPDATE purchase_invoices SET paid_amount = paid_amount + ?, remaining_amount = ?, payment_status = ?
                    WHERE id = ?
                """, (amount, new_remaining, status, purchase_id))
            
            # تسجيل الدفعة
            cursor.execute("""
                INSERT INTO supplier_payments (supplier_id, supplier_name, purchase_id, amount, payment_date, payment_type, cheque_number, note, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (supplier_id, supplier['name'], purchase_id, amount, payment_date, payment_type, cheque_number, note, user_id))
            
            # تحديث رصيد المورد
            cursor.execute("SELECT balance FROM suppliers WHERE id = ?", (supplier_id,))
            row = cursor.fetchone()
            old_balance = float(row['balance'] if row and row['balance'] else 0)
            new_balance = old_balance - amount
            
            cursor.execute("""
                INSERT INTO supplier_transactions (supplier_id, purchase_id, transaction_date, debit, credit, description, balance_after)
                VALUES (?, ?, ?, 0, ?, ?, ?)
            """, (supplier_id, purchase_id, payment_date, amount, f"سداد: {note}", new_balance))
            
            cursor.execute("""
                UPDATE suppliers SET total_paid = total_paid + ?, balance = ? WHERE id = ?
            """, (amount, new_balance, supplier_id))
            
            self.conn.commit()
            return True, f"✅ تم السداد بنجاح! المبلغ: {amount:.2f}"
        except Exception as e:
            return False, f"خطأ: {str(e)}"
    
    # ============================================================
    # عمليات المرتجعات
    # ============================================================
    
    def return_to_supplier(self, supplier_id: int, purchase_id: int, product_id: int,
                           product_name: str, quantity: int, unit_price: float,
                           reason: str = "", user_id: int = None) -> Tuple[bool, str]:
        """تسجيل مرتجع للمورد"""
        cursor = self.conn.cursor()
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return_date = datetime.now().strftime("%Y-%m-%d")
            return_no = f"RET-{datetime.now().strftime('%y%m%d%H%M%S')}"
            total = quantity * unit_price
            
            supplier = self.get_supplier_by_id(supplier_id)
            
            cursor.execute("""
                INSERT INTO returns_to_supplier (return_no, supplier_id, supplier_name, purchase_id,
                    product_id, product_name, quantity, unit_price, total_amount, reason, return_date, created_at, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (return_no, supplier_id, supplier['name'] if supplier else "", purchase_id,
                  product_id, product_name, quantity, unit_price, total, reason, return_date, now, user_id))
            
            # إنقاص المخزون
            cursor.execute("UPDATE products SET quantity = quantity - ?, updated_at = ? WHERE id = ?",
                           (quantity, now, product_id))
            
            # خصم قيمة المرتجع من دين المورد
            if purchase_id:
                cursor.execute("UPDATE purchase_invoices SET remaining_amount = remaining_amount - ?, net_total = net_total - ? WHERE id = ?",
                               (total, total, purchase_id))
            
            cursor.execute("SELECT balance FROM suppliers WHERE id = ?", (supplier_id,))
            row = cursor.fetchone()
            old_balance = float(row['balance'] if row and row['balance'] else 0)
            new_balance = old_balance - total
            
            cursor.execute("""
                INSERT INTO supplier_transactions (supplier_id, purchase_id, transaction_date, debit, credit, description, balance_after)
                VALUES (?, ?, ?, 0, ?, ?, ?)
            """, (supplier_id, purchase_id, return_date, total, f"مرتجع {return_no}: {reason}", new_balance))
            
            cursor.execute("UPDATE suppliers SET balance = ?, total_debt = total_debt - ? WHERE id = ?",
                           (new_balance, total, supplier_id))
            
            self.conn.commit()
            return True, f"تم تسجيل المرتجع {return_no}"
        except Exception as e:
            return False, f"خطأ: {str(e)}"
    
    # ============================================================
    # تقارير المشتريات
    # ============================================================
    
    def get_purchase_stats(self) -> Dict:
        """إحصائيات المشتريات"""
        cursor = self.conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        
        cursor.execute("SELECT COALESCE(SUM(net_total), 0) FROM purchase_invoices WHERE invoice_date = ?", (today,))
        today_purchases = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM suppliers")
        suppliers_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COALESCE(SUM(balance), 0) FROM suppliers")
        total_payable = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM purchase_invoices WHERE payment_status != 'paid'")
        unpaid_invoices = cursor.fetchone()[0]
        
        return {
            "today_purchases": today_purchases,
            "suppliers_count": suppliers_count,
            "total_payable": total_payable,
            "unpaid_invoices": unpaid_invoices
        }
    
    def get_price_history(self, product_id: int) -> List[Dict]:
        """سجل أسعار الشراء لمنتج"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM price_history WHERE product_id = ? ORDER BY changed_at DESC
        """, (product_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_next_purchase_number(self) -> int:
        """رقم فاتورة الشراء القادم"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT MAX(id) FROM purchase_invoices")
        max_id = cursor.fetchone()[0]
        return (max_id or 0) + 1
    





    # ========== عمليات المنتجات ==========
    
    def add_product(self, product: Product) -> Tuple[bool, str]:
        """إضافة منتج جديد"""
        cursor = self.conn.cursor()
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            product.created_at = now
            product.updated_at = now
            
            cursor.execute("""
                INSERT INTO products (name, barcode, category, purchase_price, selling_price, quantity, created_at, updated_at, min_stock_threshold)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (product.name, product.barcode, product.category, product.purchase_price, product.selling_price, 
                  product.quantity, product.created_at, product.updated_at, product.min_stock_threshold))
            
            product_id = cursor.lastrowid
            self.conn.commit()
            
            self.add_stock_history(
                product_id=product_id,
                product_name=product.name,
                operation_type="create_product",
                quantity_change=product.quantity,
                old_quantity=0,
                new_quantity=product.quantity,
                profit_change=0,
                note=f"تم إضافة منتج جديد: {product.name}"
            )
            
            self.add_notification(
                "📦 منتج جديد",
                f"تم إضافة المنتج: {product.name}",
                "info"
            )
            
            return True, "تم إضافة المنتج بنجاح"
        except Exception as e:
            return False, f"خطأ في إضافة المنتج: {str(e)}"
    
    def get_all_products(self) -> List[Product]:
        """الحصول على جميع المنتجات"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM products ORDER BY name")
        return [self._row_to_product(row) for row in cursor.fetchall()]
    
    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """الحصول على منتج حسب المعرف"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        row = cursor.fetchone()
        return self._row_to_product(row) if row else None
    
    def search_products(self, query: str) -> List[Product]:
        """البحث عن المنتجات"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM products 
            WHERE name LIKE ? OR barcode = ? OR category LIKE ?
            ORDER BY name
        """, (f"%{query}%", query, f"%{query}%"))
        return [self._row_to_product(row) for row in cursor.fetchall()]
    
    def search_products_advanced(self, name: str = "", barcode: str = "", category: str = "", 
                                  min_price: float = None, max_price: float = None,
                                  min_quantity: int = None, max_quantity: int = None) -> List[Product]:
        """بحث متقدم عن المنتجات"""
        cursor = self.conn.cursor()
        query = "SELECT * FROM products WHERE 1=1"
        params = []
        
        if name:
            query += " AND name LIKE ?"
            params.append(f"%{name}%")
        if barcode:
            query += " AND barcode LIKE ?"
            params.append(f"%{barcode}%")
        if category:
            query += " AND category = ?"
            params.append(category)
        if min_price is not None:
            query += " AND selling_price >= ?"
            params.append(min_price)
        if max_price is not None:
            query += " AND selling_price <= ?"
            params.append(max_price)
        if min_quantity is not None:
            query += " AND quantity >= ?"
            params.append(min_quantity)
        if max_quantity is not None:
            query += " AND quantity <= ?"
            params.append(max_quantity)
        
        query += " ORDER BY name"
        cursor.execute(query, params)
        return [self._row_to_product(row) for row in cursor.fetchall()]
    
    def get_categories(self) -> List[str]:
        """الحصول على قائمة التصنيفات"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT category FROM products WHERE category != '' ORDER BY category")
        return [row["category"] for row in cursor.fetchall()]
 




    def update_product(self, product: Product) -> Tuple[bool, str]:
        """تحديث بيانات منتج"""
        cursor = self.conn.cursor()
        try:
            old_product = self.get_product_by_id(product.id)
            if not old_product:
                return False, "المنتج غير موجود"
            
            old_quantity = old_product.quantity
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            cursor.execute("""
                UPDATE products 
                SET name=?, barcode=?, category=?, purchase_price=?, selling_price=?, quantity=?, 
                    updated_at=?, min_stock_threshold=?
                WHERE id=?
            """, (product.name, product.barcode, product.category, product.purchase_price, product.selling_price, 
                  product.quantity, now, product.min_stock_threshold, product.id))
            
            quantity_change = product.quantity - old_quantity
            if quantity_change != 0:
                # ✅ تسجيل مباشر في stock_history
                cursor.execute("""
                    INSERT INTO stock_history (
                        product_id, product_name, operation_type, quantity_change,
                        old_quantity, new_quantity, profit_change, note, created_at, user_id
                    ) VALUES (?, ?, 'edit_product', ?, ?, ?, 0, ?, ?, ?)
                """, (
                    product.id,
                    product.name,
                    quantity_change,
                    old_quantity,
                    product.quantity,
                    f"تعديل كمية المنتج",
                    now,
                    None
                ))
            
            self.conn.commit()
            return True, "تم تحديث المنتج بنجاح"
        except Exception as e:
            return False, f"خطأ في تحديث المنتج: {str(e)}"
    
    def delete_product(self, product_id: int) -> Tuple[bool, str]:
        """حذف منتج"""
        cursor = self.conn.cursor()
        try:
            product = self.get_product_by_id(product_id)
            if not product:
                return False, "المنتج غير موجود"
            
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # ✅ تسجيل الحركة قبل الحذف
            cursor.execute("""
                INSERT INTO stock_history (
                    product_id, product_name, operation_type, quantity_change,
                    old_quantity, new_quantity, profit_change, note, created_at, user_id
                ) VALUES (?, ?, 'delete_product', 0, ?, 0, 0, ?, ?, ?)
            """, (
                product_id,
                product.name,
                product.quantity,
                f"تم حذف المنتج: {product.name}",
                now,
                None
            ))
            
            cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
            self.conn.commit()
            
            return True, "تم حذف المنتج بنجاح"
        except Exception as e:
            return False, f"خطأ في حذف المنتج: {str(e)}"
    
    def add_stock(self, product_id: int, quantity: int) -> Tuple[bool, str]:
        """إضافة كمية جديدة للمخزون"""
        cursor = self.conn.cursor()
        try:
            product = self.get_product_by_id(product_id)
            if not product:
                return False, "المنتج غير موجود"
            
            old_quantity = product.quantity
            new_quantity = old_quantity + quantity
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            cursor.execute("""
                UPDATE products 
                SET quantity = ?, updated_at = ?
                WHERE id = ?
            """, (new_quantity, now, product_id))
            
            # ✅ تسجيل مباشر في stock_history
            cursor.execute("""
                INSERT INTO stock_history (
                    product_id, product_name, operation_type, quantity_change,
                    old_quantity, new_quantity, profit_change, note, created_at, user_id
                ) VALUES (?, ?, 'add_stock', ?, ?, ?, 0, ?, ?, ?)
            """, (
                product_id,
                product.name,
                quantity,
                old_quantity,
                new_quantity,
                f"إضافة {quantity} قطعة إلى المخزون",
                now,
                None
            ))
            
            self.conn.commit()
            return True, f"تم إضافة {quantity} قطعة إلى المخزون"
        except Exception as e:
            return False, f"خطأ في إضافة المخزون: {str(e)}"
    
    # def process_invoice(self, cart_items: List[Dict], customer_id: Optional[int], 
    #                     paid_amount: float, payment_type: str, custom_description: str = "",
    #                     user_id: int = None) -> Tuple[bool, str, Optional[int]]:
    #     """معالجة الفاتورة مع دعم الدفع الجزئي"""
    #     cursor = self.conn.cursor()
    #     try:
    #         self.conn.execute("BEGIN TRANSACTION")
            
    #         now = datetime.now()
    #         now_str = now.strftime("%Y-%m-%d %H:%M:%S")
    #         date_str = now.strftime("%Y-%m-%d")
            
    #         total_amount = 0.0
    #         total_discount = 0.0
    #         total_profit = 0.0
            
    #         processed_items = []
    #         for item in cart_items:
    #             product = self.get_product_by_id(item['product_id'])
    #             if not product:
    #                 raise Exception(f"المنتج غير موجود")
                
    #             if product.quantity < item['quantity']:
    #                 raise Exception(f"الكمية غير كافية: {product.name}")
                
    #             price = float(item.get('price', product.selling_price))
    #             discount = float(item.get('discount', 0.0))
    #             qty = int(item['quantity'])
                
    #             item_total = (price - discount) * qty
    #             item_profit = (price - discount - product.purchase_price) * qty
                
    #             total_amount += item_total
    #             total_discount += discount * qty
    #             total_profit += item_profit
                
    #             processed_items.append({
    #                 'product': product,
    #                 'quantity': qty,
    #                 'price': price,
    #                 'purchase_price': product.purchase_price,
    #                 'subtotal': item_total,
    #                 'profit': item_profit
    #             })

    #         total_amount = float(total_amount)
    #         total_discount = float(total_discount)
    #         total_profit = float(total_profit)
    #         paid_amount = float(paid_amount if paid_amount else 0.0)
            
    #         customer_name = "نقدي"
    #         if customer_id:
    #             customer = self.get_customer_by_id(customer_id)
    #             if customer:
    #                 customer_name = str(customer.get('name', 'نقدي'))

    #         remaining_amount = max(0.0, total_amount - paid_amount)
    #         invoice_no = f"INV-{now.strftime('%y%m%d%H%M%S')}"
            
    #         # إدخال رأس الفاتورة
    #         cursor.execute("""
    #             INSERT INTO sales (
    #                 invoice_no, customer_id, customer_name, total_amount, discount, 
    #                 paid_amount, remaining_amount, payment_type, profit, sale_date, created_at, user_id
    #             ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    #         """, (
    #             str(invoice_no),
    #             int(customer_id) if customer_id else None,
    #             str(customer_name),
    #             total_amount,
    #             total_discount,
    #             paid_amount,
    #             remaining_amount,
    #             str(payment_type),
    #             total_profit,
    #             str(date_str),
    #             str(now_str),
    #             int(user_id) if user_id else None
    #         ))
            
    #         sale_id = cursor.lastrowid

    #         # إدخال تفاصيل الفاتورة وتحديث المخزون
    #         for item in processed_items:
    #             cursor.execute("""
    #                 INSERT INTO sale_items (
    #                     sale_id, product_id, product_name, quantity, price, 
    #                     purchase_price, subtotal, profit
    #                 ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    #             """, (
    #                 int(sale_id),
    #                 int(item['product'].id),
    #                 str(item['product'].name),
    #                 int(item['quantity']),
    #                 float(item['price']),
    #                 float(item['purchase_price']),
    #                 float(item['subtotal']),
    #                 float(item['profit'])
    #             ))
                
    #             # تحديث المخزون
    #             old_qty = int(item['product'].quantity)
    #             new_qty = old_qty - int(item['quantity'])
    #             cursor.execute("""
    #                 UPDATE products SET quantity = ?, updated_at = ? WHERE id = ?
    #             """, (new_qty, now_str, int(item['product'].id)))

             
    #         # ====== معالجة حساب العميل (للبيع الآجل) ======
    #         if customer_id:
    #             if paid_amount > 0:
    #                 cursor.execute("SELECT balance FROM customers WHERE id = ?", (int(customer_id),))
    #                 row = cursor.fetchone()
    #                 old_balance = float(row['balance'] if row and row['balance'] else 0)
    #                 new_balance = old_balance - paid_amount
                    
    #                 cursor.execute("""
    #                     INSERT INTO customer_transactions (
    #                         customer_id, sale_id, transaction_date, debit, credit, description, balance_after
    #                     ) VALUES (?, ?, ?, 0, ?, ?, ?)
    #                 """, (
    #                     int(customer_id),
    #                     int(sale_id),
    #                     str(date_str),
    #                     paid_amount,
    #                     f"دفعة مقدمة للفاتورة {invoice_no}",
    #                     new_balance
    #                 ))
                    
    #                 cursor.execute("""
    #                     UPDATE customers SET total_paid = total_paid + ?, balance = ? WHERE id = ?
    #                 """, (paid_amount, new_balance, int(customer_id)))
                    
    #                 # ✅ تسجيل حركة السداد
    #                 cursor.execute("""
    #                     INSERT INTO stock_history (
    #                         product_id, product_name, operation_type, quantity_change,
    #                         old_quantity, new_quantity, profit_change, note, created_at, user_id
    #                     ) VALUES (0, ?, 'payment', 0, 0, 0, 0, ?, ?, ?)
    #                 """, (
    #                     str(customer_name),
    #                     f"دفعة مقدمة {paid_amount:.2f} للفاتورة {invoice_no}",
    #                     str(now_str),
    #                     int(user_id) if user_id else None
    #                 ))
                
    #             if remaining_amount > 0:
    #                 cursor.execute("SELECT balance FROM customers WHERE id = ?", (int(customer_id),))
    #                 row = cursor.fetchone()
    #                 old_balance = float(row['balance'] if row and row['balance'] else 0)
    #                 new_balance = old_balance + remaining_amount
                    
    #                 cursor.execute("""
    #                     INSERT INTO customer_transactions (
    #                         customer_id, sale_id, transaction_date, debit, credit, description, balance_after
    #                     ) VALUES (?, ?, ?, ?, 0, ?, ?)
    #                 """, (
    #                     int(customer_id),
    #                     int(sale_id),
    #                     str(date_str),
    #                     remaining_amount,
    #                     f"دين الفاتورة {invoice_no} - {custom_description}",
    #                     new_balance
    #                 ))
                    
    #                 cursor.execute("""
    #                     UPDATE customers SET balance = ?, total_debt = total_debt + ? WHERE id = ?
    #                 """, (new_balance, remaining_amount, int(customer_id)))
                    
    #                 # ✅ تسجيل حركة الدين
    #                 # cursor.execute("""
    #                 #     INSERT INTO stock_history (
    #                 #         product_id, product_name, operation_type, quantity_change,
    #                 #         old_quantity, new_quantity, profit_change, note, created_at, user_id
    #                 #     ) VALUES (0, ?, 'add_debt', 0, 0, 0, 0, ?, ?, ?)
    #                 # """, (
    #                 #     str(customer_name),
    #                 #     f"دين متبقي {remaining_amount:.2f} للفاتورة {invoice_no}",
    #                 #     str(now_str),
    #                 #     int(user_id) if user_id else None
    #                 # ))

    #         self.conn.commit()
    #         self.check_low_stock_notifications()
            
    #         return True, f"تم حفظ الفاتورة {invoice_no} بنجاح", sale_id
            
    #     except Exception as e:
    #         try:
    #             self.conn.rollback()
    #         except:
    #             pass
    #         return False, f"خطأ في معالجة الفاتورة: {str(e)}", None
        


    def process_invoice(self, cart_items: List[Dict], customer_id: Optional[int], 
                        paid_amount: float, payment_type: str, custom_description: str = "",
                        user_id: int = None) -> Tuple[bool, str, Optional[int]]:
        """معالجة الفاتورة مع دعم الدفع الجزئي"""
        cursor = self.conn.cursor()
        try:
            self.conn.execute("BEGIN TRANSACTION")
            
            now = datetime.now()
            now_str = now.strftime("%Y-%m-%d %H:%M:%S")
            date_str = now.strftime("%Y-%m-%d")
            
            total_amount = 0.0
            total_discount = 0.0
            total_profit = 0.0
            
            processed_items = []
            for item in cart_items:
                product = self.get_product_by_id(item['product_id'])
                if not product:
                    raise Exception(f"المنتج غير موجود")
                
                if product.quantity < item['quantity']:
                    raise Exception(f"الكمية غير كافية: {product.name}")
                
                price = float(item.get('price', product.selling_price))
                discount = float(item.get('discount', 0.0))
                qty = int(item['quantity'])
                
                item_total = (price - discount) * qty
                item_profit = (price - discount - product.purchase_price) * qty
                
                total_amount += item_total
                total_discount += discount * qty
                total_profit += item_profit
                
                processed_items.append({
                    'product': product,
                    'quantity': qty,
                    'price': price,
                    'purchase_price': product.purchase_price,
                    'subtotal': item_total,
                    'profit': item_profit
                })

            total_amount = float(total_amount)
            total_discount = float(total_discount)
            total_profit = float(total_profit)
            paid_amount = float(paid_amount if paid_amount else 0.0)
            
            customer_name = "نقدي"
            if customer_id:
                customer = self.get_customer_by_id(customer_id)
                if customer:
                    customer_name = str(customer.get('name', 'نقدي'))

            remaining_amount = max(0.0, total_amount - paid_amount)
            invoice_no = f"INV-{now.strftime('%y%m%d%H%M%S')}"
            
            # إدخال رأس الفاتورة
            cursor.execute("""
                INSERT INTO sales (
                    invoice_no, customer_id, customer_name, total_amount, discount, 
                    paid_amount, remaining_amount, payment_type, profit, sale_date, created_at, user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(invoice_no),
                int(customer_id) if customer_id else None,
                str(customer_name),
                total_amount,
                total_discount,
                paid_amount,
                remaining_amount,
                str(payment_type),
                total_profit,
                str(date_str),
                str(now_str),
                int(user_id) if user_id else None
            ))
            
            sale_id = cursor.lastrowid

            # إدخال تفاصيل الفاتورة وتحديث المخزون
            for item in processed_items:
                cursor.execute("""
                    INSERT INTO sale_items (
                        sale_id, product_id, product_name, quantity, price, 
                        purchase_price, subtotal, profit
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    int(sale_id),
                    int(item['product'].id),
                    str(item['product'].name),
                    int(item['quantity']),
                    float(item['price']),
                    float(item['purchase_price']),
                    float(item['subtotal']),
                    float(item['profit'])
                ))
                
                # تحديث المخزون
                old_qty = int(item['product'].quantity)
                new_qty = old_qty - int(item['quantity'])
                cursor.execute("""
                    UPDATE products SET quantity = ?, updated_at = ? WHERE id = ?
                """, (new_qty, now_str, int(item['product'].id)))

                # ✅ تسجيل الحركة في stock_history مع تفاصيل المنتج
                note_text = f"بيع {item['product'].name} ({item['quantity']} قطعة × {item['price']:.2f}) = {item['subtotal']:.2f} - فاتورة {invoice_no}"
                cursor.execute("""
                    INSERT INTO stock_history (
                        product_id, product_name, operation_type, quantity_change,
                        old_quantity, new_quantity, profit_change, note, created_at, user_id
                    ) VALUES (?, ?, 'sell', ?, ?, ?, ?, ?, ?, ?)
                """, (
                    int(item['product'].id),
                    str(item['product'].name),
                    int(-item['quantity']),
                    old_qty,
                    new_qty,
                    float(item['profit']),
                    note_text,
                    str(now_str),
                    int(user_id) if user_id else None
                ))

            # ====== معالجة حساب العميل (للبيع الآجل) ======
            if customer_id:
                if paid_amount > 0:
                    cursor.execute("SELECT balance FROM customers WHERE id = ?", (int(customer_id),))
                    row = cursor.fetchone()
                    old_balance = float(row['balance'] if row and row['balance'] else 0)
                    new_balance = old_balance - paid_amount
                    
                    cursor.execute("""
                        INSERT INTO customer_transactions (
                            customer_id, sale_id, transaction_date, debit, credit, description, balance_after
                        ) VALUES (?, ?, ?, 0, ?, ?, ?)
                    """, (
                        int(customer_id),
                        int(sale_id),
                        str(date_str),
                        paid_amount,
                        f"دفعة مقدمة للفاتورة {invoice_no}",
                        new_balance
                    ))
                    
                    cursor.execute("""
                        UPDATE customers SET total_paid = total_paid + ?, balance = ? WHERE id = ?
                    """, (paid_amount, new_balance, int(customer_id)))
                    
                    # ✅ تسجيل حركة السداد
                    cursor.execute("""
                        INSERT INTO stock_history (
                            product_id, product_name, operation_type, quantity_change,
                            old_quantity, new_quantity, profit_change, note, created_at, user_id
                        ) VALUES (0, ?, 'payment', 0, 0, 0, 0, ?, ?, ?)
                    """, (
                        str(customer_name),
                        f"دفعة {paid_amount:.2f} من {customer_name} - فاتورة {invoice_no}",
                        str(now_str),
                        int(user_id) if user_id else None
                    ))
                
                if remaining_amount > 0:
                    cursor.execute("SELECT balance FROM customers WHERE id = ?", (int(customer_id),))
                    row = cursor.fetchone()
                    old_balance = float(row['balance'] if row and row['balance'] else 0)
                    new_balance = old_balance + remaining_amount
                    
                    cursor.execute("""
                        INSERT INTO customer_transactions (
                            customer_id, sale_id, transaction_date, debit, credit, description, balance_after
                        ) VALUES (?, ?, ?, ?, 0, ?, ?)
                    """, (
                        int(customer_id),
                        int(sale_id),
                        str(date_str),
                        remaining_amount,
                        f"دين الفاتورة {invoice_no} - {custom_description}",
                        new_balance
                    ))
                    
                    cursor.execute("""
                        UPDATE customers SET balance = ?, total_debt = total_debt + ? WHERE id = ?
                    """, (new_balance, remaining_amount, int(customer_id)))
                    
                    # ⚠️ تم تعطيل تسجيل add_debt هنا لأنه يتسجل في add_debt()

            self.conn.commit()
            self.check_low_stock_notifications()
            
            return True, f"تم حفظ الفاتورة {invoice_no} بنجاح", sale_id
            
        except Exception as e:
            try:
                self.conn.rollback()
            except:
                pass
            return False, f"خطأ في معالجة الفاتورة: {str(e)}", None

    def get_sales_by_date(self, date: str = None) -> List[Dict]:
        """الحصول على المبيعات حسب التاريخ"""
        cursor = self.conn.cursor()
        if date:
            cursor.execute("SELECT * FROM sales WHERE sale_date = ? ORDER BY id DESC", (date,))
        else:
            cursor.execute("SELECT * FROM sales ORDER BY id DESC")
        return [dict(row) for row in cursor.fetchall()]
    
    def get_sales_between_dates(self, start_date: str, end_date: str) -> List[Dict]:
        """الحصول على المبيعات بين تاريخين"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM sales WHERE sale_date BETWEEN ? AND ? ORDER BY sale_date DESC
        """, (start_date, end_date))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_sale_items(self, sale_id: int) -> List[Dict]:
        """الحصول على تفاصيل فاتورة"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT si.*, p.unit FROM sale_items si
            LEFT JOIN products p ON si.product_id = p.id
            WHERE si.sale_id = ?
        """, (sale_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    # ========== عمليات العملاء ==========
    
    def add_customer(self, name: str, phone: str = "", email: str = "", address: str = "", notes: str = "") -> Tuple[bool, str, int]:
        """إضافة عميل جديد"""
        cursor = self.conn.cursor()
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO customers (name, phone, email, address, notes, created_at, total_debt, total_paid)
                VALUES (?, ?, ?, ?, ?, ?, 0, 0)
            """, (name, phone, email, address, notes, now))
            self.conn.commit()
            customer_id = cursor.lastrowid
            return True, "تم إضافة العميل بنجاح", customer_id
        except sqlite3.IntegrityError:
            return False, "العميل موجود مسبقاً", 0
    
    def get_all_customers(self) -> List[Dict]:
        """الحصول على جميع العملاء"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM customers ORDER BY name")
        return [dict(row) for row in cursor.fetchall()]
    
    def get_customer_by_id(self, customer_id: int) -> Optional[Dict]:
        """الحصول على عميل حسب المعرف"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_customer_by_name(self, name: str) -> Optional[Dict]:
        """البحث عن عميل حسب الاسم"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM customers WHERE name = ?", (name,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def search_customers(self, query: str) -> List[Dict]:
        """البحث عن العملاء"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM customers 
            WHERE name LIKE ? OR phone LIKE ? OR email LIKE ?
            ORDER BY name
        """, (f"%{query}%", f"%{query}%", f"%{query}%"))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_customer_summary(self, customer_id: int = None) -> Dict:
        """الحصول على ملخص العميل"""
        cursor = self.conn.cursor()
        if customer_id:
            cursor.execute("""
                SELECT name, phone, email, total_debt, total_paid, balance
                FROM customers WHERE id = ?
            """, (customer_id,))
            row = cursor.fetchone()
            if row:
                return {
                    "name": row["name"],
                    "phone": row["phone"],
                    "email": row["email"],
                    "total_debt": row["total_debt"] or 0,
                    "total_paid": row["total_paid"] or 0,
                    "balance": row["balance"] or 0
                }
        return {"total_debt": 0, "total_paid": 0, "balance": 0}
    
    # ========== عمليات الديون ==========
    
    def add_debt(self, customer_id: int, customer_name: str, sale_id: int, 
                 amount: float, note: str = "", due_date: str = "") -> Tuple[bool, str]:
        """تسجيل دين جديد"""
        cursor = self.conn.cursor()
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if not due_date:
                due_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
            
            cursor.execute("""
                INSERT INTO debts (customer_id, customer_name, sale_id, amount, remaining, status, created_at, note, due_date)
                VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, ?)
            """, (customer_id, customer_name, sale_id, amount, amount, now, note, due_date))
            
            # ✅ تسجيل الحركة في stock_history
            cursor.execute("""
                INSERT INTO stock_history (
                    product_id, product_name, operation_type, quantity_change,
                    old_quantity, new_quantity, profit_change, note, created_at, user_id
                ) VALUES (0, ?, 'add_debt', 0, 0, 0, 0, ?, ?, ?)
            """, (
                customer_name,
                f"تسجيل دين بقيمة {amount:.2f}",
                now,
                None
            ))
            
            self.conn.commit()
            
            self.add_notification(
                "💰 دين جديد",
                f"تم تسجيل دين جديد للعميل {customer_name} بقيمة {amount:.2f}",
                "warning"
            )
            
            return True, "تم تسجيل الدين بنجاح"
        except Exception as e:
            return False, f"خطأ: {str(e)}"



    def get_customer_debts(self, customer_id: int = None) -> List[Dict]:
        """الحصول على الديون"""
        cursor = self.conn.cursor()
        if customer_id:
            cursor.execute("""
                SELECT * FROM debts WHERE customer_id = ? AND status != 'paid' ORDER BY created_at DESC
            """, (customer_id,))
        else:
            cursor.execute("""
                SELECT * FROM debts WHERE status != 'paid' ORDER BY created_at DESC
            """)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_customer_ledger(self, customer_id: int) -> List[Dict]:
        """الحصول على كشف حساب العميل"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, transaction_date as date, debit, credit, description, balance_after
            FROM customer_transactions 
            WHERE customer_id = ? 
            ORDER BY transaction_date DESC, id DESC
        """, (customer_id,))
        return [dict(row) for row in cursor.fetchall()]
    




    def make_payment(self, customer_id: int, customer_name: str, debt_id: int = None, amount: float = None, note: str = "", user_id: int = None) -> Tuple[bool, str]:
        """تسجيل سداد - يقبل أي مبلغ (حتى لو أكثر من الدين)"""
        cursor = self.conn.cursor()
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            payment_date = datetime.now().strftime("%Y-%m-%d")
            
            total_paid = 0
            extra_amount = 0
            
            if debt_id:
                cursor.execute("SELECT * FROM debts WHERE id = ?", (debt_id,))
                debt = dict(cursor.fetchone())
                if not debt:
                    return False, "الدين غير موجود"
                
                if amount is None or amount >= debt['remaining']:
                    paid_amount = debt['remaining']
                    extra_amount = amount - debt['remaining'] if amount else 0
                    new_remaining = 0
                    status = 'paid'
                else:
                    paid_amount = amount
                    extra_amount = 0
                    new_remaining = debt['remaining'] - amount
                    status = 'partial'
                
                cursor.execute("UPDATE debts SET remaining = ?, status = ? WHERE id = ?", 
                            (new_remaining, status, debt_id))
                cursor.execute("""
                    INSERT INTO payments (customer_id, customer_name, debt_id, amount, payment_date, payment_type, note, user_id)
                    VALUES (?, ?, ?, ?, ?, 'cash', ?, ?)
                """, (customer_id, customer_name, debt_id, amount, payment_date, note, user_id))
                
                # تسجيل الحركة في customer_transactions
                cursor.execute("SELECT balance FROM customers WHERE id = ?", (customer_id,))
                row = cursor.fetchone()
                old_balance = float(row['balance'] if row and row['balance'] else 0)
                new_balance = old_balance - amount
                
                cursor.execute("""
                    INSERT INTO customer_transactions (
                        customer_id, transaction_date, debit, credit, description, balance_after
                    ) VALUES (?, ?, 0, ?, ?, ?)
                """, (customer_id, payment_date, amount, f"سداد دين #{debt_id}: {note}", new_balance))
                
                total_paid = amount
                
            else:
                cursor.execute("SELECT COALESCE(SUM(remaining), 0) as total FROM debts WHERE customer_id = ? AND status != 'paid'", (customer_id,))
                total_remaining = cursor.fetchone()['total']
                
                if total_remaining > 0:
                    cursor.execute("""
                        SELECT * FROM debts WHERE customer_id = ? AND status != 'paid' ORDER BY created_at
                    """, (customer_id,))
                    debts = [dict(row) for row in cursor.fetchall()]
                    remaining_to_pay = min(amount, total_remaining)
                    extra_amount = amount - remaining_to_pay
                    
                    for debt in debts:
                        if remaining_to_pay <= 0:
                            break
                        
                        if remaining_to_pay >= debt['remaining']:
                            paid = debt['remaining']
                            remaining_to_pay -= paid
                            new_remaining = 0
                            status = 'paid'
                        else:
                            paid = remaining_to_pay
                            new_remaining = debt['remaining'] - remaining_to_pay
                            status = 'partial'
                            remaining_to_pay = 0
                        
                        cursor.execute("UPDATE debts SET remaining = ?, status = ? WHERE id = ?", 
                                    (new_remaining, status, debt['id']))
                        cursor.execute("""
                            INSERT INTO payments (customer_id, customer_name, debt_id, amount, payment_date, payment_type, note, user_id)
                            VALUES (?, ?, ?, ?, ?, 'cash', ?, ?)
                        """, (customer_id, customer_name, debt['id'], paid, payment_date, note, user_id))
                        
                        total_paid += paid
                else:
                    extra_amount = amount
                
                # تسجيل الحركة في customer_transactions
                cursor.execute("SELECT balance FROM customers WHERE id = ?", (customer_id,))
                row = cursor.fetchone()
                old_balance = float(row['balance'] if row and row['balance'] else 0)
                new_balance = old_balance - amount
                
                cursor.execute("""
                    INSERT INTO customer_transactions (
                        customer_id, transaction_date, debit, credit, description, balance_after
                    ) VALUES (?, ?, 0, ?, ?, ?)
                """, (customer_id, payment_date, amount, f"سداد: {note}", new_balance))
            
            # تحديث العميل
            cursor.execute("UPDATE customers SET total_paid = total_paid + ?, balance = balance - ? WHERE id = ?", 
                        (total_paid + extra_amount, total_paid + extra_amount, customer_id))

            # ✅ تسجيل الحركة في stock_history
            cursor.execute("""
                INSERT INTO stock_history (
                    product_id, product_name, operation_type, quantity_change,
                    old_quantity, new_quantity, profit_change, note, created_at, user_id
                ) VALUES (0, ?, 'payment', 0, 0, 0, 0, ?, ?, ?)
            """, (
                customer_name,
                f"سداد بقيمة {amount:.2f} - {note}" if note else f"سداد بقيمة {amount:.2f}",
                now,
                user_id
            ))
            
            self.conn.commit()
            
            # رسالة توضيحية
            msg = f"✅ تم السداد بنجاح! المبلغ: {amount:.2f}"
            if total_paid > 0 and extra_amount > 0:
                msg += f"\n💰 سدد الدين: {total_paid:.2f}"
                msg += f"\n📥 باقي للعميل (أمانة): {extra_amount:.2f}"
            elif extra_amount > 0:
                msg += f"\n📥 المبلغ كامل أمانة للعميل: {extra_amount:.2f}"
            
            self.add_notification("✅ سداد", msg, "success")
            return True, msg
            
        except Exception as e:
            return False, f"❌ خطأ: {str(e)}"



    def get_debts_by_date_range(self, start_date: str, end_date: str) -> List[Dict]:
        """الحصول على الديون في نطاق زمني"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM debts WHERE created_at BETWEEN ? AND ? ORDER BY created_at DESC
        """, (start_date, end_date))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_overdue_debts(self) -> List[Dict]:
        """الحصول على الديون المتأخرة"""
        cursor = self.conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("""
            SELECT * FROM debts WHERE status != 'paid' AND due_date < ? ORDER BY due_date
        """, (today,))
        return [dict(row) for row in cursor.fetchall()]
    
    def add_expense(self, title: str, amount: float, category: str = "عام", note: str = "", user_id: int = None) -> Tuple[bool, str]:
        """إضافة مصروف"""
        cursor = self.conn.cursor()
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            expense_date = datetime.now().strftime("%Y-%m-%d")
            
            cursor.execute("""
                INSERT INTO expenses (title, amount, category, expense_date, note, user_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (title, amount, category, expense_date, note, user_id))
            
            # ✅ تسجيل الحركة في stock_history
            cursor.execute("""
                INSERT INTO stock_history (
                    product_id, product_name, operation_type, quantity_change,
                    old_quantity, new_quantity, profit_change, note, created_at, user_id
                ) VALUES (0, ?, 'expense', 0, 0, 0, ?, ?, ?, ?)
            """, (
                title,
                -amount,
                f"مصروف: {title} بقيمة {amount:.2f}" + (f" - {note}" if note else ""),
                now,
                user_id
            ))
            
            self.conn.commit()
            return True, "تم تسجيل المصروف بنجاح"
        except Exception as e:
            return False, f"خطأ: {str(e)}"
    
    def get_expenses(self, start_date: str = None, end_date: str = None, category: str = None) -> List[Dict]:
        """الحصول على المصروفات"""
        cursor = self.conn.cursor()
        query = "SELECT * FROM expenses WHERE 1=1"
        params = []
        
        if start_date and end_date:
            query += " AND expense_date BETWEEN ? AND ?"
            params.extend([start_date, end_date])
        if category:
            query += " AND category = ?"
            params.append(category)
        
        query += " ORDER BY expense_date DESC"
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_expense_categories(self) -> List[str]:
        """الحصول على تصنيفات المصروفات"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT category FROM expenses ORDER BY category")
        return [row["category"] for row in cursor.fetchall()]
    
    def delete_expense(self, expense_id: int) -> Tuple[bool, str]:
        """حذف مصروف"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
            self.conn.commit()
            return True, "تم حذف المصروف بنجاح"
        except Exception as e:
            return False, f"خطأ: {str(e)}"
    
    # ========== التقارير والإحصائيات المتقدمة ==========
    
    def get_dashboard_stats(self) -> Dict:
        """إحصائيات لوحة التحكم"""
        cursor = self.conn.cursor()
        
        # إحصائيات اليوم
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("""
            SELECT COALESCE(SUM(total_amount), 0) as sales, COALESCE(SUM(profit), 0) as profit, COUNT(*) as count
            FROM sales WHERE sale_date = ?
        """, (today,))
        today_stats = dict(cursor.fetchone())
        
        # إحصائيات الأسبوع
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        cursor.execute("""
            SELECT COALESCE(SUM(total_amount), 0) as sales, COALESCE(SUM(profit), 0) as profit, COUNT(*) as count
            FROM sales WHERE sale_date BETWEEN ? AND ?
        """, (week_ago, today))
        week_stats = dict(cursor.fetchone())
        
        # إحصائيات الشهر
        month_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        cursor.execute("""
            SELECT COALESCE(SUM(total_amount), 0) as sales, COALESCE(SUM(profit), 0) as profit, COUNT(*) as count
            FROM sales WHERE sale_date BETWEEN ? AND ?
        """, (month_ago, today))
        month_stats = dict(cursor.fetchone())
        
        cursor.execute("SELECT COUNT(*) FROM products")
        products_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM customers")
        customers_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COALESCE(SUM(remaining), 0) FROM debts WHERE status != 'paid'")
        total_debts = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM products WHERE quantity <= min_stock_threshold")
        low_stock_count = cursor.fetchone()[0]
        
        return {
            "today": today_stats,
            "week": week_stats,
            "month": month_stats,
            "products_count": products_count,
            "customers_count": customers_count,
            "total_debts": total_debts,
            "low_stock_count": low_stock_count
        }
    
    def get_sales_chart_data(self, days: int = 30) -> List[Dict]:
        """بيانات الرسم البياني للمبيعات"""
        cursor = self.conn.cursor()
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        cursor.execute("""
            SELECT sale_date, COALESCE(SUM(total_amount), 0) as total, COALESCE(SUM(profit), 0) as profit, COUNT(*) as count
            FROM sales 
            WHERE sale_date >= ?
            GROUP BY sale_date
            ORDER BY sale_date
        """, (start_date,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_top_products(self, limit: int = 10) -> List[Dict]:
        """أكثر المنتجات مبيعاً"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT product_name, SUM(quantity) as total_qty, SUM(profit) as total_profit
            FROM sale_items
            GROUP BY product_id
            ORDER BY total_qty DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_top_customers(self, limit: int = 10) -> List[Dict]:
        """أكثر العملاء تعاملاً"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT customer_name, COUNT(*) as visits, COALESCE(SUM(total_amount), 0) as total_spent
            FROM sales
            WHERE customer_name != 'نقدي'
            GROUP BY customer_id
            ORDER BY total_spent DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_product_statistics(self, product_id: int) -> Dict:
        """إحصائيات منتج"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COALESCE(SUM(quantity), 0) as total_sold, COALESCE(SUM(profit), 0) as total_profit
            FROM sale_items WHERE product_id = ?
        """, (product_id,))
        stats = dict(cursor.fetchone())
        
        cursor.execute("""
            SELECT created_at, quantity_change, note FROM stock_history 
            WHERE product_id = ? AND operation_type = 'add_stock'
            ORDER BY created_at DESC
        """, (product_id,))
        stock_history = [dict(row) for row in cursor.fetchall()]
        
        return {
            "total_sold": stats["total_sold"] or 0,
            "total_profit": stats["total_profit"] or 0,
            "stock_history": stock_history
        }
    
    def get_overall_profit_loss(self) -> Dict:
        """إجمالي الأرباح والخسائر"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COALESCE(SUM(profit), 0) FROM sales")
        total_profit = cursor.fetchone()[0]
        
        cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses")
        total_expenses = cursor.fetchone()[0]
        
        cursor.execute("SELECT COALESCE(SUM(purchase_price * quantity), 0) FROM products")
        inventory_value = cursor.fetchone()[0]
        
        cursor.execute("SELECT COALESCE(SUM(remaining), 0) FROM debts WHERE status != 'paid'")
        total_debts = cursor.fetchone()[0]
        
        return {
            "total_profit": total_profit,
            "total_expenses": total_expenses,
            "net_profit": total_profit - total_expenses,
            "inventory_value": inventory_value,
            "total_debts": total_debts
        }
    
    def get_yearly_report(self, year: int = None) -> Dict:
        """تقرير سنوي"""
        if year is None:
            year = datetime.now().year
        
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT strftime('%m', sale_date) as month,
                COALESCE(SUM(profit), 0) as total_profit,
                COUNT(*) as total_sales,
                COALESCE(SUM(total_amount), 0) as total_revenue
            FROM sales 
            WHERE strftime('%Y', sale_date) = ?
            GROUP BY strftime('%m', sale_date)
            ORDER BY month
        """, (str(year),))
        monthly_data = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute("""
            SELECT COALESCE(SUM(profit), 0) as year_profit,
                COUNT(*) as year_sales,
                COALESCE(SUM(total_amount), 0) as year_revenue
            FROM sales WHERE strftime('%Y', sale_date) = ?
        """, (str(year),))
        summary = dict(cursor.fetchone())
        
        return {
            "year": year,
            "monthly_data": monthly_data,
            "summary": summary
        }
    
    def get_stock_history(self, product_id: int = None, limit: int = 100) -> List[StockHistory]:
        """الحصول على سجل الحركات"""
        cursor = self.conn.cursor()
        if product_id:
            cursor.execute("""
                SELECT * FROM stock_history WHERE product_id = ? ORDER BY created_at DESC LIMIT ?
            """, (product_id, limit))
        else:
            cursor.execute("""
                SELECT * FROM stock_history ORDER BY created_at DESC LIMIT ?
            """, (limit,))
        return [self._row_to_history(row) for row in cursor.fetchall()]
    
    def get_detailed_product_history(self, product_id: int) -> Dict:
        """سجل كامل لمنتج"""
        product = self.get_product_by_id(product_id)
        if not product:
            return None
        
        history = self.get_stock_history(product_id, limit=1000)
        statistics = self.get_product_statistics(product_id)
        
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM sales s JOIN sale_items si ON s.id = si.sale_id
            WHERE si.product_id = ? ORDER BY s.sale_date DESC LIMIT 50
        """, (product_id,))
        sales = [dict(row) for row in cursor.fetchall()]
        
        return {
            "product": product,
            "sales": sales,
            "history": history,
            "statistics": statistics
        }
    
    def get_next_invoice_number(self) -> int:
        """الحصول على رقم الفاتورة القادم"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT MAX(id) FROM sales")
        max_id = cursor.fetchone()[0]
        return (max_id or 0) + 1
    
    # ========== دوال مساعدة ==========
    
    def _row_to_product(self, row) -> Product:
        """تحويل صف إلى كائن Product"""
        if row is None:
            return None
        return Product(
            id=row["id"], name=row["name"], barcode=row["barcode"] or "",
            category=row["category"] or "عام", purchase_price=row["purchase_price"],
            selling_price=row["selling_price"], quantity=row["quantity"],
            created_at=row["created_at"], updated_at=row["updated_at"],
            min_stock_threshold=row["min_stock_threshold"] or 5,
            unit=dict(row).get("unit", "حبة")
        )
    
    def _row_to_history(self, row) -> StockHistory:
        """تحويل صف إلى كائن StockHistory"""
        if row is None:
            return None
        return StockHistory(
            id=row["id"], product_id=row["product_id"],
            product_name=row["product_name"], operation_type=row["operation_type"],
            quantity_change=row["quantity_change"], old_quantity=row["old_quantity"],
            new_quantity=row["new_quantity"], profit_change=row["profit_change"] or 0.0,
            note=row["note"] or "", created_at=row["created_at"]
        )
    
    def add_stock_history(self, product_id: int, product_name: str, operation_type: str,
                          quantity_change: int, old_quantity: int, new_quantity: int,
                          profit_change: float, note: str, user_id: int = None):
        """إضافة سجل حركة"""
        cursor = self.conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO stock_history (product_id, product_name, operation_type, quantity_change, 
                old_quantity, new_quantity, profit_change, note, created_at, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (product_id, product_name, operation_type, quantity_change,
              old_quantity, new_quantity, profit_change, note, now, user_id))
        self.conn.commit()
    
    def close(self):
        """إغلاق اتصال قاعدة البيانات"""
        self.conn.close()

# =============================================================================
# واجهة المستخدم (UI)
# =============================================================================

class StoreManagementApp:
    """التطبيق الرئيسي"""



    def __init__(self, page: ft.Page):
        self.page = page
        self.current_user = None
        
        storage_path = ""
        try:
            import sys
            if sys.platform == 'android':
                storage_path = os.getenv("FLET_DATA_DIR", "")
        except:
            pass
        
        self.db = Database(storage_path)
        
        self.page.title = "نظام إدارة المتجر المتكامل"
        self.page.bgcolor = "#F4F7FC"
        self.page.rtl = True
        self.page.theme_mode = ft.ThemeMode.LIGHT
        
        # ====== إعدادات التكيف مع الأندرويد ======
        self.is_android = False
        try:
            import sys
            if sys.platform == 'android':
                self.is_android = True
        except:
            pass
        
        if self.is_android:
            self._btn_h = 48
            self._btn_small = 40
            self._icon_s = 22
            self._icon_big = 30
            self._font_s = 13
            self._font_m = 15
            self._font_l = 20
            self._grid_cols = 2
            self._grid_extent = 140
            self._dialog_w = None
        else:
            self._btn_h = 40
            self._btn_small = 32
            self._icon_s = 18
            self._icon_big = 26
            self._font_s = 11
            self._font_m = 13
            self._font_l = 17
            self._grid_cols = 3
            self._grid_extent = 150
            self._dialog_w = 450
        # ====== نهاية إعدادات الأندرويد ======
        
        self.current_page = "login"
        self.cart = []
        self.selected_customer = None
        self.theme_color = ft.Colors.BLUE
        
        # مكونات واجهة البيع
        self.products_grid = None
        self.sales_table = None
        self.search_field_name = None
        self.search_field_barcode = None
        self.customer_name_display = None
        self.customer_debt_display = None
        self.total_label_pos = ft.Text("0.00", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700)
        self.cart_count = ft.Text("0", size=self._font_s, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD)
        
        self.show_home()

    def _adapt(self, value, increase: float = 1.3):
        """تكبير القيمة إذا كان أندرويد"""
        if self.is_android:
            return value * increase
        return value
    
    # def __init__(self, page: ft.Page):
    #     self.page = page
    #     self.current_user = None
        
    #     storage_path = ""
    #     try:
    #         import sys
    #         if sys.platform == 'android':
    #             storage_path = os.getenv("FLET_DATA_DIR", "")
    #     except:
    #         pass
        
    #     self.db = Database(storage_path)
        
    #     self.page.title = "نظام إدارة المتجر المتكامل"
    #     self.page.bgcolor = "#F4F7FC"
    #     self.page.rtl = True
    #     self.page.theme_mode = ft.ThemeMode.LIGHT
        
    #     try:
    #         import sys
    #         if sys.platform not in ('android', 'ios'):
    #             self.page.window.width = 450
    #             self.page.window.height = 850
    #     except:
    #         pass
        
    #     self.current_page = "login"
    #     self.cart = []
    #     self.selected_customer = None
    #     self.theme_color = ft.Colors.BLUE
        
    #     # مكونات واجهة البيع
    #     self.products_grid = None
    #     self.sales_table = None
    #     self.search_field_name = None
    #     self.search_field_barcode = None
    #     self.customer_name_display = None
    #     self.customer_debt_display = None
    #     self.total_label_pos = ft.Text("0.00", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700)
    #     self.cart_count = ft.Text("0", size=self._font_s, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD)
        
    #     self.show_home()
    
    def show_login(self, e=None):
        """صفحة تسجيل الدخول"""
        self.page.clean()
        self.current_page = "login"
        
        username_field = ft.TextField(
            label="اسم المستخدم",
            autofocus=True,
            prefix_icon=ft.Icons.PERSON,
            border_radius=10,
            on_submit=lambda e: password_field.focus()
        )
        
        password_field = ft.TextField(
            label="كلمة المرور",
            password=True,
            can_reveal_password=True,
            prefix_icon=ft.Icons.LOCK,
            border_radius=10,
            on_submit=lambda e: do_login(e)
        )
        
        error_text = ft.Text("", color=ft.Colors.RED, size=self._font_s)
        
        def do_login(e):
            user = self.db.authenticate_user(username_field.value, password_field.value)
            if user:
                self.current_user = dict(user)
                self.show_home()
            else:
                error_text.value = "اسم المستخدم أو كلمة المرور غير صحيحة"
                self.page.update()
        
        self.page.add(
            ft.Container(
                expand=True,
                gradient=ft.LinearGradient(
                    begin=ft.alignment.top_center,
                    end=ft.alignment.bottom_center,
                    colors=["#1565C0", "#0D47A1"]
                ),
                content=ft.Column(
                    [
                        ft.Container(height=80),
                        ft.Icon(ft.Icons.STORE_MALL_DIRECTORY, size=70, color=ft.Colors.WHITE),
                        ft.Text("نظام إدارة المتجر", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ft.Text("تسجيل الدخول", size=self._font_l, color=ft.Colors.WHITE70),
                        ft.Container(height=self._btn_h),
                        ft.Container(
                            width=350,
                            padding=30,
                            bgcolor=ft.Colors.WHITE,
                            border_radius=20,
                            shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK)),
                            content=ft.Column([
                                username_field,
                                ft.Container(height=15),
                                password_field,
                                ft.Container(height=10),
                                error_text,
                                ft.Container(height=20),
                                ft.ElevatedButton(
                                    "دخول",
                                    on_click=do_login,
                                    style=ft.ButtonStyle(
                                        bgcolor="#1565C0",
                                        color=ft.Colors.WHITE,
                                        shape=ft.RoundedRectangleBorder(radius=10),
                                    ),
                                    width=float("inf"),
                                    height=50,
                                ),
                            ], spacing=5)
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )
        )
        self.page.update()
    
    def show_message(self, text: str, color: str = ft.Colors.GREEN):
        """عرض رسالة منبثقة"""
        snack = ft.SnackBar(
            content=ft.Text(text, color=ft.Colors.WHITE),
            bgcolor=color,
            duration=3000
        )
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()
    
    def close_dialog(self, dlg):
        """إغلاق نافذة"""
        dlg.open = False
        self.page.update()
    
    def _create_stat_card(self, title: str, value: str, icon, color, col_size=None):
        """إنشاء بطاقة إحصائية"""
        return ft.Container(
            col=col_size if col_size else {"sm": 6, "md": 3},
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            padding=15,
            content=ft.Column([
                ft.Row([
                    ft.Icon(icon, color=color, size=30),
                    ft.Container(expand=True),
                    ft.Text(str(value), size=24, weight=ft.FontWeight.BOLD, color=color),
                ]),
                ft.Text(title, size=self._font_m, color=ft.Colors.GREY_600),
            ], spacing=5),
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK)),
        )
    
    # ========== الصفحة الرئيسية ==========
    
    # def show_home(self, e=None):
    #     """الصفحة الرئيسية"""
    #     self.current_page = "home"
    #     self.page.clean()
        
    #     stats = self.db.get_dashboard_stats()
        
    #     self.page.appbar = ft.AppBar(
    #         title=ft.Text("لوحة التحكم", color=ft.Colors.WHITE, size=18, weight=ft.FontWeight.BOLD),
    #         center_title=True,
    #         bgcolor="#1565C0",
    #         leading=ft.IconButton(ft.Icons.MENU, icon_color=ft.Colors.WHITE),
    #         actions=[
    #             ft.IconButton(ft.Icons.NOTIFICATIONS_OUTLINED, icon_color=ft.Colors.WHITE, 
    #                          on_click=self.show_notifications),
    #             ft.IconButton(ft.Icons.LOGOUT, icon_color=ft.Colors.WHITE, 
    #                          on_click=self.show_login),
    #         ]
    #     )
        
    #     cards_row1 = ft.ResponsiveRow([
    #         self._create_stat_card("مبيعات اليوم", f"{stats['today']['sales']:.0f}", ft.Icons.TODAY, ft.Colors.BLUE),
    #         self._create_stat_card("ربح اليوم", f"{stats['today']['profit']:.0f}", ft.Icons.TRENDING_UP, ft.Colors.GREEN),
    #         self._create_stat_card("المنتجات", str(stats['products_count']), ft.Icons.INVENTORY_2, ft.Colors.ORANGE),
    #         self._create_stat_card("العملاء", str(stats['customers_count']), ft.Icons.PEOPLE, ft.Colors.PURPLE),
    #     ], spacing=10)
        
    #     cards_row2 = ft.ResponsiveRow([
    #         self._create_stat_card("مبيعات الأسبوع", f"{stats['week']['sales']:.0f}", ft.Icons.DATE_RANGE, ft.Colors.CYAN),
    #         self._create_stat_card("مبيعات الشهر", f"{stats['month']['sales']:.0f}", ft.Icons.CALENDAR_MONTH, ft.Colors.TEAL),
    #         self._create_stat_card("الديون", f"{stats['total_debts']:.0f}", ft.Icons.MONEY_OFF, ft.Colors.RED),
    #         self._create_stat_card("مخزون منخفض", str(stats['low_stock_count']), ft.Icons.WARNING, ft.Colors.AMBER),
    #     ], spacing=10)
        
    #     # أزرار سريعة
    #     quick_actions = ft.GridView(
    #         expand=True,
    #         runs_count=self._grid_cols,
    #         max_extent=self._grid_extent,
    #         child_aspect_ratio=0.9,
    #         spacing=10,
    #         run_spacing=10,
    #     )
        
    #     actions = [
    #         ("الموردين", ft.Icons.LOCAL_SHIPPING, ft.Colors.BROWN, self.show_suppliers),
    #         ("فواتير الشراء", ft.Icons.SHOPPING_CART, ft.Colors.INDIGO, self.show_purchases),
     

    #         ("نظام البيع", ft.Icons.POINT_OF_SALE, ft.Colors.BLUE, self.show_pos),
    #         ("المنتجات", ft.Icons.INVENTORY_2, ft.Colors.GREEN, self.show_products),
    #         ("تقارير المشتريات", ft.Icons.ANALYTICS, ft.Colors.INDIGO_900, self.show_purchase_reports),
    #         ("العملاء", ft.Icons.PEOPLE, ft.Colors.CYAN, self.show_customers),
    #         ("الديون", ft.Icons.ACCOUNT_BALANCE, ft.Colors.RED, self.show_debts),
    #         ("المصروفات", ft.Icons.MONEY_OFF, ft.Colors.ORANGE, self.show_expenses),
    #         ("التقارير", ft.Icons.BAR_CHART, ft.Colors.PURPLE, self.show_reports),
    #         ("نسخ احتياطي", ft.Icons.BACKUP, ft.Colors.BLUE_GREY, self.backup_database),
    #         ("سجل الحركات", ft.Icons.HISTORY, ft.Colors.TEAL, self.show_history),
    #         ("تتبع منتج", ft.Icons.TRACK_CHANGES, ft.Colors.DEEP_PURPLE, self.show_product_tracking),
    #         ("تقرير سنوي", ft.Icons.CALENDAR_MONTH, ft.Colors.BROWN, self.show_yearly_reports),
    #         ("إدارة المستخدمين", ft.Icons.MANAGE_ACCOUNTS, ft.Colors.INDIGO, self.show_users),
    #         ("الإعدادات", ft.Icons.SETTINGS, ft.Colors.GREY, self.show_settings),
        
    #     ]
        
    #     for title, icon, color, on_click in actions:
    #         quick_actions.controls.append(
    #             ft.Container(
    #                 bgcolor=ft.Colors.WHITE,
    #                 border_radius=15,
    #                 padding=10,
    #                 ink=True,
    #                 on_click=on_click,
    #                 shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.with_opacity(0.05, ft.Colors.BLACK)),
    #                 content=ft.Column([
    #                     ft.Icon(icon, size=35, color=color),
    #                     ft.Text(title, size=self._font_s, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
    #                 ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5)
    #             )
    #         )
        
    #     self.page.add(
    #         ft.Container(
    #             expand=True,
    #             padding=15,
    #             content=ft.Column([
    #                 cards_row1,
    #                 ft.Container(height=10),
    #                 cards_row2,
    #                 ft.Container(height=20),
    #                 ft.Text("الوصول السريع", size=self._font_l, weight=ft.FontWeight.BOLD),
    #                 quick_actions,
    #             ], scroll=ft.ScrollMode.AUTO, expand=True)
    #         )
    #     )
    #     self.page.update()






    def show_home(self, e=None):
        """الصفحة الرئيسية - تصميم عصري جذاب"""
        self.current_page = "home"
        self.page.clean()
        
        # ====== الإحصائيات السريعة ======
        cursor = self.db.conn.cursor()
        
        cursor.execute("SELECT COALESCE(SUM(purchase_price * quantity), 0) FROM products")
        inventory_value = cursor.fetchone()[0]
        
        cursor.execute("SELECT COALESCE(SUM(remaining), 0) FROM debts WHERE status != 'paid'")
        total_debts = cursor.fetchone()[0]
        
        cursor.execute("SELECT COALESCE(SUM(profit), 0) FROM sales")
        total_profit = cursor.fetchone()[0]
        cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses")
        total_expenses = cursor.fetchone()[0]
        net_profit = total_profit - total_expenses
        
        # ====== شريط إحصائي علوي بتصميم جذاب ======
        stats_bar = ft.Container(
            padding=15,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=["#1A237E", "#283593", "#3949AB"],
            ),
            border_radius=20,
            shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.with_opacity(0.3, "#1A237E")),
            content=ft.Row([
                # بطاقة المخزون
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Icon(ft.Icons.INVENTORY_2_ROUNDED, size=28, color=ft.Colors.WHITE),
                            bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
                            border_radius=15,
                            padding=10,
                        ),
                        ft.Container(width=10),
                        ft.Column([
                            ft.Text(f"{inventory_value:,.0f}", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                            ft.Text("💰 قيمة المخزون", size=self._font_s, color=ft.Colors.WHITE70),
                        ], spacing=2),
                    ]),
                    col={"sm": 4},
                ),
                ft.VerticalDivider(color=ft.Colors.WHITE24),
                # بطاقة الديون
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Icon(ft.Icons.ACCOUNT_BALANCE_WALLET_ROUNDED, size=28, color=ft.Colors.WHITE),
                            bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
                            border_radius=15,
                            padding=10,
                        ),
                        ft.Container(width=10),
                        ft.Column([
                            ft.Text(f"{total_debts:,.0f}", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                            ft.Text("📊 ديون العملاء", size=self._font_s, color=ft.Colors.WHITE70),
                        ], spacing=2),
                    ]),
                    col={"sm": 4},
                ),
                ft.VerticalDivider(color=ft.Colors.WHITE24),
                # بطاقة الأرباح
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Icon(ft.Icons.TRENDING_UP_ROUNDED, size=28, color=ft.Colors.WHITE),
                            bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
                            border_radius=15,
                            padding=10,
                        ),
                        ft.Container(width=10),
                        ft.Column([
                            ft.Text(f"{net_profit:,.0f}", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                            ft.Text("📈 صافي الأرباح", size=self._font_s, color=ft.Colors.WHITE70),
                        ], spacing=2),
                    ]),
                    col={"sm": 4},
                ),
            ], spacing=5, alignment=ft.MainAxisAlignment.SPACE_AROUND),
        )
        
        # ====== أزرار سريعة بتصميم جديد ======
        quick_actions = ft.GridView(
            expand=True,
            runs_count=self._grid_cols,
            max_extent=160,
            child_aspect_ratio=0.85,
            spacing=12,
            run_spacing=12,
        )
        
        actions = [
            ("🛒 نظام البيع", ft.Icons.POINT_OF_SALE_ROUNDED, ["#4CAF50", "#2E7D32"], self.show_pos),
            ("📦 المنتجات", ft.Icons.INVENTORY_2_ROUNDED, ["#2196F3", "#1565C0"], self.show_products),
            ("👥 العملاء", ft.Icons.PEOPLE_ROUNDED, ["#00BCD4", "#00838F"], self.show_customers),
            ("🚚 الموردين", ft.Icons.LOCAL_SHIPPING_ROUNDED, ["#795548", "#4E342E"], self.show_suppliers),
            ("🧾 فواتير الشراء", ft.Icons.SHOPPING_CART_ROUNDED, ["#5C6BC0", "#283593"], self.show_purchases),
            ("💰 الديون", ft.Icons.ACCOUNT_BALANCE_ROUNDED, ["#F44336", "#B71C1C"], self.show_debts),
            ("💸 المصروفات", ft.Icons.MONEY_OFF_ROUNDED, ["#FF9800", "#E65100"], self.show_expenses),
            ("📊 التقارير", ft.Icons.BAR_CHART_ROUNDED, ["#9C27B0", "#4A148C"], self.show_reports),
            ("📈 تقارير المشتريات", ft.Icons.ANALYTICS_ROUNDED, ["#3F51B5", "#1A237E"], self.show_purchase_reports),
            ("💾 نسخ احتياطي", ft.Icons.BACKUP_ROUNDED, ["#607D8B", "#37474F"], self.backup_database),
            ("📋 سجل الحركات", ft.Icons.HISTORY_ROUNDED, ["#009688", "#004D40"], self.show_history),
            ("⚙️ الإعدادات", ft.Icons.SETTINGS_ROUNDED, ["#9E9E9E", "#424242"], self.show_settings),
        ]
        
        for title, icon, colors, on_click in actions:
            quick_actions.controls.append(
                ft.Container(
                    gradient=ft.LinearGradient(
                        begin=ft.alignment.top_left,
                        end=ft.alignment.bottom_right,
                        colors=colors,
                    ),
                    border_radius=18,
                    padding=15,
                    ink=True,
                    on_click=on_click,
                    shadow=ft.BoxShadow(blur_radius=8, color=ft.Colors.with_opacity(0.3, colors[1])),
                    content=ft.Column([
                        ft.Container(
                            content=ft.Icon(icon, size=30, color=ft.Colors.WHITE),
                            bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
                            border_radius=15,
                            padding=8,
                        ),
                        ft.Container(height=8),
                        ft.Text(title, size=self._font_s, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER),
                    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                )
            )
        
        # ====== بناء الواجهة ======
        self.page.add(
            ft.AppBar(
                title=ft.Row([
                    ft.Icon(ft.Icons.STORE_ROUNDED, color=ft.Colors.WHITE, size=24),
                    ft.Container(width=8),
                    ft.Text("لوحة التحكم", color=ft.Colors.WHITE, size=18, weight=ft.FontWeight.BOLD),
                ]),
                center_title=True,
                bgcolor="#1A237E",
                actions=[
                    ft.Container(
                        content=ft.IconButton(
                            ft.Icons.NOTIFICATIONS_OUTLINED,
                            icon_color=ft.Colors.WHITE,
                            on_click=self.show_notifications,
                        ),
                        margin=ft.Margin(0, 0, 10, 0),
                    ),
                ]
            ),
            ft.Container(
                expand=True,
                gradient=ft.LinearGradient(
                    begin=ft.alignment.top_center,
                    end=ft.alignment.bottom_center,
                    colors=["#F5F7FA", "#E8ECF1", "#D5DCE8"],
                ),
                padding=15,
                content=ft.Column([
                    stats_bar,
                    ft.Container(height=20),
                    ft.Container(
                        content=ft.Row([
                            ft.Container(
                                content=ft.Container(width=30, height=3, bgcolor="#1A237E", border_radius=2),
                            ),
                            ft.Container(width=10),
                            ft.Text("الوصول السريع", size=15, weight=ft.FontWeight.BOLD, color="#1A237E"),
                        ]),
                    ),
                    ft.Container(height=10),
                    quick_actions,
                ], scroll=ft.ScrollMode.AUTO, expand=True),
            )
        )
        self.page.update()













    
    def show_notifications(self, e=None):
        """عرض الإشعارات"""
        notifications = self.db.get_notifications(user_id=self.current_user.get('id') if self.current_user else None)
        unread_count = self.db.get_unread_notifications_count(user_id=self.current_user.get('id') if self.current_user else None)
        
        notif_list = ft.ListView(expand=True, spacing=10)
        
        for n in notifications[:30]:
            icon_map = {"info": ft.Icons.INFO, "warning": ft.Icons.WARNING, "error": ft.Icons.ERROR, "success": ft.Icons.CHECK_CIRCLE}
            color_map = {"info": ft.Colors.BLUE, "warning": ft.Colors.ORANGE, "error": ft.Colors.RED, "success": ft.Colors.GREEN}
            bg_map = {"info": ft.Colors.BLUE_50, "warning": ft.Colors.ORANGE_50, "error": ft.Colors.RED_50, "success": ft.Colors.GREEN_50}
            
            notif_list.controls.append(
                ft.Container(
                    bgcolor=bg_map.get(n['type'], ft.Colors.GREY_50),
                    border_radius=10,
                    padding=15,
                    opacity=0.7 if n['is_read'] else 1,
                    on_click=lambda _, nid=n['id']: self.db.mark_notification_read(nid),
                    content=ft.Row([
                        ft.Icon(icon_map.get(n['type'], ft.Icons.INFO), color=color_map.get(n['type'], ft.Colors.BLUE)),
                        ft.Column([
                            ft.Text(n['title'], weight=ft.FontWeight.BOLD, size=self._font_m),
                            ft.Text(n['message'], size=self._font_s, color=ft.Colors.GREY_700),
                            ft.Text(n['created_at'][:16], size=10, color=ft.Colors.GREY_500),
                        ], expand=True, spacing=3),
                    ])
                )
            )
        
        if not notifications:
            notif_list.controls.append(
                ft.Container(content=ft.Text("لا توجد إشعارات", text_align=ft.TextAlign.CENTER), padding=50)
            )
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"الإشعارات ({unread_count} غير مقروءة)"),
            content=ft.Container(width=400, height=500, content=notif_list),
            actions=[ft.TextButton("إغلاق", on_click=lambda _: self.close_dialog(dlg))],
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()
    
    def show_users(self, e=None):
        """إدارة المستخدمين"""
        if not self.current_user or self.current_user.get('role') != 'admin':
            self.show_message("ليس لديك صلاحية الوصول", ft.Colors.RED)
            return
        
        self.page.clean()
        users_list = ft.ListView(expand=True, spacing=10)
        
        def refresh_users():
            users_list.controls.clear()
            for user in self.db.get_all_users():
                role_colors = {'admin': ft.Colors.RED, 'manager': ft.Colors.ORANGE, 'cashier': ft.Colors.BLUE, 'inventory': ft.Colors.GREEN}
                role_names = {'admin': 'مدير', 'manager': 'مدير فرعي', 'cashier': 'كاشير', 'inventory': 'مخزني'}
                
                users_list.controls.append(
                    ft.Container(
                        bgcolor=ft.Colors.WHITE,
                        border_radius=10,
                        padding=15,
                        content=ft.Row([
                            ft.Column([
                                ft.Text(user['full_name'], size=self._font_l, weight=ft.FontWeight.BOLD),
                                ft.Text(f"@{user['username']} | {role_names.get(user['role'], user['role'])}", size=self._font_s, color=role_colors.get(user['role'], ft.Colors.GREY)),
                                ft.Text(f"آخر دخول: {user.get('last_login', 'لم يسجل')}", size=self._font_s, color=ft.Colors.GREY_500),
                            ], expand=True),
                            ft.IconButton(ft.Icons.EDIT, icon_color=ft.Colors.BLUE, on_click=lambda _, u=user: edit_user(u)),
                            ft.IconButton(ft.Icons.DELETE, icon_color=ft.Colors.RED, on_click=lambda _, u=user: delete_user(u)),
                        ])
                    )
                )
            self.page.update()
        
        def add_user_dlg(e):
            uname_f = ft.TextField(label="اسم المستخدم", autofocus=True)
            pass_f = ft.TextField(label="كلمة المرور", password=True, can_reveal_password=True)
            name_f = ft.TextField(label="الاسم الكامل")
            role_f = ft.Dropdown(label="الدور", options=[
                ft.dropdown.Option("admin", "مدير"),
                ft.dropdown.Option("manager", "مدير فرعي"),
                ft.dropdown.Option("cashier", "كاشير"),
                ft.dropdown.Option("inventory", "مخزني"),
            ], value="cashier")
            
            def save(e):
                if not all([uname_f.value, pass_f.value, name_f.value]):
                    self.show_message("جميع الحقول مطلوبة", ft.Colors.RED)
                    return
                success, msg = self.db.add_user(uname_f.value, pass_f.value, name_f.value, role_f.value)
                self.show_message(msg, ft.Colors.GREEN if success else ft.Colors.RED)
                if success:
                    self.close_dialog(dlg)
                    refresh_users()
            
            dlg = ft.AlertDialog(
                title=ft.Text("إضافة مستخدم جديد"),
                content=ft.Column([uname_f, pass_f, name_f, role_f], tight=True, spacing=10),
                actions=[
                    ft.TextButton("إلغاء", on_click=lambda _: self.close_dialog(dlg)),
                    ft.ElevatedButton("حفظ", on_click=save)
                ]
            )
            self.page.overlay.append(dlg)
            dlg.open = True
            self.page.update()
        
        def edit_user(user):
            uname_f = ft.TextField(label="اسم المستخدم", value=user['username'], disabled=True)
            name_f = ft.TextField(label="الاسم الكامل", value=user['full_name'])
            pass_f = ft.TextField(label="كلمة مرور جديدة (اترك فارغاً لعدم التغيير)", password=True, can_reveal_password=True)
            role_f = ft.Dropdown(label="الدور", options=[
                ft.dropdown.Option("admin", "مدير"),
                ft.dropdown.Option("manager", "مدير فرعي"),
                ft.dropdown.Option("cashier", "كاشير"),
                ft.dropdown.Option("inventory", "مخزني"),
            ], value=user['role'])
            active_f = ft.Switch(label="نشط", value=bool(user['is_active']))
            
            def save(e):
                kwargs = {"full_name": name_f.value, "role": role_f.value, "is_active": 1 if active_f.value else 0}
                if pass_f.value:
                    kwargs["password"] = pass_f.value
                success, msg = self.db.update_user(user['id'], **kwargs)
                self.show_message(msg, ft.Colors.GREEN if success else ft.Colors.RED)
                if success:
                    self.close_dialog(dlg)
                    refresh_users()
            
            dlg = ft.AlertDialog(
                title=ft.Text("تعديل مستخدم"),
                content=ft.Column([uname_f, name_f, pass_f, role_f, active_f], tight=True, spacing=10, scroll=ft.ScrollMode.AUTO),
                actions=[
                    ft.TextButton("إلغاء", on_click=lambda _: self.close_dialog(dlg)),
                    ft.ElevatedButton("حفظ", on_click=save)
                ]
            )
            self.page.overlay.append(dlg)
            dlg.open = True
            self.page.update()
        
        def delete_user(user):
            def confirm(e):
                success, msg = self.db.delete_user(user['id'])
                self.show_message(msg, ft.Colors.GREEN if success else ft.Colors.RED)
                self.close_dialog(dlg)
                if success:
                    refresh_users()
            
            dlg = ft.AlertDialog(
                title=ft.Text("تأكيد الحذف"),
                content=ft.Text(f"هل تريد حذف المستخدم '{user['full_name']}'؟"),
                actions=[
                    ft.TextButton("إلغاء", on_click=lambda _: self.close_dialog(dlg)),
                    ft.ElevatedButton("حذف", on_click=confirm, bgcolor=ft.Colors.RED, color=ft.Colors.WHITE)
                ]
            )
            self.page.overlay.append(dlg)
            dlg.open = True
            self.page.update()
        
        self.page.add(
            ft.AppBar(
                title=ft.Text("إدارة المستخدمين"),
                bgcolor=ft.Colors.INDIGO_700,
                color=ft.Colors.WHITE,
                leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=self.show_home, icon_color=ft.Colors.WHITE),
            ),
            ft.Container(
                expand=True, padding=20,
                content=ft.Column([
                    ft.ElevatedButton("إضافة مستخدم", on_click=add_user_dlg),
                    ft.Divider(),
                    users_list,
                ], expand=True)
            )
        )
        refresh_users()
    
    def show_settings(self, e=None):
        """صفحة الإعدادات"""
        self.page.clean()
        
        store_name = ft.TextField(label="اسم المتجر", value=self.db.get_setting("store_name", "متجري"))
        currency = ft.TextField(label="العملة", value=self.db.get_setting("currency", "ج.م"))
        low_stock_threshold = ft.TextField(label="حد المخزون المنخفض الافتراضي", value=self.db.get_setting("default_threshold", "5"), keyboard_type=ft.KeyboardType.NUMBER)
        auto_backup = ft.Switch(label="نسخ احتياطي تلقائي", value=self.db.get_setting("auto_backup", "false") == "true")
        
        def save(e):
            self.db.set_setting("store_name", store_name.value)
            self.db.set_setting("currency", currency.value)
            self.db.set_setting("default_threshold", low_stock_threshold.value)
            self.db.set_setting("auto_backup", "true" if auto_backup.value else "false")
            self.show_message("تم حفظ الإعدادات")
        
        self.page.add(
            ft.AppBar(
                title=ft.Text("الإعدادات"),
                bgcolor=ft.Colors.GREY_700,
                color=ft.Colors.WHITE,
                leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=self.show_home, icon_color=ft.Colors.WHITE),
            ),
            ft.Container(
                expand=True, padding=20,
                content=ft.Column([
                    store_name, currency, low_stock_threshold,
                    ft.Container(height=20),
                    auto_backup,
                    ft.Container(height=20),
                    ft.ElevatedButton("حفظ الإعدادات", on_click=save),
                    
                    # قسم النسخ الاحتياطي
                    ft.Divider(),
                    ft.Text("النسخ الاحتياطي", size=18, weight=ft.FontWeight.BOLD),
                    ft.ElevatedButton("عمل نسخة احتياطية الآن", on_click=lambda _: self.backup_database()),
                    
                    # معلومات النظام
                    ft.Divider(),
                    ft.Text("معلومات النظام", size=18, weight=ft.FontWeight.BOLD),
                    ft.Text(f"إصدار التطبيق: 2.0", size=self._font_s),
                    ft.Text(f"حجم قاعدة البيانات: {os.path.getsize('grocery_store.db') / 1024:.1f} KB" if os.path.exists('grocery_store.db') else "غير متوفر", size=self._font_s),
                ], scroll=ft.ScrollMode.AUTO)
            )
        )
    
    def backup_database(self, e=None):
        """النسخ الاحتياطي"""
        success, msg = self.db.backup_database()
        self.show_message(msg, ft.Colors.GREEN if success else ft.Colors.RED)
    
    # ========== إدارة المنتجات ==========
    
    def show_products(self, e=None):
        """عرض صفحة إدارة المنتجات"""
        self.current_page = "products"
        self.page.clean()
        
        search_field = ft.TextField(
            hint_text="🔍 بحث عن منتج...",
            on_change=self._search_products,
            expand=True,
            border_radius=10,
        )
        
        add_button = ft.ElevatedButton(
            "إضافة منتج جديد",
            icon=ft.Icons.ADD,
            bgcolor=ft.Colors.GREEN,
            color=ft.Colors.WHITE,
            on_click=self.show_add_product_dialog,
        )
        
        self.products_list = ft.ListView(expand=True, spacing=10, padding=10)
        
        self.page.add(
            ft.AppBar(
                title=ft.Text("إدارة المنتجات"),
                bgcolor=ft.Colors.BLUE_700,
                color=ft.Colors.WHITE,
                leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=self.show_home, icon_color=ft.Colors.WHITE),
            ),
            ft.Container(
                padding=20,
                content=ft.Column([
                    ft.ResponsiveRow([
                        ft.Column([search_field], col={"sm": 8, "md": 9}),
                        ft.Column([add_button], col={"sm": 4, "md": 3}),
                    ], spacing=10),
                    ft.Container(height=20),
                    ft.Text("قائمة المنتجات", size=18, weight=ft.FontWeight.BOLD),
                    ft.Container(content=self.products_list, expand=True),
                ], expand=True),
            ),
        )
        self._refresh_products_list()



    def show_add_product_dialog(self, e=None):
        name_field = ft.TextField(label="اسم المنتج", autofocus=True)
        barcode_field = ft.TextField(label="الباركود")
        category_field = ft.TextField(label="التصنيف", value="عام")
        purchase_price_field = ft.TextField(label="سعر الشراء", keyboard_type=ft.KeyboardType.NUMBER)
        selling_price_field = ft.TextField(label="سعر البيع", keyboard_type=ft.KeyboardType.NUMBER)
        quantity_field = ft.TextField(label="الكمية الأولية", keyboard_type=ft.KeyboardType.NUMBER, value="0")
        threshold_field = ft.TextField(label="حد التنبيه الأدنى", keyboard_type=ft.KeyboardType.NUMBER, value="5")
        
        def save_product(e):
            try:
                product = Product(
                    name=name_field.value,
                    barcode=barcode_field.value,
                    category=category_field.value,
                    purchase_price=float(purchase_price_field.value or 0),
                    selling_price=float(selling_price_field.value or 0),
                    quantity=int(quantity_field.value or 0),
                    min_stock_threshold=int(threshold_field.value or 5),
                )
                success, message = self.db.add_product(product)
                if success:
                    self.show_message(message)
                    self.close_dialog(dlg)
                    self._refresh_products_list()
                else:
                    self.show_message(message, ft.Colors.RED)
            except ValueError:
                self.show_message("يرجى إدخال قيم صحيحة", ft.Colors.RED)
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("إضافة منتج جديد"),
            content=ft.Column(
                [name_field, barcode_field, category_field, purchase_price_field, selling_price_field, quantity_field, threshold_field],
                tight=True, spacing=10, scroll=ft.ScrollMode.AUTO,
            ),
            actions=[
                ft.TextButton("إلغاء", on_click=lambda _: self.close_dialog(dlg)),
                ft.ElevatedButton("حفظ", on_click=save_product, bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE),
            ],
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()
    def _search_products(self, e):
        query = e.control.value
        products = self.db.search_products(query) if query else self.db.get_all_products()
        self._render_products_list(products)
    
    def _refresh_products_list(self):
        products = self.db.get_all_products()
        self._render_products_list(products)
    
    def _render_products_list(self, products: List[Product]):
        self.products_list.controls.clear()
        
        if not products:
            self.products_list.controls.append(
                ft.Container(
                    content=ft.Text("لا توجد منتجات", size=self._font_l, color=ft.Colors.GREY_500),
                    alignment=ft.Alignment(0, 0),
                    padding=50,
                )
            )
            self.page.update()
            return
        
        for product in products:
            is_low_stock = product.quantity <= product.min_stock_threshold
            
            self.products_list.controls.append(
                ft.Container(
                    bgcolor=ft.Colors.WHITE,
                    border_radius=10,
                    padding=15,
                    content=ft.Row([
                        ft.Column([
                            ft.Text(product.name, size=self._font_l, weight=ft.FontWeight.BOLD),
                            ft.Text(f"التصنيف: {product.category} | الباركود: {product.barcode}", size=self._font_s, color=ft.Colors.BLUE_GREY_400),
                            ft.Text(f"سعر الشراء: {product.purchase_price:.2f} | سعر البيع: {product.selling_price:.2f}", size=self._font_s, color=ft.Colors.GREY_600),
                            ft.Text(f"المخزون: {product.quantity}", size=self._font_s, color=ft.Colors.RED if is_low_stock else ft.Colors.GREEN),
                        ], expand=True, spacing=5),
                        ft.Row([
                            ft.IconButton(ft.Icons.ADD_CIRCLE, icon_color=ft.Colors.GREEN, tooltip="إضافة مخزون", on_click=lambda _, p=product: self.show_add_stock_dialog(p)),
                            ft.IconButton(ft.Icons.EDIT, icon_color=ft.Colors.BLUE, tooltip="تعديل", on_click=lambda _, p=product: self.show_edit_product_dialog(p)),
                            ft.IconButton(ft.Icons.DELETE, icon_color=ft.Colors.RED, tooltip="حذف", on_click=lambda _, p=product: self._confirm_delete_product(p)),
                        ], spacing=5),
                    ]),
                    shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK)),
                )
            )
        
        self.page.update()
    
    # def show_add_product_dialog(self, e=None):
        name_field = ft.TextField(label="اسم المنتج", autofocus=True)
        barcode_field = ft.TextField(label="الباركود")
        category_field = ft.TextField(label="التصنيف", value="عام")
        purchase_price_field = ft.TextField(label="سعر الشراء", keyboard_type=ft.KeyboardType.NUMBER)
        selling_price_field = ft.TextField(label="سعر البيع", keyboard_type=ft.KeyboardType.NUMBER)
        quantity_field = ft.TextField(label="الكمية الأولية", keyboard_type=ft.KeyboardType.NUMBER, value="0")
        threshold_field = ft.TextField(label="حد التنبيه الأدنى", keyboard_type=ft.KeyboardType.NUMBER, value="5")
        
        def save_product(e):
            try:
                product = Product(
                    name=name_field.value,
                    barcode=barcode_field.value,
                    category=category_field.value,
                    purchase_price=float(purchase_price_field.value),
                    selling_price=float(selling_price_field.value),
                    quantity=int(quantity_field.value),
                    min_stock_threshold=int(threshold_field.value),
                )
                success, message = self.db.add_product(product)
                if success:
                    self.show_message(message)
                    dlg.open = False
                    self._refresh_products_list()
                else:
                    self.show_message(message, ft.Colors.RED)
            except ValueError:
                self.show_message("يرجى إدخال قيم صحيحة", ft.Colors.RED)
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("إضافة منتج جديد"),
            content=ft.Column(
                [name_field, barcode_field, category_field, purchase_price_field, selling_price_field, quantity_field, threshold_field],
                tight=True, spacing=10, scroll=ft.ScrollMode.AUTO,
            ),
            actions=[
                ft.TextButton("إلغاء", on_click=lambda _: self.close_dialog(dlg)),
                ft.ElevatedButton("حفظ", on_click=save_product, bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE),
            ],
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()
    
    def show_edit_product_dialog(self, product: Product):
        name_field = ft.TextField(label="اسم المنتج", value=product.name, autofocus=True)
        barcode_field = ft.TextField(label="الباركود", value=product.barcode)
        category_field = ft.TextField(label="التصنيف", value=product.category)
        purchase_price_field = ft.TextField(label="سعر الشراء", value=str(product.purchase_price), keyboard_type=ft.KeyboardType.NUMBER)
        selling_price_field = ft.TextField(label="سعر البيع", value=str(product.selling_price), keyboard_type=ft.KeyboardType.NUMBER)
        quantity_field = ft.TextField(label="الكمية", value=str(product.quantity), keyboard_type=ft.KeyboardType.NUMBER)
        threshold_field = ft.TextField(label="حد التنبيه الأدنى", value=str(product.min_stock_threshold), keyboard_type=ft.KeyboardType.NUMBER)
        
        def save_edit(e):
            try:
                product.name = name_field.value
                product.barcode = barcode_field.value
                product.category = category_field.value
                product.purchase_price = float(purchase_price_field.value)
                product.selling_price = float(selling_price_field.value)
                product.quantity = int(quantity_field.value)
                product.min_stock_threshold = int(threshold_field.value)
                
                success, message = self.db.update_product(product)
                if success:
                    self.show_message(message)
                    dlg.open = False
                    self._refresh_products_list()
                else:
                    self.show_message(message, ft.Colors.RED)
            except ValueError:
                self.show_message("يرجى إدخال قيم صحيحة", ft.Colors.RED)
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("تعديل المنتج"),
            content=ft.Column(
                [name_field, barcode_field, category_field, purchase_price_field, selling_price_field, quantity_field, threshold_field],
                tight=True, spacing=10, scroll=ft.ScrollMode.AUTO,
            ),
            actions=[
                ft.TextButton("إلغاء", on_click=lambda _: self.close_dialog(dlg)),
                ft.ElevatedButton("حفظ", on_click=save_edit, bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE),
            ],
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()
    
    def show_add_stock_dialog(self, product: Product):
        quantity_field = ft.TextField(label="الكمية المضافة", keyboard_type=ft.KeyboardType.NUMBER, autofocus=True)
        
        def add_stock(e):
            try:
                quantity = int(quantity_field.value)
                if quantity <= 0:
                    self.show_message("يجب أن تكون الكمية أكبر من 0", ft.Colors.RED)
                    return
                success, message = self.db.add_stock(product.id, quantity)
                if success:
                    self.show_message(message)
                    dlg.open = False
                    self._refresh_products_list()
                else:
                    self.show_message(message, ft.Colors.RED)
            except ValueError:
                self.show_message("يرجى إدخال كمية صحيحة", ft.Colors.RED)
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"إضافة مخزون - {product.name}"),
            content=ft.Column([quantity_field], tight=True),
            actions=[
                ft.TextButton("إلغاء", on_click=lambda _: self.close_dialog(dlg)),
                ft.ElevatedButton("إضافة", on_click=add_stock, bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE),
            ],
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()
    
    def _confirm_delete_product(self, product: Product):
        def delete(e):
            success, message = self.db.delete_product(product.id)
            self.show_message(message, ft.Colors.GREEN if success else ft.Colors.RED)
            self.close_dialog(dlg)
            self._refresh_products_list()
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("تأكيد الحذف"),
            content=ft.Text(f"هل أنت متأكد من حذف المنتج '{product.name}'؟"),
            actions=[
                ft.TextButton("إلغاء", on_click=lambda _: self.close_dialog(dlg)),
                ft.ElevatedButton("تأكيد", on_click=delete, bgcolor=ft.Colors.RED, color=ft.Colors.WHITE),
            ],
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()



    # ========== نظام البيع ==========
    
    def show_pos(self, e=None):
        """نظام البيع"""
        self.current_page = "pos"
        self.cart = []
        self.selected_customer = None
        self.page.clean()
        
        invoice_number = self.db.get_next_invoice_number()
        
        header = ft.Container(
            padding=10, bgcolor=ft.Colors.BLUE_GREY_50, border_radius=8,
            content=ft.Row([
                ft.Row([
                    ft.IconButton(ft.Icons.ARROW_BACK, on_click=self.show_home),
                    ft.Icon(ft.Icons.RECEIPT_LONG, size=20, color=ft.Colors.BLUE_700),
                    ft.Text(f"فاتورة: {invoice_number}", weight="bold", size=self._font_m),
                ], spacing=5),
                ft.Text(datetime.now().strftime("%Y-%m-%d %H:%M"), size=self._font_s),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        )
        
        self.customer_name_display = ft.Text("العميل: نقدي (افتراضي)", weight="bold", size=self._font_m)
        self.customer_debt_display = ft.Text("ديون سابقة: 0.00", size=self._font_s, color=ft.Colors.RED_700)
        
        customer_section = ft.Container(
            padding=10, border=ft.border.all(1, ft.Colors.BLUE_GREY_100), border_radius=10,
            bgcolor=ft.Colors.WHITE,
            content=ft.Column([
                ft.Row([
                    ft.TextField(
                        hint_text="🔍 ابحث عن عميل...",
                        on_change=self._search_customers_pos,
                        expand=True, height=38, text_size=self._font_s, border_radius=8,
                    ),
                ]),
                ft.Row([self.customer_name_display, self.customer_debt_display], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ], spacing=5)
        )
        
        self.search_field_name = ft.TextField(
            hint_text="بحث باسم المنتج...",
            on_change=self._search_product_for_sale,
            expand=True, height=self._btn_h, text_size=self._font_m, border_radius=8,
        )
        self.search_field_barcode = ft.TextField(
            hint_text="الباركود...",
            on_submit=self._handle_barcode_scan,
            width=150, height=self._btn_h, text_size=self._font_m, border_radius=8,
        )
        
        search_section = ft.Container(
            content=ft.Row([
                self.search_field_name,
                self.search_field_barcode,
            ], spacing=10)
        )
        
        self.products_grid = ft.GridView(
            runs_count=self._grid_cols, max_extent=self._grid_extent, child_aspect_ratio=0.85,
            spacing=8, run_spacing=8, height=200,
        )
        
        self.sales_table = ft.ListView(expand=True, spacing=2)
        table_header = ft.Container(
            padding=ft.padding.symmetric(vertical=8, horizontal=5),
            bgcolor=ft.Colors.BLUE_700,
            border_radius=ft.border_radius.only(top_left=8, top_right=8),
            content=ft.Row([
                ft.Text("المنتج", expand=3, color=ft.Colors.WHITE, weight="bold", size=self._font_s),
                ft.Text("الكمية", expand=1, color=ft.Colors.WHITE, weight="bold", size=self._font_s),
                ft.Text("السعر", expand=1, color=ft.Colors.WHITE, weight="bold", size=self._font_s),
                ft.Text("الإجمالي", expand=1.2, color=ft.Colors.WHITE, weight="bold", size=self._font_s),
                ft.Text("", width=30),
            ])
        )
        
        self.page.add(
            header,
            customer_section,
            search_section,
            ft.Container(content=self.products_grid, border=ft.border.all(1, ft.Colors.BLUE_GREY_50), border_radius=8, bgcolor=ft.Colors.GREY_50),
            ft.Divider(height=1, color=ft.Colors.TRANSPARENT),
            ft.Container(
                expand=True,
                content=ft.Column([
                    table_header,
                    ft.Container(content=self.sales_table, expand=True, border=ft.border.all(1, ft.Colors.BLUE_GREY_100), border_radius=ft.border_radius.only(bottom_left=8, bottom_right=8)),
                ], spacing=0)
            ),
            # ====== شريط الإجمالي مع أزرار المسودة ======
            ft.Container(
                padding=12,
                bgcolor=ft.Colors.WHITE,
                border_radius=10,
                shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK)),
                content=ft.Column([
                    ft.Row([
                        ft.Column([
                            ft.Text("إجمالي الفاتورة", size=self._font_s, color=ft.Colors.BLUE_GREY_400),
                            ft.Row([self.total_label_pos, ft.Text("ج.م", size=self._font_m, weight="bold", color=ft.Colors.BLUE_700)]),
                        ], spacing=0),
                        ft.ElevatedButton(
                            "إتمام وحفظ",
                            icon=ft.Icons.CHECK_CIRCLE_OUTLINE,
                            bgcolor=ft.Colors.BLUE_700,
                            color=ft.Colors.WHITE,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                            expand=True,
                            height=48,
                            on_click=self._show_checkout_options,
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Container(height=5),
                    ft.Row([
                        ft.OutlinedButton(
                            "💾 حفظ كمسودة",
                            icon=ft.Icons.SAVE_OUTLINED,
                            on_click=self._save_draft_invoice,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                            expand=True,
                            height=self._btn_small,
                        ),
                        ft.Container(width=5),
                        ft.OutlinedButton(
                            "📂 استرجاع مسودة",
                            icon=ft.Icons.FOLDER_OPEN_OUTLINED,
                            on_click=self._show_drafts_dialog,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                            expand=True,
                            height=self._btn_small,
                        ),
                    ]),
                ]),
            )
        )
        
        self._refresh_cart_display()
        self._refresh_products_grid()

    # ====== دوال المسودة ======
    
    def _save_draft_invoice(self, e=None):
        """حفظ الفاتورة الحالية كمسودة"""
        if not self.cart:
            self.show_message("السلة فارغة!", ft.Colors.RED)
            return
        
        customer_name = self.selected_customer['name'] if self.selected_customer else "نقدي"
        customer_id = self.selected_customer['id'] if self.selected_customer else None
        user_id = int(self.current_user.get('id')) if self.current_user else None
        
        success, msg = self.db.save_draft(self.cart, customer_name, customer_id, user_id)
        if success:
            self.show_message(msg, ft.Colors.GREEN)
            self.cart = []
            self.selected_customer = None
            self._refresh_cart_display()
        else:
            self.show_message(msg, ft.Colors.RED)
    
    def _show_drafts_dialog(self, e=None):
        """عرض المسودات المحفوظة"""
        drafts = self.db.get_drafts()
        
        if not drafts:
            self.show_message("لا توجد مسودات محفوظة", ft.Colors.BLUE)
            return
        
        drafts_list = ft.ListView(height=300, spacing=8)
        
        for draft in drafts:
            cart_data = json.loads(draft['cart_data'])
            items_text = " | ".join([f"{item['product_name']} ×{item['quantity']}" for item in cart_data[:3]])
            if len(cart_data) > 3:
                items_text += f" ... +{len(cart_data)-3}"
            
            drafts_list.controls.append(
                ft.Container(
                    bgcolor=ft.Colors.WHITE, border_radius=10, padding=12,
                    content=ft.Row([
                        ft.Column([
                            ft.Text(f"🧾 {draft['customer_name']}", weight=ft.FontWeight.BOLD, size=self._font_m),
                            ft.Text(items_text, size=self._font_s, color=ft.Colors.GREY_600, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Text(f"💰 {draft['total_amount']:.2f} | 🕐 {draft['created_at'][:16]}", size=self._font_s, color=ft.Colors.GREY_500),
                        ], expand=True),
                        ft.Row([
                            ft.IconButton(ft.Icons.ADD_SHOPPING_CART, icon_color=ft.Colors.GREEN, tooltip="استرجاع", 
                                on_click=lambda _, d=draft: self._load_draft(d['id'])),
                            ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.RED, tooltip="حذف",
                                on_click=lambda _, d=draft: self._delete_draft(d['id'])),
                        ]),
                    ]),
                )
            )
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("📂 المسودات المحفوظة", weight=ft.FontWeight.BOLD),
            content=ft.Container(width=self._dialog_w, height=self._btn_small0, content=drafts_list),
            actions=[ft.TextButton("إغلاق", on_click=lambda _: self.close_dialog(dlg))],
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()
    
    def _load_draft(self, draft_id: int):
        """تحميل مسودة إلى السلة"""
        draft = self.db.get_draft_by_id(draft_id)
        if not draft:
            return
        
        cart_data = json.loads(draft['cart_data'])
        
        # إغلاق نافذة المسودات
        for overlay in self.page.overlay[:]:
            if isinstance(overlay, ft.AlertDialog):
                self.close_dialog(overlay)
                break
        
        self.cart = []
        for item in cart_data:
            product = self.db.get_product_by_id(item['product_id'])
            if product:
                self.cart.append({
                    "product_id": item['product_id'],
                    "product": product,
                    "quantity": item['quantity'],
                    "selling_price": item['price'],
                    "discount": item.get('discount', 0.0),
                })
        
        if draft['customer_name'] != "نقدي":
            self.selected_customer = {'id': draft.get('customer_id'), 'name': draft['customer_name']}
            self.customer_name_display.value = f"العميل: {draft['customer_name']}"
        
        self._refresh_cart_display()
        self._refresh_products_grid()
        self.show_message(f"✅ تم تحميل المسودة - {draft['customer_name']}", ft.Colors.GREEN)
    
    def _delete_draft(self, draft_id: int):
        """حذف مسودة"""
        success, msg = self.db.delete_draft(draft_id)
        self.show_message(msg, ft.Colors.GREEN if success else ft.Colors.RED)
        if success:
            # إعادة فتح نافذة المسودات
            self._show_drafts_dialog()

    # # ========== نظام البيع ==========
    
    # def show_pos(self, e=None):
    #     """نظام البيع"""
    #     self.current_page = "pos"
    #     self.cart = []
    #     self.selected_customer = None
    #     self.page.clean()
        
    #     invoice_number = self.db.get_next_invoice_number()
        
    #     header = ft.Container(
    #         padding=10, bgcolor=ft.Colors.BLUE_GREY_50, border_radius=8,
    #         content=ft.Row([
    #             ft.Row([
    #                 ft.IconButton(ft.Icons.ARROW_BACK, on_click=self.show_home),
    #                 ft.Icon(ft.Icons.RECEIPT_LONG, size=20, color=ft.Colors.BLUE_700),
    #                 ft.Text(f"فاتورة: {invoice_number}", weight="bold", size=self._font_m),
    #             ], spacing=5),
    #             ft.Text(datetime.now().strftime("%Y-%m-%d %H:%M"), size=self._font_s),
    #         ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
    #     )
        
    #     self.customer_name_display = ft.Text("العميل: نقدي (افتراضي)", weight="bold", size=self._font_m)
    #     self.customer_debt_display = ft.Text("ديون سابقة: 0.00", size=self._font_s, color=ft.Colors.RED_700)
        
    #     customer_section = ft.Container(
    #         padding=10, border=ft.border.all(1, ft.Colors.BLUE_GREY_100), border_radius=10,
    #         bgcolor=ft.Colors.WHITE,
    #         content=ft.Column([
    #             ft.Row([
    #                 ft.TextField(
    #                     hint_text="🔍 ابحث عن عميل...",
    #                     on_change=self._search_customers_pos,
    #                     expand=True, height=38, text_size=self._font_s, border_radius=8,
    #                 ),
    #             ]),
    #             ft.Row([self.customer_name_display, self.customer_debt_display], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
    #         ], spacing=5)
    #     )
        
    #     self.search_field_name = ft.TextField(
    #         hint_text="بحث باسم المنتج...",
    #         on_change=self._search_product_for_sale,
    #         expand=True, height=self._btn_h, text_size=self._font_m, border_radius=8,
    #     )
    #     self.search_field_barcode = ft.TextField(
    #         hint_text="الباركود...",
    #         on_submit=self._handle_barcode_scan,
    #         width=150, height=self._btn_h, text_size=self._font_m, border_radius=8,
    #     )
        
    #     search_section = ft.Container(
    #         content=ft.Row([
    #             self.search_field_name,
    #             self.search_field_barcode,
    #         ], spacing=10)
    #     )
        
    #     self.products_grid = ft.GridView(
    #         runs_count=self._grid_cols, max_extent=self._grid_extent, child_aspect_ratio=0.85,
    #         spacing=8, run_spacing=8, height=200,
    #     )
        
    #     self.sales_table = ft.ListView(expand=True, spacing=2)
    #     table_header = ft.Container(
    #         padding=ft.padding.symmetric(vertical=8, horizontal=5),
    #         bgcolor=ft.Colors.BLUE_700,
    #         border_radius=ft.border_radius.only(top_left=8, top_right=8),
    #         content=ft.Row([
    #             ft.Text("المنتج", expand=3, color=ft.Colors.WHITE, weight="bold", size=self._font_s),
    #             ft.Text("الكمية", expand=1, color=ft.Colors.WHITE, weight="bold", size=self._font_s),
    #             ft.Text("السعر", expand=1, color=ft.Colors.WHITE, weight="bold", size=self._font_s),
    #             ft.Text("الإجمالي", expand=1.2, color=ft.Colors.WHITE, weight="bold", size=self._font_s),
    #             ft.Text("", width=30),
    #         ])
    #     )
        
    #     self.page.add(
    #         header,
    #         customer_section,
    #         search_section,
    #         ft.Container(content=self.products_grid, border=ft.border.all(1, ft.Colors.BLUE_GREY_50), border_radius=8, bgcolor=ft.Colors.GREY_50),
    #         ft.Divider(height=1, color=ft.Colors.TRANSPARENT),
    #         ft.Container(
    #             expand=True,
    #             content=ft.Column([
    #                 table_header,
    #                 ft.Container(content=self.sales_table, expand=True, border=ft.border.all(1, ft.Colors.BLUE_GREY_100), border_radius=ft.border_radius.only(bottom_left=8, bottom_right=8)),
    #             ], spacing=0)
    #         ),
    #         ft.Container(
    #             padding=12,
    #             bgcolor=ft.Colors.WHITE,
    #             border_radius=10,
    #             shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK)),
    #             content=ft.Row([
    #                 ft.Column([
    #                     ft.Text("إجمالي الفاتورة", size=self._font_s, color=ft.Colors.BLUE_GREY_400),
    #                     ft.Row([self.total_label_pos, ft.Text("ج.م", size=self._font_m, weight="bold", color=ft.Colors.BLUE_700)]),
    #                 ], spacing=0),
    #                 ft.ElevatedButton(
    #                     "إتمام وحفظ",
    #                     icon=ft.Icons.CHECK_CIRCLE_OUTLINE,
    #                     bgcolor=ft.Colors.BLUE_700,
    #                     color=ft.Colors.WHITE,
    #                     style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
    #                     expand=True,
    #                     height=48,
    #                     on_click=self._show_checkout_options,
    #                 )
    #             ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
    #         )
    #     )
        
    #     self._refresh_cart_display()
    #     self._refresh_products_grid()
    
   



    def _refresh_products_grid(self, category=None, query=None):
        self.products_grid.controls.clear()
        if query:
            products = self.db.search_products(query)
        else:
            products = self.db.get_all_products()
        if category:
            products = [p for p in products if p.category == category]
        
        for product in products:
            if product.quantity > 0:
                # استخدم default argument لالتقاط المنتج الصحيح
                self.products_grid.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Container(
                                content=ft.Icon(ft.Icons.INVENTORY_2, size=30, color=ft.Colors.GREEN_700),
                                alignment=ft.Alignment(0, 0), expand=True,
                            ),
                            ft.Text(product.name, size=self._font_m, weight=ft.FontWeight.BOLD, max_lines=1, text_align=ft.TextAlign.CENTER),
                            ft.Text(f"{product.selling_price:.2f} ج.م", size=self._font_s, color=ft.Colors.BLUE_700, weight=ft.FontWeight.BOLD),
                            ft.Text(f"متوفر: {product.quantity}", size=10, color=ft.Colors.GREY_600),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                        bgcolor=ft.Colors.WHITE, border_radius=12, padding=10, ink=True,
                        on_click=lambda _, prod=product: self._add_to_cart(prod),  # 👈 prod=product يثبت القيمة
                        shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK)),
                    )
                )
        self.page.update()



    def _search_product_for_sale(self, e):
        query = e.control.value.strip() if e and e.control.value else ""
        self._refresh_products_grid(query=query if query else None)
    
    def _handle_barcode_scan(self, e):
        query = e.control.value.strip()
        if not query:
            return
        all_prods = self.db.get_all_products()
        for p in all_prods:
            if p.barcode == query:
                self._add_to_cart(p)
                e.control.value = ""
                e.control.focus()
                self.page.update()
                return
        self._search_product_for_sale(e)
    
    def _add_to_cart(self, product: Product):
        for item in self.cart:
            if item["product_id"] == product.id:
                if item["quantity"] + 1 > product.quantity:
                    self.show_message(f"الكمية المتوفرة فقط: {product.quantity}", ft.Colors.RED)
                    return
                item["quantity"] += 1
                self._refresh_cart_display()
                return
        if product.quantity > 0:
            self.cart.append({
                "product_id": product.id,
                "product": product,
                "quantity": 1,
                "selling_price": product.selling_price,
                "discount": 0.0,
            })
            self._refresh_cart_display()
        else:
            self.show_message(f"المنتج {product.name} غير متوفر", ft.Colors.RED)
    
    def _refresh_cart_display(self):
        self.sales_table.controls.clear()
        total = 0
        
        for item in self.cart:
            product = item["product"]
            quantity = item["quantity"]
            selling_price = item.get("selling_price", product.selling_price)
            discount = item.get("discount", 0.0)
            subtotal = (selling_price - discount) * quantity
            total += subtotal
            
            self.sales_table.controls.append(
                ft.Container(
                    padding=5,
                    border=ft.border.only(bottom=ft.border.BorderSide(1, ft.Colors.BLUE_GREY_50)),
                    content=ft.Row([
                        ft.Text(product.name, expand=3, size=self._font_s, weight="bold", max_lines=1),
                        ft.Row([
                            ft.IconButton(ft.Icons.REMOVE_CIRCLE_OUTLINE, icon_size=self._icon_s, on_click=lambda _, it=item: self._update_cart_quantity(it, -1)),
                            ft.Text(str(quantity), size=self._font_s, weight="bold"),
                            ft.IconButton(ft.Icons.ADD_CIRCLE_OUTLINE, icon_size=self._icon_s, on_click=lambda _, it=item: self._update_cart_quantity(it, 1)),
                        ], expand=1, spacing=0, alignment=ft.MainAxisAlignment.CENTER),
                        ft.Text(f"{selling_price:.2f}", expand=1, size=self._font_s),
                        ft.Text(f"{subtotal:.2f}", expand=1.2, size=self._font_s, weight="bold", color=ft.Colors.BLUE_700),
                        ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_size=self._icon_s, icon_color=ft.Colors.RED_400, on_click=lambda _, it=item: self._remove_from_cart(it)),
                    ], alignment=ft.MainAxisAlignment.CENTER)
                )
            )
        
        self.total_label_pos.value = f"{total:.2f}"
        
        if not self.cart:
            self.sales_table.controls.append(
                ft.Container(
                    alignment=ft.Alignment(0, 0), padding=50,
                    content=ft.Column([
                        ft.Icon(ft.Icons.SHOPPING_BASKET_OUTLINED, size=40, color=ft.Colors.BLUE_GREY_100),
                        ft.Text("فاتورة خالية", color=ft.Colors.BLUE_GREY_200, size=self._font_s),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                )
            )
        self.page.update()
    
    def _update_cart_quantity(self, item, change):
        new_quantity = item["quantity"] + change
        if new_quantity > 0:
            if new_quantity <= item["product"].quantity:
                item["quantity"] = new_quantity
                self._refresh_cart_display()
            else:
                self.show_message(f"الكمية المتوفرة فقط: {item['product'].quantity}", ft.Colors.RED)
        elif new_quantity == 0:
            self._remove_from_cart(item)
    
    def _remove_from_cart(self, item):
        if item in self.cart:
            self.cart.remove(item)
            self._refresh_cart_display()
    
    def _search_customers_pos(self, e):
        query = e.control.value.strip()
        if not query:
            self.selected_customer = None
            self.customer_name_display.value = "العميل: نقدي (افتراضي)"
            self.customer_debt_display.value = "ديون سابقة: 0.00"
            self.page.update()
            return
        customers = self.db.search_customers(query)
        if customers:
            c = customers[0]
            self.selected_customer = c
            self.customer_name_display.value = f"العميل: {c['name']}"
            summary = self.db.get_customer_summary(c['id'])
            self.customer_debt_display.value = f"ديون سابقة: {summary['total_debt']:.2f}"
            self.page.update()



    def _show_checkout_options(self, e):
        if not self.cart:
            self.show_message("السلة فارغة!", ft.Colors.RED)
            return
        
        # حساب الإجمالي
        total = sum(
            (float(item.get("selling_price", item["product"].selling_price)) - float(item.get("discount", 0.0))) * item["quantity"]
            for item in self.cart
        )
        
        dlg = ft.BottomSheet(
            ft.Container(
                padding=20,
                content=ft.Column([
                    ft.Text(f"الإجمالي: {total:.2f} ج.م", size=20, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.MONEY, color=ft.Colors.GREEN),
                        title=ft.Text("دفع نقدي (كامل)"),
                        subtitle=ft.Text(f"يدفع {total:.2f} ج.م"),
                        on_click=lambda _: [self.close_dialog(dlg), self._complete_sale(customer=self.selected_customer['name'] if self.selected_customer else "", is_debt=False)]
                    ),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.CREDIT_CARD, color=ft.Colors.ORANGE),
                        title=ft.Text("بيع آجل (بدون دفعة)"),
                        subtitle=ft.Text(f"كامل المبلغ دين"),
                        on_click=lambda _: [self.close_dialog(dlg), self._complete_sale_with_partial_payment(total, 0)]
                    ),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.PAYMENT, color=ft.Colors.BLUE),
                        title=ft.Text("بيع آجل مع دفعة جزئية"),
                        subtitle=ft.Text("تحديد المبلغ المدفوع"),
                        on_click=lambda _: [self.close_dialog(dlg), self._show_partial_payment_dialog(total)]
                    ),
                ], tight=True)
            )
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def _show_partial_payment_dialog(self, total_amount: float):
        """نافذة تحديد الدفعة الجزئية"""
        paid_field = ft.TextField(
            label=f"المبلغ المدفوع (الإجمالي: {total_amount:.2f})",
            keyboard_type=ft.KeyboardType.NUMBER,
            autofocus=True,
            prefix_icon=ft.Icons.MONEY,
            border_radius=10,
            hint_text="أدخل المبلغ المدفوع",
        )
        
        remaining_text = ft.Text(f"المتبقي: {total_amount:.2f}", size=self._font_m, color=ft.Colors.ORANGE)
        
        def on_change(e):
            try:
                paid = float(paid_field.value or 0)
                if paid > total_amount:
                    paid_field.value = str(total_amount)
                    paid = total_amount
                remaining = total_amount - paid
                remaining_text.value = f"المدفوع: {paid:.2f} | المتبقي: {remaining:.2f}"
            except:
                remaining_text.value = f"المتبقي: {total_amount:.2f}"
            self.page.update()
        
        paid_field.on_change = on_change
        
        def confirm(e):
            try:
                paid = float(paid_field.value or 0)
                if paid < 0:
                    paid = 0
                if paid > total_amount:
                    paid = total_amount
                dlg.open = False
                self.page.update()
                self._complete_sale_with_partial_payment(total_amount, paid)
            except ValueError:
                dlg.open = False
                self.page.update()
                self._complete_sale_with_partial_payment(total_amount, 0)
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row([ft.Icon(ft.Icons.PAYMENT, color=ft.Colors.ORANGE), ft.Text("دفعة جزئية", weight=ft.FontWeight.BOLD)]),
            content=ft.Column([paid_field, ft.Container(height=10), remaining_text], tight=True, spacing=10),
            actions=[
                ft.TextButton("إلغاء", on_click=lambda _: self.close_dialog(dlg)),
                ft.ElevatedButton("تأكيد", on_click=confirm, bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE),
            ],
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def _complete_sale_with_partial_payment(self, total_amount: float, paid_amount: float):
        """إتمام البيع مع دفعة جزئية"""
        if not self.cart:
            return
        
        # إذا كان فيه عميل مختار، استخدمه. وإلا اسأل عن اسم العميل
        if self.selected_customer:
            self._complete_sale_with_customer(self.selected_customer['name'], total_amount, paid_amount)
        else:
            customer_field = ft.TextField(label="اسم العميل", autofocus=True)
            
            def confirm(e):
                if customer_field.value.strip():
                    dlg.open = False
                    self.page.update()
                    self._complete_sale_with_customer(customer_field.value.strip(), total_amount, paid_amount)
                else:
                    self.show_message("يرجى إدخال اسم العميل", ft.Colors.RED)
            
            dlg = ft.AlertDialog(
                modal=True,
                title=ft.Text("بيع آجل - اسم العميل"),
                content=ft.Column([ft.Text("أدخل اسم العميل:"), customer_field], tight=True, spacing=10),
                actions=[
                    ft.TextButton("إلغاء", on_click=lambda _: self.close_dialog(dlg)),
                    ft.ElevatedButton("تأكيد", on_click=confirm, bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE),
                ],
            )
            self.page.overlay.append(dlg)
            dlg.open = True
            self.page.update()

    def _complete_sale_with_customer(self, customer_name: str, total_amount: float, paid_amount: float):
        """تنفيذ عملية البيع"""
        cart_items = []
        for item in self.cart:
            selling_price = float(item.get("selling_price", item["product"].selling_price))
            discount = float(item.get("discount", 0.0))
            qty = int(item['quantity'])
            cart_items.append({
                'product_id': int(item['product_id']),
                'product_name': str(item['product'].name),
                'quantity': qty,
                'price': selling_price,
                'discount': discount,
            })
        
        # البحث عن العميل أو إنشائه
        customer_id = None
        if customer_name and customer_name.strip():
            customer_data = self.db.get_customer_by_name(customer_name)
            if not customer_data:
                success, _, new_id = self.db.add_customer(customer_name)
                if success:
                    customer_id = int(new_id)
            else:
                customer_id = int(customer_data['id'])
        
        remaining = total_amount - paid_amount
        payment_type = "آجل" if remaining > 0 else "نقدي"
        user_id = int(self.current_user.get('id')) if self.current_user else None
        
        success, message, sale_id = self.db.process_invoice(
            cart_items, customer_id, paid_amount, payment_type,
            f"إجمالي: {total_amount:.2f}", user_id
        )
        
        if success:
            # تسجيل الدين إذا فيه باقي
            if customer_id and remaining > 0:
                self.db.add_debt(
                    customer_id, customer_name, sale_id, remaining,
                    f"فاتورة #{sale_id} - دفع {paid_amount:.2f} وباقي {remaining:.2f}"
                )
            
            msg = f"✅ تم البيع بنجاح!\nالإجمالي: {total_amount:.2f}\nالمدفوع: {paid_amount:.2f}\nالباقي: {remaining:.2f}"
            self.show_message(msg, ft.Colors.GREEN)
            self.cart = []
            self.selected_customer = None
            self._refresh_cart_display()
            self.show_home()
        else:
            self.show_message(f"❌ خطأ: {message}", ft.Colors.RED)
        
  



    # ============================================================
    # إدارة العملاء المتكاملة (جميع الدوال)
    # ============================================================
    
    def show_customers(self, e=None):
        """الصفحة الرئيسية لإدارة العملاء - لوحة تحكم متكاملة"""
        self.current_page = "customers"
        self.page.clean()
        
        # إحصائيات
        customers = self.db.get_all_customers()
        total_customers = len(customers)
        total_debts = sum(c['total_debt'] for c in customers)
        total_paid = sum(c['total_paid'] for c in customers)
        remaining = total_debts - total_paid
        overdue_debts = len(self.db.get_overdue_debts()) if hasattr(self.db, 'get_overdue_debts') else 0
        
        # شريط البحث
        search_field = ft.TextField(
            hint_text="🔍 بحث بالاسم، الهاتف، البريد...",
            on_change=lambda e: self._filter_customers(e.control.value),
            expand=True, border_radius=12, prefix_icon=ft.Icons.SEARCH, height=self._btn_h,
            suffix=ft.IconButton(ft.Icons.CLEAR, on_click=lambda _: self._clear_search(search_field))
        )
        
        # أزرار الإجراءات السريعة
        add_button = ft.ElevatedButton("➕ عميل جديد", on_click=self.show_add_customer_dialog,
            bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)), height=self._btn_h)
        
        send_all_button = ft.OutlinedButton("📩 تذكير جماعي", on_click=self.send_debt_reminders_to_all,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), side=ft.BorderSide(1, ft.Colors.ORANGE), color=ft.Colors.ORANGE), height=self._btn_h)
        
        export_button = ft.OutlinedButton("📊 تصدير", on_click=self.export_customers_list,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), side=ft.BorderSide(1, ft.Colors.BLUE), color=ft.Colors.BLUE), height=self._btn_h)
        
        # بطاقات إحصائية
        stats_row = ft.ResponsiveRow([
            self._create_stat_card("عدد العملاء", str(total_customers), ft.Icons.PEOPLE, ft.Colors.BLUE),
            self._create_stat_card("إجمالي الديون", f"{total_debts:.0f}", ft.Icons.MONEY_OFF, ft.Colors.RED),
            self._create_stat_card("المسدد", f"{total_paid:.0f}", ft.Icons.PAYMENTS, ft.Colors.GREEN),
            self._create_stat_card("المتبقي", f"{remaining:.0f}", ft.Icons.ACCOUNT_BALANCE, ft.Colors.ORANGE),
        ], spacing=10)
        
        # أزرار تصفية سريعة
        filter_chips = ft.Row([
            ft.Chip(label=ft.Text("الكل"), on_click=lambda _: self._filter_by_status("all"), bgcolor=ft.Colors.BLUE_50, leading=ft.Icon(ft.Icons.PEOPLE)),
            ft.Chip(label=ft.Text(f"عليهم ديون ({sum(1 for c in customers if c['total_debt'] > c['total_paid'])})"), on_click=lambda _: self._filter_by_status("debt"), bgcolor=ft.Colors.RED_50, leading=ft.Icon(ft.Icons.WARNING)),
            ft.Chip(label=ft.Text(f"مسددين ({sum(1 for c in customers if c['total_debt'] > 0 and c['total_debt'] <= c['total_paid'])})"), on_click=lambda _: self._filter_by_status("paid"), bgcolor=ft.Colors.GREEN_50, leading=ft.Icon(ft.Icons.CHECK_CIRCLE)),
            ft.Chip(label=ft.Text(f"بدون معاملات ({sum(1 for c in customers if c['total_debt'] == 0)})"), on_click=lambda _: self._filter_by_status("new"), bgcolor=ft.Colors.GREY_50, leading=ft.Icon(ft.Icons.INFO)),
        ], scroll=ft.ScrollMode.AUTO)
        
        # قائمة العملاء
        self.customers_list = ft.ListView(expand=True, spacing=8, padding=10)
        
        # تبويبات
          # أزرار تصفية بدل التبويبات
        tabs = ft.Row([
            ft.ElevatedButton("📋 الكل", on_click=lambda _: self._filter_by_status("all"), style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20)), height=self._btn_small),
            ft.ElevatedButton("💰 المديونين", on_click=lambda _: self._filter_by_status("debt"), style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20)), height=self._btn_small),
            ft.ElevatedButton("✅ المسددين", on_click=lambda _: self._filter_by_status("paid"), style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20)), height=self._btn_small),
            ft.ElevatedButton("🆕 الجدد", on_click=lambda _: self._filter_by_status("new"), style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20)), height=self._btn_small),
        ], scroll=ft.ScrollMode.AUTO, spacing=5)
        
        self.page.add(
            ft.AppBar(
                title=ft.Text("👥 إدارة العملاء", color=ft.Colors.WHITE, size=18, weight=ft.FontWeight.BOLD),
                bgcolor=ft.Colors.PURPLE_700,
                leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=self.show_home, icon_color=ft.Colors.WHITE),
                actions=[
                    ft.IconButton(ft.Icons.SMS, icon_color=ft.Colors.WHITE, tooltip="تذكير جماعي", on_click=self.send_debt_reminders_to_all),
                    ft.IconButton(ft.Icons.FILE_DOWNLOAD, icon_color=ft.Colors.WHITE, tooltip="تصدير", on_click=self.export_customers_list),
                ]
            ),
            ft.Container(expand=True, padding=15,
                content=ft.Column([
                    stats_row,
                    ft.Container(height=10),
                    ft.Row([search_field, add_button], spacing=10),
                    ft.Container(height=5),
                    filter_chips,
                    ft.Container(height=10),
                    ft.Container(content=self.customers_list, expand=True),
                ], expand=True)),
        )
        self._render_customers_list(self.db.get_all_customers())
    
    # ========== تصفية العملاء ==========
    
    def _filter_customers(self, query):
        """تصفية العملاء حسب البحث"""
        if query:
            customers = self.db.search_customers(query)
        else:
            customers = self.db.get_all_customers()
        self._render_customers_list(customers)
    
    def _clear_search(self, search_field):
        """مسح البحث"""
        search_field.value = ""
        self._render_customers_list(self.db.get_all_customers())
        self.page.update()
    
    def _filter_by_status(self, status):
        """تصفية العملاء حسب الحالة"""
        customers = self.db.get_all_customers()
        if status == "debt":
            customers = [c for c in customers if c['total_debt'] > c['total_paid']]
        elif status == "paid":
            customers = [c for c in customers if c['total_debt'] > 0 and c['total_debt'] <= c['total_paid']]
        elif status == "new":
            customers = [c for c in customers if c['total_debt'] == 0]
        self._render_customers_list(customers)
    
    def _on_tab_change(self, e):
        """تغيير التبويب"""
        tab_index = e.control.selected_index
        if tab_index == 0:
            self._filter_by_status("all")
        elif tab_index == 1:
            self._filter_by_status("debt")
        elif tab_index == 2:
            self._filter_by_status("paid")
        elif tab_index == 3:
            self._filter_by_status("new")
    
    # ========== عرض قائمة العملاء ==========
    
    def _render_customers_list(self, customers):
        """عرض قائمة العملاء بتصميم متطور"""
        self.customers_list.controls.clear()
        
        if not customers:
            self.customers_list.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.PEOPLE_OUTLINE, size=60, color=ft.Colors.GREY_300),
                        ft.Text("لا يوجد عملاء", size=18, color=ft.Colors.GREY_400, weight=ft.FontWeight.BOLD),
                        ft.Text("اضغط على 'عميل جديد' لإضافة أول عميل", size=self._font_m, color=ft.Colors.GREY_400),
                    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.center, padding=50,
                )
            )
            self.page.update()
            return
        
        for customer in customers:
            remaining = customer['total_debt'] - customer['total_paid']
            
            # تحديد حالة العميل
            if remaining > 0:
                status_color, status_bg, status_text, status_icon = ft.Colors.RED_700, ft.Colors.RED_50, "عليه دين", ft.Icons.WARNING
            elif customer['total_debt'] > 0:
                status_color, status_bg, status_text, status_icon = ft.Colors.GREEN_700, ft.Colors.GREEN_50, "مسدد", ft.Icons.CHECK_CIRCLE
            else:
                status_color, status_bg, status_text, status_icon = ft.Colors.BLUE_700, ft.Colors.BLUE_50, "جديد", ft.Icons.INFO
            
            # بطاقة العميل
            self.customers_list.controls.append(
                ft.Container(
                    bgcolor=ft.Colors.WHITE, border_radius=12, padding=15,
                    shadow=ft.BoxShadow(blur_radius=8, color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK)),
                    content=ft.Column([
                        # الصف الأول: الاسم والحالة
                        ft.Row([
                            ft.Container(
                                content=ft.Text(customer['name'][0].upper(), size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                bgcolor=ft.Colors.PURPLE_500, border_radius=25, width=45, height=self._btn_h, alignment=ft.alignment.center,
                            ),
                            ft.Container(width=10),
                            ft.Column([
                                ft.Text(customer['name'], size=self._font_l, weight=ft.FontWeight.BOLD),
                                ft.Text(f"📱 {customer['phone'] or 'غير مسجل'}", size=self._font_s, color=ft.Colors.GREY_600),
                                ft.Text(f"📧 {customer.get('email', '') or 'بدون بريد'}", size=self._font_s, color=ft.Colors.GREY_500) if customer.get('email') else ft.Container(),
                            ], expand=True),
                            ft.Container(
                                content=ft.Row([ft.Icon(status_icon, size=self._font_m, color=status_color), ft.Text(status_text, size=self._font_s, weight=ft.FontWeight.BOLD, color=status_color)], spacing=3),
                                bgcolor=status_bg, border_radius=15, padding=ft.padding.symmetric(horizontal=10, vertical=4),
                            ),
                            ft.PopupMenuButton(
                                icon=ft.Icons.MORE_VERT,
                                items=[
                                    ft.PopupMenuItem(text="📊 كشف حساب", on_click=lambda _, c=customer: self.show_customer_ledger(c['id'], c['name'])),
                                    ft.PopupMenuItem(text="💵 تسجيل سداد", on_click=lambda _, c=customer: self.show_payment_dialog(c['id'], c['name'])),
                                    ft.PopupMenuItem(text="📩 إرسال رسالة", on_click=lambda _, c=customer: self.send_sms_to_customer(c['id'], c['name'], c.get('phone', ''))),
                                    ft.PopupMenuItem(),
                                    ft.PopupMenuItem(text="📝 تعديل", on_click=lambda _, c=customer: self.show_edit_customer_dialog(c)),
                                    ft.PopupMenuItem(text="🗑️ حذف", on_click=lambda _, c=customer: self.delete_customer(c['id'], c['name'])),
                                ],
                            ),
                        ]),
                        ft.Container(height=10), ft.Divider(color=ft.Colors.GREY_200), ft.Container(height=10),
                        # الصف الثاني: المعلومات المالية
                        ft.Row([
                            ft.Container(
                                content=ft.Column([
                                    ft.Text("إجمالي الدين", size=10, color=ft.Colors.GREY_500),
                                    ft.Text(f"{customer['total_debt']:.2f} ج.م", size=self._font_m, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700),
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                                expand=True, bgcolor=ft.Colors.RED_50, border_radius=8, padding=8,
                            ),
                            ft.Container(width=8),
                            ft.Container(
                                content=ft.Column([
                                    ft.Text("المسدد", size=10, color=ft.Colors.GREY_500),
                                    ft.Text(f"{customer['total_paid']:.2f} ج.م", size=self._font_m, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700),
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                                expand=True, bgcolor=ft.Colors.GREEN_50, border_radius=8, padding=8,
                            ),
                            ft.Container(width=8),
                            ft.Container(
                                content=ft.Column([
                                    ft.Text("المتبقي", size=10, color=ft.Colors.GREY_500),
                                    ft.Text(f"{remaining:.2f} ج.م", size=self._font_m, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_700 if remaining > 0 else ft.Colors.GREEN_700),
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                                expand=True, bgcolor=ft.Colors.ORANGE_50 if remaining > 0 else ft.Colors.GREEN_50, border_radius=8, padding=8,
                            ),
                        ]),
                        ft.Container(height=10),
                        # الصف الثالث: أزرار سريعة
                        ft.Row([
                            ft.OutlinedButton("📊 كشف حساب", on_click=lambda _, c=customer: self.show_customer_ledger(c['id'], c['name']),
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), side=ft.BorderSide(1, ft.Colors.BLUE), color=ft.Colors.BLUE), height=self._btn_small, expand=True),
                            ft.Container(width=5),
                            ft.OutlinedButton("💵 سداد", on_click=lambda _, c=customer: self.show_payment_dialog(c['id'], c['name']),
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), side=ft.BorderSide(1, ft.Colors.GREEN), color=ft.Colors.GREEN),
                                height=self._btn_small, expand=True, visible=remaining > 0),
                            ft.Container(width=5),
                            ft.IconButton(ft.Icons.SMS, icon_color=ft.Colors.BLUE, tooltip="إرسال رسالة",
                                on_click=lambda _, c=customer: self.send_sms_to_customer(c['id'], c['name'], c.get('phone', ''))),
                        ], scroll=ft.ScrollMode.AUTO),
                    ]),
                )
            )
        self.page.update()
    
    # ========== إضافة عميل ==========
    
    def show_add_customer_dialog(self, e=None):
        """نافذة إضافة عميل جديدة"""
        name_field = ft.TextField(label="اسم العميل *", autofocus=True, prefix_icon=ft.Icons.PERSON, border_radius=10)
        phone_field = ft.TextField(label="رقم الهاتف", prefix_icon=ft.Icons.PHONE, keyboard_type=ft.KeyboardType.PHONE, border_radius=10)
        email_field = ft.TextField(label="البريد الإلكتروني", prefix_icon=ft.Icons.EMAIL, border_radius=10)
        address_field = ft.TextField(label="العنوان", prefix_icon=ft.Icons.LOCATION_ON, border_radius=10, multiline=True, min_lines=1, max_lines=2)
        notes_field = ft.TextField(label="ملاحظات", prefix_icon=ft.Icons.NOTE, border_radius=10, multiline=True, min_lines=1, max_lines=3)
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row([ft.Icon(ft.Icons.PERSON_ADD, color=ft.Colors.GREEN_700), ft.Text("إضافة عميل جديد", weight=ft.FontWeight.BOLD, size=18)]),
            content=ft.Container(width=self._dialog_w, height=self._btn_h0,
                content=ft.Column([name_field, phone_field, email_field, address_field, notes_field], tight=True, spacing=10, scroll=ft.ScrollMode.AUTO)),
            actions=[
                ft.TextButton("إلغاء", on_click=lambda _: self.close_dialog(dlg)),
                ft.ElevatedButton("💾 حفظ", on_click=lambda _: self._save_customer(name_field, phone_field, email_field, address_field, notes_field, dlg),
                    bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))),
            ],
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()
    
    def _save_customer(self, name_field, phone_field, email_field, address_field, notes_field, dlg):
        """حفظ العميل الجديد"""
        if not name_field.value or not name_field.value.strip():
            self.show_message("⚠️ يرجى إدخال اسم العميل", ft.Colors.RED)
            return
        success, msg, _ = self.db.add_customer(
            name_field.value.strip(), phone_field.value or "", email_field.value or "",
            address_field.value or "", notes_field.value or ""
        )
        if success:
            self.show_message(f"✅ {msg}", ft.Colors.GREEN)
            self.close_dialog(dlg)
            self._render_customers_list(self.db.get_all_customers())
        else:
            self.show_message(f"❌ {msg}", ft.Colors.RED)
    
    # ========== تعديل عميل ==========
    
    def show_edit_customer_dialog(self, customer: Dict):
        """نافذة تعديل بيانات العميل"""
        name_field = ft.TextField(label="اسم العميل *", value=customer['name'], prefix_icon=ft.Icons.PERSON, border_radius=10)
        phone_field = ft.TextField(label="رقم الهاتف", value=customer.get('phone', ''), prefix_icon=ft.Icons.PHONE, keyboard_type=ft.KeyboardType.PHONE, border_radius=10)
        email_field = ft.TextField(label="البريد الإلكتروني", value=customer.get('email', ''), prefix_icon=ft.Icons.EMAIL, border_radius=10)
        address_field = ft.TextField(label="العنوان", value=customer.get('address', ''), prefix_icon=ft.Icons.LOCATION_ON, border_radius=10, multiline=True, min_lines=1, max_lines=2)
        notes_field = ft.TextField(label="ملاحظات", value=customer.get('notes', ''), prefix_icon=ft.Icons.NOTE, border_radius=10, multiline=True, min_lines=1, max_lines=3)
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row([ft.Icon(ft.Icons.EDIT, color=ft.Colors.BLUE_700), ft.Text(f"تعديل: {customer['name']}", weight=ft.FontWeight.BOLD, size=18)]),
            content=ft.Container(width=self._dialog_w, height=self._btn_h0,
                content=ft.Column([name_field, phone_field, email_field, address_field, notes_field], tight=True, spacing=10, scroll=ft.ScrollMode.AUTO)),
            actions=[
                ft.TextButton("إلغاء", on_click=lambda _: self.close_dialog(dlg)),
                ft.ElevatedButton("💾 حفظ التعديلات", on_click=lambda _: self._update_customer(customer['id'], name_field, phone_field, email_field, address_field, notes_field, dlg),
                    bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))),
            ],
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()
    
    def _update_customer(self, customer_id, name_field, phone_field, email_field, address_field, notes_field, dlg):
        """تحديث بيانات العميل"""
        if not name_field.value or not name_field.value.strip():
            self.show_message("⚠️ يرجى إدخال اسم العميل", ft.Colors.RED)
            return
        cursor = self.db.conn.cursor()
        try:
            cursor.execute("UPDATE customers SET name=?, phone=?, email=?, address=?, notes=? WHERE id=?",
                           (name_field.value.strip(), phone_field.value, email_field.value, address_field.value, notes_field.value, customer_id))
            self.db.conn.commit()
            self.show_message("✅ تم تحديث بيانات العميل بنجاح", ft.Colors.GREEN)
            self.close_dialog(dlg)
            self._render_customers_list(self.db.get_all_customers())
        except Exception as e:
            self.show_message(f"❌ خطأ: {str(e)}", ft.Colors.RED)
    
    # ========== حذف عميل ==========
    
    def delete_customer(self, customer_id: int, customer_name: str):
        """تأكيد حذف العميل"""
        # التحقق من وجود ديون
        summary = self.db.get_customer_summary(customer_id)
        has_debt = summary['total_debt'] > summary['total_paid']
        
        warning_text = ""
        if has_debt:
            warning_text = f"\n\n⚠️ تحذير: العميل عليه ديون متبقية بقيمة {(summary['total_debt'] - summary['total_paid']):.2f} ج.م"
        
        def confirm_delete(e):
            cursor = self.db.conn.cursor()
            try:
                # حذف الديون والمدفوعات المرتبطة
                cursor.execute("DELETE FROM payments WHERE customer_id=?", (customer_id,))
                cursor.execute("DELETE FROM debts WHERE customer_id=?", (customer_id,))
                cursor.execute("DELETE FROM customer_transactions WHERE customer_id=?", (customer_id,))
                cursor.execute("DELETE FROM customers WHERE id=?", (customer_id,))
                self.db.conn.commit()
                self.show_message("✅ تم حذف العميل بنجاح", ft.Colors.GREEN)
                self.close_dialog(dlg)
                self._render_customers_list(self.db.get_all_customers())
            except Exception as e:
                self.show_message(f"❌ خطأ: {str(e)}", ft.Colors.RED)
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row([ft.Icon(ft.Icons.DELETE, color=ft.Colors.RED), ft.Text("تأكيد الحذف", weight=ft.FontWeight.BOLD)]),
            content=ft.Text(f"هل أنت متأكد من حذف العميل '{customer_name}'؟\nلا يمكن التراجع عن هذا الإجراء.{warning_text}", size=self._font_m),
            actions=[
                ft.TextButton("إلغاء", on_click=lambda _: self.close_dialog(dlg)),
                ft.ElevatedButton("🗑️ حذف", on_click=confirm_delete, bgcolor=ft.Colors.RED, color=ft.Colors.WHITE),
            ],
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()
        
    def show_payment_dialog(self, customer_id: int, customer_name: str, debt_id: int = None):
        """نافذة تسجيل سداد"""
        debts = self.db.get_customer_debts(customer_id)
        total_remaining = sum(d['remaining'] for d in debts)
        
        amount_field = ft.TextField(
            label=f"المبلغ (المتبقي: {total_remaining:.2f} ج.م)", 
            keyboard_type=ft.KeyboardType.NUMBER, 
            autofocus=True,
            prefix_icon=ft.Icons.MONEY, 
            border_radius=10, 
            hint_text="أدخل المبلغ المراد سداده"
        )
        note_field = ft.TextField(
            label="ملاحظة (اختياري)", 
            prefix_icon=ft.Icons.NOTE, 
            border_radius=10, 
            multiline=True, 
            min_lines=1, 
            max_lines=2
        )
        
        debt_selector = None
        content_controls = []
        
        if debts and not debt_id:
            debt_options = [
                ft.dropdown.Option(
                    str(d['id']), 
                    f"فاتورة #{d['sale_id']} - المتبقي: {d['remaining']:.2f} ({d['created_at'][:10]})"
                ) for d in debts
            ]
            debt_selector = ft.Dropdown(
                label="اختر الدين المراد سداده", 
                options=debt_options, 
                border_radius=10
            )
            content_controls.append(debt_selector)
        
        content_controls.extend([amount_field, note_field])
        
        def process(e):
            try:
                amount = float(amount_field.value or 0)
                if amount <= 0:
                    self.show_message("⚠️ المبلغ يجب أن يكون أكبر من 0", ft.Colors.RED)
                    return
            except ValueError:
                self.show_message("⚠️ يرجى إدخال مبلغ صحيح", ft.Colors.RED)
                return
            
            user_id = self.current_user.get('id') if self.current_user else None
            
            # ✅ إصلاح المشكلة: التحقق من القيمة قبل التحويل
            if debt_selector and debt_selector.value:
                try:
                    selected_debt = int(debt_selector.value)
                except (ValueError, TypeError):
                    self.show_message("⚠️ يرجى اختيار دين صحيح", ft.Colors.RED)
                    return
            else:
                selected_debt = debt_id
            
            if not selected_debt:
                self.show_message("⚠️ لا يوجد دين محدد", ft.Colors.RED)
                return
            
            success, message = self.db.make_payment(
                customer_id, customer_name, selected_debt, amount, note_field.value, user_id
            )
            if success:
                self.show_message(f"✅ {message}", ft.Colors.GREEN)
                self.close_dialog(dlg)
                self._render_customers_list(self.db.get_all_customers())
            else:
                self.show_message(f"❌ {message}", ft.Colors.RED)
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.PAYMENT, color=ft.Colors.GREEN_700), 
                ft.Text(f"تسجيل سداد - {customer_name}", weight=ft.FontWeight.BOLD, size=18)
            ]),
            content=ft.Container(
                width=400, 
                content=ft.Column(content_controls, tight=True, spacing=10)
            ),
            actions=[
                ft.TextButton("إلغاء", on_click=lambda _: self.close_dialog(dlg)),
                ft.ElevatedButton(
                    "💵 تسجيل السداد", 
                    on_click=process, 
                    bgcolor=ft.Colors.GREEN_700, 
                    color=ft.Colors.WHITE, 
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                )
            ]
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()
        
    # ========== كشف حساب ==========
    
    def show_customer_ledger(self, customer_id: int, customer_name: str):
        """كشف حساب العميل"""
        self.page.clean()
        ledger = self.db.get_customer_ledger(customer_id)
        summary = self.db.get_customer_summary(customer_id)
        customer = self.db.get_customer_by_id(customer_id)
        
        header = ft.Container(padding=20, bgcolor=ft.Colors.WHITE, border_radius=15,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK)),
            content=ft.Column([
                ft.Row([
                    ft.Container(content=ft.Text(customer_name[0].upper(), size=30, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        bgcolor=ft.Colors.PURPLE_500, border_radius=30, width=55, height=55, alignment=ft.alignment.center),
                    ft.Container(width=15),
                    ft.Column([
                        ft.Text(customer_name, size=22, weight=ft.FontWeight.BOLD),
                        ft.Text(f"📱 {customer.get('phone', 'غير مسجل')} | 📧 {customer.get('email', 'غير مسجل')}", size=self._font_m, color=ft.Colors.GREY_600),
                        ft.Text(f"📍 {customer.get('address', 'غير مسجل')}", size=self._font_s, color=ft.Colors.GREY_500),
                    ], expand=True),
                    ft.IconButton(ft.Icons.SMS, icon_color=ft.Colors.BLUE, tooltip="إرسال رسالة",
                        on_click=lambda _: self.send_sms_to_customer(customer_id, customer_name, customer.get('phone', ''))),
                ]),
                ft.Container(height=15), ft.Divider(), ft.Container(height=10),
                ft.Row([
                    ft.Container(content=ft.Column([ft.Text("إجمالي الدين", size=self._font_s, color=ft.Colors.GREY_500),
                        ft.Text(f"{summary.get('total_debt', 0):.2f} ج.م", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700)],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=3), expand=True),
                    ft.VerticalDivider(),
                    ft.Container(content=ft.Column([ft.Text("المسدد", size=self._font_s, color=ft.Colors.GREY_500),
                        ft.Text(f"{summary.get('total_paid', 0):.2f} ج.م", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700)],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=3), expand=True),
                    ft.VerticalDivider(),
                    ft.Container(content=ft.Column([ft.Text("المتبقي", size=self._font_s, color=ft.Colors.GREY_500),
                        ft.Text(f"{summary.get('total_debt', 0) - summary.get('total_paid', 0):.2f} ج.م", size=18, weight=ft.FontWeight.BOLD,
                            color=ft.Colors.ORANGE_700 if (summary.get('total_debt', 0) - summary.get('total_paid', 0)) > 0 else ft.Colors.GREEN_700)],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=3), expand=True),
                ]),
            ]))
        
        ledger_list = ft.ListView(expand=True, spacing=8)
        if not ledger:
            ledger_list.controls.append(ft.Container(content=ft.Column([ft.Icon(ft.Icons.HISTORY, size=50, color=ft.Colors.GREY_300),
                ft.Text("لا توجد حركات مالية", size=self._font_l, color=ft.Colors.GREY_400)], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.center, padding=50))
        else:
            for record in ledger:
                is_debit = record['debit'] > 0
                color = ft.Colors.RED_700 if is_debit else ft.Colors.GREEN_700
                bg = ft.Colors.RED_50 if is_debit else ft.Colors.GREEN_50
                icon = ft.Icons.ARROW_DOWNWARD if is_debit else ft.Icons.ARROW_UPWARD
                tag = "دين (عليه)" if is_debit else "سداد (له)"
                amount = record['debit'] if is_debit else record['credit']
                
                ledger_list.controls.append(ft.Container(bgcolor=ft.Colors.WHITE, border_radius=10, padding=12,
                    border=ft.border.only(left=ft.border.BorderSide(4, color)),
                    shadow=ft.BoxShadow(blur_radius=3, color=ft.Colors.with_opacity(0.05, ft.Colors.BLACK)),
                    content=ft.Row([
                        ft.Container(content=ft.Icon(icon, color=color, size=20), bgcolor=bg, border_radius=20, padding=8),
                        ft.Container(width=10),
                        ft.Column([ft.Text(tag, weight=ft.FontWeight.BOLD, color=color, size=self._font_m),
                            ft.Text(record['description'] or "", size=self._font_s, color=ft.Colors.GREY_700),
                            ft.Text(f"التاريخ: {record['date'][:10]}", size=10, color=ft.Colors.GREY_500)], expand=True, spacing=2),
                        ft.Column([ft.Text(f"{amount:.2f}", size=self._font_l, weight=ft.FontWeight.BOLD, color=color),
                            ft.Text("ج.م", size=10, color=color), ft.Container(height=3),
                            ft.Text(f"الرصيد: {record['balance_after']:.2f}", size=10, color=ft.Colors.GREY_600)], horizontal_alignment=ft.CrossAxisAlignment.END),
                    ])))
        
        remaining = summary.get('total_debt', 0) - summary.get('total_paid', 0)
        bottom_bar = None
        if remaining > 0:
            bottom_bar = ft.Container(padding=15, bgcolor=ft.Colors.WHITE, border_radius=15,
                shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK)),
                content=ft.Row([ft.Text(f"💰 المتبقي: {remaining:.2f} ج.م", size=self._font_l, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_700),
                    ft.Container(expand=True),
                    ft.ElevatedButton("تسجيل سداد", on_click=lambda _: self.show_payment_dialog(customer_id, customer_name),
                        bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)), height=self._btn_h)]))
        
        content_controls = [header, ft.Container(height=15), ft.Text("📊 الحركات المالية", size=self._font_l, weight=ft.FontWeight.BOLD), ft.Container(content=ledger_list, expand=True)]
        if bottom_bar:
            content_controls.append(bottom_bar)
        
        self.page.add(ft.AppBar(title=ft.Text(f"كشف حساب: {customer_name}", size=self._font_l, weight=ft.FontWeight.BOLD),
            bgcolor=ft.Colors.BLUE_GREY_900, color=ft.Colors.WHITE, leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=self.show_customers, icon_color=ft.Colors.WHITE),
            actions=[ft.IconButton(ft.Icons.SMS, icon_color=ft.Colors.WHITE, tooltip="إرسال رسالة", on_click=lambda _: self.send_sms_to_customer(customer_id, customer_name, customer.get('phone', '')))]),
            ft.Container(expand=True, padding=15, content=ft.Column(content_controls, expand=True)))
    
    # ========== المراسلة ==========
    
    def send_sms_to_customer(self, customer_id: int, customer_name: str, phone: str):
        """إرسال رسالة للعميل"""
        if not phone:
            self.show_message("⚠️ لا يوجد رقم هاتف للعميل", ft.Colors.RED)
            return
        
        message_field = ft.TextField(label="نص الرسالة", value=MessagingSystem.generate_debt_reminder(customer_name, 0),
            multiline=True, min_lines=3, max_lines=6, border_radius=10)
        
        quick_templates = ft.Row([
            ft.Chip(label=ft.Text("تذكير بالدين"), on_click=lambda _: set_template("debt"), bgcolor=ft.Colors.ORANGE_50),
            ft.Chip(label=ft.Text("تأكيد سداد"), on_click=lambda _: set_template("receipt"), bgcolor=ft.Colors.GREEN_50),
            ft.Chip(label=ft.Text("رسالة ترحيب"), on_click=lambda _: set_template("welcome"), bgcolor=ft.Colors.BLUE_50),
        ], scroll=ft.ScrollMode.AUTO)
        
        def set_template(template_type):
            if template_type == "debt":
                debts = self.db.get_customer_debts(customer_id)
                total = sum(d['remaining'] for d in debts)
                message_field.value = MessagingSystem.generate_debt_reminder(customer_name, total)
            elif template_type == "receipt":
                message_field.value = MessagingSystem.generate_payment_receipt(customer_name, 0)
            elif template_type == "welcome":
                message_field.value = f"أهلاً وسهلاً {customer_name}،\nنرحب بكم في متجرنا.\nنتمنى لكم تجربة تسوق ممتعة"
            self.page.update()
        
        dlg = ft.AlertDialog(modal=True,
            title=ft.Row([ft.Icon(ft.Icons.SMS, color=ft.Colors.BLUE_700), ft.Text(f"إرسال رسالة إلى {customer_name}", weight=ft.FontWeight.BOLD, size=self._font_l)]),
            content=ft.Column([ft.Text(f"📱 رقم الهاتف: {phone}", size=self._font_m, color=ft.Colors.GREY_600), quick_templates, ft.Container(height=10), message_field], tight=True, spacing=10),
            actions=[ft.TextButton("إلغاء", on_click=lambda _: self.close_dialog(dlg)),
                     ft.Row([ft.ElevatedButton("💬 واتساب", on_click=lambda _: self._send_whatsapp(phone, message_field.value, dlg), bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE),
                         ft.Container(width=10),
                         ft.ElevatedButton("📩 SMS", on_click=lambda _: self._send_sms(phone, message_field.value, dlg), bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE)])])
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()
    
    def _send_sms(self, phone, message, dlg):
        success, msg = MessagingSystem.send_sms(phone, message)
        if success:
            self.show_message("✅ تم فتح تطبيق الرسائل", ft.Colors.GREEN)
            self.close_dialog(dlg)
        else:
            self.show_message(f"❌ {msg}", ft.Colors.RED)
    
    def _send_whatsapp(self, phone, message, dlg):
        success, msg = MessagingSystem.send_whatsapp(phone, message)
        if success:
            self.show_message("✅ تم فتح واتساب", ft.Colors.GREEN)
            self.close_dialog(dlg)
        else:
            self.show_message(f"❌ {msg}", ft.Colors.RED)
    
    def send_debt_reminders_to_all(self, e=None):
        """إرسال تذكير لجميع المديونين"""
        debts = self.db.get_customer_debts()
        if not debts:
            self.show_message("لا توجد ديون مستحقة", ft.Colors.BLUE)
            return
        
        customers_debts = {}
        for debt in debts:
            if debt['customer_name'] not in customers_debts:
                customers_debts[debt['customer_name']] = {'customer_id': debt['customer_id'], 'total': 0}
            customers_debts[debt['customer_name']]['total'] += debt['remaining']
        
        def confirm_send(e):
            dlg.open = False
            self.page.update()
            count = 0
            for name, data in customers_debts.items():
                customer = self.db.get_customer_by_id(data['customer_id'])
                if customer and customer.get('phone'):
                    message = MessagingSystem.generate_debt_reminder(name, data['total'])
                    MessagingSystem.send_whatsapp(customer['phone'], message)
                    count += 1
                    time.sleep(0.5)
            self.show_message(f"✅ تم إرسال تذكير لـ {count} عميل", ft.Colors.GREEN)
        
        customers_list = ""
        for name, data in customers_debts.items():
            customers_list += f"• {name}: {data['total']:.2f} ريال\n"
        
        dlg = ft.AlertDialog(modal=True, title=ft.Text("تأكيد إرسال التذكيرات"),
            content=ft.Column([ft.Text(f"سيتم إرسال تذكير لـ {len(customers_debts)} عميل:"), ft.Text(customers_list, size=self._font_m), ft.Text("هل تريد المتابعة؟", weight=ft.FontWeight.BOLD)], tight=True, spacing=10),
            actions=[ft.TextButton("إلغاء", on_click=lambda _: self.close_dialog(dlg)), ft.ElevatedButton("إرسال للجميع", on_click=confirm_send, bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE)])
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()
    
    def export_customers_list(self, e=None):
        """تصدير قائمة العملاء"""
        customers = self.db.get_all_customers()
        if not customers:
            self.show_message("لا يوجد عملاء للتصدير", ft.Colors.BLUE)
            return
        
        # إنشاء ملف نصي
        filename = f"customers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(filename, "w", encoding="utf-8-sig") as f:
            f.write("الاسم,الهاتف,البريد,العنوان,إجمالي الدين,المسدد,المتبقي,ملاحظات\n")
            for c in customers:
                remaining = c['total_debt'] - c['total_paid']
                f.write(f"{c['name']},{c.get('phone','')},{c.get('email','')},{c.get('address','')},{c['total_debt']:.2f},{c['total_paid']:.2f},{remaining:.2f},{c.get('notes','')}\n")
        
        self.show_message(f"✅ تم تصدير القائمة إلى {filename}", ft.Colors.GREEN)



   
    def _save_draft_invoice(self, e=None):
        """حفظ الفاتورة الحالية كمسودة"""
        if not self.cart:
            self.show_message("السلة فارغة!", ft.Colors.RED)
            return
        
        customer_name = self.selected_customer['name'] if self.selected_customer else "نقدي"
        customer_id = self.selected_customer['id'] if self.selected_customer else None
        user_id = int(self.current_user.get('id')) if self.current_user else None
        
        success, msg = self.db.save_draft(self.cart, customer_name, customer_id, user_id)
        if success:
            self.show_message(msg, ft.Colors.GREEN)
            self.cart = []
            self.selected_customer = None
            self._refresh_cart_display()
        else:
            self.show_message(msg, ft.Colors.RED)
    
    def _show_drafts_dialog(self, e=None):
        """عرض المسودات المحفوظة"""
        drafts = self.db.get_drafts()
        
        if not drafts:
            self.show_message("لا توجد مسودات محفوظة", ft.Colors.BLUE)
            return
        
        drafts_list = ft.ListView(height=300, spacing=8)
        
        for draft in drafts:
            cart_data = json.loads(draft['cart_data'])
            items_text = " | ".join([f"{item['product_name']} ×{item['quantity']}" for item in cart_data[:3]])
            if len(cart_data) > 3:
                items_text += f" ... +{len(cart_data)-3}"
            
            drafts_list.controls.append(
                ft.Container(
                    bgcolor=ft.Colors.WHITE, border_radius=10, padding=12,
                    content=ft.Row([
                        ft.Column([
                            ft.Text(f"🧾 {draft['customer_name']}", weight=ft.FontWeight.BOLD, size=self._font_m),
                            ft.Text(items_text, size=self._font_s, color=ft.Colors.GREY_600, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Text(f"💰 {draft['total_amount']:.2f} | 🕐 {draft['created_at'][:16]}", size=self._font_s, color=ft.Colors.GREY_500),
                        ], expand=True),
                        ft.Row([
                            ft.IconButton(ft.Icons.ADD_SHOPPING_CART, icon_color=ft.Colors.GREEN, tooltip="استرجاع", 
                                on_click=lambda _, d=draft: self._load_draft(d['id'])),
                            ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.RED, tooltip="حذف",
                                on_click=lambda _, d=draft: self._delete_draft(d['id'])),
                        ]),
                    ]),
                )
            )
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("📂 المسودات المحفوظة", weight=ft.FontWeight.BOLD),
            content=ft.Container(width=self._dialog_w, height=self._btn_small0, content=drafts_list),
            actions=[ft.TextButton("إغلاق", on_click=lambda _: self.close_dialog(dlg))],
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()
    
    def _load_draft(self, draft_id: int):
        """تحميل مسودة إلى السلة"""
        draft = self.db.get_draft_by_id(draft_id)
        if not draft:
            return
        
        cart_data = json.loads(draft['cart_data'])
        
        self.cart = []
        for item in cart_data:
            product = self.db.get_product_by_id(item['product_id'])
            if product:
                self.cart.append({
                    "product_id": item['product_id'],
                    "product": product,
                    "quantity": item['quantity'],
                    "selling_price": item['price'],
                    "discount": item.get('discount', 0.0),
                })
        
        if draft['customer_name'] != "نقدي":
            self.selected_customer = {'id': draft.get('customer_id'), 'name': draft['customer_name']}
            self.customer_name_display.value = f"العميل: {draft['customer_name']}"
        
        self._refresh_cart_display()
        self._refresh_products_grid()
        self.show_message(f"✅ تم تحميل المسودة ({draft['customer_name']})", ft.Colors.GREEN)
        self.close_dialog(self.page.overlay[-1] if self.page.overlay else None)
    
    def _delete_draft(self, draft_id: int):
        """حذف مسودة"""
        success, msg = self.db.delete_draft(draft_id)
        self.show_message(msg, ft.Colors.GREEN if success else ft.Colors.RED)
        if success:
            self._show_drafts_dialog()

    # def _complete_sale(self, customer: str = "", is_debt: bool = False):
    #     if not self.cart:
    #         return
        
    #     cart_items = []
    #     total_invoice_amount = 0.0
        
    #     for item in self.cart:
    #         selling_price = float(item.get("selling_price", item["product"].selling_price))
    #         discount = float(item.get("discount", 0.0))
    #         qty = int(item['quantity'])
            
    #         cart_items.append({
    #             'product_id': int(item['product_id']),
    #             'product_name': str(item['product'].name),
    #             'quantity': qty,
    #             'price': selling_price,
    #             'discount': discount,
    #         })
    #         total_invoice_amount += (selling_price - discount) * qty
        
    #     customer_id = None
    #     if customer and customer.strip():
    #         customer_data = self.db.get_customer_by_name(customer)
    #         if not customer_data:
    #             success, _, new_id = self.db.add_customer(customer)
    #             if success:
    #                 customer_id = int(new_id)
    #         else:
    #             customer_id = int(customer_data['id'])
        
    #     # ====== للبيع النقدي: كامل المبلغ ======
    #     if not is_debt:
    #         paid_amount = total_invoice_amount
    #         payment_type = "نقدي"
    #         remaining = 0
    #     else:
    #         # ====== للبيع الآجل: نسأل كم دفع ======
    #         paid_amount = self._ask_paid_amount(total_invoice_amount)
    #         if paid_amount is None:  # المستخدم ألغى
    #             return
    #         payment_type = "آجل"
    #         remaining = total_invoice_amount - paid_amount
        
    #     user_id = int(self.current_user.get('id')) if self.current_user else None
        
    #     success, message, sale_id = self.db.process_invoice(
    #         cart_items, customer_id, paid_amount, payment_type, 
    #         f"فاتورة إجماليها {total_invoice_amount:.2f}", user_id
    #     )
        
    #     if success:
    #         # تسجيل الدين في جدول debts إذا فيه باقي
    #         if is_debt and customer_id and remaining > 0:
    #             self.db.add_debt(
    #                 customer_id, customer, sale_id, remaining,
    #                 f"فاتورة #{sale_id} - دفع {paid_amount:.2f} وباقي {remaining:.2f}"
    #             )
            
    #         # رسالة توضيحية
    #         if is_debt:
    #             msg = f"✅ تم البيع الآجل!\nالإجمالي: {total_invoice_amount:.2f}\nالمدفوع: {paid_amount:.2f}\nالباقي: {remaining:.2f}"
    #         else:
    #             msg = f"✅ تم البيع النقدي!\nالإجمالي: {total_invoice_amount:.2f}"
            
    #         self.show_message(msg, ft.Colors.GREEN)
    #         self.cart = []
    #         self.selected_customer = None
    #         self._refresh_cart_display()
    #         self.show_home()
    #     else:
    #         self.show_message(f"❌ خطأ: {message}", ft.Colors.RED)


    # def _complete_sale(self, customer: str = "", is_debt: bool = False):
    #     if not self.cart:
    #         return
        
    #     cart_items = []
    #     total_invoice_amount = 0.0
        
    #     for item in self.cart:
    #         selling_price = float(item.get("selling_price", item["product"].selling_price))
    #         discount = float(item.get("discount", 0.0))
    #         qty = int(item['quantity'])
            
    #         cart_items.append({
    #             'product_id': int(item['product_id']),
    #             'product_name': str(item['product'].name),
    #             'quantity': qty,
    #             'price': selling_price,
    #             'discount': discount,
    #         })
    #         total_invoice_amount += (selling_price - discount) * qty
        
    #     customer_id = None
    #     if customer and customer.strip():
    #         customer_data = self.db.get_customer_by_name(customer)
    #         if not customer_data:
    #             success, _, new_id = self.db.add_customer(customer)
    #             if success:
    #                 customer_id = int(new_id)
    #         else:
    #             customer_id = int(customer_data['id'])
        
    #     if not is_debt:
    #         # نقدي - يدفع كامل المبلغ
    #         paid_amount = total_invoice_amount
    #         payment_type = "نقدي"
    #         remaining = 0
    #         # self._complete_payment(cart_items, customer_id, customer, paid_amount, payment_type, total_invoice_amount, remaining)
    #     else:
    #         # آجل - استخدم الدفع الجزئي بدل _ask_paid_amount
    #         self._show_partial_payment_dialog(total_invoice_amount)



    def _complete_sale(self, customer: str = "", is_debt: bool = False):
        if not self.cart:
            return
        
        cart_items = []
        total_invoice_amount = 0.0
        
        for item in self.cart:
            selling_price = float(item.get("selling_price", item["product"].selling_price))
            discount = float(item.get("discount", 0.0))
            qty = int(item['quantity'])
            
            cart_items.append({
                'product_id': int(item['product_id']),
                'product_name': str(item['product'].name),
                'quantity': qty,
                'price': selling_price,
                'discount': discount,
            })
            total_invoice_amount += (selling_price - discount) * qty
        
        customer_id = None
        if customer and customer.strip():
            customer_data = self.db.get_customer_by_name(customer)
            if not customer_data:
                success, _, new_id = self.db.add_customer(customer)
                if success:
                    customer_id = int(new_id)
            else:
                customer_id = int(customer_data['id'])
        
        if not is_debt:
            # نقدي - يدفع كامل
            paid_amount = total_invoice_amount
            payment_type = "نقدي"
            remaining = 0
            
            user_id = int(self.current_user.get('id')) if self.current_user else None
            
            success, message, sale_id = self.db.process_invoice(
                cart_items, customer_id, paid_amount, payment_type, 
                f"فاتورة إجماليها {total_invoice_amount:.2f}", user_id
            )
            
            if success:
                self.show_message(f"✅ تم البيع النقدي!\nالإجمالي: {total_invoice_amount:.2f}", ft.Colors.GREEN)
                self.cart = []
                self.selected_customer = None
                self._refresh_cart_display()
                self.show_home()
            else:
                self.show_message(f"❌ خطأ: {message}", ft.Colors.RED)
        else:
            # آجل - افتح نافذة الدفع الجزئي
            self._show_partial_payment_dialog(total_invoice_amount)


    def _ask_paid_amount(self, total_amount: float):
        """نافذة تسأل عن المبلغ المدفوع للبيع الآجل - ترجع المبلغ"""
        # نستخدم متغير لتخزين النتيجة
        self._temp_paid_amount = 0
        self._temp_dlg_closed = False
        
        paid_field = ft.TextField(
            label=f"المبلغ المدفوع (الإجمالي: {total_amount:.2f})",
            keyboard_type=ft.KeyboardType.NUMBER,
            autofocus=True,
            prefix_icon=ft.Icons.MONEY,
            border_radius=10,
            hint_text="0 = بدون دفعة (كامل المبلغ دين)",
        )
        
        info_text = ft.Text(
            f"الإجمالي: {total_amount:.2f} | المتبقي: {total_amount:.2f}",
            size=self._font_m, color=ft.Colors.ORANGE
        )
        
        def on_change(e):
            try:
                paid = float(paid_field.value or 0)
                if paid > total_amount:
                    paid = total_amount
                    paid_field.value = str(total_amount)
                remaining = total_amount - paid
                info_text.value = f"المدفوع: {paid:.2f} | المتبقي: {remaining:.2f}"
            except:
                info_text.value = f"الإجمالي: {total_amount:.2f} | المتبقي: {total_amount:.2f}"
            self.page.update()
        
        paid_field.on_change = on_change
        
        def confirm(e):
            try:
                amount = float(paid_field.value or 0)
                if amount < 0:
                    amount = 0
                if amount > total_amount:
                    amount = total_amount
                self._temp_paid_amount = amount
            except ValueError:
                self._temp_paid_amount = 0
            self._temp_dlg_closed = True
            dlg.open = False
            self.page.update()
        
        def cancel(e):
            self._temp_paid_amount = None
            self._temp_dlg_closed = True
            dlg.open = False
            self.page.update()
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row([ft.Icon(ft.Icons.PAYMENT, color=ft.Colors.ORANGE), 
                ft.Text("البيع الآجل - تحديد الدفعة", weight=ft.FontWeight.BOLD)]),
            content=ft.Column([paid_field, ft.Container(height=10), info_text], tight=True, spacing=10),
            actions=[
                ft.TextButton("إلغاء", on_click=cancel),
                ft.ElevatedButton("تأكيد", on_click=confirm, bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE),
            ],
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()
        # الدالة ما ترجع شيء، النتيجة تتخزن في self._temp_paid_amount
        return None
    # ========== باقي الصفحات (موجودة في الكود الأصلي مع تحسينات) ==========
    



    # ============================================================
    # إدارة الموردين
    # ============================================================
    
    def show_suppliers(self, e=None):
        """صفحة إدارة الموردين"""
        self.current_page = "suppliers"
        self.page.clean()
        
        suppliers = self.db.get_all_suppliers()
        total_suppliers = len(suppliers)
        total_debts = sum(s['total_debt'] for s in suppliers)
        total_paid = sum(s['total_paid'] for s in suppliers)
        remaining = total_debts - total_paid
        
        search_field = ft.TextField(
            hint_text="🔍 بحث عن مورد...",
            on_change=lambda e: self._filter_suppliers(e.control.value),
            expand=True, border_radius=12, prefix_icon=ft.Icons.SEARCH, height=self._btn_h,
        )
        
        add_button = ft.ElevatedButton("➕ مورد جديد", on_click=self.show_add_supplier_dialog,
            bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)), height=self._btn_h)
        
        stats_row = ft.ResponsiveRow([
            self._create_stat_card("عدد الموردين", str(total_suppliers), ft.Icons.LOCAL_SHIPPING, ft.Colors.BROWN),
            self._create_stat_card("إجمالي الديون", f"{total_debts:.0f}", ft.Icons.MONEY_OFF, ft.Colors.RED),
            self._create_stat_card("المسدد", f"{total_paid:.0f}", ft.Icons.PAYMENTS, ft.Colors.GREEN),
            self._create_stat_card("المتبقي", f"{remaining:.0f}", ft.Icons.ACCOUNT_BALANCE, ft.Colors.ORANGE),
        ], spacing=10)
        
        self.suppliers_list = ft.ListView(expand=True, spacing=8, padding=10)
        
        self.page.add(
            ft.AppBar(
                title=ft.Text("🚚 إدارة الموردين", color=ft.Colors.WHITE, size=18, weight=ft.FontWeight.BOLD),
                bgcolor=ft.Colors.BROWN_700,
                leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=self.show_home, icon_color=ft.Colors.WHITE),
            ),
            ft.Container(expand=True, padding=15,
                content=ft.Column([
                    stats_row,
                    ft.Container(height=10),
                    ft.Row([search_field, add_button], spacing=10),
                    ft.Container(height=10),
                    ft.Container(content=self.suppliers_list, expand=True),
                ], expand=True)),
        )
        self._render_suppliers_list(suppliers)
    
    def _filter_suppliers(self, query):
        if query:
            suppliers = self.db.search_suppliers(query)
        else:
            suppliers = self.db.get_all_suppliers()
        self._render_suppliers_list(suppliers)
    
    def _render_suppliers_list(self, suppliers):
        self.suppliers_list.controls.clear()
        
        if not suppliers:
            self.suppliers_list.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.LOCAL_SHIPPING, size=60, color=ft.Colors.GREY_300),
                        ft.Text("لا يوجد موردين", size=18, color=ft.Colors.GREY_400),
                    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.center, padding=50,
                )
            )
            self.page.update()
            return
        
        for supplier in suppliers:
            remaining = supplier['total_debt'] - supplier['total_paid']
            
            if remaining > 0:
                status_color, status_bg, status_text = ft.Colors.RED_700, ft.Colors.RED_50, "عليه ديون"
            elif supplier['total_debt'] > 0:
                status_color, status_bg, status_text = ft.Colors.GREEN_700, ft.Colors.GREEN_50, "مسدد"
            else:
                status_color, status_bg, status_text = ft.Colors.BLUE_700, ft.Colors.BLUE_50, "جديد"
            
            self.suppliers_list.controls.append(
                ft.Container(
                    bgcolor=ft.Colors.WHITE, border_radius=12, padding=15,
                    shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK)),
                    content=ft.Column([
                        ft.Row([
                            ft.Container(
                                content=ft.Text(supplier['name'][0].upper(), size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                bgcolor=ft.Colors.BROWN_500, border_radius=25, width=45, height=self._btn_h, alignment=ft.alignment.center,
                            ),
                            ft.Container(width=10),
                            ft.Column([
                                ft.Text(supplier['name'], size=self._font_l, weight=ft.FontWeight.BOLD),
                                ft.Text(f"📱 {supplier.get('phone', 'غير مسجل')}", size=self._font_s, color=ft.Colors.GREY_600),
                                ft.Text(f"🏢 {supplier.get('company', '')}", size=self._font_s, color=ft.Colors.GREY_500) if supplier.get('company') else ft.Container(),
                            ], expand=True),
                            ft.Container(
                                content=ft.Text(status_text, size=self._font_s, weight=ft.FontWeight.BOLD, color=status_color),
                                bgcolor=status_bg, border_radius=15, padding=ft.padding.symmetric(horizontal=10, vertical=4),
                            ),
                            ft.PopupMenuButton(
                                icon=ft.Icons.MORE_VERT,
                                items=[
                                    ft.PopupMenuItem(text="📊 كشف حساب", on_click=lambda _, s=supplier: self.show_supplier_ledger(s['id'], s['name'])),
                                    ft.PopupMenuItem(text="💰 تسجيل سداد", on_click=lambda _, s=supplier: self.show_supplier_payment_dialog(s['id'], s['name'])),
                                    ft.PopupMenuItem(text="🧾 فاتورة شراء", on_click=lambda _, s=supplier: self.show_add_purchase_dialog(s['id'], s['name'])),
                                    ft.PopupMenuItem(),
                                    ft.PopupMenuItem(text="📝 تعديل", on_click=lambda _, s=supplier: self.show_edit_supplier_dialog(s)),
                                    ft.PopupMenuItem(text="🗑️ حذف", on_click=lambda _, s=supplier: self.delete_supplier(s['id'], s['name'])),
                                ],
                            ),
                        ]),
                        ft.Container(height=10), ft.Divider(),
                        ft.Container(height=10),
                        ft.Row([
                            ft.Container(
                                content=ft.Column([
                                    ft.Text("إجمالي الدين", size=10, color=ft.Colors.GREY_500),
                                    ft.Text(f"{supplier['total_debt']:.2f}", size=self._font_m, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700),
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                expand=True, bgcolor=ft.Colors.RED_50, border_radius=8, padding=8,
                            ),
                            ft.Container(width=8),
                            ft.Container(
                                content=ft.Column([
                                    ft.Text("المسدد", size=10, color=ft.Colors.GREY_500),
                                    ft.Text(f"{supplier['total_paid']:.2f}", size=self._font_m, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700),
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                expand=True, bgcolor=ft.Colors.GREEN_50, border_radius=8, padding=8,
                            ),
                            ft.Container(width=8),
                            ft.Container(
                                content=ft.Column([
                                    ft.Text("المتبقي", size=10, color=ft.Colors.GREY_500),
                                    ft.Text(f"{remaining:.2f}", size=self._font_m, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_700 if remaining > 0 else ft.Colors.GREEN_700),
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                expand=True, bgcolor=ft.Colors.ORANGE_50 if remaining > 0 else ft.Colors.GREEN_50, border_radius=8, padding=8,
                            ),
                        ]),
                        ft.Container(height=10),
                        ft.Row([
                            ft.OutlinedButton("📊 كشف حساب", on_click=lambda _, s=supplier: self.show_supplier_ledger(s['id'], s['name']),
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), side=ft.BorderSide(1, ft.Colors.BLUE), color=ft.Colors.BLUE), height=self._btn_small, expand=True),
                            ft.Container(width=5),
                            ft.OutlinedButton("🧾 شراء", on_click=lambda _, s=supplier: self.show_add_purchase_dialog(s['id'], s['name']),
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), side=ft.BorderSide(1, ft.Colors.GREEN), color=ft.Colors.GREEN), height=self._btn_small, expand=True),
                        ], scroll=ft.ScrollMode.AUTO),
                    ]),
                )
            )
        self.page.update()
    
    def show_add_supplier_dialog(self, e=None):
        """نافذة إضافة مورد"""
        name_field = ft.TextField(label="اسم المورد *", autofocus=True, prefix_icon=ft.Icons.PERSON, border_radius=10)
        phone_field = ft.TextField(label="رقم الهاتف", prefix_icon=ft.Icons.PHONE, border_radius=10)
        email_field = ft.TextField(label="البريد الإلكتروني", prefix_icon=ft.Icons.EMAIL, border_radius=10)
        company_field = ft.TextField(label="اسم الشركة", prefix_icon=ft.Icons.BUSINESS, border_radius=10)
        address_field = ft.TextField(label="العنوان", prefix_icon=ft.Icons.LOCATION_ON, border_radius=10, multiline=True, min_lines=1, max_lines=2)
        tax_field = ft.TextField(label="الرقم الضريبي", prefix_icon=ft.Icons.NUMBERS, border_radius=10)
        notes_field = ft.TextField(label="ملاحظات", prefix_icon=ft.Icons.NOTE, border_radius=10, multiline=True, min_lines=1, max_lines=2)
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row([ft.Icon(ft.Icons.PERSON_ADD, color=ft.Colors.GREEN_700), ft.Text("إضافة مورد جديد", weight=ft.FontWeight.BOLD)]),
            content=ft.Container(width=self._dialog_w, height=self._btn_h0,
                content=ft.Column([name_field, phone_field, email_field, company_field, address_field, tax_field, notes_field], tight=True, spacing=10, scroll=ft.ScrollMode.AUTO)),
            actions=[
                ft.TextButton("إلغاء", on_click=lambda _: self.close_dialog(dlg)),
                ft.ElevatedButton("💾 حفظ", on_click=lambda _: self._save_supplier(name_field, phone_field, email_field, company_field, address_field, tax_field, notes_field, dlg),
                    bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE),
            ],
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()
    
    def _save_supplier(self, name_field, phone_field, email_field, company_field, address_field, tax_field, notes_field, dlg):
        if not name_field.value or not name_field.value.strip():
            self.show_message("⚠️ يرجى إدخال اسم المورد", ft.Colors.RED)
            return
        success, msg, _ = self.db.add_supplier(
            name_field.value.strip(), phone_field.value or "", email_field.value or "",
            address_field.value or "", company_field.value or "", tax_field.value or "", notes_field.value or ""
        )
        if success:
            self.show_message(f"✅ {msg}", ft.Colors.GREEN)
            self.close_dialog(dlg)
            self._render_suppliers_list(self.db.get_all_suppliers())
        else:
            self.show_message(f"❌ {msg}", ft.Colors.RED)
    
    def show_edit_supplier_dialog(self, supplier: Dict):
        """نافذة تعديل مورد"""
        name_field = ft.TextField(label="اسم المورد *", value=supplier['name'], prefix_icon=ft.Icons.PERSON, border_radius=10)
        phone_field = ft.TextField(label="رقم الهاتف", value=supplier.get('phone', ''), prefix_icon=ft.Icons.PHONE, border_radius=10)
        email_field = ft.TextField(label="البريد الإلكتروني", value=supplier.get('email', ''), prefix_icon=ft.Icons.EMAIL, border_radius=10)
        company_field = ft.TextField(label="اسم الشركة", value=supplier.get('company', ''), prefix_icon=ft.Icons.BUSINESS, border_radius=10)
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row([ft.Icon(ft.Icons.EDIT, color=ft.Colors.BLUE_700), ft.Text(f"تعديل: {supplier['name']}", weight=ft.FontWeight.BOLD)]),
            content=ft.Column([name_field, phone_field, email_field, company_field], tight=True, spacing=10),
            actions=[
                ft.TextButton("إلغاء", on_click=lambda _: self.close_dialog(dlg)),
                ft.ElevatedButton("💾 حفظ", on_click=lambda _: self._update_supplier(supplier['id'], name_field, phone_field, email_field, company_field, dlg),
                    bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE),
            ],
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()
    
    def _update_supplier(self, supplier_id, name_field, phone_field, email_field, company_field, dlg):
        if not name_field.value or not name_field.value.strip():
            self.show_message("⚠️ يرجى إدخال اسم المورد", ft.Colors.RED)
            return
        cursor = self.db.conn.cursor()
        try:
            cursor.execute("UPDATE suppliers SET name=?, phone=?, email=?, company=? WHERE id=?",
                           (name_field.value.strip(), phone_field.value, email_field.value, company_field.value, supplier_id))
            self.db.conn.commit()
            self.show_message("✅ تم تحديث بيانات المورد", ft.Colors.GREEN)
            self.close_dialog(dlg)
            self._render_suppliers_list(self.db.get_all_suppliers())
        except Exception as e:
            self.show_message(f"❌ خطأ: {str(e)}", ft.Colors.RED)
    
    def delete_supplier(self, supplier_id: int, supplier_name: str):
        def confirm_delete(e):
            success, msg = self.db.delete_supplier(supplier_id)
            self.show_message(msg, ft.Colors.GREEN if success else ft.Colors.RED)
            self.close_dialog(dlg)
            self._render_suppliers_list(self.db.get_all_suppliers())
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row([ft.Icon(ft.Icons.DELETE, color=ft.Colors.RED), ft.Text("تأكيد الحذف")]),
            content=ft.Text(f"هل أنت متأكد من حذف المورد '{supplier_name}'؟"),
            actions=[
                ft.TextButton("إلغاء", on_click=lambda _: self.close_dialog(dlg)),
                ft.ElevatedButton("🗑️ حذف", on_click=confirm_delete, bgcolor=ft.Colors.RED, color=ft.Colors.WHITE),
            ],
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()
    
    def show_supplier_payment_dialog(self, supplier_id: int, supplier_name: str, purchase_id: int = None):
        """نافذة سداد للمورد"""
        summary = self.db.get_supplier_summary(supplier_id)
        
        amount_field = ft.TextField(
            label=f"المبلغ (المتبقي: {summary['balance']:.2f})",
            keyboard_type=ft.KeyboardType.NUMBER, autofocus=True,
            prefix_icon=ft.Icons.MONEY, border_radius=10,
        )
        payment_type_field = ft.Dropdown(
            label="طريقة الدفع",
            options=[
                ft.dropdown.Option("cash", "نقدي"),
                ft.dropdown.Option("bank", "تحويل بنكي"),
                ft.dropdown.Option("cheque", "شيك"),
            ],
            value="cash", border_radius=10,
        )
        note_field = ft.TextField(label="ملاحظة", prefix_icon=ft.Icons.NOTE, border_radius=10)
        
        # اختيار الفاتورة
        invoices = self.db.get_purchase_invoices(supplier_id)
        unpaid_invoices = [i for i in invoices if i['payment_status'] != 'paid']
        
        invoice_selector = None
        if unpaid_invoices and not purchase_id:
            invoice_options = [
                ft.dropdown.Option(str(i['id']), f"فاتورة {i['invoice_no']} - المتبقي: {i['remaining_amount']:.2f}")
                for i in unpaid_invoices
            ]
            invoice_selector = ft.Dropdown(label="اختر الفاتورة (اختياري)", options=invoice_options, border_radius=10)
        
        content_controls = [amount_field, payment_type_field, note_field]
        if invoice_selector:
            content_controls.insert(0, invoice_selector)
        
        def process(e):
            try:
                amount = float(amount_field.value or 0)
                if amount <= 0:
                    self.show_message("⚠️ المبلغ يجب أن يكون أكبر من 0", ft.Colors.RED)
                    return
            except ValueError:
                self.show_message("⚠️ يرجى إدخال مبلغ صحيح", ft.Colors.RED)
                return
            
            selected_invoice = int(invoice_selector.value) if invoice_selector and invoice_selector.value else purchase_id
            user_id = self.current_user.get('id') if self.current_user else None
            success, msg = self.db.pay_supplier(
                supplier_id, amount, payment_type_field.value, "", note_field.value, selected_invoice, user_id
            )
            if success:
                self.show_message(f"✅ {msg}", ft.Colors.GREEN)
                self.close_dialog(dlg)
                self._render_suppliers_list(self.db.get_all_suppliers())
            else:
                self.show_message(f"❌ {msg}", ft.Colors.RED)
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row([ft.Icon(ft.Icons.PAYMENT, color=ft.Colors.GREEN_700), ft.Text(f"سداد - {supplier_name}", weight=ft.FontWeight.BOLD)]),
            content=ft.Container(width=400, content=ft.Column(content_controls, tight=True, spacing=10)),
            actions=[
                ft.TextButton("إلغاء", on_click=lambda _: self.close_dialog(dlg)),
                ft.ElevatedButton("💵 سداد", on_click=process, bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE),
            ],
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()
    
    def show_supplier_ledger(self, supplier_id: int, supplier_name: str):
        """كشف حساب المورد"""
        self.page.clean()
        ledger = self.db.get_supplier_ledger(supplier_id)
        summary = self.db.get_supplier_summary(supplier_id)
        supplier = self.db.get_supplier_by_id(supplier_id)
        
        header = ft.Container(padding=20, bgcolor=ft.Colors.WHITE, border_radius=15,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK)),
            content=ft.Column([
                ft.Row([
                    ft.Container(content=ft.Text(supplier_name[0].upper(), size=30, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        bgcolor=ft.Colors.BROWN_500, border_radius=30, width=55, height=55, alignment=ft.alignment.center),
                    ft.Container(width=15),
                    ft.Column([
                        ft.Text(supplier_name, size=22, weight=ft.FontWeight.BOLD),
                        ft.Text(f"📱 {supplier.get('phone', 'غير مسجل')} | 🏢 {supplier.get('company', '')}", size=self._font_m, color=ft.Colors.GREY_600),
                    ], expand=True),
                ]),
                ft.Container(height=15), ft.Divider(), ft.Container(height=10),
                ft.Row([
                    ft.Container(content=ft.Column([ft.Text("إجمالي الدين", size=self._font_s),
                        ft.Text(f"{summary.get('total_debt', 0):.2f}", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700)],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER), expand=True),
                    ft.VerticalDivider(),
                    ft.Container(content=ft.Column([ft.Text("المسدد", size=self._font_s),
                        ft.Text(f"{summary.get('total_paid', 0):.2f}", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700)],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER), expand=True),
                    ft.VerticalDivider(),
                    ft.Container(content=ft.Column([ft.Text("المتبقي", size=self._font_s),
                        ft.Text(f"{summary.get('balance', 0):.2f}", size=18, weight=ft.FontWeight.BOLD,
                            color=ft.Colors.ORANGE_700 if summary.get('balance', 0) > 0 else ft.Colors.GREEN_700)],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER), expand=True),
                ]),
            ]))
        
        ledger_list = ft.ListView(expand=True, spacing=8)
        
        if not ledger:
            ledger_list.controls.append(ft.Container(content=ft.Text("لا توجد حركات", size=self._font_l), alignment=ft.alignment.center, padding=50))
        else:
            for record in ledger:
                is_debit = record['debit'] > 0
                color = ft.Colors.RED_700 if is_debit else ft.Colors.GREEN_700
                bg = ft.Colors.RED_50 if is_debit else ft.Colors.GREEN_50
                icon = ft.Icons.ARROW_UPWARD if is_debit else ft.Icons.ARROW_DOWNWARD
                tag = "فاتورة شراء" if is_debit else "سداد"
                amount = record['debit'] if is_debit else record['credit']
                
                ledger_list.controls.append(ft.Container(bgcolor=ft.Colors.WHITE, border_radius=10, padding=12,
                    border=ft.border.only(left=ft.border.BorderSide(4, color)),
                    content=ft.Row([
                        ft.Container(content=ft.Icon(icon, color=color, size=20), bgcolor=bg, border_radius=20, padding=8),
                        ft.Container(width=10),
                        ft.Column([ft.Text(tag, weight=ft.FontWeight.BOLD, color=color, size=self._font_m),
                            ft.Text(record['description'] or "", size=self._font_s),
                            ft.Text(f"التاريخ: {record['date'][:10]}", size=10, color=ft.Colors.GREY_500)], expand=True, spacing=2),
                        ft.Column([ft.Text(f"{amount:.2f}", size=self._font_l, weight=ft.FontWeight.BOLD, color=color),
                            ft.Text(f"الرصيد: {record['balance_after']:.2f}", size=10, color=ft.Colors.GREY_600)], horizontal_alignment=ft.CrossAxisAlignment.END),
                    ])))
        
        remaining = summary.get('balance', 0)
        bottom_bar = None
        if remaining > 0:
            bottom_bar = ft.Container(padding=15, bgcolor=ft.Colors.WHITE, border_radius=15,
                content=ft.Row([ft.Text(f"💰 المتبقي: {remaining:.2f}", size=self._font_l, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_700),
                    ft.Container(expand=True),
                    ft.ElevatedButton("تسجيل سداد", on_click=lambda _: self.show_supplier_payment_dialog(supplier_id, supplier_name),
                        bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)), height=self._btn_h)]))
        
        content_controls = [header, ft.Container(height=15), ft.Text("📊 الحركات المالية", size=self._font_l, weight=ft.FontWeight.BOLD), ft.Container(content=ledger_list, expand=True)]
        if bottom_bar:
            content_controls.append(bottom_bar)
        
        self.page.add(ft.AppBar(title=ft.Text(f"كشف حساب: {supplier_name}", size=self._font_l, weight=ft.FontWeight.BOLD),
            bgcolor=ft.Colors.BROWN_900, color=ft.Colors.WHITE, leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=self.show_suppliers, icon_color=ft.Colors.WHITE)),
            ft.Container(expand=True, padding=15, content=ft.Column(content_controls, expand=True)))
    









    def edit_purchase_invoice(self, purchase_id: int):
        """تعديل فاتورة شراء"""
        invoice = self.db.get_purchase_invoices()
        invoice = next((i for i in invoice if i['id'] == purchase_id), None)
        if not invoice:
            self.show_message("الفاتورة غير موجودة", ft.Colors.RED)
            return
        
        items = self.db.get_purchase_items(purchase_id)
        suppliers = self.db.get_all_suppliers()
        
        # حقول التعديل
        supplier_dropdown = ft.Dropdown(
            label="المورد",
            options=[ft.dropdown.Option(str(s['id']), s['name']) for s in suppliers],
            value=str(invoice['supplier_id']),
            border_radius=10,
        )
        date_field = ft.TextField(label="التاريخ", value=invoice['invoice_date'], border_radius=10)
        transport_field = ft.TextField(label="النقل", value=str(invoice['transport_cost']), border_radius=10)
        discount_field = ft.TextField(label="الخصم", value=str(invoice['discount']), border_radius=10)
        paid_field = ft.TextField(label="المدفوع", value=str(invoice['paid_amount']), border_radius=10)
        
        # قائمة المنتجات الحالية
        items_list = ft.ListView(height=200, spacing=5)
        for item in items:
            items_list.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text(item['product_name'], expand=2),
                        ft.Text(f"{item['quantity']} × {item['unit_price']:.2f}"),
                        ft.Text(f"= {item['subtotal']:.2f}", weight=ft.FontWeight.BOLD),
                    ]),
                    padding=8, bgcolor=ft.Colors.GREY_50, border_radius=5,
                )
            )
        
        def save_changes(e):
            try:
                new_transport = float(transport_field.value or 0)
                new_discount = float(discount_field.value or 0)
                new_paid = float(paid_field.value or 0)
            except ValueError:
                self.show_message("قيم غير صحيحة", ft.Colors.RED)
                return
            
            cursor = self.db.conn.cursor()
            try:
                # إرجاع المخزون القديم
                for item in items:
                    cursor.execute("UPDATE products SET quantity = quantity - ? WHERE id = ?",
                                   (item['quantity'], item['product_id']))
                
                # تحديث الفاتورة
                cursor.execute("""
                    UPDATE purchase_invoices SET supplier_id=?, invoice_date=?, transport_cost=?,
                    discount=?, paid_amount=?, remaining_amount=net_total-paid_amount
                    WHERE id=?
                """, (int(supplier_dropdown.value), date_field.value, new_transport, new_discount, new_paid, purchase_id))
                
                self.db.conn.commit()
                self.show_message("✅ تم تعديل الفاتورة", ft.Colors.GREEN)
                self.close_dialog(dlg)
                self.show_purchases()
            except Exception as ex:
                self.show_message(f"❌ خطأ: {str(ex)}", ft.Colors.RED)
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"تعديل فاتورة {invoice['invoice_no']}", weight=ft.FontWeight.BOLD),
            content=ft.Container(width=500, height=self._btn_h0,
                content=ft.Column([
                    supplier_dropdown, date_field,
                    ft.Row([transport_field, discount_field, paid_field], spacing=10),
                    ft.Text("المنتجات:", weight=ft.FontWeight.BOLD),
                    ft.Container(content=items_list, border=ft.border.all(1, ft.Colors.GREY_300), border_radius=8),
                ], tight=True, spacing=8, scroll=ft.ScrollMode.AUTO)),
            actions=[
                ft.TextButton("إلغاء", on_click=lambda _: self.close_dialog(dlg)),
                ft.ElevatedButton("💾 حفظ", on_click=save_changes, bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE),
            ],
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()
    
    def delete_purchase_invoice(self, purchase_id: int, invoice_no: str):
        """حذف فاتورة شراء"""
        def confirm_delete(e):
            cursor = self.db.conn.cursor()
            try:
                # إرجاع المخزون
                items = self.db.get_purchase_items(purchase_id)
                for item in items:
                    cursor.execute("UPDATE products SET quantity = quantity - ? WHERE id = ?",
                                   (item['quantity'], item['product_id']))
                
                # حذف الفاتورة والتفاصيل
                cursor.execute("DELETE FROM purchase_items WHERE purchase_id = ?", (purchase_id,))
                cursor.execute("DELETE FROM supplier_payments WHERE purchase_id = ?", (purchase_id,))
                cursor.execute("DELETE FROM supplier_transactions WHERE purchase_id = ?", (purchase_id,))
                cursor.execute("DELETE FROM purchase_invoices WHERE id = ?", (purchase_id,))
                
                self.db.conn.commit()
                self.show_message("✅ تم حذف الفاتورة", ft.Colors.GREEN)
                self.close_dialog(dlg)
                self.show_purchases()
            except Exception as ex:
                self.show_message(f"❌ خطأ: {str(ex)}", ft.Colors.RED)
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row([ft.Icon(ft.Icons.DELETE, color=ft.Colors.RED), ft.Text("تأكيد الحذف")]),
            content=ft.Text(f"هل أنت متأكد من حذف الفاتورة {invoice_no}؟\nسيتم إرجاع المنتجات للمخزون."),
            actions=[
                ft.TextButton("إلغاء", on_click=lambda _: self.close_dialog(dlg)),
                ft.ElevatedButton("🗑️ حذف", on_click=confirm_delete, bgcolor=ft.Colors.RED, color=ft.Colors.WHITE),
            ],
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()


    # ============================================================
    # التقارير الاحترافية للمشتريات
    # ============================================================
    
    def show_purchase_reports(self, e=None):
        """صفحة تقارير المشتريات المتقدمة"""
        self.current_page = "purchase_reports"
        self.page.clean()
        
        # تبويبات التقارير - بدون أيقونات لتجنب الخطأ مع Python 3.8
        # أزرار التبويب بدل ft.Tabs
        tabs = ft.Row([
            ft.ElevatedButton("📊 ملخص", on_click=lambda _: self._load_summary_report(), style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20)), height=self._btn_small),
            ft.ElevatedButton("🏆 الموردين", on_click=lambda _: self._load_top_suppliers_report(), style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20)), height=self._btn_small),
            ft.ElevatedButton("📅 شهري", on_click=lambda _: self._load_monthly_report(), style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20)), height=self._btn_small),
            ft.ElevatedButton("📦 المنتجات", on_click=lambda _: self._load_product_report(), style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20)), height=self._btn_small),
            ft.ElevatedButton("👤 المستخدمين", on_click=lambda _: self._load_user_report(), style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20)), height=self._btn_small),
        ], scroll=ft.ScrollMode.AUTO, spacing=5)
        
        self.report_content = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO)
        
        self.page.add(
            ft.AppBar(
                title=ft.Text("📊 تقارير المشتريات", color=ft.Colors.WHITE, size=18, weight=ft.FontWeight.BOLD),
                bgcolor=ft.Colors.INDIGO_900,
                leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=self.show_home, icon_color=ft.Colors.WHITE),
            ),
            ft.Container(expand=True, padding=15,
                content=ft.Column([tabs, ft.Container(height=10), self.report_content], expand=True)),
        )
        self._load_summary_report()
    
    def _on_report_tab_change(self, e):
        tab_index = e.control.selected_index
        if tab_index == 0:
            self._load_summary_report()
        elif tab_index == 1:
            self._load_top_suppliers_report()
        elif tab_index == 2:
            self._load_monthly_report()
        elif tab_index == 3:
            self._load_product_report()
        elif tab_index == 4:
            self._load_user_report()
    
    def _load_summary_report(self):
        """ملخص المشتريات"""
        self.report_content.controls.clear()
        cursor = self.db.conn.cursor()
        
        today = datetime.now().strftime("%Y-%m-%d")
        month_start = datetime.now().strftime("%Y-%m-01")
        
        # إحصائيات اليوم
        cursor.execute("SELECT COALESCE(SUM(net_total), 0), COUNT(*) FROM purchase_invoices WHERE invoice_date = ?", (today,))
        today_total, today_count = cursor.fetchone()
        
        # إحصائيات الشهر
        cursor.execute("SELECT COALESCE(SUM(net_total), 0), COUNT(*) FROM purchase_invoices WHERE invoice_date >= ?", (month_start,))
        month_total, month_count = cursor.fetchone()
        
        # إجمالي الديون للموردين
        cursor.execute("SELECT COALESCE(SUM(balance), 0) FROM suppliers")
        total_payable = cursor.fetchone()[0]
        
        # عدد الموردين
        cursor.execute("SELECT COUNT(*) FROM suppliers")
        suppliers_count = cursor.fetchone()[0]
        
        # فواتير غير مسددة
        cursor.execute("SELECT COUNT(*) FROM purchase_invoices WHERE payment_status != 'paid'")
        unpaid_count = cursor.fetchone()[0]
        
        self.report_content.controls.extend([
            ft.Text("📊 ملخص المشتريات", size=20, weight=ft.FontWeight.BOLD),
            ft.Container(height=15),
            ft.ResponsiveRow([
                self._create_stat_card("مشتريات اليوم", f"{today_total:.0f}", ft.Icons.TODAY, ft.Colors.BLUE),
                self._create_stat_card("عدد فواتير اليوم", str(today_count), ft.Icons.RECEIPT, ft.Colors.CYAN),
                self._create_stat_card("مشتريات الشهر", f"{month_total:.0f}", ft.Icons.CALENDAR_MONTH, ft.Colors.GREEN),
                self._create_stat_card("فواتير الشهر", str(month_count), ft.Icons.LIST, ft.Colors.TEAL),
            ], spacing=10),
            ft.Container(height=10),
            ft.ResponsiveRow([
                self._create_stat_card("الموردين", str(suppliers_count), ft.Icons.LOCAL_SHIPPING, ft.Colors.BROWN),
                self._create_stat_card("مستحق للموردين", f"{total_payable:.0f}", ft.Icons.MONEY_OFF, ft.Colors.RED),
                self._create_stat_card("فواتير غير مسددة", str(unpaid_count), ft.Icons.WARNING, ft.Colors.ORANGE),
            ], spacing=10),
        ])
        self.page.update()
    
    def _load_top_suppliers_report(self):
        """أفضل الموردين"""
        self.report_content.controls.clear()
        cursor = self.db.conn.cursor()
        
        cursor.execute("""
            SELECT supplier_name, COUNT(*) as count, COALESCE(SUM(net_total), 0) as total
            FROM purchase_invoices
            GROUP BY supplier_id
            ORDER BY total DESC
            LIMIT 10
        """)
        top_suppliers = [dict(row) for row in cursor.fetchall()]
        
        self.report_content.controls.append(ft.Text("🏆 أكثر الموردين تعاملاً", size=20, weight=ft.FontWeight.BOLD))
        self.report_content.controls.append(ft.Container(height=10))
        
        if not top_suppliers:
            self.report_content.controls.append(ft.Text("لا توجد بيانات", size=self._font_m, color=ft.Colors.GREY_500))
        else:
            colors = [ft.Colors.AMBER_700, ft.Colors.GREY_600, ft.Colors.BROWN_500, ft.Colors.BLUE_700, ft.Colors.GREEN_700]
            
            for i, supplier in enumerate(top_suppliers):
                color = colors[i] if i < len(colors) else ft.Colors.GREY_400
                self.report_content.controls.append(
                    ft.Container(
                        bgcolor=ft.Colors.WHITE, border_radius=10, padding=15, margin=ft.Margin(0, 0, 0, 8),
                        border=ft.border.only(left=ft.border.BorderSide(5, color)),
                        content=ft.Row([
                            ft.Container(
                                content=ft.Text(str(i + 1), size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                bgcolor=color, border_radius=20, width=35, height=self._btn_small, alignment=ft.alignment.center,
                            ),
                            ft.Container(width=10),
                            ft.Column([
                                ft.Text(supplier['supplier_name'], size=15, weight=ft.FontWeight.BOLD),
                                ft.Text(f"{supplier['count']} فاتورة", size=self._font_s, color=ft.Colors.GREY_600),
                            ], expand=True),
                            ft.Column([
                                ft.Text(f"{supplier['total']:.0f}", size=self._font_l, weight=ft.FontWeight.BOLD, color=color),
                                ft.Text("ج.م", size=self._font_s, color=ft.Colors.GREY_500),
                            ], horizontal_alignment=ft.CrossAxisAlignment.END),
                        ]),
                    )
                )
        self.page.update()
    
    def _load_monthly_report(self):
        """تقرير شهري"""
        self.report_content.controls.clear()
        cursor = self.db.conn.cursor()
        
        year = datetime.now().year
        
        cursor.execute("""
            SELECT strftime('%m', invoice_date) as month, 
                   COALESCE(SUM(net_total), 0) as total, 
                   COUNT(*) as count
            FROM purchase_invoices 
            WHERE strftime('%Y', invoice_date) = ?
            GROUP BY strftime('%m', invoice_date)
            ORDER BY month
        """, (str(year),))
        monthly_data = [dict(row) for row in cursor.fetchall()]
        
        month_names = {"01":"يناير","02":"فبراير","03":"مارس","04":"أبريل","05":"مايو","06":"يونيو",
                      "07":"يوليو","08":"أغسطس","09":"سبتمبر","10":"أكتوبر","11":"نوفمبر","12":"ديسمبر"}
        
        self.report_content.controls.append(ft.Text(f"📅 المشتريات الشهرية - {year}", size=20, weight=ft.FontWeight.BOLD))
        self.report_content.controls.append(ft.Container(height=10))
        
        for m in monthly_data:
            month_name = month_names.get(m['month'], m['month'])
            self.report_content.controls.append(
                ft.Container(
                    bgcolor=ft.Colors.WHITE, border_radius=8, padding=12, margin=ft.Margin(0, 0, 0, 5),
                    content=ft.Row([
                        ft.Text(month_name, size=self._font_m, weight=ft.FontWeight.BOLD, width=100),
                        ft.Text(f"{m['count']} فاتورة", size=self._font_s, expand=True),
                        ft.Text(f"{m['total']:.2f} ج.م", size=self._font_m, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_700),
                    ]),
                )
            )
        self.page.update()
    
    def _load_product_report(self):
        """تقرير حسب المنتج"""
        self.report_content.controls.clear()
        cursor = self.db.conn.cursor()
        
        cursor.execute("""
            SELECT product_name, SUM(quantity) as total_qty, SUM(subtotal) as total_amount
            FROM purchase_items
            GROUP BY product_id
            ORDER BY total_qty DESC
            LIMIT 20
        """)
        products = [dict(row) for row in cursor.fetchall()]
        
        self.report_content.controls.append(ft.Text("📦 أكثر المنتجات شراءً", size=20, weight=ft.FontWeight.BOLD))
        self.report_content.controls.append(ft.Container(height=10))
        
        for p in products:
            self.report_content.controls.append(
                ft.Container(
                    bgcolor=ft.Colors.WHITE, border_radius=8, padding=12, margin=ft.Margin(0, 0, 0, 5),
                    content=ft.Row([
                        ft.Text(p['product_name'], size=self._font_m, weight=ft.FontWeight.BOLD, expand=2),
                        ft.Text(f"الكمية: {p['total_qty']}", size=self._font_s, expand=1),
                        ft.Text(f"{p['total_amount']:.2f} ج.م", size=self._font_m, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700),
                    ]),
                )
            )
        self.page.update()
    
    def _load_user_report(self):
        """تقرير حسب المستخدم"""
        self.report_content.controls.clear()
        cursor = self.db.conn.cursor()
        
        cursor.execute("""
            SELECT u.full_name, COUNT(*) as count, COALESCE(SUM(p.net_total), 0) as total
            FROM purchase_invoices p
            JOIN users u ON p.user_id = u.id
            GROUP BY p.user_id
            ORDER BY total DESC
        """)
        users = [dict(row) for row in cursor.fetchall()]
        
        self.report_content.controls.append(ft.Text("👤 المشتريات حسب المستخدم", size=20, weight=ft.FontWeight.BOLD))
        self.report_content.controls.append(ft.Container(height=10))
        
        if not users:
            self.report_content.controls.append(ft.Text("لا توجد بيانات", size=self._font_m, color=ft.Colors.GREY_500))
        else:
            for u in users:
                self.report_content.controls.append(
                    ft.Container(
                        bgcolor=ft.Colors.WHITE, border_radius=8, padding=12, margin=ft.Margin(0, 0, 0, 5),
                        content=ft.Row([
                            ft.Text(u['full_name'] or "غير معروف", size=self._font_m, weight=ft.FontWeight.BOLD, expand=2),
                            ft.Text(f"{u['count']} فاتورة", size=self._font_s, expand=1),
                            ft.Text(f"{u['total']:.2f} ج.م", size=self._font_m, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700),
                        ]),
                    )
                )
        self.page.update()
    
    def _on_report_tab_change(self, e):
        tab_index = e.control.selected_index
        if tab_index == 0:
            self._load_summary_report()
        elif tab_index == 1:
            self._load_top_suppliers_report()
        elif tab_index == 2:
            self._load_monthly_report()
        elif tab_index == 3:
            self._load_product_report()
        elif tab_index == 4:
            self._load_user_report()
    
    def _load_summary_report(self):
        """ملخص المشتريات"""
        self.report_content.controls.clear()
        cursor = self.db.conn.cursor()
        
        today = datetime.now().strftime("%Y-%m-%d")
        month_start = datetime.now().strftime("%Y-%m-01")
        
        # إحصائيات اليوم
        cursor.execute("SELECT COALESCE(SUM(net_total), 0), COUNT(*) FROM purchase_invoices WHERE invoice_date = ?", (today,))
        today_total, today_count = cursor.fetchone()
        
        # إحصائيات الشهر
        cursor.execute("SELECT COALESCE(SUM(net_total), 0), COUNT(*) FROM purchase_invoices WHERE invoice_date >= ?", (month_start,))
        month_total, month_count = cursor.fetchone()
        
        # إجمالي الديون للموردين
        cursor.execute("SELECT COALESCE(SUM(balance), 0) FROM suppliers")
        total_payable = cursor.fetchone()[0]
        
        # عدد الموردين
        cursor.execute("SELECT COUNT(*) FROM suppliers")
        suppliers_count = cursor.fetchone()[0]
        
        # فواتير غير مسددة
        cursor.execute("SELECT COUNT(*) FROM purchase_invoices WHERE payment_status != 'paid'")
        unpaid_count = cursor.fetchone()[0]
        
        self.report_content.controls.extend([
            ft.Text("📊 ملخص المشتريات", size=20, weight=ft.FontWeight.BOLD),
            ft.Container(height=15),
            ft.ResponsiveRow([
                self._create_stat_card("مشتريات اليوم", f"{today_total:.0f}", ft.Icons.TODAY, ft.Colors.BLUE),
                self._create_stat_card("عدد فواتير اليوم", str(today_count), ft.Icons.RECEIPT, ft.Colors.CYAN),
                self._create_stat_card("مشتريات الشهر", f"{month_total:.0f}", ft.Icons.CALENDAR_MONTH, ft.Colors.GREEN),
                self._create_stat_card("فواتير الشهر", str(month_count), ft.Icons.LIST, ft.Colors.TEAL),
            ], spacing=10),
            ft.Container(height=10),
            ft.ResponsiveRow([
                self._create_stat_card("الموردين", str(suppliers_count), ft.Icons.LOCAL_SHIPPING, ft.Colors.BROWN),
                self._create_stat_card("مستحق للموردين", f"{total_payable:.0f}", ft.Icons.MONEY_OFF, ft.Colors.RED),
                self._create_stat_card("فواتير غير مسددة", str(unpaid_count), ft.Icons.WARNING, ft.Colors.ORANGE),
            ], spacing=10),
        ])
        self.page.update()
    
    def _load_top_suppliers_report(self):
        """أفضل الموردين"""
        self.report_content.controls.clear()
        cursor = self.db.conn.cursor()
        
        # أكثر الموردين تعاملاً
        cursor.execute("""
            SELECT supplier_name, COUNT(*) as count, COALESCE(SUM(net_total), 0) as total
            FROM purchase_invoices
            GROUP BY supplier_id
            ORDER BY total DESC
            LIMIT 10
        """)
        top_suppliers = [dict(row) for row in cursor.fetchall()]
        
        self.report_content.controls.append(ft.Text("🏆 أكثر الموردين تعاملاً", size=20, weight=ft.FontWeight.BOLD))
        self.report_content.controls.append(ft.Container(height=10))
        
        if not top_suppliers:
            self.report_content.controls.append(ft.Text("لا توجد بيانات", size=self._font_m, color=ft.Colors.GREY_500))
        else:
            # ترتيب الألوان
            colors = [ft.Colors.AMBER_700, ft.Colors.GREY_600, ft.Colors.BROWN_500, ft.Colors.BLUE_700, ft.Colors.GREEN_700]
            
            for i, supplier in enumerate(top_suppliers):
                color = colors[i] if i < len(colors) else ft.Colors.GREY_400
                self.report_content.controls.append(
                    ft.Container(
                        bgcolor=ft.Colors.WHITE, border_radius=10, padding=15, margin=ft.Margin(0, 0, 0, 8),
                        border=ft.border.only(left=ft.border.BorderSide(5, color)),
                        content=ft.Row([
                            ft.Container(
                                content=ft.Text(str(i + 1), size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                bgcolor=color, border_radius=20, width=35, height=self._btn_small, alignment=ft.alignment.center,
                            ),
                            ft.Container(width=10),
                            ft.Column([
                                ft.Text(supplier['supplier_name'], size=15, weight=ft.FontWeight.BOLD),
                                ft.Text(f"{supplier['count']} فاتورة", size=self._font_s, color=ft.Colors.GREY_600),
                            ], expand=True),
                            ft.Column([
                                ft.Text(f"{supplier['total']:.0f}", size=self._font_l, weight=ft.FontWeight.BOLD, color=color),
                                ft.Text("ج.م", size=self._font_s, color=ft.Colors.GREY_500),
                            ], horizontal_alignment=ft.CrossAxisAlignment.END),
                        ]),
                    )
                )
        self.page.update()
    
    def _load_monthly_report(self):
        """تقرير شهري"""
        self.report_content.controls.clear()
        cursor = self.db.conn.cursor()
        
        year = datetime.now().year
        
        cursor.execute("""
            SELECT strftime('%m', invoice_date) as month, 
                   COALESCE(SUM(net_total), 0) as total, 
                   COUNT(*) as count
            FROM purchase_invoices 
            WHERE strftime('%Y', invoice_date) = ?
            GROUP BY strftime('%m', invoice_date)
            ORDER BY month
        """, (str(year),))
        monthly_data = [dict(row) for row in cursor.fetchall()]
        
        month_names = {"01":"يناير","02":"فبراير","03":"مارس","04":"أبريل","05":"مايو","06":"يونيو",
                      "07":"يوليو","08":"أغسطس","09":"سبتمبر","10":"أكتوبر","11":"نوفمبر","12":"ديسمبر"}
        
        self.report_content.controls.append(ft.Text(f"📅 المشتريات الشهرية - {year}", size=20, weight=ft.FontWeight.BOLD))
        self.report_content.controls.append(ft.Container(height=10))
        
        for m in monthly_data:
            month_name = month_names.get(m['month'], m['month'])
            self.report_content.controls.append(
                ft.Container(
                    bgcolor=ft.Colors.WHITE, border_radius=8, padding=12, margin=ft.Margin(0, 0, 0, 5),
                    content=ft.Row([
                        ft.Text(month_name, size=self._font_m, weight=ft.FontWeight.BOLD, width=100),
                        ft.Text(f"{m['count']} فاتورة", size=self._font_s, expand=True),
                        ft.Text(f"{m['total']:.2f} ج.م", size=self._font_m, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_700),
                    ]),
                )
            )
        self.page.update()
    
    def _load_product_report(self):
        """تقرير حسب المنتج"""
        self.report_content.controls.clear()
        cursor = self.db.conn.cursor()
        
        cursor.execute("""
            SELECT product_name, SUM(quantity) as total_qty, SUM(subtotal) as total_amount
            FROM purchase_items
            GROUP BY product_id
            ORDER BY total_qty DESC
            LIMIT 20
        """)
        products = [dict(row) for row in cursor.fetchall()]
        
        self.report_content.controls.append(ft.Text("📦 أكثر المنتجات شراءً", size=20, weight=ft.FontWeight.BOLD))
        self.report_content.controls.append(ft.Container(height=10))
        
        for p in products:
            self.report_content.controls.append(
                ft.Container(
                    bgcolor=ft.Colors.WHITE, border_radius=8, padding=12, margin=ft.Margin(0, 0, 0, 5),
                    content=ft.Row([
                        ft.Text(p['product_name'], size=self._font_m, weight=ft.FontWeight.BOLD, expand=2),
                        ft.Text(f"الكمية: {p['total_qty']}", size=self._font_s, expand=1),
                        ft.Text(f"{p['total_amount']:.2f} ج.م", size=self._font_m, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700),
                    ]),
                )
            )
        self.page.update()
    
    def _load_user_report(self):
        """تقرير حسب المستخدم"""
        self.report_content.controls.clear()
        cursor = self.db.conn.cursor()
        
        cursor.execute("""
            SELECT u.full_name, COUNT(*) as count, COALESCE(SUM(p.net_total), 0) as total
            FROM purchase_invoices p
            JOIN users u ON p.user_id = u.id
            GROUP BY p.user_id
            ORDER BY total DESC
        """)
        users = [dict(row) for row in cursor.fetchall()]
        
        self.report_content.controls.append(ft.Text("👤 المشتريات حسب المستخدم", size=20, weight=ft.FontWeight.BOLD))
        self.report_content.controls.append(ft.Container(height=10))
        
        if not users:
            self.report_content.controls.append(ft.Text("لا توجد بيانات", size=self._font_m, color=ft.Colors.GREY_500))
        else:
            for u in users:
                self.report_content.controls.append(
                    ft.Container(
                        bgcolor=ft.Colors.WHITE, border_radius=8, padding=12, margin=ft.Margin(0, 0, 0, 5),
                        content=ft.Row([
                            ft.Text(u['full_name'] or "غير معروف", size=self._font_m, weight=ft.FontWeight.BOLD, expand=2),
                            ft.Text(f"{u['count']} فاتورة", size=self._font_s, expand=1),
                            ft.Text(f"{u['total']:.2f} ج.م", size=self._font_m, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700),
                        ]),
                    )
                )
        self.page.update()
    # ============================================================
    # فواتير الشراء
    # ============================================================
    
    def show_purchases(self, e=None):
        """صفحة فواتير الشراء"""
        self.current_page = "purchases"
        self.page.clean()
        
        invoices = self.db.get_purchase_invoices()
        
        purchases_list = ft.ListView(expand=True, spacing=10, padding=10)
        
        for inv in invoices:
            status_colors = {'paid': ft.Colors.GREEN, 'partial': ft.Colors.ORANGE, 'pending': ft.Colors.RED}
            status_names = {'paid': 'مسدد', 'partial': 'مسدد جزئياً', 'pending': 'غير مسدد'}
            
            purchases_list.controls.append(
                ft.Container(
                    bgcolor=ft.Colors.WHITE, border_radius=10, padding=15,
                    content=ft.Column([
                        ft.Row([
                            ft.Text(f"📄 {inv['invoice_no']}", weight=ft.FontWeight.BOLD, size=self._font_m),
                            ft.Container(expand=True),
                            ft.Container(
                                content=ft.Text(status_names.get(inv['payment_status'], inv['payment_status']), size=self._font_s, weight=ft.FontWeight.BOLD,
                                    color=status_colors.get(inv['payment_status'], ft.Colors.GREY)),
                                bgcolor=ft.Colors.GREY_50, border_radius=10, padding=ft.padding.symmetric(horizontal=8, vertical=3),
                            ),
                        ]),
                        ft.Row([
                            ft.IconButton(ft.Icons.EDIT, icon_color=ft.Colors.BLUE, icon_size=self._icon_s,
                                on_click=lambda _, pid=inv['id']: self.edit_purchase_invoice(pid)),
                            ft.IconButton(ft.Icons.DELETE, icon_color=ft.Colors.RED, icon_size=self._icon_s,
                                on_click=lambda _, pid=inv['id'], pno=inv['invoice_no']: self.delete_purchase_invoice(pid, pno)),
                        ]),
                        ft.Row([
                            ft.Text(f"المورد: {inv['supplier_name']}", size=self._font_s, color=ft.Colors.GREY_600),
                            ft.Text(f"التاريخ: {inv['invoice_date']}", size=self._font_s, color=ft.Colors.GREY_600),
                        ]),
                        ft.Row([
                            ft.Text(f"الإجمالي: {inv['net_total']:.2f}", size=self._font_m, weight=ft.FontWeight.BOLD),
                            ft.Text(f"المدفوع: {inv['paid_amount']:.2f}", size=self._font_m, color=ft.Colors.GREEN_700),
                            ft.Text(f"المتبقي: {inv['remaining_amount']:.2f}", size=self._font_m, color=ft.Colors.RED_700),
                        ]),
                    ], spacing=5),
                )
            )
        
        self.page.add(
            ft.AppBar(
                title=ft.Text("🧾 فواتير الشراء", color=ft.Colors.WHITE, size=18, weight=ft.FontWeight.BOLD),
                bgcolor=ft.Colors.INDIGO_700,
                leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=self.show_home, icon_color=ft.Colors.WHITE),
                actions=[
                    ft.IconButton(ft.Icons.ADD, icon_color=ft.Colors.WHITE, tooltip="فاتورة جديدة", on_click=lambda _: self.show_add_purchase_dialog()),
                ]
            ),
            ft.Container(expand=True, padding=15, content=purchases_list),
        )
    



    def show_add_purchase_dialog(self, supplier_id: int = None, supplier_name: str = ""):
        """نافذة فاتورة شراء جديدة - متطورة"""
        if not supplier_id:
            self.show_suppliers()
            self.show_message("اختر مورد من القائمة ثم اضغط 'شراء'", ft.Colors.BLUE)
            return
        
        products = self.db.get_all_products()
        purchase_cart = []
        
        # حقول الفاتورة الأساسية
        supplier_field = ft.TextField(label="المورد", value=supplier_name, disabled=True, border_radius=10)
        date_field = ft.TextField(label="التاريخ", value=datetime.now().strftime("%Y-%m-%d"), border_radius=10)
        discount_field = ft.TextField(label="الخصم", keyboard_type=ft.KeyboardType.NUMBER, value="0", border_radius=10)
        paid_field = ft.TextField(label="المبلغ المدفوع", keyboard_type=ft.KeyboardType.NUMBER, value="0", border_radius=10)
        notes_field = ft.TextField(label="ملاحظات", border_radius=10, multiline=True, min_lines=1, max_lines=2)
        
        # ====== حقول اختيارية مع Checkbox ======
        has_transport = ft.Checkbox(label="🚚 يوجد تكلفة نقل", value=False)
        has_loading = ft.Checkbox(label="📦 يوجد تحميل وتفريغ", value=False)
        has_tax = ft.Checkbox(label="🧾 يوجد ضريبة", value=False)
        has_other = ft.Checkbox(label="💰 مصاريف أخرى", value=False)
        
        transport_field = ft.TextField(label="تكلفة النقل", value="0", keyboard_type=ft.KeyboardType.NUMBER, border_radius=10, visible=False)
        loading_field = ft.TextField(label="التحميل والتفريغ", value="0", keyboard_type=ft.KeyboardType.NUMBER, border_radius=10, visible=False)
        tax_field = ft.TextField(label="الضريبة", value="0", keyboard_type=ft.KeyboardType.NUMBER, border_radius=10, visible=False)
        other_field = ft.TextField(label="مصاريف أخرى", value="0", keyboard_type=ft.KeyboardType.NUMBER, border_radius=10, visible=False)
        
        # دوال التبديل - داخل الدالة عشان تقدر توصل للمتغيرات
        def toggle_transport(e):
            transport_field.visible = has_transport.value
            if not has_transport.value:
                transport_field.value = "0"
            self.page.update()
        
        def toggle_loading(e):
            loading_field.visible = has_loading.value
            if not has_loading.value:
                loading_field.value = "0"
            self.page.update()
        
        def toggle_tax(e):
            tax_field.visible = has_tax.value
            if not has_tax.value:
                tax_field.value = "0"
            self.page.update()
        
        def toggle_other(e):
            other_field.visible = has_other.value
            if not has_other.value:
                other_field.value = "0"
            self.page.update()
        
        has_transport.on_change = toggle_transport
        has_loading.on_change = toggle_loading
        has_tax.on_change = toggle_tax
        has_other.on_change = toggle_other
        
        # اختيار المنتج
        product_dropdown = ft.Dropdown(
            label="اختر منتج",
            options=[ft.dropdown.Option(str(p.id), f"{p.name} (المخزون: {p.quantity})") for p in products],
            border_radius=10, width=250,
        )
        qty_field = ft.TextField(label="الكمية", keyboard_type=ft.KeyboardType.NUMBER, value="1", width=80, border_radius=10)
        price_field = ft.TextField(label="سعر الشراء", keyboard_type=ft.KeyboardType.NUMBER, border_radius=10, width=120)
        
        cart_list = ft.ListView(height=150, spacing=5)
        total_label = ft.Text("الإجمالي: 0.00", size=self._font_l, weight=ft.FontWeight.BOLD)
        
        def add_to_cart(e):
            if not product_dropdown.value:
                self.show_message("اختر منتج", ft.Colors.RED)
                return
            try:
                qty = int(qty_field.value or 1)
                price = float(price_field.value or 0)
                if qty <= 0 or price <= 0:
                    self.show_message("قيم غير صحيحة", ft.Colors.RED)
                    return
            except ValueError:
                self.show_message("قيم غير صحيحة", ft.Colors.RED)
                return
            
            product = self.db.get_product_by_id(int(product_dropdown.value))
            purchase_cart.append({
                'product_id': int(product_dropdown.value),
                'product_name': product.name if product else "منتج",
                'quantity': qty,
                'unit_price': price,
                'discount_percent': 0,
            })
            refresh_cart()
        
        def refresh_cart():
            cart_list.controls.clear()
            total = 0
            for i, item in enumerate(purchase_cart):
                subtotal = item['unit_price'] * item['quantity']
                total += subtotal
                cart_list.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Text(f"{item['product_name']}", expand=2, size=self._font_s),
                            ft.Text(f"{item['quantity']} × {item['unit_price']:.2f}", size=self._font_s),
                            ft.Text(f"= {subtotal:.2f}", size=self._font_s, weight=ft.FontWeight.BOLD),
                            ft.IconButton(ft.Icons.DELETE, icon_size=self._icon_s, icon_color=ft.Colors.RED,
                                on_click=lambda _, idx=i: remove_item(idx)),
                        ]),
                        padding=5,
                    )
                )
            total_label.value = f"الإجمالي: {total:.2f}"
            self.page.update()
        
        def remove_item(idx):
            if 0 <= idx < len(purchase_cart):
                purchase_cart.pop(idx)
                refresh_cart()
        
        def save_purchase(e):
            if not purchase_cart:
                self.show_message("أضف منتجات للفاتورة", ft.Colors.RED)
                return
            
            try:
                discount = float(discount_field.value or 0)
                paid = float(paid_field.value or 0)
                transport = float(transport_field.value or 0)
                loading = float(loading_field.value or 0)
                tax = float(tax_field.value or 0)
                other = float(other_field.value or 0)
            except ValueError:
                self.show_message("قيم غير صحيحة", ft.Colors.RED)
                return
            
            user_id = self.current_user.get('id') if self.current_user else None
            success, msg, _ = self.db.process_purchase_invoice(
                supplier_id, purchase_cart, date_field.value,
                transport_cost=transport, loading_cost=loading, tax=tax,
                other_costs=other, discount=discount,
                paid_amount=paid, notes=notes_field.value, user_id=user_id
            )
            
            if success:
                self.show_message(f"✅ {msg}", ft.Colors.GREEN)
                self.close_dialog(dlg)
                self.show_purchases()
            else:
                self.show_message(f"❌ {msg}", ft.Colors.RED)
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"فاتورة شراء - {supplier_name}", weight=ft.FontWeight.BOLD, size=18),
            content=ft.Container(
                width=550, height=600,
                content=ft.Column([
                    supplier_field,
                    ft.Row([date_field, discount_field, paid_field], spacing=10),
                    ft.Divider(),
                    ft.Text("مصاريف إضافية:", weight=ft.FontWeight.BOLD, size=self._font_m),
                    ft.Row([has_transport, has_loading], spacing=10),
                    ft.Row([has_tax, has_other], spacing=10),
                    ft.Row([transport_field, loading_field], spacing=10),
                    ft.Row([tax_field, other_field], spacing=10),
                    ft.Divider(),
                    ft.Text("إضافة منتج:", weight=ft.FontWeight.BOLD, size=self._font_m),
                    ft.Row([product_dropdown, qty_field, price_field], spacing=5),
                    ft.ElevatedButton("➕ إضافة للفاتورة", on_click=add_to_cart, bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE),
                    total_label,
                    ft.Container(content=cart_list, border=ft.border.all(1, ft.Colors.GREY_300), border_radius=8, height=150),
                    notes_field,
                ], tight=True, spacing=8, scroll=ft.ScrollMode.AUTO),
            ),
            actions=[
                ft.TextButton("إلغاء", on_click=lambda _: self.close_dialog(dlg)),
                ft.ElevatedButton("💾 حفظ الفاتورة", on_click=save_purchase, bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE),
            ],
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()















    
    def show_debts(self, e=None):
        self.current_page = "debts"
        self.page.clean()
        
        debts_list = ft.ListView(expand=True, spacing=10)
        debts = self.db.get_customer_debts()
        
        for debt in debts:
            debts_list.controls.append(
                ft.Container(
                    bgcolor=ft.Colors.WHITE, border_radius=10, padding=15,
                    content=ft.Column([
                        ft.Row([
                            ft.Text(debt['customer_name'], size=self._font_l, weight=ft.FontWeight.BOLD),
                            ft.Container(expand=True),
                            ft.Text(debt['status'], size=self._font_s, color=ft.Colors.RED if debt['remaining'] > 0 else ft.Colors.GREEN),
                        ]),
                        ft.Row([
                            ft.Text(f"المبلغ: {debt['amount']:.2f}", size=self._font_m),
                            ft.Text(f"المتبقي: {debt['remaining']:.2f}", size=self._font_m, color=ft.Colors.RED if debt['remaining'] > 0 else ft.Colors.GREEN),
                            ft.Container(expand=True),
                            ft.IconButton(ft.Icons.PAYMENT, icon_color=ft.Colors.GREEN, on_click=lambda _, d=debt: self.show_payment_dialog(d['customer_id'], d['customer_name'], d['id'])),
                        ]),
                    ], spacing=8),
                    shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK)),
                )
            )
        
        self.page.add(
            ft.AppBar(
                title=ft.Text("سجل الديون"),
                bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE,
                leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=self.show_home, icon_color=ft.Colors.WHITE),
            ),
            ft.Container(expand=True, padding=20, content=ft.Column([
                ft.Text("الديون غير المسددة", size=18, weight=ft.FontWeight.BOLD),
                ft.Container(content=debts_list, expand=True),
            ], expand=True)),
        )
    
    def show_expenses(self, e=None):
        self.current_page = "expenses"
        self.page.clean()
        
        expenses_list = ft.ListView(expand=True, spacing=10)
        
        def refresh():
            expenses_list.controls.clear()
            items = self.db.get_expenses()
            total = sum(i['amount'] for i in items)
            
            for item in items:
                expenses_list.controls.append(
                    ft.Container(
                        bgcolor=ft.Colors.WHITE, border_radius=10, padding=15,
                        content=ft.Row([
                            ft.Column([
                                ft.Text(item['title'], weight=ft.FontWeight.BOLD),
                                ft.Text(f"{item['category']} | {item['expense_date']}", size=self._font_s, color=ft.Colors.GREY_600),
                            ], expand=True),
                            ft.Text(f"{item['amount']:.2f} ج.م", size=self._font_l, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700),
                            ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.RED_400, on_click=lambda _, iid=item['id']: delete_expense(iid)),
                        ])
                    )
                )
            self.page.update()
        
        def delete_expense(eid):
            self.db.delete_expense(eid)
            refresh()
        
        def add_dlg(e):
            title_f = ft.TextField(label="عنوان المصروف", autofocus=True)
            amount_f = ft.TextField(label="المبلغ", keyboard_type=ft.KeyboardType.NUMBER)
            cat_f = ft.TextField(label="التصنيف", value="عام")
            note_f = ft.TextField(label="ملاحظات", multiline=True)
            
            def save(e):
                try:
                    amt = float(amount_f.value)
                    user_id = self.current_user.get('id') if self.current_user else None
                    success, msg = self.db.add_expense(title_f.value, amt, cat_f.value, note_f.value, user_id)
                    self.show_message(msg)
                    if success:
                        self.close_dialog(dlg)
                        refresh()
                except:
                    self.show_message("خطأ في القيمة", ft.Colors.RED)
            
            dlg = ft.AlertDialog(
                title=ft.Text("تسجيل مصروف"),
                content=ft.Column([title_f, amount_f, cat_f, note_f], tight=True),
                actions=[ft.TextButton("إلغاء", on_click=lambda _: self.close_dialog(dlg)),
                         ft.ElevatedButton("حفظ", on_click=save)]
            )
            self.page.overlay.append(dlg)
            dlg.open = True
            self.page.update()
        
        self.page.add(
            ft.AppBar(
                title=ft.Text("إدارة المصروفات"),
                bgcolor=ft.Colors.ORANGE_700, color=ft.Colors.WHITE,
                leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=self.show_home, icon_color=ft.Colors.WHITE),
            ),
            ft.Container(expand=True, padding=20, content=ft.Column([
                ft.ElevatedButton("إضافة مصروف", on_click=add_dlg, bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE),
                ft.Divider(),
                expenses_list,
            ], expand=True)),
        )
        refresh()



    def show_debts(self, e=None):
        """صفحة الديون"""
        self.current_page = "debts"
        self.page.clean()
        
        debts_list = ft.ListView(expand=True, spacing=10)
        debts = self.db.get_customer_debts()
        
        if not debts:
            debts_list.controls.append(
                ft.Container(
                    content=ft.Text("لا توجد ديون مستحقة", size=self._font_l, color=ft.Colors.GREY_500),
                    alignment=ft.alignment.center, padding=50,
                )
            )
        else:
            for debt in debts:
                status_color = ft.Colors.RED if debt['remaining'] > 0 else ft.Colors.GREEN
                status_text = "غير مسدد" if debt['remaining'] > 0 else "مسدد"
                
                debts_list.controls.append(
                    ft.Container(
                        bgcolor=ft.Colors.WHITE, border_radius=10, padding=15,
                        shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK)),
                        content=ft.Column([
                            ft.Row([
                                ft.Text(debt['customer_name'], size=self._font_l, weight=ft.FontWeight.BOLD),
                                ft.Container(expand=True),
                                ft.Container(
                                    content=ft.Text(status_text, size=self._font_s, weight=ft.FontWeight.BOLD, color=status_color),
                                    bgcolor=ft.Colors.GREY_50, border_radius=10,
                                    padding=ft.padding.symmetric(horizontal=8, vertical=3),
                                ),
                            ]),
                            ft.Container(height=10),
                            ft.Row([
                                ft.Column([
                                    ft.Text("المبلغ", size=10, color=ft.Colors.GREY_500),
                                    ft.Text(f"{debt['amount']:.2f} ج.م", size=self._font_m, weight=ft.FontWeight.BOLD),
                                ], expand=True),
                                ft.Column([
                                    ft.Text("المتبقي", size=10, color=ft.Colors.GREY_500),
                                    ft.Text(f"{debt['remaining']:.2f} ج.م", size=self._font_m, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700),
                                ], expand=True),
                                ft.Column([
                                    ft.Text("التاريخ", size=10, color=ft.Colors.GREY_500),
                                    ft.Text(debt['created_at'][:10], size=self._font_s),
                                ], expand=True),
                            ]),
                            ft.Container(height=10),
                            ft.Row([
                                ft.Container(expand=True),
                                ft.ElevatedButton(
                                    "💵 سداد",
                                    icon=ft.Icons.PAYMENT,
                                    on_click=lambda _, d=debt: self.show_payment_dialog(d['customer_id'], d['customer_name'], d['id']),
                                    bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE,
                                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                                    height=self._btn_small,
                                ),
                            ]),
                        ], spacing=5),
                    )
                )
        
        self.page.add(
            ft.AppBar(
                title=ft.Text("💰 سجل الديون", color=ft.Colors.WHITE, size=18, weight=ft.FontWeight.BOLD),
                bgcolor=ft.Colors.RED_700,
                leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=self.show_home, icon_color=ft.Colors.WHITE),
            ),
            ft.Container(expand=True, padding=15, content=debts_list),
        )
    
    def show_reports(self, e=None):
        self.current_page = "reports"
        self.page.clean()
        
        start_date = ft.TextField(label="من", value=datetime.now().strftime("%Y-%m-%d"), width=150)
        end_date = ft.TextField(label="إلى", value=datetime.now().strftime("%Y-%m-%d"), width=150)
        
        sales_list = ft.ListView(expand=True, spacing=10)
        total_label = ft.Text("0", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE)
        profit_label = ft.Text("0", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN)
        
        def filter_sales(e):
            sales = self.db.get_sales_between_dates(start_date.value, end_date.value)
            total_profit = sum(s["profit"] for s in sales)
            total_sales_amount = sum(s["total_amount"] for s in sales)
            
            total_label.value = f"{total_sales_amount:.0f}"
            profit_label.value = f"{total_profit:.0f}"
            
            sales_list.controls.clear()
            for sale in sales:
                sales_list.controls.append(
                    ft.Container(
                        bgcolor=ft.Colors.WHITE, border_radius=8, padding=10,
                        content=ft.Row([
                            ft.Column([
                                ft.Text(f"فاتورة: {sale['invoice_no']}", weight=ft.FontWeight.BOLD),
                                ft.Text(f"العميل: {sale['customer_name']} | {sale['payment_type']}", size=self._font_s),
                            ], expand=True),
                            ft.Column([
                                ft.Text(f"{sale['total_amount']:.2f}", size=self._font_m, weight=ft.FontWeight.BOLD),
                                ft.Text(f"ربح: {sale['profit']:.2f}", size=self._font_s, color=ft.Colors.GREEN),
                            ], horizontal_alignment=ft.CrossAxisAlignment.END),
                        ])
                    )
                )
            self.page.update()
        
        self.page.add(
            ft.AppBar(
                title=ft.Text("التقارير"),
                bgcolor=ft.Colors.TEAL_700, color=ft.Colors.WHITE,
                leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=self.show_home, icon_color=ft.Colors.WHITE),
            ),
            ft.Container(expand=True, padding=20, content=ft.Column([
                ft.Row([start_date, end_date, ft.ElevatedButton("عرض", on_click=filter_sales)], spacing=10),
                ft.Row([
                    self._create_stat_card("إجمالي المبيعات", total_label.value, ft.Icons.RECEIPT, ft.Colors.BLUE),
                    self._create_stat_card("صافي الربح", profit_label.value, ft.Icons.TRENDING_UP, ft.Colors.GREEN),
                ], spacing=20),
                ft.Divider(),
                sales_list,
            ], expand=True)),
        )
        filter_sales(None)
    
    



    def show_history(self, e=None):
        """سجل الحركات المتقدم"""
        self.current_page = "history"
        self.page.clean()
        
        # متغيرات التاريخ (افتراضي: الكل)
        self._history_start = "2000-01-01"
        self._history_end = datetime.now().strftime("%Y-%m-%d")
        self._history_filter = "all"
        
        # ====== قوائم منسدلة للسنة والشهر ======
        current_year = datetime.now().year
        
        # قائمة السنوات
        year_options = [ft.dropdown.Option("all", "🌐 كل السنين")]
        for y in range(current_year, current_year - 10, -1):
            year_options.append(ft.dropdown.Option(str(y), str(y)))
        
        year_dropdown = ft.Dropdown(
            label="السنة", width=120, border_radius=10,
            options=year_options, value="all",
        )
        
        # قائمة الشهور
        month_names = {1:"يناير",2:"فبراير",3:"مارس",4:"أبريل",5:"مايو",6:"يونيو",
                       7:"يوليو",8:"أغسطس",9:"سبتمبر",10:"أكتوبر",11:"نوفمبر",12:"ديسمبر"}
        
        month_options = [ft.dropdown.Option("all", "🌐 كل الشهور")]
        for m in range(1, 13):
            month_options.append(ft.dropdown.Option(str(m), month_names[m]))
        
        month_dropdown = ft.Dropdown(
            label="الشهر", width=120, border_radius=10,
            options=month_options, value="all",
        )
        
        # اختيار نوع الحركة
        type_dropdown = ft.Dropdown(
            label="نوع الحركة", width=160, border_radius=10,
            options=[
                ft.dropdown.Option("all", "🔍 كل الحركات"),
                ft.dropdown.Option("sell", "🛒 مبيعات"),
                ft.dropdown.Option("add_stock", "📥 إضافة مخزون"),
                ft.dropdown.Option("payment", "💵 سداد"),
                ft.dropdown.Option("add_debt", "💰 ديون"),
                ft.dropdown.Option("expense", "💸 مصروفات"),
                ft.dropdown.Option("purchase", "🧾 مشتريات"),
                ft.dropdown.Option("create_product", "📦 منتجات جديدة"),
            ],
            value="all",
        )
        
        # دالة تحديد التاريخ من السنة والشهر
        def set_date_from_selectors(e=None):
            year_val = year_dropdown.value
            month_val = month_dropdown.value
            
            if year_val == "all":
                self._history_start = "2000-01-01"
                self._history_end = datetime.now().strftime("%Y-%m-%d")
            elif month_val == "all":
                self._history_start = f"{year_val}-01-01"
                self._history_end = f"{year_val}-12-31"
            else:
                m = int(month_val)
                self._history_start = f"{year_val}-{m:02d}-01"
                if m == 12:
                    self._history_end = f"{year_val}-12-31"
                else:
                    next_month = f"{year_val}-{m+1:02d}-01"
                    last_day = (datetime.strptime(next_month, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
                    self._history_end = last_day
            
            self._load_history(self._history_start, self._history_end, type_dropdown.value or "all")
        
        year_dropdown.on_change = set_date_from_selectors
        month_dropdown.on_change = set_date_from_selectors
        type_dropdown.on_change = lambda e: self._load_history(self._history_start, self._history_end, type_dropdown.value or "all")
        
        # أزرار سريعة
        def set_period(days):
            if days == 0:
                self._history_start = datetime.now().strftime("%Y-%m-%d")
                self._history_end = datetime.now().strftime("%Y-%m-%d")
            elif days == -1:
                self._history_start = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
                self._history_end = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            elif days == -2:
                self._history_start = "2000-01-01"
                self._history_end = datetime.now().strftime("%Y-%m-%d")
            else:
                self._history_start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
                self._history_end = datetime.now().strftime("%Y-%m-%d")
            year_dropdown.value = "all"
            month_dropdown.value = "all"
            self._load_history(self._history_start, self._history_end, type_dropdown.value or "all")
            self.page.update()
        
        quick_periods = ft.Row([
            ft.Chip(label=ft.Text("📅 اليوم"), on_click=lambda _: set_period(0), bgcolor=ft.Colors.BLUE_50),
            ft.Chip(label=ft.Text("⬅ أمس"), on_click=lambda _: set_period(-1), bgcolor=ft.Colors.CYAN_50),
            ft.Chip(label=ft.Text("7 أيام"), on_click=lambda _: set_period(7), bgcolor=ft.Colors.GREEN_50),
            ft.Chip(label=ft.Text("30 يوم"), on_click=lambda _: set_period(30), bgcolor=ft.Colors.ORANGE_50),
            ft.Chip(label=ft.Text("الكل"), on_click=lambda _: set_period(-2), bgcolor=ft.Colors.GREY_50),
        ], scroll=ft.ScrollMode.AUTO, spacing=5)
        
        # قائمة الحركات
        self.history_list = ft.ListView(expand=True, spacing=8, padding=10)
        self.stats_text = ft.Text("", size=self._font_m, color=ft.Colors.GREY_600)
        
        self.page.add(
            ft.AppBar(
                title=ft.Text("📋 سجل الحركات", color=ft.Colors.WHITE, size=18, weight=ft.FontWeight.BOLD),
                bgcolor=ft.Colors.PURPLE_700,
                leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=self.show_home, icon_color=ft.Colors.WHITE),
            ),
            ft.Container(
                expand=True, padding=15,
                content=ft.Column([
                    ft.Container(
                        bgcolor=ft.Colors.WHITE, border_radius=12, padding=15,
                        shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK)),
                        content=ft.Column([
                            ft.Row([year_dropdown, month_dropdown, type_dropdown], spacing=8),
                            ft.Container(height=8),
                            quick_periods,
                        ], spacing=5),
                    ),
                    ft.Container(height=10),
                    self.stats_text,
                    ft.Container(height=5),
                    ft.Container(content=self.history_list, expand=True),
                ], expand=True),
            ),
        )
        self._load_history(self._history_start, self._history_end, "all")
    
    def _load_history(self, start_date: str, end_date: str, filter_type: str = "all"):
        """تحميل وعرض الحركات"""
        self.history_list.controls.clear()
        cursor = self.db.conn.cursor()
        
        query = """
            SELECT id, product_name, operation_type, quantity_change, 
                   old_quantity, new_quantity, profit_change, note, created_at, user_id
            FROM stock_history 
            WHERE created_at BETWEEN ? AND ?
        """
        params = [f"{start_date} 00:00:00", f"{end_date} 23:59:59"]
        
        if filter_type != "all":
            query += " AND operation_type = ?"
            params.append(filter_type)
        
        query += " ORDER BY created_at DESC LIMIT 500"
        cursor.execute(query, params)
        history = [dict(row) for row in cursor.fetchall()]
        
        type_config = {
            "create_product": ("📦", ft.Colors.BLUE_700, ft.Colors.BLUE_50, "إضافة منتج"),
            "edit_product": ("✏️", ft.Colors.ORANGE_700, ft.Colors.ORANGE_50, "تعديل منتج"),
            "delete_product": ("🗑️", ft.Colors.RED_700, ft.Colors.RED_50, "حذف منتج"),
            "add_stock": ("📥", ft.Colors.GREEN_700, ft.Colors.GREEN_50, "إضافة مخزون"),
            "sell": ("🛒", ft.Colors.CYAN_700, ft.Colors.CYAN_50, "عملية بيع"),
            "add_customer": ("👤", ft.Colors.PURPLE_700, ft.Colors.PURPLE_50, "إضافة عميل"),
            "add_debt": ("💰", ft.Colors.AMBER_700, ft.Colors.AMBER_50, "تسجيل دين"),
            "payment": ("💵", ft.Colors.GREEN_700, ft.Colors.GREEN_50, "سداد دين"),
            "expense": ("💸", ft.Colors.RED_700, ft.Colors.RED_50, "مصروف"),
            "purchase": ("🧾", ft.Colors.INDIGO_700, ft.Colors.INDIGO_50, "فاتورة شراء"),
        }
        
        self.stats_text.value = f"📊 عدد الحركات: {len(history)} | {start_date} → {end_date}"
        
        if not history:
            self.history_list.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.HISTORY, size=60, color=ft.Colors.GREY_300),
                        ft.Text("لا توجد حركات في هذه الفترة", size=self._font_l, color=ft.Colors.GREY_400),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.center, padding=50,
                )
            )
            self.page.update()
            return
        
        for record in history:
            op_type = record['operation_type']
            emoji, color, bg_color, type_name = type_config.get(op_type, ("📋", ft.Colors.GREY_700, ft.Colors.GREY_50, op_type))
            
            qty_text = ""
            if record['quantity_change'] != 0:
                qty_text = f"الكمية: {record['old_quantity']} → {record['new_quantity']} (تغير: {record['quantity_change']:+d})"
            
            profit_text = ""
            if record['profit_change'] != 0:
                profit_text = f" | الربح: {record['profit_change']:+.2f} ج.م"
            
            self.history_list.controls.append(
                ft.Container(
                    bgcolor=ft.Colors.WHITE, border_radius=12, padding=12,
                    border=ft.border.only(left=ft.border.BorderSide(4, color)),
                    shadow=ft.BoxShadow(blur_radius=3, color=ft.Colors.with_opacity(0.05, ft.Colors.BLACK)),
                    content=ft.Row([
                        ft.Container(
                            content=ft.Text(emoji, size=22),
                            bgcolor=bg_color, border_radius=12, padding=8, width=45, height=self._btn_h,
                            alignment=ft.alignment.center,
                        ),
                        ft.Container(width=10),
                        ft.Column([
                            ft.Row([
                                ft.Text(type_name, size=self._font_m, weight=ft.FontWeight.BOLD, color=color),
                                ft.Container(width=8),
                                ft.Text(record['product_name'] or "", size=self._font_m, color=ft.Colors.GREY_700),
                            ]),
                            ft.Text(qty_text, size=self._font_s, color=ft.Colors.GREY_600) if qty_text else ft.Container(),
                            ft.Text(f"{record['note'] or ''}{profit_text}", size=self._font_s, color=ft.Colors.GREY_500) if record['note'] else ft.Container(),
                            ft.Text(f"🕐 {record['created_at'][:16]}", size=10, color=ft.Colors.GREY_400),
                        ], expand=True, spacing=3),
                    ]),
                )
            )
        
        self.page.update()
    def show_product_tracking(self, e=None):
        self.current_page = "tracking"
        self.page.clean()
        
        products = self.db.get_all_products()
        products_dropdown = ft.Dropdown(
            label="اختر منتجاً",
            options=[ft.dropdown.Option(str(p.id), p.name) for p in products],
            width=300,
        )
        
        product_details = ft.Column(visible=False, scroll=ft.ScrollMode.AUTO, expand=True)
        
        def show_stats(e):
            if not products_dropdown.value:
                return
            product_id = int(products_dropdown.value)
            data = self.db.get_detailed_product_history(product_id)
            if not data:
                return
            
            product_details.visible = True
            product_details.controls.clear()
            
            p = data["product"]
            stats = data["statistics"]
            
            product_details.controls.append(
                ft.Container(
                    bgcolor=ft.Colors.BLUE_50, border_radius=10, padding=15,
                    content=ft.Column([
                        ft.Text(p.name, size=20, weight=ft.FontWeight.BOLD),
                        ft.Text(f"سعر: {p.selling_price:.2f} | مخزون: {p.quantity} | حد التنبيه: {p.min_stock_threshold}", size=self._font_m),
                        ft.Text(f"إجمالي المبيعات: {stats['total_sold']} قطعة | إجمالي الربح: {stats['total_profit']:.2f}", size=self._font_m, color=ft.Colors.GREEN),
                    ], spacing=5)
                )
            )
            
            product_details.controls.append(ft.Text("سجل المخزون", size=self._font_l, weight=ft.FontWeight.BOLD))
            for record in data["history"][:20]:
                product_details.controls.append(
                    ft.Container(
                        bgcolor=ft.Colors.WHITE, border_radius=8, padding=10, margin=ft.Margin(0,0,0,5),
                        content=ft.Row([
                            ft.Text(f"{record.quantity_change:+d}", size=self._font_m, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN if record.quantity_change > 0 else ft.Colors.RED),
                            ft.Text(record.note or "", size=self._font_s),
                            ft.Container(expand=True),
                            ft.Text(record.created_at[:16], size=self._font_s, color=ft.Colors.GREY_600),
                        ])
                    )
                )
            
            self.page.update()
        
        self.page.add(
            ft.AppBar(
                title=ft.Text("تتبع المنتجات"),
                bgcolor=ft.Colors.TEAL_700, color=ft.Colors.WHITE,
                leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=self.show_home, icon_color=ft.Colors.WHITE),
            ),
            ft.Container(expand=True, padding=20, content=ft.Column([
                ft.Row([products_dropdown, ft.ElevatedButton("عرض", on_click=show_stats)], spacing=10),
                ft.Divider(),
                ft.Container(content=product_details, expand=True),
            ], expand=True)),
        )
    
    def show_yearly_reports(self, e=None):
        self.current_page = "yearly"
        self.page.clean()
        
        current_year = datetime.now().year
        year_dropdown = ft.Dropdown(
            label="السنة",
            options=[ft.dropdown.Option(str(y), str(y)) for y in range(current_year, current_year - 5, -1)],
            value=str(current_year), width=150,
        )
        
        report_content = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO)
        
        def show_report(e):
            report = self.db.get_yearly_report(int(year_dropdown.value))
            report_content.controls.clear()
            
            summary = report["summary"]
            report_content.controls.append(
                ft.Container(
                    bgcolor=ft.Colors.BLUE_50, border_radius=10, padding=15,
                    content=ft.Column([
                        ft.Text(f"تقرير عام {report['year']}", size=20, weight=ft.FontWeight.BOLD),
                        ft.Row([
                            self._create_stat_card("الأرباح", f"{summary['year_profit']:.0f}", ft.Icons.TRENDING_UP, ft.Colors.GREEN),
                            self._create_stat_card("العمليات", str(summary['year_sales']), ft.Icons.RECEIPT, ft.Colors.BLUE),
                            self._create_stat_card("الإيرادات", f"{summary['year_revenue']:.0f}", ft.Icons.MONEY, ft.Colors.ORANGE),
                        ], spacing=20),
                    ])
                )
            )
            
            month_names = {"01": "يناير", "02": "فبراير", "03": "مارس", "04": "أبريل", "05": "مايو", "06": "يونيو",
                          "07": "يوليو", "08": "أغسطس", "09": "سبتمبر", "10": "أكتوبر", "11": "نوفمبر", "12": "ديسمبر"}
            
            for m in report["monthly_data"]:
                report_content.controls.append(
                    ft.Container(
                        bgcolor=ft.Colors.WHITE, border_radius=8, padding=10, margin=ft.Margin(0,0,0,5),
                        content=ft.Row([
                            ft.Text(month_names.get(m['month'], m['month']), size=self._font_m, weight=ft.FontWeight.BOLD, width=100),
                            ft.Text(f"عمليات: {m['total_sales']}", size=self._font_s, expand=True),
                            ft.Text(f"ربح: {m['total_profit']:.2f}", size=self._font_s, color=ft.Colors.GREEN),
                        ])
                    )
                )
            
            self.page.update()
        
        self.page.add(
            ft.AppBar(
                title=ft.Text("التقارير السنوية"),
                bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE,
                leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=self.show_home, icon_color=ft.Colors.WHITE),
            ),
            ft.Container(expand=True, padding=20, content=ft.Column([
                ft.Row([year_dropdown, ft.ElevatedButton("عرض", on_click=show_report)], spacing=10),
                ft.Divider(),
                ft.Container(content=report_content, expand=True),
            ], expand=True)),
        )
        show_report(None)

# =============================================================================
# تشغيل التطبيق
# =============================================================================

def main(page: ft.Page):
    try:
        app = StoreManagementApp(page)
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        page.clean()
        page.add(
            ft.Container(
                expand=True, padding=30,
                content=ft.Column([
                    ft.Icon(ft.Icons.ERROR_OUTLINE, size=60, color=ft.Colors.RED),
                    ft.Text("حدث خطأ", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.RED),
                    ft.Text(str(e), size=self._font_m, color=ft.Colors.GREY_700),
                    ft.Container(
                        padding=10, bgcolor=ft.Colors.GREY_100, border_radius=8,
                        content=ft.Text(error_msg, size=10, selectable=True),
                    ),
                    ft.ElevatedButton("إعادة المحاولة", on_click=lambda _: main(page)),
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15, scroll=ft.ScrollMode.AUTO),
            )
        )
        page.update()

if __name__ == "__main__":
    ft.app(target=main)





















