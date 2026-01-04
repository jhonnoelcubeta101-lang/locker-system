import flet as ft
import sqlite3
def delete_data(e, user_id, page, table_container):
    conn=sqlite3.connect('locker_system.db')
    cursor=conn.cursor()
    cursor.execute("DELETE FROM users where user_id=?", (user_id,))
    print(f"deleting {user_id}")
    conn.commit()
    table_container.content = get_data(page, table_container)
    page.update()
def refresh(table):
    table.update()
def get_data(page, table_container):
    conn=sqlite3.connect('locker_system.db')
    cursor=conn.cursor()
    cursor.execute("SELECT * FROM users")
    rows=cursor.fetchall()
    user_table=ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("User RFID")),
            ft.DataColumn(ft.Text("First Name")),
            ft.DataColumn(ft.Text("Last Name")),
            ft.DataColumn(ft.Text("Section")),
            ft.DataColumn(ft.Text(""))
        ],
        rows=[]
        )
    for row in rows:
        user_table.rows.append(
            ft.DataRow(cells=[
                ft.DataCell(ft.Text(str(row[1]))),
                ft.DataCell(ft.Text(str(row[2]))),
                ft.DataCell(ft.Text(str(row[3]))),
                ft.DataCell(ft.Text(str(row[4]))),
                ft.DataCell(ft.ElevatedButton(
                        "Delete",
                        bgcolor="#A556B3",
                        color="WHITE",
                        on_click=lambda e, rid=row[1]: delete_data(e, rid, page, table_container)
                        ))
            ])
        )
    return user_table
def get_admin_page(page):
    table_container = ft.Container()
    table_container.content = get_data(page, table_container)
    main_view = ft.Column([
        ft.Text("Admin Dashboard", size=30, weight=ft.FontWeight.BOLD),
        ft.Divider(),
        table_container
    ],
    horizontal_alignment = ft.CrossAxisAlignment.CENTER)
    return main_view
