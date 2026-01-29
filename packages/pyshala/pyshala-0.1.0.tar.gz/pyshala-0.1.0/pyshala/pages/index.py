"""Home page - displays all available modules."""

import os

import reflex as rx

from ..components.navbar import navbar
from ..state.app_state import AppState, ModuleInfo


def get_app_description() -> str:
    """Get the application description from environment or default."""
    return os.getenv(
        "APP_DESCRIPTION",
        "Interactive lessons with hands-on coding exercises and instant feedback"
    )


def module_card(module: ModuleInfo) -> rx.Component:
    """Create a module card component.

    Args:
        module: ModuleInfo object.

    Returns:
        Module card component.
    """
    return rx.link(
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon("book-open", size=20, color="#3b82f6"),
                    rx.spacer(),
                    rx.badge(
                        f"{module.lesson_count} lessons",
                        color_scheme="blue",
                        size="1",
                    ),
                    width="100%",
                ),
                rx.heading(
                    module.name,
                    size="4",
                    color=rx.cond(AppState.dark_mode, "#f3f4f6", "#1f2937"),
                    margin_top="0.375rem",
                ),
                rx.text(
                    module.description,
                    color=rx.cond(AppState.dark_mode, "#9ca3af", "#6b7280"),
                    font_size="0.8rem",
                    line_height="1.5",
                    min_height="2.5rem",
                ),
                rx.spacer(),
                width="100%",
                height="100%",
                spacing="1",
                align="start",
            ),
            padding="1rem",
            background=rx.cond(AppState.dark_mode, "#1e293b", "white"),
            border_radius="0.5rem",
            border=rx.cond(AppState.dark_mode, "1px solid #374151", "none"),
            box_shadow="0 1px 2px rgba(0, 0, 0, 0.08)",
            _hover={
                "box_shadow": "0 4px 12px rgba(0, 0, 0, 0.15)",
                "transform": "translateY(-2px)",
            },
            transition="all 0.2s ease",
            height="100%",
            min_height="150px",
        ),
        href=f"/module/{module.id}",
        _hover={"text_decoration": "none"},
        width="100%",
    )


def empty_state() -> rx.Component:
    """Display when no modules are available."""
    return rx.center(
        rx.vstack(
            rx.icon(
                "folder-open",
                size=48,
                color=rx.cond(AppState.dark_mode, "#6b7280", "#9ca3af"),
            ),
            rx.heading(
                "No Lessons Yet",
                size="5",
                color=rx.cond(AppState.dark_mode, "#e5e7eb", "#374151"),
            ),
            rx.text(
                "Lessons will appear here once they're configured.",
                color=rx.cond(AppState.dark_mode, "#9ca3af", "#6b7280"),
                font_size="0.85rem",
                text_align="center",
            ),
            rx.text(
                "Add lesson YAML files to the lessons directory to get started.",
                color=rx.cond(AppState.dark_mode, "#6b7280", "#9ca3af"),
                font_size="0.8rem",
                text_align="center",
            ),
            spacing="2",
            align="center",
            padding="2rem",
        ),
        width="100%",
        min_height="300px",
    )


def index() -> rx.Component:
    """Home page component displaying all modules.

    Returns:
        Home page component.
    """
    return rx.box(
        navbar(),
        rx.box(
            rx.vstack(
                # Hero section
                rx.box(
                    rx.vstack(
                        rx.heading(
                            "Learn Python, One Lesson at a Time",
                            size="6",
                            color=rx.cond(AppState.dark_mode, "#f3f4f6", "#1f2937"),
                            text_align="center",
                        ),
                        rx.text(
                            get_app_description(),
                            color=rx.cond(AppState.dark_mode, "#9ca3af", "#6b7280"),
                            font_size="0.9rem",
                            text_align="center",
                            max_width="600px",
                        ),
                        spacing="2",
                        align="center",
                        padding_y="1.25rem",
                    ),
                    width="100%",
                ),
                # Modules grid
                rx.cond(
                    AppState.modules.length() > 0,
                    rx.box(
                        rx.grid(
                            rx.foreach(
                                AppState.modules,
                                module_card,
                            ),
                            columns="3",
                            spacing="3",
                            width="100%",
                        ),
                        width="100%",
                    ),
                    empty_state(),
                ),
                width="100%",
                max_width="1200px",
                margin="0 auto",
                padding="1.5rem",
                spacing="3",
            ),
            width="100%",
            min_height="calc(100vh - 44px)",
            background=rx.cond(AppState.dark_mode, "#0f172a", "#f9fafb"),
        ),
        on_mount=[AppState.load_modules, AppState.load_progress],
        width="100%",
    )
