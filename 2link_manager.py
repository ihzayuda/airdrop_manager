import sqlite3
import webbrowser
from datetime import datetime, timedelta, timezone
import customtkinter as ctk
from tkinter import messagebox, simpledialog
import threading
import time
from win10toast import ToastNotifier

DB_NAME = 'links.db'
UTC_PLUS_8 = timezone(timedelta(hours=8))

# Inisialisasi database
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            url TEXT NOT NULL,
            category TEXT,
            reminder_interval INTEGER DEFAULT 24,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_opened DATETIME
        )
    ''')
    conn.commit()
    conn.close()

# Tambah link ke database
def add_link(name, url, category, reminder_interval):
    now_utc8 = datetime.now(UTC_PLUS_8).strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO links (name, url, category, reminder_interval, created_at, last_opened) VALUES (?, ?, ?, ?, ?, ?)", (name, url, category, reminder_interval, now_utc8, now_utc8))
    conn.commit()
    conn.close()

# Hapus link dari database
def delete_link(link_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM links WHERE id = ?", (link_id,))
    conn.commit()
    conn.close()
    refresh_links()

# Ambil semua link
def get_links(filter_text="", category=""):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    query = "SELECT id, name, url, category, reminder_interval, created_at, last_opened FROM links WHERE 1=1"
    params = []
    if filter_text:
        query += " AND (url LIKE ? OR name LIKE ?)"
        params.extend([f"%{filter_text}%", f"%{filter_text}%"])
    if category and category != "Semua":
        query += " AND category = ?"
        params.append(category)
    query += " ORDER BY created_at DESC"
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return rows

# Ambil kategori unik
def get_categories():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT DISTINCT category FROM links WHERE category IS NOT NULL")
    categories = [row[0] for row in c.fetchall() if row[0]]
    conn.close()
    return categories

# Update waktu buka link
def update_last_opened(link_id):
    now_utc8 = datetime.now(UTC_PLUS_8).strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE links SET last_opened = ? WHERE id = ?", (now_utc8, link_id))
    conn.commit()
    conn.close()

# Buka link dan catat waktunya
def open_link(link_id, url):
    webbrowser.open(url)
    update_last_opened(link_id)
    refresh_links()

# Cek apakah butuh reminder
def needs_reminder(last_opened, interval):
    if not last_opened:
        return True
    try:
        try:
            last_time = datetime.strptime(last_opened, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            last_time = datetime.strptime(last_opened, "%Y-%m-%d %H:%M:%S.%f")
        return datetime.now(UTC_PLUS_8) - last_time > timedelta(hours=interval)
    except:
        return False

# Tambah kategori baru
def add_new_category():
    new_cat = simpledialog.askstring("Kategori Baru", "Masukkan nama kategori:")
    if new_cat:
        current = category_dropdown.get()
        category_dropdown.configure(values=list(set(get_categories() + [new_cat])), state="readonly")
        category_dropdown.set(new_cat)
        refresh_filter_dropdown()

# Refresh filter dropdown
def refresh_filter_dropdown():
    filter_dropdown.configure(values=["Semua"] + get_categories())
    filter_dropdown.set("Semua")

# Refresh link
def refresh_links(apply_category_filter=True):
    for widget in link_frame.winfo_children():
        widget.destroy()

    selected_category = filter_dropdown.get() if apply_category_filter else ""
    rows = get_links(search_entry.get(), selected_category)
    reminder_count = 0

    for idx, row in enumerate(rows):
        link_id, name, url, category, interval, created_at, last_opened = row
        reminder = needs_reminder(last_opened, interval) if last_opened != created_at else False
        if reminder:
            reminder_count += 1

        bg_color = "#8B0000" if reminder else "#1a1a1a"
        text_color = "white"
        category_color = "#00BFFF"

        frame = ctk.CTkFrame(link_frame, fg_color=bg_color, corner_radius=10, border_width=1, border_color="#333")
        frame.grid(row=idx // 2, column=idx % 2, padx=10, pady=10, sticky="nsew")

        top_frame = ctk.CTkFrame(frame, fg_color="transparent")
        top_frame.pack(fill="x", padx=5, pady=(5, 0))

        category_label = ctk.CTkLabel(top_frame, text=f"🔴 [{category}]", font=("Montserrat", 16, "bold"), text_color=category_color)
        category_label.pack(side="left")

        delete_btn = ctk.CTkButton(top_frame, text="🗑", width=30, command=lambda i=link_id: delete_link(i))
        delete_btn.pack(side="right")

        name_label = ctk.CTkLabel(frame, text=f"📌 {name}", font=("Montserrat", 14), text_color=text_color)
        name_label.pack(anchor="w", padx=10)

        created_label = ctk.CTkLabel(frame, text=f"🕓 Created: {created_at}", font=("Montserrat", 14), text_color=text_color)
        created_label.pack(anchor="w", padx=10)

        opened_label = ctk.CTkLabel(frame, text=f"⏱ Last Opened: {last_opened or 'Never'}", font=("Montserrat", 14), text_color=text_color)
        opened_label.pack(anchor="w", padx=10)

        interval_label = ctk.CTkLabel(frame, text=f"🔔 Reminder: setiap {interval} jam", font=("Montserrat", 14), text_color=text_color)
        interval_label.pack(anchor="w", padx=10, pady=(0, 10))

        open_btn = ctk.CTkButton(frame, text="🔓 Buka Link", command=lambda i=link_id, u=url: open_link(i, u))
        open_btn.pack(padx=10, pady=(0, 10), anchor="e")

    if reminder_count > 0:
        reminder_label.configure(text=f"⚠ {reminder_count} link belum dibuka sesuai intervalnya!", text_color="red")
        reminder_label.pack(pady=(0, 10))
    else:
        reminder_label.pack_forget()

# Tambahkan link
def handle_add():
    name = name_entry.get()
    url = url_entry.get()
    category = category_dropdown.get()
    try:
        interval = int(interval_entry.get())
    except:
        messagebox.showerror("Error", "Interval harus berupa angka.")
        return

    if not url:
        messagebox.showerror("Error", "Link airdrop tidak boleh kosong.")
        return
    add_link(name, url, category, interval)
    name_entry.delete(0, 'end')
    url_entry.delete(0, 'end')
    interval_entry.delete(0, 'end')
    refresh_links()
    refresh_filter_dropdown()

# Cek reminder background
def check_reminders_background():
    toaster = ToastNotifier()
    while True:
        time.sleep(600)
        rows = get_links()
        count = 0
        for row in rows:
            _, _, _, _, interval, created_at, last_opened = row
            if last_opened != created_at and needs_reminder(last_opened, interval):
                count += 1
        if count > 0:
            toaster.show_toast("⏰ Link Reminder", f"{count} link belum dibuka sesuai intervalnya!", duration=10, threaded=True)

# GUI setup
init_db()
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Link Manager with Reminder")
app.geometry("750x850")

name_entry = ctk.CTkEntry(app, placeholder_text="Nama Airdrop")
name_entry.pack(fill="x", padx=10, pady=5)
url_entry = ctk.CTkEntry(app, placeholder_text="Link Airdrop")
url_entry.pack(fill="x", padx=10, pady=5)
interval_entry = ctk.CTkEntry(app, placeholder_text="Reminder tiap berapa jam? (contoh: 24)")
interval_entry.pack(fill="x", padx=10, pady=5)

frame_category = ctk.CTkFrame(app)
frame_category.pack(fill="x", padx=10, pady=5)

category_dropdown = ctk.CTkComboBox(frame_category, values=get_categories(), state="readonly", width=250)
category_dropdown.set("Pilih kategori")
category_dropdown.pack(side="left", padx=(0, 5))

add_cat_button = ctk.CTkButton(frame_category, text="+ Tambah Kategori", command=add_new_category)
add_cat_button.pack(side="left")

add_button = ctk.CTkButton(frame_category, text="Tambahkan Airdrop", command=handle_add, fg_color="green")
add_button.pack(side="left", padx=(10, 0))

search_entry = ctk.CTkEntry(app, placeholder_text="Cari link atau nama airdrop...")
search_entry.pack(fill="x", padx=10, pady=5)
search_entry.bind("<KeyRelease>", lambda e: refresh_links())

filter_frame = ctk.CTkFrame(app)
filter_frame.pack(fill="x", padx=10, pady=5)

filter_dropdown = ctk.CTkComboBox(filter_frame, values=["Semua"] + get_categories(), state="readonly", width=250)
filter_dropdown.set("Semua")
filter_dropdown.pack(side="left", padx=(0, 5))

filter_button = ctk.CTkButton(filter_frame, text="Terapkan Filter", command=lambda: refresh_links(apply_category_filter=True))
filter_button.pack(side="left")

reminder_label = ctk.CTkLabel(app, text="", font=("Montserrat", 16))
reminder_label.pack(pady=(0, 0))

link_frame = ctk.CTkScrollableFrame(app)
link_frame.pack(expand=True, fill="both", padx=10, pady=10)
link_frame.grid_columnconfigure((0, 1), weight=1)

threading.Thread(target=check_reminders_background, daemon=True).start()
refresh_links(apply_category_filter=False)
app.mainloop()
