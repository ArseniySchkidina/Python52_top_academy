import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk


DB_NAME = "food_delivery.db"
IMG_DIR = "images"


class BikeDeliveryApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Велосипед — доставка еды на дом")
        self.geometry("1280x780")
        self.minsize(1180, 700)
        self.configure(bg="#f4f7fb")

        self.cart = {}  # dish_id -> {"name", "price", "qty"}
        self.image_cache = {}

        self._init_db()
        self.dishes = self._load_dishes()

        self._setup_style()
        self._build_ui()
        self._render_menu()
        self._refresh_cart()

    def _init_db(self):
        self.conn = sqlite3.connect(DB_NAME)
        self.cur = self.conn.cursor()

        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS dishes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                price REAL NOT NULL,
                image_path TEXT
            )
        """)

        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                address TEXT NOT NULL,
                total REAL NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                dish_name TEXT NOT NULL,
                price REAL NOT NULL,
                qty INTEGER NOT NULL,
                FOREIGN KEY(order_id) REFERENCES orders(id)
            )
        """)

        self.conn.commit()

        self.cur.execute("SELECT COUNT(*) FROM dishes")
        count = self.cur.fetchone()[0]

        if count == 0:
            sample_dishes = [
                ("Пицца «Маргарита»", "Томатный соус, сыр моцарелла, базилик", 590, "pizza.png"),
                ("Бургер с говядиной", "Сочная котлета, сыр, овощи и фирменный соус", 520, "burger.png"),
                ("Суши-сет", "Набор из роллов с лососем, креветкой и угрём", 890, "sushi.png"),
                ("Паста Карбонара", "Паста с беконом, сливочным соусом и пармезаном", 640, "pasta.png"),
                ("Салат Цезарь", "Курица, листья салата, сухарики и соус Цезарь", 430, "salad.png"),
                ("Куриный суп", "Лёгкий домашний суп с курицей и овощами", 360, "soup.png"),
            ]
            self.cur.executemany(
                "INSERT INTO dishes (name, description, price, image_path) VALUES (?, ?, ?, ?)",
                sample_dishes
            )
            self.conn.commit()

    def _load_dishes(self):
        self.cur.execute("SELECT id, name, description, price, image_path FROM dishes ORDER BY id")
        dishes = []
        for row in self.cur.fetchall():
            dishes.append({
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "price": float(row[3]),
                "image_path": row[4]
            })
        return dishes

    def _setup_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("TFrame", background="#f4f7fb")
        style.configure("White.TFrame", background="white")
        style.configure("Header.TFrame", background="#1f2a44")
        style.configure("Sidebar.TFrame", background="white")

        style.configure("TLabel", background="#f4f7fb", font=("Segoe UI", 10))
        style.configure("HeaderTitle.TLabel", background="#1f2a44", foreground="white", font=("Segoe UI", 22, "bold"))
        style.configure("HeaderSub.TLabel", background="#1f2a44", foreground="#cbd5e1", font=("Segoe UI", 10))
        style.configure("Section.TLabel", background="#f4f7fb", foreground="#111827", font=("Segoe UI", 16, "bold"))
        style.configure("CardTitle.TLabel", background="white", foreground="#111827", font=("Segoe UI", 11, "bold"))
        style.configure("CardDesc.TLabel", background="white", foreground="#475569", font=("Segoe UI", 9), wraplength=230, justify="left")
        style.configure("Price.TLabel", background="white", foreground="#0f766e", font=("Segoe UI", 11, "bold"))
        style.configure("CartTitle.TLabel", background="white", foreground="#111827", font=("Segoe UI", 14, "bold"))
        style.configure("Total.TLabel", background="white", foreground="#1d4ed8", font=("Segoe UI", 14, "bold"))

        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), padding=10)
        style.map("Accent.TButton",
                  background=[("active", "#0f766e"), ("!active", "#14b8a6")],
                  foreground=[("active", "white"), ("!active", "white")])

        style.configure("Danger.TButton", font=("Segoe UI", 9, "bold"), padding=7)
        style.map("Danger.TButton",
                  background=[("active", "#b91c1c"), ("!active", "#ef4444")],
                  foreground=[("active", "white"), ("!active", "white")])

        style.configure("Primary.TButton", font=("Segoe UI", 11, "bold"), padding=12)
        style.map("Primary.TButton",
                  background=[("active", "#1d4ed8"), ("!active", "#2563eb")],
                  foreground=[("active", "white"), ("!active", "white")])

        style.configure("Small.TButton", font=("Segoe UI", 9, "bold"), padding=4)
        style.map("Small.TButton",
                  background=[("active", "#334155"), ("!active", "#475569")],
                  foreground=[("active", "white"), ("!active", "white")])

    def _build_ui(self):
        header = ttk.Frame(self, style="Header.TFrame")
        header.pack(fill="x")

        header_left = ttk.Frame(header, style="Header.TFrame")
        header_left.pack(side="left", padx=24, pady=16)

        ttk.Label(header_left, text="🚴 Велосипед", style="HeaderTitle.TLabel").pack(anchor="w")
        ttk.Label(header_left, text="Доставка вкусной еды на дом", style="HeaderSub.TLabel").pack(anchor="w")

        header_right = ttk.Frame(header, style="Header.TFrame")
        header_right.pack(side="right", padx=24)

        self.header_total_var = tk.StringVar(value="Корзина: 0 ₽")
        ttk.Label(header_right, textvariable=self.header_total_var, style="HeaderSub.TLabel", font=("Segoe UI", 12, "bold")).pack(anchor="e", pady=20)

        # Main layout
        main = ttk.Frame(self)
        main.pack(fill="both", expand=True, padx=18, pady=18)

        menu_area = ttk.Frame(main)
        menu_area.pack(side="left", fill="both", expand=True, padx=(0, 12))

        ttk.Label(menu_area, text="Меню", style="Section.TLabel").pack(anchor="w", pady=(0, 10))

        self.menu_canvas = tk.Canvas(menu_area, bg="#f4f7fb", highlightthickness=0)
        self.menu_scroll = ttk.Scrollbar(menu_area, orient="vertical", command=self.menu_canvas.yview)
        self.menu_container = ttk.Frame(self.menu_canvas)

        self.menu_container.bind(
            "<Configure>",
            lambda e: self.menu_canvas.configure(scrollregion=self.menu_canvas.bbox("all"))
        )

        self.menu_window = self.menu_canvas.create_window((0, 0), window=self.menu_container, anchor="nw")
        self.menu_canvas.configure(yscrollcommand=self.menu_scroll.set)

        self.menu_canvas.pack(side="left", fill="both", expand=True)
        self.menu_scroll.pack(side="right", fill="y")

        self.menu_canvas.bind("<Configure>", self._resize_menu_window)
        self.menu_canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # Right: sidebar/cart
        sidebar = ttk.Frame(main, style="Sidebar.TFrame", width=380)
        sidebar.pack(side="right", fill="y")
        sidebar.pack_propagate(False)

        ttk.Label(sidebar, text="Корзина", style="CartTitle.TLabel", background="white").pack(anchor="w", padx=16, pady=(14, 8))

        cart_wrap = ttk.Frame(sidebar, style="Sidebar.TFrame")
        cart_wrap.pack(fill="both", expand=True, padx=14, pady=(0, 10))

        self.cart_tree = ttk.Treeview(
            cart_wrap,
            columns=("name", "qty", "sum"),
            show="headings",
            height=13
        )
        self.cart_tree.heading("name", text="Блюдо")
        self.cart_tree.heading("qty", text="Кол-во")
        self.cart_tree.heading("sum", text="Сумма")
        self.cart_tree.column("name", width=170, anchor="w")
        self.cart_tree.column("qty", width=60, anchor="center")
        self.cart_tree.column("sum", width=80, anchor="e")

        self.cart_tree.pack(side="left", fill="both", expand=True)

        cart_scroll = ttk.Scrollbar(cart_wrap, orient="vertical", command=self.cart_tree.yview)
        cart_scroll.pack(side="right", fill="y")
        self.cart_tree.configure(yscrollcommand=cart_scroll.set)

        btns = ttk.Frame(sidebar, style="Sidebar.TFrame")
        btns.pack(fill="x", padx=14, pady=(4, 10))

        ttk.Button(btns, text="− Уменьшить количество", style="Danger.TButton", command=self.decrease_selected).pack(fill="x", pady=(0, 6))
        ttk.Button(btns, text="Удалить блюдо полностью", style="Danger.TButton", command=self.remove_selected).pack(fill="x", pady=(0, 6))
        ttk.Button(btns, text="Очистить корзину", style="Danger.TButton", command=self.clear_cart).pack(fill="x")

        ttk.Separator(sidebar).pack(fill="x", padx=14, pady=10)

        self.cart_total_var = tk.StringVar(value="Итого: 0 ₽")
        ttk.Label(sidebar, textvariable=self.cart_total_var, background="white", foreground="#111827",
                  font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=16, pady=(0, 10))

        ttk.Label(sidebar, text="Оформление заказа", style="Section.TLabel", background="white").pack(anchor="w", padx=16, pady=(4, 8))

        form = ttk.Frame(sidebar, style="Sidebar.TFrame")
        form.pack(fill="x", padx=14)

        self.name_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.address_text = None

        self._make_field(form, "Имя", entry_var=self.name_var)
        self._make_field(form, "Телефон", entry_var=self.phone_var)
        self._make_field(form, "Адрес доставки", multiline=True)

        ttk.Button(sidebar, text="Оформить заказ", style="Primary.TButton", command=self.place_order).pack(fill="x", padx=14, pady=14)

        self.status_var = tk.StringVar(value="Выберите блюда и добавьте их в корзину.")
        status = ttk.Label(self, textvariable=self.status_var, background="#dbeafe", foreground="#0f172a", anchor="w",
                           font=("Segoe UI", 10))
        status.pack(fill="x", side="bottom")

    def _make_field(self, parent, label, entry_var=None, multiline=False):
        wrap = ttk.Frame(parent, style="Sidebar.TFrame")
        wrap.pack(fill="x", pady=6)

        ttk.Label(wrap, text=label, background="white", foreground="#334155", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 4))

        if multiline:
            txt = tk.Text(
                wrap, height=3, wrap="word",
                font=("Segoe UI", 10),
                bg="#f8fafc", fg="#0f172a",
                bd=0, highlightthickness=1, highlightbackground="#e2e8f0"
            )
            txt.pack(fill="x", ipady=4)
            self.address_text = txt
        else:
            ent = tk.Entry(
                wrap, textvariable=entry_var,
                font=("Segoe UI", 10),
                bg="#f8fafc", fg="#0f172a",
                bd=0, highlightthickness=1, highlightbackground="#e2e8f0"
            )
            ent.pack(fill="x", ipady=7)

    def _resize_menu_window(self, event):
        self.menu_canvas.itemconfig(self.menu_window, width=event.width)

    def _on_mousewheel(self, event):
        try:
            self.menu_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except Exception:
            pass

    def _render_menu(self):
        for widget in self.menu_container.winfo_children():
            widget.destroy()

        columns = 2
        for index, dish in enumerate(self.dishes):
            row = index // columns
            col = index % columns

            card = ttk.Frame(self.menu_container, style="White.TFrame")
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            card.configure(width=300, height=330)
            card.grid_propagate(False)

            # Image
            img_frame = ttk.Frame(card, style="White.TFrame")
            img_frame.pack(fill="x", padx=12, pady=(12, 8))

            image = self._load_image(dish["image_path"], size=(270, 150))
            if image:
                lbl = ttk.Label(img_frame, image=image, background="white")
                lbl.image = image
                lbl.pack()
            else:
                canvas = tk.Canvas(img_frame, width=270, height=150, bg="#e2e8f0", highlightthickness=0)
                canvas.create_text(135, 75, text="Нет изображения", fill="#475569", font=("Segoe UI", 12, "bold"))
                canvas.pack()

            ttk.Label(card, text=dish["name"], style="CardTitle.TLabel").pack(anchor="w", padx=12, pady=(2, 0))
            ttk.Label(card, text=dish["description"], style="CardDesc.TLabel").pack(anchor="w", padx=12, pady=(4, 0))
            ttk.Label(card, text=f'{dish["price"]:.0f} ₽', style="Price.TLabel").pack(anchor="w", padx=12, pady=(8, 0))

            bottom = ttk.Frame(card, style="White.TFrame")
            bottom.pack(fill="x", padx=12, pady=12)

            ttk.Button(
                bottom,
                text="Добавить в корзину",
                style="Accent.TButton",
                command=lambda d=dish: self.add_to_cart(d)
            ).pack(fill="x")

        for c in range(columns):
            self.menu_container.grid_columnconfigure(c, weight=1)

    def _load_image(self, image_path, size=(270, 150)):
        if not image_path:
            return None

        path = os.path.join(IMG_DIR, image_path)
        if not os.path.exists(path):
            return None

        key = (path, size)
        if key in self.image_cache:
            return self.image_cache[key]

        try:
            img = Image.open(path).convert("RGBA")
            img.thumbnail(size, Image.Resampling.LANCZOS)

            bg = Image.new("RGBA", size, (255, 255, 255, 255))
            x = (size[0] - img.width) // 2
            y = (size[1] - img.height) // 2
            bg.paste(img, (x, y), img)

            photo = ImageTk.PhotoImage(bg)
            self.image_cache[key] = photo
            return photo
        except Exception:
            return None

    def add_to_cart(self, dish):
        dish_id = dish["id"]

        if dish_id in self.cart:
            self.cart[dish_id]["qty"] += 1
        else:
            self.cart[dish_id] = {
                "name": dish["name"],
                "price": dish["price"],
                "qty": 1
            }

        self.status_var.set(f'Добавлено в корзину: {dish["name"]}')
        self._refresh_cart()

    def _refresh_cart(self):
        for item in self.cart_tree.get_children():
            self.cart_tree.delete(item)

        total = 0
        for dish_id, item in self.cart.items():
            item_sum = item["price"] * item["qty"]
            total += item_sum

            self.cart_tree.insert(
                "",
                "end",
                iid=str(dish_id),
                values=(item["name"], item["qty"], f"{item_sum:.0f} ₽")
            )

        self.cart_total_var.set(f"Итого: {total:.0f} ₽")
        self.header_total_var.set(f"Корзина: {total:.0f} ₽")

    def _selected_cart_id(self):
        selection = self.cart_tree.selection()
        if not selection:
            return None
        try:
            return int(selection[0])
        except ValueError:
            return None

    def decrease_selected(self):
        dish_id = self._selected_cart_id()
        if dish_id is None:
            messagebox.showinfo("Корзина", "Выберите блюдо в корзине.")
            return

        if dish_id not in self.cart:
            return

        if self.cart[dish_id]["qty"] > 1:
            self.cart[dish_id]["qty"] -= 1
        else:
            del self.cart[dish_id]

        self.status_var.set("Количество блюда уменьшено.")
        self._refresh_cart()

    def remove_selected(self):
        dish_id = self._selected_cart_id()
        if dish_id is None:
            messagebox.showinfo("Корзина", "Выберите блюдо в корзине.")
            return

        if dish_id in self.cart:
            del self.cart[dish_id]
            self.status_var.set("Блюдо удалено из корзины.")
            self._refresh_cart()

    def clear_cart(self):
        self.cart.clear()
        self.status_var.set("Корзина очищена.")
        self._refresh_cart()

    def _cart_total(self):
        return sum(item["price"] * item["qty"] for item in self.cart.values())

    def place_order(self):
        if not self.cart:
            messagebox.showwarning("Заказ", "Корзина пуста. Сначала добавьте блюда.")
            return

        name = self.name_var.get().strip()
        phone = self.phone_var.get().strip()
        address = self.address_text.get("1.0", "end").strip() if self.address_text else ""

        if not name or not phone or not address:
            messagebox.showwarning("Заказ", "Заполните имя, телефон и адрес доставки.")
            return

        total = self._cart_total()

        self.cur.execute(
            "INSERT INTO orders (customer_name, phone, address, total) VALUES (?, ?, ?, ?)",
            (name, phone, address, total)
        )
        order_id = self.cur.lastrowid

        for item in self.cart.values():
            self.cur.execute(
                "INSERT INTO order_items (order_id, dish_name, price, qty) VALUES (?, ?, ?, ?)",
                (order_id, item["name"], item["price"], item["qty"])
            )

        self.conn.commit()

        messagebox.showinfo(
            "Заказ оформлен",
            f"Спасибо, {name}!\nВаш заказ №{order_id} принят.\nСумма: {total:.0f} ₽"
        )

        self.cart.clear()
        self._refresh_cart()
        self.name_var.set("")
        self.phone_var.set("")
        if self.address_text:
            self.address_text.delete("1.0", "end")

        self.status_var.set(f"Заказ №{order_id} успешно сохранён в базе данных.")

    def on_close(self):
        try:
            self.conn.close()
        except Exception:
            pass
        self.destroy()


if __name__ == "__main__":
    app = BikeDeliveryApp()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
