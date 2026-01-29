"""Code editor component using Monaco editor."""

import reflex as rx
from reflex_monaco import monaco

from ..state.app_state import AppState


def code_editor(
    code: str,
    on_change: rx.EventHandler,
    height: str = "400px",
    editor_key: str = "",
) -> rx.Component:
    """Create a code editor component.

    Args:
        code: Current code content.
        on_change: Event handler for code changes.
        height: Editor height.
        editor_key: Unique key to force re-mount on lesson change.

    Returns:
        Code editor component.
    """
    return rx.box(
        monaco(
            key=editor_key,
            default_value=code,
            default_language="python",
            theme=rx.cond(AppState.dark_mode, "vs-dark", "vs-light"),
            on_change=on_change,
            height=height,
            width="100%",
        ),
        width="100%",
        border_radius="0.375rem",
        overflow="hidden",
        box_shadow="0 1px 2px rgba(0, 0, 0, 0.08)",
    )


def editor_toolbar(
    on_run: rx.EventHandler,
    on_reset: rx.EventHandler,
    is_running: rx.Var[bool],
) -> rx.Component:
    """Create the editor toolbar with run and reset buttons.

    Args:
        on_run: Event handler for run button.
        on_reset: Event handler for reset button.
        is_running: Whether code is currently being executed.

    Returns:
        Toolbar component.
    """
    return rx.hstack(
        rx.button(
            rx.cond(
                is_running,
                rx.hstack(
                    rx.spinner(size="1"),
                    rx.text("Running...", font_size="0.8rem"),
                    spacing="1",
                ),
                rx.hstack(
                    rx.icon("send", size=14),
                    rx.text("Submit", font_size="0.8rem"),
                    spacing="1",
                ),
            ),
            on_click=on_run,
            disabled=is_running,
            color_scheme="green",
            size="1",
            cursor=rx.cond(is_running, "not-allowed", "pointer"),
        ),
        rx.button(
            rx.hstack(
                rx.icon("rotate-ccw", size=14),
                rx.text("Reset", font_size="0.8rem"),
                spacing="1",
            ),
            on_click=on_reset,
            disabled=is_running,
            variant="outline",
            color_scheme="gray",
            size="1",
            color=rx.cond(AppState.dark_mode, "#d1d5db", "#374151"),
            border_color=rx.cond(AppState.dark_mode, "#4b5563", "#9ca3af"),
        ),
        spacing="2",
        width="100%",
        justify="start",
        padding_y="0.5rem",
    )
