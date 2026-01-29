"""Quiz toolbar component with Submit and Try Again buttons."""

import reflex as rx

from ..state.app_state import AppState


def quiz_toolbar() -> rx.Component:
    """Toolbar for quiz lessons with Submit and Try Again buttons."""
    return rx.hstack(
        rx.button(
            rx.hstack(
                rx.icon("send", size=14),
                rx.text("Submit", font_size="0.8rem"),
                spacing="1",
            ),
            on_click=AppState.submit_quiz,
            disabled=AppState.quiz_submitted,
            color_scheme="green",
            size="1",
            cursor=rx.cond(AppState.quiz_submitted, "not-allowed", "pointer"),
        ),
        rx.cond(
            AppState.quiz_submitted,
            rx.button(
                rx.hstack(
                    rx.icon("rotate-ccw", size=14),
                    rx.text("Try Again", font_size="0.8rem"),
                    spacing="1",
                ),
                on_click=AppState.reset_quiz,
                variant="outline",
                color_scheme="gray",
                size="1",
                color=rx.cond(AppState.dark_mode, "#d1d5db", "#374151"),
                border_color=rx.cond(AppState.dark_mode, "#4b5563", "#9ca3af"),
            ),
            rx.fragment(),
        ),
        spacing="2",
        width="100%",
        justify="start",
        padding_y="0.5rem",
    )
