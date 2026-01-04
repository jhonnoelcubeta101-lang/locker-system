import flet as ft
from home import get_home_page, reset_db

def main(page: ft.Page):
    # Set page properties
    reset_db()
    page.title = "Locker System"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 800
    page.window_height = 600
    page.window_resizable = True
    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(surface="#2E8B57", background="#2E8B57")
    )

    # Function to handle route changes
    def route_change(e: ft.RouteChangeEvent):
        page.views.clear()  # Clear previous views
        
        if page.route == "/":
            # When route is "/", display the home page
            page.views.append(ft.View("/", controls=[get_home_page(page)]))
        page.update()  # Update the page

    page.on_route_change = route_change
    page.go("/")  # Start with the home page

# Start the app
ft.app(target=main, view=ft.WEB_BROWSER, host='0.0.0.0', port=8550)
