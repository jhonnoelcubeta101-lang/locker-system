import flet as ft
import sqlite3
def get_data(page, table_container):
    conn=sqlite3.connect('locker_system.db')
    cursor=conn.cursor()
    cursor.execute("SELECT * FROM logs")
    rows=cursor.fetchall()
    user_table=ft.DataTable(
        columns=[
            ft.DataColumn(ft.Container(alignment=ft.alignment.center, content=ft.Text("User RFID"), expand=True)),
            ft.DataColumn(ft.Text("Locker ID")),
            ft.DataColumn(ft.Text("First Name")),
            ft.DataColumn(ft.Text("Last Name")),
            ft.DataColumn(ft.Text("Section")),
            ft.DataColumn(ft.Container(alignment=ft.alignment.center, content=ft.Text("Date and Time"), expand=True)),
            ft.DataColumn(ft.Text("Action"))
        ],
        rows=[],
        column_spacing=12
        )
    for row in rows:
        user_table.rows.append(
            ft.DataRow(cells=[
                ft.DataCell(ft.Text(str(row[1]))),
                ft.DataCell(ft.Row(alignment=ft.MainAxisAlignment.CENTER, controls=[ft.Text(str(row[2]))])),
                ft.DataCell(ft.Text(str(row[3]))),
                ft.DataCell(ft.Text(str(row[4]))),
                ft.DataCell(ft.Text(str(row[5]))),
                ft.DataCell(ft.Text(str(row[6]))),
                ft.DataCell(ft.Text(str(row[7])))
            ])
        )
    return user_table
def get_logs_page(page):
    table_container = ft.Container(600)
    table_container.content = get_data(page, table_container)
    main_view = ft.Column([
        ft.Text("Logs", size=30, weight=ft.FontWeight.BOLD),
        ft.Divider(),
        table_container
    ],
    horizontal_alignment = ft.CrossAxisAlignment.CENTER)
    return main_view
