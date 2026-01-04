import flet as ft
import sqlite3
from register import get_register_page
from logs import get_logs_page
from admin import get_admin_page
from datetime import datetime
try: 
    from mfrc522 import MFRC522, SimpleMFRC522
except ImportError:
    print("walang mfrc522 module")
try:
    import RPi.GPIO as GPIO
    import serial
except ImportError:
    print("walang RPi.GPIO module")

import threading
import time

# ========================
# HARDWARE SETUP
# ========================
try:
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    ser = serial.Serial('/dev/serial0', 9600)
except Exception as e:
    print("walang serial module")
    ser = None

# ========================
# RFID THREAD CONTROL
# ========================
rfid_lock = threading.Lock()
rfid_active = False
scan_cancel_event = threading.Event()

# ========================
# LOCKER CONFIG
# ========================
lockers = [
    "A1", "B1", "C1", "D1", "E1", "F1",
    "A2", "B2", "C2", "D2", "E2", "F2"
]
button_status = {locker: "available" for locker in lockers}
simplereader = SimpleMFRC522()
btn_size = 100
btn_clr = "#A556B3"
buttons = []
curr_locker_id = ""
action_buttons_row = None
final_column = None
selected_action = None
cancel_button = None
lockers_btn=None
register_btn=None
logs_btn=None
admin_btn=None
logout_btn=None
login_btn=None
locker_col=None
center_area=None
nav_col=None
admin_access=False
admin_id = 938539227912
# ============================
# RESET DATABASE
# ============================
def reset_db():
    conn = sqlite3.connect('locker_system.db')
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS locker(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            locker_id TEXT,
            user_id TEXT,
            status TEXT
        )
    """)
    cursor.execute("""CREATE TABLE IF NOT EXISTS users 
    (id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    first_name TEXT, 
    last_name TEXT, 
    section TEXT)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    locker_id TEXT,
    first_name TEXT, 
    last_name TEXT, 
    section TEXT,
    time TEXT,
    action TEXT)""")
    cursor.execute("UPDATE locker SET status='available'")
    conn.commit()
    conn.close()

    for locker in button_status:
        button_status[locker] = "available"

# ============================
# RFID READER (CANCELABLE)
# ============================
def read_uid(timeout=10):
    try:
        reader = MFRC522()
        start_time = time.time()

        while time.time() - start_time < timeout:
            if scan_cancel_event.is_set():
                return None

            status, _ = reader.MFRC522_Request(reader.PICC_REQIDL)
            if status == reader.MI_OK:
                status, uid = reader.MFRC522_Anticoll()
                if status == reader.MI_OK:
                    str_id = str(int.from_bytes(uid, byteorder="big"))
                    return str_id
            time.sleep(0.1)
    except Exception as e:
        print("walang mfrc522 module")
    return None
def prevent_double_read():
    global rfid_active, lockers_btn
    lockers_btn.disabled = True if rfid_active else False
    lockers_btn.update()
def close_dialog(e, dialog, page):
    dialog.open = False
    page.update()
def give_admin_access(page):
    page.update()
    def read_card(page):
        global admin_access, nav_col, logout_btn, login_btn, locker_col, rfid_active, lockers_btn
        if rfid_active:
            return
        rfid_active=True
        prevent_double_read()
        print("Reading...")
        try:
            uid, text = simplereader.read()
            if uid == admin_id:
                admin_access = True
                succ_dialog = ft.AlertDialog(
                title=ft.Text("Welcome Admin"),
                content=ft.Text("Admin recognized Successfully."),
                actions=[ft.ElevatedButton("OK", on_click=lambda e: close_dialog(e, succ_dialog, page))])
                dialog=succ_dialog
                center_area.content=locker_col
                lockers_btn.bgcolor="#A556B3"
                nav_col.controls.append(logout_btn)
                nav_col.controls.remove(login_btn)
                rfid_active = False
                print(uid)
            else:
                warn_dialog = ft.AlertDialog(
                title=ft.Text("Warning"),
                content=ft.Text("Permission denied."),
                actions=[ft.ElevatedButton("Try Again", on_click=lambda e: close_dialog(e, warn_dialog, page))],
                )
                lockers_btn.bgcolor="#A556B3"
                login_btn.bgcolor="#000000"
                login_btn.update()
                center_area.content=locker_col
                dialog=warn_dialog
                rfid_active = False
            prevent_double_read()
            dialog.open=True
            page.overlay.append(dialog)
            page.update()
        except Exception as e:
            print(f"Read Error: {e}")
    t = threading.Thread(target=read_card, args=(page,))
    t.start()
    time.sleep(2)
    GPIO.cleanup()
def logout(page):
    global admin_access, center_area, locker_col, lockers_btn, register_btn, admin_btn, logs_btn, logout_btn, login_btn, nav_col
    nav = [register_btn, admin_btn, logs_btn]
    for n in nav:
        n.bgcolor = "#000000"
        n.update()
    lockers_btn.bgcolor = "#A556B3"
    lockers_btn.update()
    admin_access = False
    center_area.content = locker_col
    logout_dialog = ft.AlertDialog(
        title=ft.Text("Logout"),
        content=ft.Text("Admin access is halted"),
        actions=[ft.ElevatedButton("OK", on_click=lambda e: close_dialog(e, logout_dialog, page))],
        )
    logout_dialog.open = True
    page.overlay.append(logout_dialog)
    nav_col.controls.remove(logout_btn)
    nav_col.controls.append(login_btn)
    login_btn.bgcolor="#000000"
    page.update()
# ============================
# DATABASE FUNCTIONS
# ============================
def req_for_dup(user_id):
    conn = sqlite3.connect('locker_system.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row

# def ver(user_id, locker_id):
#    conn = sqlite3.connect('locker_system.db')
#    cursor = conn.cursor()
#    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
#    row = cursor.fetchone()
#    conn.close()
#    return row is not None
def ver(user_id, locker_id):
    conn = sqlite3.connect('locker_system.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM locker
        WHERE user_id=? AND status='occupied' AND locker_id!=?
    """, (user_id, locker_id))

    row = cursor.fetchone()
    conn.close()

    if row:
        return False, row[1]
    return True, locker_id

def get_locker_owner(locker_id):
    conn = sqlite3.connect('locker_system.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT user_id FROM locker
        WHERE locker_id=? AND status='occupied'
    """, (locker_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None
def get_name(user_id, i):
    conn = sqlite3.connect('locker_system.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM users WHERE user_id=?
    """, (user_id, ))
    user = cursor.fetchone()
    if user is not None:
        fname, lname, section = user[2], user[3], user[4]
    if i==0:
        return fname
    elif i==1:
        return lname
    else:
        return section
def enter_logs(user_id, locker_id, action):
    conn = sqlite3.connect('locker_system.db')
    cursor = conn.cursor()
    fname=get_name(user_id, 0)
    lname=get_name(user_id, 1)
    section=get_name(user_id, 2)
    now=datetime.now()
    date=now.strftime("%Y-%m-%d")
    time=now.strftime("%H:%M")
    datetime_str = f"{date} {time}"
    cursor.execute("""INSERT INTO logs (user_id, locker_id, first_name, last_name, section, time, action)
                    VALUES(?, ?, ?, ?, ?, ?, ?)""", (user_id, locker_id, fname, lname, section, datetime_str, action))
    conn.commit()
    conn.close()
# ============================
# LOCKER OPERATIONS
# ============================
def start_locker(locker_id, user_id, page, message):
    conn = sqlite3.connect('locker_system.db')
    cursor = conn.cursor()

    btn = buttons[lockers.index(locker_id)]
    btn.bgcolor = "#BFBFBF"
    btn.style = ft.ButtonStyle(
        text_style=ft.TextStyle(size=32, color="BLACK"),
        side=ft.BorderSide(0),
        shape=ft.RoundedRectangleBorder(radius=0)
    )
    btn.update()
    cursor.execute("SELECT * FROM locker WHERE user_id=?", (user_id,))
    if cursor.fetchone():
        cursor.execute("""
            UPDATE locker SET locker_id=?, status='occupied'
            WHERE user_id=?
        """, (locker_id, user_id))
        print(user_id)
    else:
        cursor.execute("""
            INSERT INTO locker (locker_id, user_id, status)
            VALUES (?, ?, 'occupied')
        """, (locker_id, user_id))
        print(user_id)
    conn.commit()
    conn.close()
    enter_logs(user_id, locker_id, "use locker")
    button_status[locker_id] = "occupied"
    ser.write(f"{locker_id}\n".encode())
    message.value = f"Locker {locker_id} assigned"
    page.update()
#NAV FUNCTIONS
def nav_click(btn, page):
    global lockers_btn, admin_btn, logs_btn, register_btn, center_area, lockers_page, login_btn
    if admin_access:
        nav_buttons = [lockers_btn, admin_btn, logs_btn, register_btn]
    else:
        nav_buttons = [lockers_btn, admin_btn, logs_btn, register_btn, login_btn]
    for nav_btn in nav_buttons:
        if nav_btn is not btn:
            nav_btn.bgcolor="#000000"
        else:
            nav_btn.bgcolor=btn_clr
        nav_btn.update()
    if btn is register_btn:
        if admin_access:
            center_area.content=get_register_page(page)
        else:
            center_area.content = ft.Column([ft.Text("Permission from the Admin is Required", size=30, color="white"),
                                            ft.Text("Login as Admin to proceed", size=20, color="white")],
                                            horizontal_alignment = ft.CrossAxisAlignment.CENTER,
                                            alignment = ft.MainAxisAlignment.CENTER)
        center_area.alignment = ft.alignment.center
    elif btn is admin_btn:
        if admin_access:
            center_area.content=get_admin_page(page)
        else:
            center_area.content = ft.Column([ft.Text("Permission from the Admin is Required", size=30, color="white"),
                                            ft.Text("Login as Admin to proceed", size=20, color="white")],
                                            horizontal_alignment = ft.CrossAxisAlignment.CENTER,
                                            alignment = ft.MainAxisAlignment.CENTER)
        center_area.alignment = ft.alignment.center
    elif btn is logs_btn:
        center_area.content = get_logs_page(page)
    elif btn is login_btn:
        center_area.content = ft.Column([ft.Text("Login as Admin", size=30, color="white"),
                                            ft.Text("Scan the Admin ID to unlock or any Card to cancel", size=20, color="white")],
                                            horizontal_alignment = ft.CrossAxisAlignment.CENTER,
                                            alignment = ft.MainAxisAlignment.CENTER)
        center_area.alignment = ft.alignment.center
        give_admin_access(page)
        
    else:
        GPIO.cleanup()
        center_area.content = locker_col
    page.update()

def open_only(user_id, locker_id, page, message):
    enter_logs(user_id, locker_id, "open only")
    ser.write(f"{locker_id}\n".encode())
    message.value = f"{locker_id} opened"
    hide_action_buttons(page)
    page.update()

def open_and_remove(locker_id, user_id, page, message):
    conn = sqlite3.connect('locker_system.db')
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE locker SET status='available'
        WHERE locker_id=? AND user_id=?
    """, (locker_id, user_id))
    conn.commit()
    conn.close()
    enter_logs(user_id, locker_id, "open and remove")
    button_status[locker_id] = "available"

    btn = buttons[lockers.index(locker_id)]
    btn.bgcolor = btn_clr
    btn.style = ft.ButtonStyle(
        text_style=ft.TextStyle(size=32, color="WHITE"),
        side=ft.BorderSide(1, "white"),
        shape=ft.RoundedRectangleBorder(radius=10)
    )
    btn.update()

    ser.write(f"{locker_id}\n".encode())
    message.value = f"{locker_id} is now available"
    hide_action_buttons(page)
    page.update()

# ============================
# UI HELPERS
# ============================
def hide_action_buttons(page):
    global action_buttons_row
    if action_buttons_row:
        action_buttons_row.controls.clear()
        action_buttons_row.update()
        page.update()

def disable_all_lockers(disabled=True):
    global register_btn, lockers_btn, admin_btn, logs_btn
    nav = [register_btn, lockers_btn, admin_btn, logs_btn]
    for n in nav:
        if n is lockers_btn:
            n.bgcolor = "#DEDEDE" if disabled else "#A556B3"
        else:
            n.bgcolor = "#DEDEDE" if disabled else "#000000"
        n.disabled=disabled
        n.update()
    for b in buttons:
        b.disabled = disabled
        b.update()

# ============================
# HOME PAGE
# ============================
def get_home_page(page: ft.Page):
    global buttons, action_buttons_row, selected_action, rfid_active, cancel_button, register_btn, lockers_btn, admin_btn, logs_btn, center_area, locker_col, logout_btn, login_btn, nav_col

    message = ft.Text(
        "Please select your locker",
        size=30,
        weight=ft.FontWeight.BOLD,
        color="WHITE"
    )
    
    buttons_row1 = ft.Row(alignment=ft.MainAxisAlignment.CENTER)
    buttons_row2 = ft.Row(alignment=ft.MainAxisAlignment.CENTER)
    action_buttons_row = ft.Row(alignment=ft.MainAxisAlignment.CENTER)

    cancel_button = ft.ElevatedButton(
        text="Cancel",
        visible=False,
        on_click=lambda e: cancel_scan()
    )

    # ============================
    # CANCEL HANDLER
    # ============================
    def cancel_scan():
        global rfid_active
        scan_cancel_event.set()
        rfid_active = False
        disable_all_lockers(False)
        cancel_button.visible = False
        cancel_button.update()
        message.value = "Scan cancelled"
        page.update()

    # ============================
    # RFID STARTER
    # ============================
    def start_rfid_scan(locker_id):
        global rfid_active

        if rfid_active:
            return

        scan_cancel_event.clear()
        rfid_active = True
        disable_all_lockers(True)
        cancel_button.visible = True
        cancel_button.update()

        def worker():
            global rfid_active
            with rfid_lock:
                uid = read_uid()

            rfid_active = False
            disable_all_lockers(False)
            cancel_button.visible = False
            cancel_button.update()

            if uid:
                process_card(locker_id, uid)
            else:
                message.value = "RFID scan cancelled or timed out"
                page.update()

        threading.Thread(target=worker, daemon=True).start()

    # ============================
    # CARD PROCESSOR
    # ============================
    def process_card(locker_id, user_id):
        if not req_for_dup(user_id):
            message.value = "ID is not registered"
            print(user_id)
            page.update()
            return

        verified, existing = ver(user_id, locker_id)
        if not verified:
            message.value = f"You already own locker {existing}"
            page.update()
            return

        owner = get_locker_owner(locker_id)
        if not owner:
            start_locker(locker_id, user_id, page, message)
            return

        if owner != user_id:
            message.value = f"Locker {locker_id} is occupied"
            print(f"{owner} - {user_id}")
            page.update()
            return

        if selected_action == "open":
            open_only(user_id, locker_id, page, message)
        elif selected_action == "remove":
            open_and_remove(locker_id, user_id, page, message)

    # ============================
    # BUTTON HANDLERS
    # ============================
    def scan_rfid(e, locker_id):
        global selected_action
        selected_action = None
        hide_action_buttons(page)

        if button_status[locker_id] == "occupied":
            action_buttons_row.controls = [
                ft.ElevatedButton(
                    "Open",
                    bgcolor="#4CAF50",
                    color="WHITE",
                    on_click=lambda e: choose_action("open", locker_id)
                ),
                ft.ElevatedButton(
                    "Open & Remove",
                    bgcolor="#E53935",
                    color="WHITE",
                    on_click=lambda e: choose_action("remove", locker_id)
                )
            ]
            action_buttons_row.update()
        else:
            message.value = f"Scan RFID for locker {locker_id}"
            page.update()
            start_rfid_scan(locker_id)

    def choose_action(action, locker_id):
        global selected_action
        selected_action = action
        hide_action_buttons(page)
        message.value = f"Scan RFID for locker {locker_id}"
        page.update()
        start_rfid_scan(locker_id)

    # ============================
    # LOCKER GRID
    # ============================

    for locker in lockers[:6]:
        btn = ft.ElevatedButton(
            locker,
            width=btn_size,
            height=btn_size,
            bgcolor=btn_clr,
            color="WHITE",
            on_click=lambda e, l=locker: scan_rfid(e, l),
            style=ft.ButtonStyle(
                text_style=ft.TextStyle(size=32),
                shape=ft.RoundedRectangleBorder(radius=10)
            )
        )
        buttons.append(btn)
        buttons_row1.controls.append(btn)

    for locker in lockers[6:]:
        btn = ft.ElevatedButton(
            locker,
            width=btn_size,
            height=btn_size,
            bgcolor=btn_clr,
            color="WHITE",
            on_click=lambda e, l=locker: scan_rfid(e, l),
            style=ft.ButtonStyle(
                text_style=ft.TextStyle(size=32),
                shape=ft.RoundedRectangleBorder(radius=10)
            )
        )
        buttons.append(btn)
        buttons_row2.controls.append(btn)
    
    lockers_btn = ft.ElevatedButton(
        "Lockers",
        width = 75,
        height = 30,
        color="WHITE",
        bgcolor=btn_clr,
        on_click=lambda e: nav_click(lockers_btn, page),
        style=ft.ButtonStyle(
            text_style=ft.TextStyle(size=14),
            shape=ft.RoundedRectangleBorder(radius=10)
        )
    )
    register_btn = ft.ElevatedButton(
        "Register",
        width = 75,
        height = 30,
        color="WHITE",
        on_click=lambda e: nav_click(register_btn, page),
        style=ft.ButtonStyle(
            text_style=ft.TextStyle(size=14),
            shape=ft.RoundedRectangleBorder(radius=10)
        )
    )
    admin_btn = ft.ElevatedButton(
        "Admin",
        width = 75,
        height = 30,
        color="WHITE",
        on_click=lambda e: nav_click(admin_btn, page),
        style=ft.ButtonStyle(
            text_style=ft.TextStyle(size=14),
            shape=ft.RoundedRectangleBorder(radius=10)
        )
    )
    logs_btn = ft.ElevatedButton(
        "Logs",
        width = 75,
        height = 30,
        color="WHITE",
        on_click=lambda e: nav_click(logs_btn, page),
        style=ft.ButtonStyle(
            text_style=ft.TextStyle(size=14),
            shape=ft.RoundedRectangleBorder(radius=10)
        )
    )
    logout_btn = ft.ElevatedButton(
        "Logout",
        width = 75,
        height = 30,
        color="WHITE",
        on_click=lambda e: logout(page),
        style=ft.ButtonStyle(
            text_style=ft.TextStyle(size=14),
            shape=ft.RoundedRectangleBorder(radius=10)
        )
    )
    login_btn = ft.ElevatedButton(
        "Login",
        width = 75,
        height = 30,
        color="WHITE",
        on_click=lambda e: nav_click(login_btn, page),
        style=ft.ButtonStyle(
            text_style=ft.TextStyle(size=14),
            shape=ft.RoundedRectangleBorder(radius=10)
        )
    )
    
    space = ft.Divider(height=100)
    
    nav_col = ft.Column(
    [lockers_btn, register_btn, admin_btn, logs_btn, space, login_btn],
    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    spacing=20
    )
    locker_col = ft.Column(
                [message, 
                buttons_row1, 
                buttons_row2, 
                action_buttons_row, 
                cancel_button],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20
        )
    nav_bg = ft.Container(
        content=nav_col,
        bgcolor="#404040",
        width=100,
        padding=10,
    )
    lockers_page = ft.Container(
        content=locker_col,
        expand=True,
        alignment=ft.alignment.center
    )
    center_area = lockers_page
    final_row = ft.Row(
    [nav_bg, center_area],
    expand=True,
    alignment=ft.MainAxisAlignment.CENTER,
    vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )


    return final_row
