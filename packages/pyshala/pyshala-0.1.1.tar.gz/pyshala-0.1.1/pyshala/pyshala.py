"""Main Reflex application entry point."""

import os

import reflex as rx

from .pages.index import index
from .pages.lesson import lesson_page
from .state.app_state import AppState


def get_app_name() -> str:
    """Get the application name from environment or default."""
    return os.getenv("APP_NAME", "Learn Python")


# Custom CSS for global styles
GLOBAL_STYLES = {
    "font_family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
}

APP_NAME = get_app_name()

app = rx.App(
    style=GLOBAL_STYLES,
    theme=rx.theme(
        accent_color="violet",
        gray_color="slate",
        radius="medium",
    ),
)

# Add routes
# Using on_load instead of on_mount ensures data reloads on every navigation
app.add_page(index, route="/", title=f"{APP_NAME} - Learn Python")
app.add_page(
    lesson_page,
    route="/lesson/[module_id]/[lesson_id]",
    title=f"Lesson - {APP_NAME}",
    on_load=[AppState.load_lesson_from_route, AppState.load_progress],
)
