import sqlite3
import flet as ft
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple
import json

# =============================================================================
# نماذج البيانات (Models)
# =============================================================================

@dataclass
class Product:
    """نموذج المنتج"""
    id: Optional[int] = None
    name: str = ""
    purchase_price: float = 0.0  # سعر الشراء
    selling_price: float = 0.0   # سعر البيع
    quantity: int = 0
    created_at: str = ""
    updated_at: str = ""
    min_stock_threshold: int = 5  # الحد الأدنى للتنبيه

@dataclass
class Sale:
    """نموذج عملية البيع"""
    id: Optional[int] = None
    product_id: int = 0
    product_name: str = ""
    quantity: int = 0
    selling_price: float = 0.0
    purchase_price: float = 0.0
    profit: float = 0.0  # الربح من هذه العملية
    sale_date: str = ""
    customer: str = ""
    is_debt: int = 0

@dataclass
class StockHistory:
    """نموذج سجل الحركات"""
    id: Optional[int] = None
    product_id: int = 0
    product_name: str = ""
    operation_type: str = ""  # add_stock, sell, create_product, edit_product, delete_product
    quantity_change: int = 0  # التغير في الكمية (موجب للإضافة، سالب للبيع)
    old_quantity: int = 0
    new_quantity: int = 0
    profit_change: float = 0.0  # التغير في الربح
    note: str = ""
    created_at: str = ""

@dataclass
class Customer:
    """نموذج العميل"""
    id: Optional[int] = None
    name: str = ""
    phone: str = ""
    created_at: str = ""
    total_debt: float = 0.0
    total_paid: float = 0.0

@dataclass
class Debt:
    """نموذج الدين"""
    id: Optional[int] = None
    customer_id: int = 0
    customer_name: str = ""
    sale_id: int = 0
    amount: float = 0.0
    remaining: float = 0.0
    status: str = "pending"  # pending, partial, paid
    created_at: str = ""
    note: str = ""

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

# =============================================================================
# إدارة قاعدة البيانات (Database)
# =============================================================================

class Database:
    """إدارة اتصال قاعدة البيانات والعمليات الأساسية"""
    
    def __init__(self):
        self.conn = sqlite3.connect("store_management.db", check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()
    
    def create_tables(self):
        """إنشاء جميع الجداول المطلوبة"""
        cursor = self.conn.cursor()
        
        # جدول المنتجات
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                purchase_price REAL NOT NULL,
                selling_price REAL NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                min_stock_threshold INTEGER DEFAULT 5
            )
        """)
        
        # جدول المبيعات
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                selling_price REAL NOT NULL,
                purchase_price REAL NOT NULL,
                profit REAL NOT NULL,
                sale_date TEXT NOT NULL,
                customer TEXT DEFAULT '',
                is_debt INTEGER DEFAULT 0,
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)
        
        # جدول سجل الحركات
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
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)
        
        # جدول العملاء
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                phone TEXT,
                created_at TEXT NOT NULL,
                total_debt REAL DEFAULT 0,
                total_paid REAL DEFAULT 0
            )
        """)
        
        # جدول الديون
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS debts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                customer_name TEXT NOT NULL,
                sale_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                remaining REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TEXT NOT NULL,
                note TEXT,
                FOREIGN KEY (customer_id) REFERENCES customers(id),
                FOREIGN KEY (sale_id) REFERENCES sales(id)
            )
        """)
        
        # جدول السداد
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                customer_name TEXT NOT NULL,
                debt_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                payment_date TEXT NOT NULL,
                payment_type TEXT DEFAULT 'cash',
                note TEXT,
                FOREIGN KEY (customer_id) REFERENCES customers(id),
                FOREIGN KEY (debt_id) REFERENCES debts(id)
            )
        """)
        
        # إنشاء فهارس لتحسين الأداء
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(sale_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_date ON stock_history(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_product ON stock_history(product_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_debts_customer ON debts(customer_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_debts_status ON debts(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_payments_customer ON payments(customer_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_payments_date ON payments(payment_date)")
        
        self.conn.commit()
    
    # ========== عمليات المنتجات ==========
    
    def add_product(self, product: Product) -> Tuple[bool, str]:
        """إضافة منتج جديد"""
        cursor = self.conn.cursor()
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            product.created_at = now
            product.updated_at = now
            
            cursor.execute("""
                INSERT INTO products (name, purchase_price, selling_price, quantity, created_at, updated_at, min_stock_threshold)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (product.name, product.purchase_price, product.selling_price, 
                  product.quantity, product.created_at, product.updated_at, product.min_stock_threshold))
            
            product_id = cursor.lastrowid
            self.conn.commit()
            
            # تسجيل العملية في سجل الحركات
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
            WHERE name LIKE ? 
            ORDER BY name
        """, (f"%{query}%",))
        return [self._row_to_product(row) for row in cursor.fetchall()]
    
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
                SET name=?, purchase_price=?, selling_price=?, quantity=?, 
                    updated_at=?, min_stock_threshold=?
                WHERE id=?
            """, (product.name, product.purchase_price, product.selling_price, 
                  product.quantity, now, product.min_stock_threshold, product.id))
            
            self.conn.commit()
            
            quantity_change = product.quantity - old_quantity
            if quantity_change != 0:
                self.add_stock_history(
                    product_id=product.id,
                    product_name=product.name,
                    operation_type="edit_product",
                    quantity_change=quantity_change,
                    old_quantity=old_quantity,
                    new_quantity=product.quantity,
                    profit_change=0,
                    note=f"تعديل كمية المنتج"
                )
            
            return True, "تم تحديث المنتج بنجاح"
        except Exception as e:
            return False, f"خطأ في تحديث المنتج: {str(e)}"
    
    def delete_product(self, product_id: int) -> Tuple[bool, str]:
        """حذف منتج (مع الاحتفاظ بسجل المبيعات والحركات)"""
        cursor = self.conn.cursor()
        try:
            product = self.get_product_by_id(product_id)
            if not product:
                return False, "المنتج غير موجود"
            
            cursor.execute("SELECT COUNT(*) FROM sales WHERE product_id = ?", (product_id,))
            sales_count = cursor.fetchone()[0]
            
            if sales_count > 0:
                self.add_stock_history(
                    product_id=product_id,
                    product_name=product.name,
                    operation_type="delete_product",
                    quantity_change=0,
                    old_quantity=product.quantity,
                    new_quantity=0,
                    profit_change=0,
                    note=f"تم حذف المنتج (كان له {sales_count} عملية بيع مسجلة)"
                )
            
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
            
            self.conn.commit()
            
            self.add_stock_history(
                product_id=product_id,
                product_name=product.name,
                operation_type="add_stock",
                quantity_change=quantity,
                old_quantity=old_quantity,
                new_quantity=new_quantity,
                profit_change=0,
                note=f"إضافة {quantity} قطعة إلى المخزون"
            )
            
            return True, f"تم إضافة {quantity} قطعة إلى المخزون"
        except Exception as e:
            return False, f"خطأ في إضافة المخزون: {str(e)}"
    
    def get_low_stock_products(self) -> List[Product]:
        """الحصول على المنتجات المنخفضة المخزون"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM products 
            WHERE quantity <= min_stock_threshold 
            ORDER BY quantity
        """)
        return [self._row_to_product(row) for row in cursor.fetchall()]
    
    # ========== عمليات المبيعات ==========
    
    def sell_product(self, product_id: int, quantity: int, customer: str = "") -> Tuple[bool, str, float, int]:
        """بيع منتج"""
        cursor = self.conn.cursor()
        try:
            product = self.get_product_by_id(product_id)
            if not product:
                return False, "المنتج غير موجود", 0, 0
            
            if product.quantity < quantity:
                return False, f"الكمية غير كافية. المتوفر: {product.quantity}", 0, 0
            
            profit = (product.selling_price - product.purchase_price) * quantity
            
            old_quantity = product.quantity
            new_quantity = old_quantity - quantity
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sale_date = datetime.now().strftime("%Y-%m-%d")
            
            cursor.execute("""
                INSERT INTO sales (product_id, product_name, quantity, selling_price, 
                                  purchase_price, profit, sale_date, customer, is_debt)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (product_id, product.name, quantity, product.selling_price,
                  product.purchase_price, profit, sale_date, customer, 1 if customer else 0))
            
            sale_id = cursor.lastrowid
            
            cursor.execute("""
                UPDATE products 
                SET quantity = ?, updated_at = ?
                WHERE id = ?
            """, (new_quantity, now, product_id))
            
            self.conn.commit()
            
            self.add_stock_history(
                product_id=product_id,
                product_name=product.name,
                operation_type="sell",
                quantity_change=-quantity,
                old_quantity=old_quantity,
                new_quantity=new_quantity,
                profit_change=profit,
                note=f"بيع {quantity} قطعة {f'لـ {customer}' if customer else ''}"
            )
            
            return True, f"تم بيع {quantity} قطعة بنجاح. الربح: {profit:.2f}", profit, sale_id
        except Exception as e:
            return False, f"خطأ في عملية البيع: {str(e)}", 0, 0
    
    def get_sales_by_date(self, date: str = None) -> List[Dict]:
        """الحصول على المبيعات حسب التاريخ"""
        cursor = self.conn.cursor()
        if date:
            cursor.execute("""
                SELECT * FROM sales 
                WHERE sale_date = ? 
                ORDER BY id DESC
            """, (date,))
        else:
            cursor.execute("SELECT * FROM sales ORDER BY id DESC")
        return [dict(row) for row in cursor.fetchall()]
    
    def get_sales_between_dates(self, start_date: str, end_date: str) -> List[Dict]:
        """الحصول على المبيعات بين تاريخين"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM sales 
            WHERE sale_date BETWEEN ? AND ? 
            ORDER BY sale_date DESC
        """, (start_date, end_date))
        return [dict(row) for row in cursor.fetchall()]
    
    # ========== التقارير والإحصائيات ==========
    
    def get_product_statistics(self, product_id: int) -> Dict:
        """إحصائيات منتج معين"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT 
                COALESCE(SUM(quantity), 0) as total_sold,
                COALESCE(SUM(profit), 0) as total_profit
            FROM sales 
            WHERE product_id = ?
        """, (product_id,))
        sales_stats = dict(cursor.fetchone())
        
        cursor.execute("""
            SELECT sale_date 
            FROM sales 
            WHERE product_id = ? 
            ORDER BY sale_date DESC 
            LIMIT 1
        """, (product_id,))
        last_sale = cursor.fetchone()
        
        cursor.execute("""
            SELECT created_at, quantity_change, note 
            FROM stock_history 
            WHERE product_id = ? AND operation_type = 'add_stock'
            ORDER BY created_at DESC
        """, (product_id,))
        stock_history = [dict(row) for row in cursor.fetchall()]
        
        return {
            "total_sold": sales_stats["total_sold"],
            "total_profit": sales_stats["total_profit"],
            "last_sale_date": last_sale["sale_date"] if last_sale else None,
            "stock_history": stock_history
        }
    
    def get_overall_profit_loss(self) -> Dict:
        """إجمالي الأرباح والخسائر"""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COALESCE(SUM(profit), 0) FROM sales")
        total_profit = cursor.fetchone()[0]
        
        cursor.execute("SELECT COALESCE(SUM(purchase_price * quantity), 0) FROM products")
        total_inventory_value = cursor.fetchone()[0]
        
        return {
            "total_profit": total_profit,
            "total_inventory_value": total_inventory_value,
            "net_profit": total_profit
        }
    
    def get_yearly_report(self, year: int = None) -> Dict:
        """تقرير سنوي"""
        if year is None:
            year = datetime.now().year
        
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT 
                strftime('%m', sale_date) as month,
                COALESCE(SUM(profit), 0) as total_profit,
                COUNT(*) as total_sales,
                COALESCE(SUM(quantity), 0) as total_items_sold
            FROM sales 
            WHERE strftime('%Y', sale_date) = ?
            GROUP BY strftime('%m', sale_date)
            ORDER BY month
        """, (str(year),))
        
        monthly_data = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute("""
            SELECT 
                COALESCE(SUM(profit), 0) as year_profit,
                COUNT(*) as year_sales,
                COALESCE(SUM(quantity), 0) as year_items_sold
            FROM sales 
            WHERE strftime('%Y', sale_date) = ?
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
                SELECT * FROM stock_history 
                WHERE product_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (product_id, limit))
        else:
            cursor.execute("""
                SELECT * FROM stock_history 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
        
        return [self._row_to_history(row) for row in cursor.fetchall()]
    
    def get_detailed_product_history(self, product_id: int) -> Dict:
        """سجل كامل لمنتج معين"""
        product = self.get_product_by_id(product_id)
        if not product:
            return None
        
        sales = self.get_sales_by_date()
        sales = [s for s in sales if s['product_id'] == product_id]
        
        history = self.get_stock_history(product_id, limit=1000)
        statistics = self.get_product_statistics(product_id)
        
        return {
            "product": product,
            "sales": sales,
            "history": history,
            "statistics": statistics
        }
    
    # ========== عمليات العملاء ==========
    
    def add_customer(self, name: str, phone: str = "") -> Tuple[bool, str, int]:
        """إضافة عميل جديد"""
        cursor = self.conn.cursor()
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO customers (name, phone, created_at, total_debt, total_paid)
                VALUES (?, ?, ?, 0, 0)
            """, (name, phone, now))
            self.conn.commit()
            customer_id = cursor.lastrowid
            
            self.add_stock_history(
                product_id=0,
                product_name="",
                operation_type="add_customer",
                quantity_change=0,
                old_quantity=0,
                new_quantity=0,
                profit_change=0,
                note=f"تم إضافة عميل جديد: {name}"
            )
            
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
            WHERE name LIKE ? OR phone LIKE ?
            ORDER BY name
        """, (f"%{query}%", f"%{query}%"))
        return [dict(row) for row in cursor.fetchall()]
    
    def update_customer_debt(self, customer_id: int, amount: float, is_add: bool = True):
        """تحديث دين العميل"""
        cursor = self.conn.cursor()
        if is_add:
            cursor.execute("""
                UPDATE customers 
                SET total_debt = total_debt + ?
                WHERE id = ?
            """, (amount, customer_id))
        else:
            cursor.execute("""
                UPDATE customers 
                SET total_paid = total_paid + ?
                WHERE id = ?
            """, (amount, customer_id))
        self.conn.commit()
    
    # ========== عمليات الديون ==========
    
    def add_debt(self, customer_id: int, customer_name: str, sale_id: int, 
                 amount: float, note: str = "") -> Tuple[bool, str]:
        """تسجيل دين جديد"""
        cursor = self.conn.cursor()
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO debts (customer_id, customer_name, sale_id, amount, 
                                  remaining, status, created_at, note)
                VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)
            """, (customer_id, customer_name, sale_id, amount, amount, now, note))
            
            debt_id = cursor.lastrowid
            
            self.update_customer_debt(customer_id, amount, True)
            
            cursor.execute("""
                UPDATE sales SET is_debt = 1, customer = ?
                WHERE id = ?
            """, (customer_name, sale_id))
            
            self.conn.commit()
            
            self.add_stock_history(
                product_id=0,
                product_name="",
                operation_type="add_debt",
                quantity_change=0,
                old_quantity=0,
                new_quantity=0,
                profit_change=0,
                note=f"تسجيل دين للعميل {customer_name} بقيمة {amount:.2f}"
            )
            
            return True, "تم تسجيل الدين بنجاح"
        except Exception as e:
            return False, f"خطأ في تسجيل الدين: {str(e)}"
    
    def get_customer_debts(self, customer_id: int = None) -> List[Dict]:
        """الحصول على ديون عميل أو جميع الديون"""
        cursor = self.conn.cursor()
        if customer_id:
            cursor.execute("""
                SELECT d.*, s.sale_date 
                FROM debts d
                JOIN sales s ON d.sale_id = s.id
                WHERE d.customer_id = ? AND d.status != 'paid'
                ORDER BY d.created_at DESC
            """, (customer_id,))
        else:
            cursor.execute("""
                SELECT d.*, s.sale_date 
                FROM debts d
                JOIN sales s ON d.sale_id = s.id
                WHERE d.status != 'paid'
                ORDER BY d.created_at DESC
            """)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_customer_ledger(self, customer_id: int) -> List[Dict]:
        """الحصول على سجل كامل لعميل (الديون والسداد)"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT 
                'debt' as type,
                id,
                created_at as date,
                amount as amount,
                0 as paid_amount,
                remaining,
                note
            FROM debts 
            WHERE customer_id = ?
            UNION ALL
            SELECT 
                'payment' as type,
                id,
                payment_date as date,
                0 as amount,
                amount as paid_amount,
                0 as remaining,
                note
            FROM payments 
            WHERE customer_id = ?
            ORDER BY date DESC
        """, (customer_id, customer_id))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def make_payment(self, customer_id: int, customer_name: str, debt_id: int = None,
                     amount: float = None, note: str = "") -> Tuple[bool, str]:
        """تسجيل سداد (كامل أو جزئي)"""
        cursor = self.conn.cursor()
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            payment_date = datetime.now().strftime("%Y-%m-%d")
            
            if debt_id:
                cursor.execute("SELECT * FROM debts WHERE id = ?", (debt_id,))
                debt = dict(cursor.fetchone())
                
                if not debt:
                    return False, "الدين غير موجود"
                
                if amount is None or amount >= debt['remaining']:
                    paid_amount = debt['remaining']
                    new_remaining = 0
                    status = 'paid'
                else:
                    paid_amount = amount
                    new_remaining = debt['remaining'] - amount
                    status = 'partial'
                
                cursor.execute("""
                    UPDATE debts 
                    SET remaining = ?, status = ?
                    WHERE id = ?
                """, (new_remaining, status, debt_id))
                
                cursor.execute("""
                    INSERT INTO payments 
                    (customer_id, customer_name, debt_id, amount, payment_date, payment_type, note)
                    VALUES (?, ?, ?, ?, ?, 'cash', ?)
                """, (customer_id, customer_name, debt_id, paid_amount, payment_date, note))
                
                self.update_customer_debt(customer_id, paid_amount, False)
                
            else:
                cursor.execute("SELECT COALESCE(SUM(remaining), 0) as total FROM debts WHERE customer_id = ? AND status != 'paid'", (customer_id,))
                total_remaining = cursor.fetchone()['total']
                
                if amount > total_remaining:
                    return False, f"المبلغ المطلوب ({amount}) أكبر من إجمالي الدين ({total_remaining})"
                
                cursor.execute("""
                    SELECT * FROM debts 
                    WHERE customer_id = ? AND status != 'paid' 
                    ORDER BY created_at
                """, (customer_id,))
                
                debts = [dict(row) for row in cursor.fetchall()]
                remaining_to_pay = amount
                
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
                    
                    cursor.execute("""
                        UPDATE debts 
                        SET remaining = ?, status = ?
                        WHERE id = ?
                    """, (new_remaining, status, debt['id']))
                    
                    cursor.execute("""
                        INSERT INTO payments 
                        (customer_id, customer_name, debt_id, amount, payment_date, payment_type, note)
                        VALUES (?, ?, ?, ?, ?, 'cash', ?)
                    """, (customer_id, customer_name, debt['id'], paid, payment_date, note))
                
                self.update_customer_debt(customer_id, amount, False)
            
            self.conn.commit()
            
            self.add_stock_history(
                product_id=0,
                product_name="",
                operation_type="payment",
                quantity_change=0,
                old_quantity=0,
                new_quantity=0,
                profit_change=0,
                note=f"تسجيل سداد من العميل {customer_name} بقيمة {amount:.2f}"
            )
            
            return True, "تم تسجيل السداد بنجاح"
        except Exception as e:
            return False, f"خطأ في تسجيل السداد: {str(e)}"
    
    def get_customer_summary(self, customer_id: int = None) -> Dict:
        """الحصول على ملخص ديون العميل أو جميع العملاء"""
        cursor = self.conn.cursor()
        
        if customer_id:
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(d.remaining), 0) as current_unpaid_debt,
                    COALESCE(SUM(p.amount), 0) as current_total_paid
                FROM debts d
                LEFT JOIN payments p ON d.id = p.debt_id
                WHERE d.customer_id = ?
            """, (customer_id,))
        else:
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(remaining), 0) as current_unpaid_debt,
                    COALESCE(SUM(amount), 0) as current_total_paid
                FROM debts
                WHERE status != 'paid'
            """)
        
        row = cursor.fetchone()
        result = {
            "total_debt": row["current_unpaid_debt"] if row else 0,
            "total_paid": row["current_total_paid"] if row else 0
        }
        
        if customer_id:
            cursor.execute("""
                SELECT name, phone, total_debt as customer_total_debt, total_paid as customer_total_paid
                FROM customers WHERE id = ?
            """, (customer_id,))
            customer = dict(cursor.fetchone())
            result.update(customer)
        
        return result
    
    def get_debts_by_date_range(self, start_date: str, end_date: str) -> List[Dict]:
        """الحصول على الديون في نطاق زمني"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT d.*, s.sale_date 
            FROM debts d
            JOIN sales s ON d.sale_id = s.id
            WHERE d.created_at BETWEEN ? AND ?
            ORDER BY d.created_at DESC
        """, (start_date, end_date))
        return [dict(row) for row in cursor.fetchall()]
    
    # ========== دوال مساعدة ==========
    
    def _row_to_product(self, row) -> Product:
        """تحويل صف من قاعدة البيانات إلى كائن Product"""
        return Product(
            id=row["id"],
            name=row["name"],
            purchase_price=row["purchase_price"],
            selling_price=row["selling_price"],
            quantity=row["quantity"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            min_stock_threshold=row["min_stock_threshold"]
        )
    
    def _row_to_history(self, row) -> StockHistory:
        """تحويل صف من قاعدة البيانات إلى كائن StockHistory"""
        return StockHistory(
            id=row["id"],
            product_id=row["product_id"],
            product_name=row["product_name"],
            operation_type=row["operation_type"],
            quantity_change=row["quantity_change"],
            old_quantity=row["old_quantity"],
            new_quantity=row["new_quantity"],
            profit_change=row["profit_change"],
            note=row["note"],
            created_at=row["created_at"]
        )
    
    def add_stock_history(self, product_id: int, product_name: str, operation_type: str,
                          quantity_change: int, old_quantity: int, new_quantity: int,
                          profit_change: float, note: str):
        """إضافة سجل حركة"""
        cursor = self.conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute("""
            INSERT INTO stock_history 
            (product_id, product_name, operation_type, quantity_change, 
             old_quantity, new_quantity, profit_change, note, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (product_id, product_name, operation_type, quantity_change,
              old_quantity, new_quantity, profit_change, note, now))
        
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
        self.db = Database()
        
        # إعدادات الصفحة
        self.page.title = "نظام إدارة المتجر المتكامل"
        self.page.bgcolor = "#F4F7FC"
        self.page.rtl = True
        self.page.theme_mode = ft.ThemeMode.LIGHT
        # تعيين أبعاد النافذة فقط على الكمبيوتر (ليس الجوال)
        try:
            import sys
            if sys.platform not in ('android', 'ios'):
                self.page.window.width = 1100
                self.page.window.height = 800
                self.page.window.min_width = 900
                self.page.window.min_height = 600
        except Exception:
            pass
        
        # حالة التطبيق
        self.current_page = "home"
        self.selected_product = None
        self.cart = []
        
        self.theme_color = ft.Colors.BLUE # تعريف اللون أولاً
        self.setup_theme()
        self.show_welcome() # البدء بالواجهة الترحيبية
    
    def change_theme(self, color_name: str):
        """تغيير لون السمة الأساسي"""
        self.theme_color = color_name
        self.page.theme = ft.Theme(color_scheme_seed=self.theme_color)
        self.page.update()
        if self.current_page == "welcome":
            self.show_welcome()
        else:
            self.show_home()

    def show_welcome(self, e=None):
        """الواجهة الترحيبية"""
        self.current_page = "welcome"
        self.page.clean()
        self.page.bgcolor = ft.Colors.GREY_50
        
        # خيارات الألوان
        colors = [
            ("أزرق", ft.Colors.BLUE),
            ("أخضر", ft.Colors.GREEN),
            ("أحمر", ft.Colors.RED),
            ("بنفسجي", ft.Colors.PURPLE),
            ("برتقالي", ft.Colors.ORANGE),
            ("أسود", ft.Colors.BLUE_GREY_900),
        ]
        
        color_buttons = []
        for name, color in colors:
            color_buttons.append(
                ft.Container(
                    width=30,
                    height=30,
                    bgcolor=color,
                    border_radius=15,
                    tooltip=name,
                    on_click=lambda _, c=color: self.change_theme(c),
                    border=ft.border.all(2, ft.Colors.WHITE) if self.theme_color == color else None,
                    shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK))
                )
            )

        self.page.add(
            ft.Container(
                expand=True,
                content=ft.Column(
                    [
                        ft.Container(height=50),
                        ft.Icon(ft.Icons.STORE_ROUNDED, size=80, color=self.theme_color),
                        ft.Text("نظام إدارة المتجر الذكي", size=32, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900),
                        ft.Text("مرحباً بك مجدداً! ابدأ بإدارة أعمالك بكل سهولة", size=16, color=ft.Colors.GREY_600),
                        
                        ft.Container(height=30),
                        
                        ft.ElevatedButton(
                            content=ft.Container(
                                content=ft.Row(
                                    [
                                        ft.Text("الدخول إلى التطبيق", size=18, weight=ft.FontWeight.BOLD),
                                        ft.Icon(ft.Icons.ARROW_FORWARD_ROUNDED),
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                ),
                                padding=ft.padding.symmetric(horizontal=20, vertical=10),
                            ),
                            style=ft.ButtonStyle(
                                color=ft.Colors.WHITE,
                                bgcolor=self.theme_color,
                                shape=ft.RoundedRectangleBorder(radius=12),
                            ),
                            width=300,
                            height=60,
                            on_click=self.show_home,
                        ),
                        
                        ft.Container(height=40),
                        ft.Container(content=ft.Divider(color=ft.Colors.GREY_200), width=400),
                        ft.Text("اختر لون المظهر المفضل لديك", size=14, color=ft.Colors.GREY_500),
                        ft.Row(color_buttons, alignment=ft.MainAxisAlignment.CENTER, spacing=15),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )
        )
        self.page.update()
    
    def setup_theme(self):
        """إعداد الثيم"""
        self.page.theme = ft.Theme(
            color_scheme=ft.ColorScheme(
                primary=ft.Colors.BLUE_700,
                secondary=ft.Colors.ORANGE_700,
            )
        )
    
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
        dlg.open = False
        self.page.update()
    
    def _create_stat_card(self, title: str, value: str, icon, color):
        """إنشاء بطاقة إحصائية"""
        return ft.Container(
            expand=True,
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            padding=15,
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(icon, color=color, size=30),
                            ft.Container(expand=True),
                            ft.Text(value, size=24, weight=ft.FontWeight.BOLD, color=color),
                        ]
                    ),
                    ft.Text(title, size=14, color=ft.Colors.GREY_600),
                ],
                spacing=5,
            ),
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK)),
        )
    
    def _create_feature_card(self, title: str, description: str, icon, color, on_click):
        """إنشاء بطاقة ميزة"""
        return ft.Container(
            expand=True,
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            padding=20,
            on_click=on_click,
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Icon(icon, color=ft.Colors.WHITE, size=30),
                        bgcolor=color,
                        border_radius=25,
                        padding=10,
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(height=10),
                    ft.Text(title, size=16, weight=ft.FontWeight.BOLD),
                    ft.Text(description, size=12, color=ft.Colors.GREY_600, text_align=ft.TextAlign.CENTER),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=5,
            ),
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK)),
        )
    
    # ========== الصفحة الرئيسية ==========
    
    def show_home(self, e=None):
        """عرض الصفحة الرئيسية"""
        self.current_page = "home"
        self.page.clean()
        
        stats = self.db.get_overall_profit_loss()
        low_stock_count = len(self.db.get_low_stock_products())
        debt_summary = self.db.get_customer_summary()
        
        self.page.add(
            ft.AppBar(
                title=ft.Text("نظام إدارة المتجر المتكامل", size=24, weight=ft.FontWeight.BOLD),
                bgcolor=ft.Colors.BLUE_700,
                color=ft.Colors.WHITE,
                center_title=True,
            ),
            ft.Container(
                expand=True,
                padding=20,
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                self._create_stat_card("إجمالي الأرباح", f"{stats['total_profit']:.2f} ج.م", ft.Icons.TRENDING_UP, ft.Colors.GREEN),
                                self._create_stat_card("قيمة المخزون", f"{stats['total_inventory_value']:.2f} ج.م", ft.Icons.INVENTORY, ft.Colors.BLUE),
                                self._create_stat_card("إجمالي الديون", f"{debt_summary['total_debt']:.2f} ج.م", ft.Icons.MONEY_OFF, ft.Colors.RED),
                                self._create_stat_card("تنبيهات المخزون", str(low_stock_count), ft.Icons.WARNING, ft.Colors.ORANGE if low_stock_count > 0 else ft.Colors.GREY),
                            ],
                            spacing=20,
                        ),
                        ft.Container(height=20),
                        ft.Text("الوظائف الرئيسية", size=22, weight=ft.FontWeight.BOLD),
                        ft.Container(height=10),
                        ft.Row(
                            [
                                self._create_feature_card("إدارة المنتجات", "إضافة، تعديل، حذف المنتجات", ft.Icons.CATEGORY, ft.Colors.BLUE, self.show_products),
                                self._create_feature_card("نظام البيع", "تسجيل عمليات البيع", ft.Icons.SHOPPING_CART, ft.Colors.GREEN, self.show_pos),
                                self._create_feature_card("إدارة العملاء", "إدارة العملاء والديون", ft.Icons.PEOPLE, ft.Colors.PURPLE, self.show_customers),
                            ],
                            spacing=20,
                        ),
                        ft.Row(
                            [
                                self._create_feature_card("سجل الديون", "عرض وإدارة ديون العملاء", ft.Icons.ACCOUNT_BALANCE, ft.Colors.RED, self.show_debts),
                                self._create_feature_card("التقارير", "تقارير الأرباح والمبيعات", ft.Icons.BAR_CHART, ft.Colors.ORANGE, self.show_reports),
                                self._create_feature_card("سجل الحركات", "عرض جميع العمليات", ft.Icons.HISTORY, ft.Colors.TEAL, self.show_history),
                            ],
                            spacing=20,
                        ),
                        ft.Row(
                            [
                                self._create_feature_card("تتبع المنتجات", "سجل كامل لكل منتج", ft.Icons.TRACK_CHANGES, ft.Colors.CYAN, self.show_product_tracking),
                                self._create_feature_card("التقارير السنوية", "عرض الأرباح حسب السنوات", ft.Icons.CALENDAR_MONTH, ft.Colors.BROWN, self.show_yearly_reports),
                            ],
                            spacing=20,
                        ),
                    ],
                    scroll=ft.ScrollMode.AUTO,
                ),
            ),
        )
    
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
                content=ft.Column(
                    [
                        ft.Row([search_field, add_button], spacing=10),
                        ft.Container(height=20),
                        ft.Text("قائمة المنتجات", size=18, weight=ft.FontWeight.BOLD),
                        ft.Container(content=self.products_list, expand=True),
                    ],
                    expand=True,
                ),
            ),
        )
        
        self._refresh_products_list()
    
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
                    content=ft.Text("لا توجد منتجات", size=16, color=ft.Colors.GREY_500),
                    alignment=ft.alignment.center,
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
                    content=ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text(product.name, size=16, weight=ft.FontWeight.BOLD),
                                    ft.Text(f"سعر الشراء: {product.purchase_price:.2f} | سعر البيع: {product.selling_price:.2f}", size=12, color=ft.Colors.GREY_600),
                                    ft.Text(f"المخزون: {product.quantity}", size=12, color=ft.Colors.RED if is_low_stock else ft.Colors.GREEN),
                                ],
                                expand=True,
                                spacing=5,
                            ),
                            ft.Row(
                                [
                                    ft.IconButton(
                                        ft.Icons.ADD_CIRCLE,
                                        icon_color=ft.Colors.GREEN,
                                        tooltip="إضافة مخزون",
                                        on_click=lambda _, p=product: self.show_add_stock_dialog(p),
                                    ),
                                    ft.IconButton(
                                        ft.Icons.EDIT,
                                        icon_color=ft.Colors.BLUE,
                                        tooltip="تعديل",
                                        on_click=lambda _, p=product: self.show_edit_product_dialog(p),
                                    ),
                                    ft.IconButton(
                                        ft.Icons.DELETE,
                                        icon_color=ft.Colors.RED,
                                        tooltip="حذف",
                                        on_click=lambda _, p=product: self._confirm_delete_product(p),
                                    ),
                                ],
                                spacing=5,
                            ),
                        ]
                    ),
                    shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK)),
                )
            )
        
        self.page.update()
    
    def show_add_product_dialog(self, e=None):
        name_field = ft.TextField(label="اسم المنتج", autofocus=True)
        purchase_price_field = ft.TextField(label="سعر الشراء", keyboard_type=ft.KeyboardType.NUMBER)
        selling_price_field = ft.TextField(label="سعر البيع", keyboard_type=ft.KeyboardType.NUMBER)
        quantity_field = ft.TextField(label="الكمية الأولية", keyboard_type=ft.KeyboardType.NUMBER, value="0")
        threshold_field = ft.TextField(label="حد التنبيه الأدنى", keyboard_type=ft.KeyboardType.NUMBER, value="5")
        
        def save_product(e):
            try:
                product = Product(
                    name=name_field.value,
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
                [name_field, purchase_price_field, selling_price_field, quantity_field, threshold_field],
                tight=True,
                spacing=10,
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
        purchase_price_field = ft.TextField(label="سعر الشراء", value=str(product.purchase_price), keyboard_type=ft.KeyboardType.NUMBER)
        selling_price_field = ft.TextField(label="سعر البيع", value=str(product.selling_price), keyboard_type=ft.KeyboardType.NUMBER)
        quantity_field = ft.TextField(label="الكمية", value=str(product.quantity), keyboard_type=ft.KeyboardType.NUMBER)
        threshold_field = ft.TextField(label="حد التنبيه الأدنى", value=str(product.min_stock_threshold), keyboard_type=ft.KeyboardType.NUMBER)
        
        def save_edit(e):
            try:
                product.name = name_field.value
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
                [name_field, purchase_price_field, selling_price_field, quantity_field, threshold_field],
                tight=True,
                spacing=10,
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
            content=ft.Text(f"هل أنت متأكد من حذف المنتج '{product.name}'؟\nملاحظة: ستبقى سجلات المبيعات والحركات محفوظة."),
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
        self.current_page = "pos"
        self.cart = []
        self.page.clean()
        
        search_field = ft.TextField(
            hint_text="🔍 ابحث عن منتج...",
            on_change=self._search_product_for_sale,
            expand=True,
            border_radius=10,
            autofocus=True,
        )
        
        self.search_results = ft.ListView(expand=True, spacing=5) # إزالة الارتفاع الثابت وجعلها تتوسع
        self.cart_list = ft.ListView(expand=True, spacing=10)
        self.total_label = ft.Text("0.00", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN)
        
        self.page.add(
            ft.AppBar(
                title=ft.Text("نظام البيع"),
                bgcolor=ft.Colors.GREEN_700,
                color=ft.Colors.WHITE,
                leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=self.show_home, icon_color=ft.Colors.WHITE),
            ),
            ft.Container(
                expand=True,
                padding=20,
                content=ft.Row(
                    [
                        # القسم الأيمن: البحث واختيار المنتجات
                        ft.Container(
                            expand=2,
                            padding=10,
                            bgcolor=ft.Colors.WHITE,
                            border_radius=15,
                            content=ft.Column(
                                [
                                    ft.Text("إضافة منتجات للفاتورة", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700),
                                    search_field,
                                    ft.Divider(height=1, color=ft.Colors.GREY_100),
                                    ft.Text("المنتجات المتوفرة", size=14, color=ft.Colors.GREY_600),
                                    ft.Container(
                                        content=self.search_results,
                                        expand=True,
                                    ),
                                ],
                                spacing=15,
                                expand=True,
                            ),
                            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK)),
                        ),
                        
                        # فاصل
                        ft.Container(width=10),
                        
                        # القسم الأيسر: سلة المشتريات وإتمام البيع
                        ft.Container(
                            expand=1,
                            padding=15,
                            bgcolor=ft.Colors.GREY_50,
                            border_radius=15,
                            content=ft.Column(
                                [
                                    ft.Row(
                                        [
                                            ft.Icon(ft.Icons.SHOPPING_BASKET, color=ft.Colors.GREEN_700),
                                            ft.Text("سلة المشتريات", size=18, weight=ft.FontWeight.BOLD),
                                        ],
                                        spacing=10,
                                    ),
                                    ft.Divider(),
                                    ft.Container(
                                        content=self.cart_list,
                                        expand=True,
                                    ),
                                    ft.Divider(),
                                    ft.Container(
                                        padding=10,
                                        bgcolor=ft.Colors.WHITE,
                                        border_radius=10,
                                        content=ft.Row(
                                            [
                                                ft.Text("الإجمالي:", size=16, weight=ft.FontWeight.BOLD),
                                                ft.Container(expand=True),
                                                self.total_label,
                                                ft.Text("ج.م", size=14, color=ft.Colors.GREEN),
                                            ],
                                            alignment=ft.MainAxisAlignment.CENTER,
                                        ),
                                    ),
                                    ft.Column(
                                        [
                                            ft.ElevatedButton(
                                                "إتمام البيع نقداً (Cash)",
                                                icon=ft.Icons.CHECK_CIRCLE,
                                                bgcolor=ft.Colors.GREEN_700,
                                                color=ft.Colors.WHITE,
                                                expand=True,
                                                height=50,
                                                on_click=self._complete_cash_sale,
                                            ),
                                            ft.ElevatedButton(
                                                "تسجيل كدين (Debt)",
                                                icon=ft.Icons.PERSON_OUTLINE,
                                                bgcolor=ft.Colors.ORANGE_800,
                                                color=ft.Colors.WHITE,
                                                expand=True,
                                                height=50,
                                                on_click=self._complete_credit_sale,
                                            ),
                                        ],
                                        spacing=10,
                                    ),
                                ],
                                spacing=15,
                                expand=True,
                            ),
                            border=ft.border.all(1, ft.Colors.GREY_200),
                        ),
                    ],
                    expand=True,
                ),
            ),
        )
        
        self._refresh_cart_display()
        self._search_product_for_sale(None)  # عرض المنتجات المتوفرة افتراضياً
    
    def _search_product_for_sale(self, e):
        query = e.control.value.strip() if e and e.control.value else ""
        
        products = self.db.search_products(query) if query else self.db.get_all_products()
        self.search_results.controls.clear()
        
        for product in products:
            if product.quantity > 0:
                self.search_results.controls.append(
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Text(product.name, weight=ft.FontWeight.BOLD),
                                        ft.Text(f"{product.selling_price:.2f} ج.م | متوفر: {product.quantity}", size=12, color=ft.Colors.GREY_600),
                                    ],
                                    expand=True,
                                    spacing=2,
                                ),
                                ft.IconButton(
                                    ft.Icons.ADD_SHOPPING_CART,
                                    icon_color=ft.Colors.GREEN,
                                    on_click=lambda _, p=product: self._add_to_cart(p),
                                ),
                            ]
                        ),
                        padding=10,
                        bgcolor=ft.Colors.WHITE,
                        border_radius=8,
                        shadow=ft.BoxShadow(blur_radius=2, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK)),
                    )
                )
        
        self.search_results.visible = True
        self.page.update()
    
    def _add_to_cart(self, product: Product):
        for item in self.cart:
            if item["product_id"] == product.id:
                if item["quantity"] + 1 > product.quantity:
                    self.show_message(f"الكمية المتوفرة فقط: {product.quantity}", ft.Colors.RED)
                    return
                item["quantity"] += 1
                self._refresh_cart_display()
                self.show_message(f"تم إضافة {product.name} إلى السلة", ft.Colors.GREEN)
                return
        
        if product.quantity > 0:
            self.cart.append({
                "product_id": product.id,
                "product": product,
                "quantity": 1,
            })
            self._refresh_cart_display()
            self.show_message(f"تم إضافة {product.name} إلى السلة", ft.Colors.GREEN)
        else:
            self.show_message(f"المنتج {product.name} غير متوفر في المخزون", ft.Colors.RED)
    
    def _update_cart_quantity(self, index: int, delta: int):
        item = self.cart[index]
        new_qty = item["quantity"] + delta
        
        if new_qty <= 0:
            self.cart.pop(index)
        elif new_qty <= item["product"].quantity:
            item["quantity"] = new_qty
        else:
            self.show_message(f"الكمية المتوفرة فقط: {item['product'].quantity}", ft.Colors.RED)
            return
        
        self._refresh_cart_display()
    
    def _remove_from_cart(self, index: int):
        self.cart.pop(index)
        self._refresh_cart_display()
    
    def _refresh_cart_display(self):
        self.cart_list.controls.clear()
        total = 0
        
        for i, item in enumerate(self.cart):
            product = item["product"]
            quantity = item["quantity"]
            subtotal = product.selling_price * quantity
            total += subtotal
            
            self.cart_list.controls.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text(product.name, weight=ft.FontWeight.BOLD),
                                    ft.Text(f"{product.selling_price:.2f} × {quantity} = {subtotal:.2f}", size=12, color=ft.Colors.GREY_600),
                                ],
                                expand=True,
                                spacing=2,
                            ),
                            ft.Row(
                                [
                                    ft.IconButton(
                                        ft.Icons.REMOVE,
                                        icon_size=20,
                                        on_click=lambda _, idx=i: self._update_cart_quantity(idx, -1),
                                    ),
                                    ft.Text(str(quantity), size=16, weight=ft.FontWeight.BOLD),
                                    ft.IconButton(
                                        ft.Icons.ADD,
                                        icon_size=20,
                                        on_click=lambda _, idx=i: self._update_cart_quantity(idx, 1),
                                    ),
                                    ft.IconButton(
                                        ft.Icons.DELETE,
                                        icon_color=ft.Colors.RED,
                                        icon_size=20,
                                        on_click=lambda _, idx=i: self._remove_from_cart(idx),
                                    ),
                                ],
                                spacing=5,
                            ),
                        ]
                    ),
                    padding=10,
                    bgcolor=ft.Colors.WHITE,
                    border_radius=8,
                )
            )
        
        self.total_label.value = f"{total:.2f}"
        
        if not self.cart:
            self.cart_list.controls.append(
                ft.Container(
                    content=ft.Text("السلة فارغة", size=16, color=ft.Colors.GREY_500),
                    alignment=ft.alignment.center,
                    padding=50,
                )
            )
        
        self.page.update()
    
    def _complete_cash_sale(self, e):
        self._complete_sale(customer="")
    
    def _complete_credit_sale(self, e):
        customer_field = ft.TextField(label="اسم العميل", autofocus=True)
        
        def confirm(e):
            if customer_field.value.strip():
                dlg.open = False
                self._complete_sale(customer=customer_field.value.strip())
            else:
                self.show_message("يرجى إدخال اسم العميل", ft.Colors.RED)
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("بيع آجل - تسجيل دين"),
            content=ft.Column([ft.Text("أدخل اسم العميل:"), customer_field], tight=True, spacing=10),
            actions=[
                ft.TextButton("إلغاء", on_click=lambda _: self.close_dialog(dlg)),
                ft.ElevatedButton("تأكيد", on_click=confirm, bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE),
            ],
        )
        
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()
    
    def _complete_sale(self, customer: str = ""):
        if not self.cart:
            self.show_message("السلة فارغة!", ft.Colors.RED)
            return
        
        total_profit = 0
        sale_ids = []
        all_success = True
        
        for item in self.cart:
            success, message, profit, sale_id = self.db.sell_product(
                item["product_id"],
                item["quantity"],
                customer
            )
            if success:
                total_profit += profit
                sale_ids.append(sale_id)
            else:
                all_success = False
                self.show_message(f"خطأ في بيع {item['product'].name}: {message}", ft.Colors.RED)
                break
        
        if all_success:
            total = sum(item["product"].selling_price * item["quantity"] for item in self.cart)
            
            if customer and customer.strip():
                customer_data = self.db.get_customer_by_name(customer)
                if not customer_data:
                    success, _, customer_id = self.db.add_customer(customer)
                    if success:
                        customer_data = {'id': customer_id, 'name': customer}
                
                if customer_data:
                    for sale_id in sale_ids:
                        self.db.add_debt(
                            customer_data['id'],
                            customer,
                            sale_id,
                            total,
                            f"فاتورة رقم {sale_id}"
                        )
            
            self.show_message(
                f"تم البيع بنجاح!\nالإجمالي: {total:.2f} ج.م\nالربح: {total_profit:.2f} ج.م",
                ft.Colors.GREEN
            )
            self.cart = []
            self._refresh_cart_display()
            self.show_home() # الانتقال للصفحة الرئيسية مباشرة لتجنب خطأ الإصدار
        else:
            self.show_message("حدث خطأ في عملية البيع", ft.Colors.RED)
    
    # ========== إدارة العملاء ==========
    
    def show_customers(self, e=None):
        self.current_page = "customers"
        self.page.clean()
        
        search_field = ft.TextField(
            hint_text="🔍 بحث عن عميل...",
            on_change=self._search_customers,
            expand=True,
            border_radius=10,
        )
        
        add_button = ft.ElevatedButton(
            "إضافة عميل جديد",
            icon=ft.Icons.PERSON_ADD,
            bgcolor=ft.Colors.GREEN,
            color=ft.Colors.WHITE,
            on_click=self.show_add_customer_dialog,
        )
        
        self.customers_list = ft.ListView(expand=True, spacing=10, padding=10)
        
        self.page.add(
            ft.AppBar(
                title=ft.Text("إدارة العملاء"),
                bgcolor=ft.Colors.PURPLE_700,
                color=ft.Colors.WHITE,
                leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=self.show_home, icon_color=ft.Colors.WHITE),
            ),
            ft.Container(
                padding=20,
                content=ft.Column(
                    [
                        ft.Row([search_field, add_button], spacing=10),
                        ft.Container(height=20),
                        ft.Text("قائمة العملاء", size=18, weight=ft.FontWeight.BOLD),
                        ft.Container(content=self.customers_list, expand=True),
                    ],
                    expand=True,
                ),
            ),
        )
        
        self._refresh_customers_list()
    
    def _search_customers(self, e):
        query = e.control.value
        customers = self.db.search_customers(query) if query else self.db.get_all_customers()
        self._render_customers_list(customers)
    
    def _refresh_customers_list(self):
        customers = self.db.get_all_customers()
        self._render_customers_list(customers)
    
    def _render_customers_list(self, customers: List[Dict]):
        self.customers_list.controls.clear()
        
        if not customers:
            self.customers_list.controls.append(
                ft.Container(
                    content=ft.Text("لا يوجد عملاء", size=16, color=ft.Colors.GREY_500),
                    alignment=ft.alignment.center,
                    padding=50,
                )
            )
            self.page.update()
            return
        
        for customer in customers:
            remaining = customer['total_debt'] - customer['total_paid']
            
            self.customers_list.controls.append(
                ft.Container(
                    bgcolor=ft.Colors.WHITE,
                    border_radius=10,
                    padding=15,
                    content=ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text(customer['name'], size=16, weight=ft.FontWeight.BOLD),
                                    ft.Text(f"الهاتف: {customer['phone'] or 'غير مسجل'}", size=12, color=ft.Colors.GREY_600),
                                    ft.Text(f"تاريخ التسجيل: {customer['created_at'][:10]}", size=11, color=ft.Colors.GREY_500),
                                ],
                                expand=True,
                                spacing=5,
                            ),
                            ft.Column(
                                [
                                    ft.Text(f"المتبقي: {remaining:.2f}", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.RED if remaining > 0 else ft.Colors.GREEN),
                                    ft.Text(f"إجمالي الدين: {customer['total_debt']:.2f}", size=11, color=ft.Colors.ORANGE),
                                    ft.Text(f"مسدد: {customer['total_paid']:.2f}", size=11, color=ft.Colors.GREEN),
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.END,
                                spacing=3,
                            ),
                            ft.Row(
                                [
                                    ft.IconButton(
                                        ft.Icons.ACCOUNT_BALANCE,
                                        icon_color=ft.Colors.BLUE,
                                        tooltip="سجل الديون",
                                        on_click=lambda _, c=customer: self.show_customer_ledger(c['id'], c['name']),
                                    ),
                                    ft.IconButton(
                                        ft.Icons.PAYMENT,
                                        icon_color=ft.Colors.GREEN,
                                        tooltip="تسجيل سداد",
                                        on_click=lambda _, c=customer: self.show_payment_dialog(c['id'], c['name']),
                                    ),
                                ],
                                spacing=5,
                            ),
                        ]
                    ),
                    shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK)),
                )
            )
        
        self.page.update()
    
    def show_add_customer_dialog(self, e=None):
        name_field = ft.TextField(label="اسم العميل", autofocus=True)
        phone_field = ft.TextField(label="رقم الهاتف (اختياري)", keyboard_type=ft.KeyboardType.PHONE)
        
        def save_customer(e):
            if not name_field.value.strip():
                self.show_message("يرجى إدخال اسم العميل", ft.Colors.RED)
                return
            
            success, message, _ = self.db.add_customer(name_field.value.strip(), phone_field.value)
            if success:
                self.show_message(message)
                dlg.open = False
                self._refresh_customers_list()
            else:
                self.show_message(message, ft.Colors.RED)
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("إضافة عميل جديد"),
            content=ft.Column(
                [name_field, phone_field],
                tight=True,
                spacing=10,
            ),
            actions=[
                ft.TextButton("إلغاء", on_click=lambda _: self.close_dialog(dlg)),
                ft.ElevatedButton("حفظ", on_click=save_customer, bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE),
            ],
        )
        
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()
    
    # ========== إدارة الديون ==========
    
    def show_debts(self, e=None):
        self.current_page = "debts"
        self.page.clean()
        
        debt_summary = self.db.get_customer_summary()
        debts_list = ft.ListView(expand=True, spacing=10)
        
        start_date = ft.TextField(
            label="من تاريخ",
            hint_text="YYYY-MM-DD",
            value=datetime.now().strftime("%Y-%m-%d"),
            width=150,
        )
        end_date = ft.TextField(
            label="إلى تاريخ",
            hint_text="YYYY-MM-DD",
            value=datetime.now().strftime("%Y-%m-%d"),
            width=150,
        )
        
        def filter_debts(e):
            start = start_date.value
            end = end_date.value
            
            if start and end:
                debts = self.db.get_debts_by_date_range(start, end)
            else:
                debts = self.db.get_customer_debts()
            
            _render_debts_list(debts)
        
        def _render_debts_list(debts):
            debts_list.controls.clear()
            
            if not debts:
                debts_list.controls.append(
                    ft.Container(
                        content=ft.Text("لا توجد ديون مسجلة", size=16, color=ft.Colors.GREY_500),
                        alignment=ft.alignment.center,
                        padding=50,
                    )
                )
                self.page.update()
                return
            
            for debt in debts:
                status_colors = {
                    'pending': ft.Colors.RED,
                    'partial': ft.Colors.ORANGE,
                    'paid': ft.Colors.GREEN
                }
                status_texts = {
                    'pending': 'غير مسدد',
                    'partial': 'مسدد جزئياً',
                    'paid': 'مسدد كامل'
                }
                
                debts_list.controls.append(
                    ft.Container(
                        bgcolor=ft.Colors.WHITE,
                        border_radius=10,
                        padding=15,
                        content=ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Text(debt['customer_name'], size=16, weight=ft.FontWeight.BOLD),
                                        ft.Container(expand=True),
                                        ft.Text(status_texts.get(debt['status'], debt['status']), 
                                                size=12, color=status_colors.get(debt['status'], ft.Colors.GREY)),
                                    ]
                                ),
                                ft.Row(
                                    [
                                        ft.Text(f"المبلغ: {debt['amount']:.2f} ج.م", size=14),
                                        ft.Text(f"المتبقي: {debt['remaining']:.2f} ج.م", size=14, 
                                               color=ft.Colors.RED if debt['remaining'] > 0 else ft.Colors.GREEN),
                                        ft.Container(expand=True),
                                        ft.Text(debt['sale_date'], size=12, color=ft.Colors.GREY_600),
                                    ]
                                ),
                                ft.Row(
                                    [
                                        ft.IconButton(
                                            ft.Icons.PAYMENT,
                                            icon_color=ft.Colors.GREEN,
                                            text="تسديد",
                                            on_click=lambda _, d=debt: self.show_payment_dialog(d['customer_id'], d['customer_name'], d['id']),
                                        ),
                                        ft.IconButton(
                                            ft.Icons.INFO,
                                            icon_color=ft.Colors.BLUE,
                                            text="تفاصيل",
                                            on_click=lambda _, d=debt: self.show_debt_details(d),
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.END,
                                ),
                            ],
                            spacing=8,
                        ),
                        shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK)),
                    )
                )
            
            self.page.update()
        
        self.page.add(
            ft.AppBar(
                title=ft.Text("سجل الديون"),
                bgcolor=ft.Colors.RED_700,
                color=ft.Colors.WHITE,
                leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=self.show_home, icon_color=ft.Colors.WHITE),
            ),
            ft.Container(
                expand=True,
                padding=20,
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                self._create_stat_card("إجمالي الديون", f"{debt_summary['total_debt']:.2f}", ft.Icons.MONEY_OFF, ft.Colors.RED),
                                self._create_stat_card("إجمالي المسدد", f"{debt_summary['total_paid']:.2f}", ft.Icons.PAYMENT, ft.Colors.GREEN),
                            ],
                            spacing=20,
                        ),
                        ft.Container(height=20),
                        ft.Row(
                            [
                                start_date,
                                end_date,
                                ft.ElevatedButton("فلترة", on_click=filter_debts, bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE),
                                ft.ElevatedButton("الكل", on_click=lambda _: filter_debts(None), bgcolor=ft.Colors.GREY, color=ft.Colors.WHITE),
                            ],
                            spacing=10,
                        ),
                        ft.Divider(),
                        ft.Text("قائمة الديون", size=18, weight=ft.FontWeight.BOLD),
                        ft.Container(content=debts_list, expand=True),
                    ],
                    expand=True,
                ),
            ),
        )
        
        filter_debts(None)
    
    def show_customer_ledger(self, customer_id: int, customer_name: str):
        self.page.clean()
        
        ledger = self.db.get_customer_ledger(customer_id)
        summary = self.db.get_customer_summary(customer_id)
        
        ledger_list = ft.ListView(expand=True, spacing=10)
        
        for record in ledger:
            if record['type'] == 'debt':
                ledger_list.controls.append(
                    ft.Container(
                        bgcolor=ft.Colors.RED_50,
                        border_radius=8,
                        padding=12,
                        content=ft.Row(
                            [
                                ft.Container(
                                    content=ft.Icon(ft.Icons.ADD_CIRCLE, color=ft.Colors.RED, size=24),
                                ),
                                ft.Column(
                                    [
                                        ft.Text("دين جديد", weight=ft.FontWeight.BOLD, color=ft.Colors.RED),
                                        ft.Text(f"المبلغ: {record['amount']:.2f} ج.م", size=13),
                                        ft.Text(f"المتبقي: {record['remaining']:.2f} ج.م", size=12, color=ft.Colors.ORANGE),
                                        ft.Text(record['note'] or "", size=11, color=ft.Colors.GREY_600),
                                    ],
                                    expand=True,
                                    spacing=2,
                                ),
                                ft.Text(record['date'][:10], size=12, color=ft.Colors.GREY_600),
                            ]
                        ),
                    )
                )
            else:
                ledger_list.controls.append(
                    ft.Container(
                        bgcolor=ft.Colors.GREEN_50,
                        border_radius=8,
                        padding=12,
                        content=ft.Row(
                            [
                                ft.Container(
                                    content=ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN, size=24),
                                ),
                                ft.Column(
                                    [
                                        ft.Text("سداد", weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN),
                                        ft.Text(f"المبلغ المدفوع: {record['paid_amount']:.2f} ج.م", size=13),
                                        ft.Text(record['note'] or "", size=11, color=ft.Colors.GREY_600),
                                    ],
                                    expand=True,
                                    spacing=2,
                                ),
                                ft.Text(record['date'][:10], size=12, color=ft.Colors.GREY_600),
                            ]
                        ),
                    )
                )
        
        self.page.add(
            ft.AppBar(
                title=ft.Text(f"سجل العميل: {customer_name}"),
                bgcolor=ft.Colors.PURPLE_700,
                color=ft.Colors.WHITE,
                leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=self.show_customers, icon_color=ft.Colors.WHITE),
            ),
            ft.Container(
                expand=True,
                padding=20,
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                self._create_stat_card("إجمالي الدين", f"{summary.get('total_debt', 0):.2f}", ft.Icons.MONEY_OFF, ft.Colors.RED),
                                self._create_stat_card("المسدد", f"{summary.get('total_paid', 0):.2f}", ft.Icons.PAYMENT, ft.Colors.GREEN),
                                self._create_stat_card("المتبقي", f"{summary.get('customer_total_debt', 0) - summary.get('customer_total_paid', 0):.2f}", ft.Icons.ACCOUNT_BALANCE, ft.Colors.ORANGE),
                            ],
                            spacing=20,
                        ),
                        ft.Divider(),
                        ft.Text("سجل العمليات", size=18, weight=ft.FontWeight.BOLD),
                        ft.Container(content=ledger_list, expand=True),
                    ],
                    expand=True,
                ),
            ),
        )
    
    def show_payment_dialog(self, customer_id: int, customer_name: str, debt_id: int = None):
        amount_field = ft.TextField(
            label="المبلغ",
            keyboard_type=ft.KeyboardType.NUMBER,
            autofocus=True,
        )
        
        note_field = ft.TextField(
            label="ملاحظة (اختياري)",
            multiline=True,
            min_lines=2,
            max_lines=3,
        )
        
        if debt_id:
            full_amount_field = ft.Checkbox(label="سداد كامل", value=True)
            
            def toggle_full_amount(e):
                amount_field.read_only = full_amount_field.value
                if full_amount_field.value:
                    amount_field.value = ""
                self.page.update()
            
            full_amount_field.on_change = toggle_full_amount
            
            def process_payment(e):
                if full_amount_field.value:
                    amount = None
                else:
                    try:
                        amount = float(amount_field.value)
                        if amount <= 0:
                            self.show_message("المبلغ يجب أن يكون أكبر من 0", ft.Colors.RED)
                            return
                    except ValueError:
                        self.show_message("يرجى إدخال مبلغ صحيح", ft.Colors.RED)
                        return
                
                success, message = self.db.make_payment(customer_id, customer_name, debt_id, amount, note_field.value)
                if success:
                    self.show_message(message)
                    dlg.open = False
                    self.page.update() # تحديث فوري لإغلاق النافذة
                    if self.current_page == "debts":
                        self.show_debts()
                    else:
                        self.show_customers()
                else:
                    self.show_message(message, ft.Colors.RED)
            
            content = ft.Column([full_amount_field, amount_field, note_field], tight=True, spacing=10)
        
        else:
            def process_payment(e):
                try:
                    amount = float(amount_field.value)
                    if amount <= 0:
                        self.show_message("المبلغ يجب أن يكون أكبر من 0", ft.Colors.RED)
                        return
                except ValueError:
                    self.show_message("يرجى إدخال مبلغ صحيح", ft.Colors.RED)
                    return
                
                success, message = self.db.make_payment(customer_id, customer_name, None, amount, note_field.value)
                if success:
                    self.show_message(message)
                    dlg.open = False
                    self.page.update() # تحديث فوري لإغلاق النافذة
                    if self.current_page == "debts":
                        self.show_debts()
                    else:
                        self.show_customers()
                else:
                    self.show_message(message, ft.Colors.RED)
            
            content = ft.Column([amount_field, note_field], tight=True, spacing=10)
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"تسجيل سداد - {customer_name}"),
            content=content,
            actions=[
                ft.TextButton("إلغاء", on_click=lambda _: self.close_dialog(dlg)),
                ft.ElevatedButton("تسجيل السداد", on_click=process_payment, bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE),
            ],
        )
        
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()
    
    def show_debt_details(self, debt: Dict):
        sales = self.db.get_sales_by_date()
        sale = next((s for s in sales if s['id'] == debt['sale_id']), None)
        
        if not sale:
            self.show_message("لا توجد تفاصيل للدين", ft.Colors.RED)
            return
        
        details = ft.Column(
            [
                ft.Text(f"رقم الفاتورة: {sale['id']}", weight=ft.FontWeight.BOLD),
                ft.Text(f"التاريخ: {sale['sale_date']}"),
                ft.Text(f"المنتج: {sale['product_name']}"),
                ft.Text(f"الكمية: {sale['quantity']}"),
                ft.Text(f"سعر البيع: {sale['selling_price']:.2f} ج.م"),
                ft.Text(f"إجمالي الدين: {debt['amount']:.2f} ج.م"),
                ft.Text(f"المتبقي: {debt['remaining']:.2f} ج.م"),
                ft.Text(f"الحالة: {debt['status']}"),
                ft.Text(f"ملاحظة: {debt['note'] or 'لا توجد ملاحظات'}"),
            ],
            spacing=8,
        )
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"تفاصيل الدين - {debt['customer_name']}"),
            content=details,
            actions=[
                ft.TextButton("إغلاق", on_click=lambda _: self.close_dialog(dlg)),
            ],
        )
        
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()
    
    # ========== التقارير ==========
    
    def show_reports(self, e=None):
        self.current_page = "reports"
        self.page.clean()
        
        start_date = ft.TextField(
            label="تاريخ البداية",
            hint_text="YYYY-MM-DD",
            value=datetime.now().strftime("%Y-%m-%d"),
            width=150,
        )
        end_date = ft.TextField(
            label="تاريخ النهاية",
            hint_text="YYYY-MM-DD",
            value=datetime.now().strftime("%Y-%m-%d"),
            width=150,
        )
        
        sales_list = ft.ListView(expand=True, spacing=10)
        
        total_sales_label = ft.Text("0", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE)
        total_items_label = ft.Text("0", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN)
        total_profit_label = ft.Text("0", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE)
        
        def filter_sales(e):
            start = start_date.value
            end = end_date.value
            
            if start and end:
                sales = self.db.get_sales_between_dates(start, end)
            else:
                sales = self.db.get_sales_by_date()
            
            total_sales = len(sales)
            total_items = sum(s["quantity"] for s in sales)
            total_profit = sum(s["profit"] for s in sales)
            
            total_sales_label.value = str(total_sales)
            total_items_label.value = str(total_items)
            total_profit_label.value = f"{total_profit:.2f}"
            
            sales_list.controls.clear()
            for sale in sales:
                sales_list.controls.append(
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Text(sale["product_name"], weight=ft.FontWeight.BOLD),
                                        ft.Text(f"الكمية: {sale['quantity']} | السعر: {sale['selling_price']:.2f}", size=12),
                                        ft.Text(f"الربح: {sale['profit']:.2f} ج.م", size=12, color=ft.Colors.GREEN),
                                    ],
                                    expand=True,
                                    spacing=2,
                                ),
                                ft.Text(sale["sale_date"], size=12, color=ft.Colors.GREY_600),
                            ]
                        ),
                        padding=10,
                        bgcolor=ft.Colors.WHITE,
                        border_radius=8,
                    )
                )
            
            self.page.update()
        
        self.page.add(
            ft.AppBar(
                title=ft.Text("التقارير"),
                bgcolor=ft.Colors.ORANGE_700,
                color=ft.Colors.WHITE,
                leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=self.show_home, icon_color=ft.Colors.WHITE),
            ),
            ft.Container(
                expand=True,
                padding=20,
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Text("الفترة:", size=16, weight=ft.FontWeight.BOLD),
                                start_date,
                                ft.Text("إلى"),
                                end_date,
                                ft.ElevatedButton("عرض", on_click=filter_sales, bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE),
                            ],
                            spacing=10,
                        ),
                        ft.Container(height=20),
                        ft.Row(
                            [
                                self._create_stat_card("عدد العمليات", total_sales_label.value, ft.Icons.RECEIPT, ft.Colors.BLUE),
                                self._create_stat_card("إجمالي القطع المباعة", total_items_label.value, ft.Icons.INVENTORY, ft.Colors.GREEN),
                                self._create_stat_card("صافي الربح", f"{total_profit_label.value} ج.م", ft.Icons.TRENDING_UP, ft.Colors.ORANGE),
                            ],
                            spacing=20,
                        ),
                        ft.Container(height=20),
                        ft.Text("قائمة المبيعات", size=18, weight=ft.FontWeight.BOLD),
                        ft.Container(content=sales_list, expand=True),
                    ],
                    expand=True,
                ),
            ),
        )
        
        filter_sales(None)
    
    # ========== سجل الحركات ==========
    
    def show_history(self, e=None):
        self.current_page = "history"
        self.page.clean()
        
        history_list = ft.ListView(expand=True, spacing=10)
        history = self.db.get_stock_history(limit=500)
        
        operation_names = {
            "create_product": "إضافة منتج جديد",
            "add_stock": "إضافة مخزون",
            "sell": "بيع",
            "edit_product": "تعديل منتج",
            "delete_product": "حذف منتج",
            "add_customer": "إضافة عميل",
            "add_debt": "تسجيل دين",
            "payment": "سداد دين",
        }
        
        for record in history:
            operation_name = operation_names.get(record.operation_type, record.operation_type)
            profit_text = f"الربح: {record.profit_change:.2f}" if record.profit_change != 0 else ""
            
            history_list.controls.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Container(
                                content=ft.Icon(
                                    ft.Icons.ADD_CIRCLE if record.quantity_change > 0 else ft.Icons.REMOVE_CIRCLE,
                                    color=ft.Colors.GREEN if record.quantity_change > 0 else ft.Colors.RED,
                                    size=30,
                                ),
                            ),
                            ft.Column(
                                [
                                    ft.Text(operation_name, weight=ft.FontWeight.BOLD),
                                    ft.Text(f"المنتج: {record.product_name}", size=12) if record.product_name else ft.Container(),
                                    ft.Text(f"التغير: {record.quantity_change:+d} | {record.old_quantity} → {record.new_quantity}", size=12) if record.quantity_change != 0 else ft.Container(),
                                    ft.Text(profit_text, size=12, color=ft.Colors.GREEN) if profit_text else ft.Container(),
                                    ft.Text(record.note or "", size=11, color=ft.Colors.GREY_600) if record.note else ft.Container(),
                                ],
                                expand=True,
                                spacing=2,
                            ),
                            ft.Text(record.created_at, size=12, color=ft.Colors.GREY_600),
                        ]
                    ),
                    padding=10,
                    bgcolor=ft.Colors.WHITE,
                    border_radius=8,
                )
            )
        
        if not history:
            history_list.controls.append(
                ft.Container(
                    content=ft.Text("لا توجد حركات مسجلة", size=16, color=ft.Colors.GREY_500),
                    alignment=ft.alignment.center,
                    padding=50,
                )
            )
        
        self.page.add(
            ft.AppBar(
                title=ft.Text("سجل الحركات"),
                bgcolor=ft.Colors.PURPLE_700,
                color=ft.Colors.WHITE,
                leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=self.show_home, icon_color=ft.Colors.WHITE),
            ),
            ft.Container(
                expand=True,
                padding=20,
                content=ft.Column(
                    [
                        ft.Text("جميع عمليات النظام", size=18, weight=ft.FontWeight.BOLD),
                        ft.Divider(),
                        ft.Container(content=history_list, expand=True),
                    ],
                    expand=True,
                ),
            ),
        )
    
    # ========== تتبع المنتجات ==========
    
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
        
        def show_product_stats(e):
            if not products_dropdown.value:
                return
            
            product_id = int(products_dropdown.value)
            data = self.db.get_detailed_product_history(product_id)
            
            if not data:
                return
            
            product = data["product"]
            sales = data["sales"]
            statistics = data["statistics"]
            
            product_details.controls.clear()
            product_details.visible = True
            
            product_details.controls.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(product.name, size=20, weight=ft.FontWeight.BOLD),
                            ft.Text(f"سعر الشراء: {product.purchase_price:.2f} | سعر البيع: {product.selling_price:.2f}", size=14),
                            ft.Text(f"الكمية الحالية: {product.quantity} | الحد الأدنى: {product.min_stock_threshold}", size=14),
                            ft.Text(f"آخر تحديث: {product.updated_at}", size=12, color=ft.Colors.GREY_600),
                        ],
                        spacing=5,
                    ),
                    padding=15,
                    bgcolor=ft.Colors.BLUE_50,
                    border_radius=10,
                )
            )
            
            product_details.controls.append(
                ft.Container(
                    content=ft.Row(
                        [
                            self._create_stat_card("إجمالي المبيعات", f"{statistics['total_sold']}", ft.Icons.SHOPPING_CART, ft.Colors.BLUE),
                            self._create_stat_card("إجمالي الربح", f"{statistics['total_profit']:.2f}", ft.Icons.TRENDING_UP, ft.Colors.GREEN),
                            self._create_stat_card("الكمية المتبقية", f"{product.quantity}", ft.Icons.INVENTORY, ft.Colors.ORANGE),
                        ],
                        spacing=20,
                    ),
                    margin=ft.margin.only(top=15, bottom=15),
                )
            )
            
            product_details.controls.append(ft.Text("سجل المبيعات", size=16, weight=ft.FontWeight.BOLD))
            for sale in sales[:20]:
                product_details.controls.append(
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Text(f"{sale['quantity']} قطعة", size=14, weight=ft.FontWeight.BOLD),
                                ft.Text(f"{sale['selling_price']:.2f} ج.م للقطعة", size=12),
                                ft.Container(expand=True),
                                ft.Text(f"الربح: {sale['profit']:.2f}", size=12, color=ft.Colors.GREEN),
                                ft.Text(sale['sale_date'][:10], size=12, color=ft.Colors.GREY_600),
                            ]
                        ),
                        padding=10,
                        bgcolor=ft.Colors.WHITE,
                        border_radius=8,
                        margin=ft.margin.only(bottom=5),
                    )
                )
            
            product_details.controls.append(
                ft.Container(
                    content=ft.Text("سجل إضافة المخزون", size=16, weight=ft.FontWeight.BOLD),
                    margin=ft.margin.only(top=15)
                )
            )
            for record in statistics['stock_history'][:20]:
                product_details.controls.append(
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Text(f"+{record['quantity_change']} قطعة", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN),
                                ft.Text(record['note'], size=12, color=ft.Colors.GREY_600),
                                ft.Container(expand=True),
                                ft.Text(record['created_at'][:16], size=12, color=ft.Colors.GREY_600),
                            ]
                        ),
                        padding=10,
                        bgcolor=ft.Colors.WHITE,
                        border_radius=8,
                        margin=ft.margin.only(bottom=5),
                    )
                )
            
            self.page.update()
        
        self.page.add(
            ft.AppBar(
                title=ft.Text("تتبع المنتجات"),
                bgcolor=ft.Colors.TEAL_700,
                color=ft.Colors.WHITE,
                leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=self.show_home, icon_color=ft.Colors.WHITE),
            ),
            ft.Container(
                expand=True,
                padding=20,
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Text("اختر منتجاً:", size=16, weight=ft.FontWeight.BOLD),
                                products_dropdown,
                                ft.ElevatedButton("عرض", on_click=show_product_stats, bgcolor=ft.Colors.TEAL, color=ft.Colors.WHITE),
                            ],
                            spacing=10,
                        ),
                        ft.Divider(),
                        ft.Container(
                content=ft.Column([product_details], scroll=ft.ScrollMode.AUTO),
                expand=True,
            ),
                    ],
                    expand=True,
                ),
            ),
        )
    
    # ========== التقارير السنوية ==========
    
    def show_yearly_reports(self, e=None):
        self.current_page = "yearly"
        self.page.clean()
        
        current_year = datetime.now().year
        year_dropdown = ft.Dropdown(
            label="اختر السنة",
            options=[ft.dropdown.Option(str(y), str(y)) for y in range(current_year, current_year - 5, -1)],
            value=str(current_year),
            width=150,
        )
        
        report_content = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO)
        
        def show_report(e):
            year = int(year_dropdown.value)
            report = self.db.get_yearly_report(year)
            
            report_content.controls.clear()
            
            summary = report["summary"]
            report_content.controls.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(f"تقرير عام {year}", size=20, weight=ft.FontWeight.BOLD),
                            ft.Row(
                                [
                                    self._create_stat_card("إجمالي الأرباح", f"{summary['year_profit']:.2f}", ft.Icons.TRENDING_UP, ft.Colors.GREEN),
                                    self._create_stat_card("عدد العمليات", str(summary['year_sales']), ft.Icons.RECEIPT, ft.Colors.BLUE),
                                    self._create_stat_card("القطع المباعة", str(summary['year_items_sold']), ft.Icons.INVENTORY, ft.Colors.ORANGE),
                                ],
                                spacing=20,
                            ),
                        ],
                        spacing=10,
                    ),
                    padding=15,
                    bgcolor=ft.Colors.BLUE_50,
                    border_radius=10,
                    margin=ft.margin.only(bottom=20),
                )
            )
            
            report_content.controls.append(ft.Text("التقرير الشهري", size=18, weight=ft.FontWeight.BOLD))
            
            month_names = {
                "01": "يناير", "02": "فبراير", "03": "مارس", "04": "أبريل",
                "05": "مايو", "06": "يونيو", "07": "يوليو", "08": "أغسطس",
                "09": "سبتمبر", "10": "أكتوبر", "11": "نوفمبر", "12": "ديسمبر"
            }
            
            for month_data in report["monthly_data"]:
                month = month_data["month"]
                month_name = month_names.get(month, month)
                report_content.controls.append(
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Text(month_name, size=14, weight=ft.FontWeight.BOLD, width=100),
                                ft.Text(f"العمليات: {month_data['total_sales']}", size=12, expand=True),
                                ft.Text(f"القطع: {month_data['total_items_sold']}", size=12, expand=True),
                                ft.Text(f"الربح: {month_data['total_profit']:.2f}", size=12, color=ft.Colors.GREEN),
                            ]
                        ),
                        padding=10,
                        bgcolor=ft.Colors.WHITE,
                        border_radius=8,
                        margin=ft.margin.only(bottom=5),
                    )
                )
            
            self.page.update()
        
        self.page.add(
            ft.AppBar(
                title=ft.Text("التقارير السنوية"),
                bgcolor=ft.Colors.RED_700,
                color=ft.Colors.WHITE,
                leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=self.show_home, icon_color=ft.Colors.WHITE),
            ),
            ft.Container(
                expand=True,
                padding=20,
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                year_dropdown,
                                ft.ElevatedButton("عرض التقرير", on_click=show_report, bgcolor=ft.Colors.RED, color=ft.Colors.WHITE),
                            ],
                            spacing=10,
                        ),
                        ft.Divider(),
                        ft.Container(content=report_content, expand=True),
                    ],
                    expand=True,
                ),
            ),
        )
        
        show_report(None)

# =============================================================================
# تشغيل التطبيق
# =============================================================================

def main(page: ft.Page):
    try:
        app = StoreManagementApp(page)
    except Exception as e:
        # عرض رسالة خطأ واضحة بدل الشاشة البيضاء
        import traceback
        error_msg = traceback.format_exc()
        page.clean()
        page.add(
            ft.Container(
                expand=True,
                padding=30,
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.ERROR_OUTLINE, size=60, color=ft.Colors.RED),
                        ft.Text("حدث خطأ أثناء تشغيل التطبيق", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.RED),
                        ft.Text(str(e), size=14, color=ft.Colors.GREY_700),
                        ft.Container(
                            padding=10,
                            bgcolor=ft.Colors.GREY_100,
                            border_radius=8,
                            content=ft.Text(error_msg, size=10, selectable=True),
                        ),
                        ft.ElevatedButton("إعادة المحاولة", on_click=lambda _: main(page)),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=15,
                    scroll=ft.ScrollMode.AUTO,
                ),
            )
        )
        page.update()


if __name__ == "__main__":
    ft.app(target=main)
