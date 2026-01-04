import flet as ft
import sqlite3
import time
from mfrc522 import SimpleMFRC522
from admin import get_admin_page
reader = SimpleMFRC522()
message = None
fname_txt=None
lname_txt=None
section_txt=None
def close_dialog(e, dialog, page):
    dialog.open = False
    page.update()
def register_user(fname, lname, section, page):
    global message
    conn = sqlite3.connect('locker_system.db')
    cursor = conn.cursor()
    dup_dialog = ft.AlertDialog(
        title=ft.Text("Duplicate RFID"),
        content=ft.Text("This RFID is already registered."),
        actions=[ft.ElevatedButton("OK", on_click=lambda e: close_dialog(e, dup_dialog, page))],
    )
    succ_dialog = ft.AlertDialog(
        title=ft.Text("Registration Successful"),
        content=ft.Text("User registered successfully."),
        actions=[ft.ElevatedButton("OK", on_click=lambda e: close_dialog(e, succ_dialog, page))],
    )
    message.value='Please place you ID near the Scanner'
    message.update()
    rfid, text = reader.read()
    cursor.execute("SELECT * FROM users WHERE user_id=?", (rfid,))
    if cursor.fetchone() is not None:
        page.overlay.append(dup_dialog)
        dup_dialog.open = True
        page.update()
        return
    succ_dialog.open = True
    page.overlay.append(succ_dialog)
    message.value=''
    lname_txt.value=''
    fname_txt.value=''
    section_txt.value=''
    page.update()
    time.sleep(2)
    close_dialog(None, succ_dialog, page)
    page.update()
    cursor.execute("INSERT INTO users (user_id, first_name, last_name, section) VALUES (?, ?, ?, ?)", (rfid, fname, lname, section))
    conn.commit()
def get_register_page(page):
    global message, fname_txt, lname_txt, section_txt
    message = ft.Text('')
    fname_txt = ft.TextField(
                label='First Name', 
                width=200,
                border_color = "WHITE"
            )
    lname_txt = ft.TextField(
                label='Last Name', 
                width=200,
                border_color = "WHITE"
            )
    section_txt = ft.TextField(
            label="Section (eg. CPE-4A)",
            width=400,
            border_color="WHITE"
        )
    main_view = ft.Column([
        ft.Text("Register a Locker User", size=30, weight=ft.FontWeight.BOLD),
        ft.Divider(),
        ft.Row([fname_txt, lname_txt], alignment=ft.MainAxisAlignment.CENTER),
        section_txt,
        ft.ElevatedButton(
            "Register",
            width=100,
            bgcolor="#A556B3",
            color="WHITE",
            on_click=lambda e: register_user(fname_txt.value, lname_txt.value, section_txt.value, page)
        ),
        message
        
    ],
    horizontal_alignment = ft.CrossAxisAlignment.CENTER)
    return main_view
