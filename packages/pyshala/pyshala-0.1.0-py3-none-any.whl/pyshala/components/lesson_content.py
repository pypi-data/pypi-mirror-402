"""Lesson content display component for Markdown instructions."""

import reflex as rx

from ..state.app_state import AppState


def lesson_content(instructions: str) -> rx.Component:
    """Create a lesson content component for displaying instructions.

    Args:
        instructions: Markdown content for the lesson.

    Returns:
        Lesson content component.
    """
    return rx.box(
        rx.markdown(
            instructions,
            component_map={
                "h1": lambda text: rx.heading(
                    text,
                    size="4",
                    margin_bottom="0.5rem",
                    color=rx.cond(AppState.dark_mode, "#f3f4f6", "#1f2937"),
                ),
                "h2": lambda text: rx.heading(
                    text,
                    size="3",
                    margin_top="0.75rem",
                    margin_bottom="0.375rem",
                    color=rx.cond(AppState.dark_mode, "#e5e7eb", "#374151"),
                ),
                "h3": lambda text: rx.heading(
                    text,
                    size="2",
                    margin_top="0.5rem",
                    margin_bottom="0.25rem",
                    color=rx.cond(AppState.dark_mode, "#d1d5db", "#4b5563"),
                ),
                "p": lambda text: rx.text(
                    text,
                    margin_bottom="0.375rem",
                    line_height="1.5",
                    color=rx.cond(AppState.dark_mode, "#d1d5db", "#374151"),
                    font_size="0.8rem",
                ),
                "code": lambda text: rx.code(
                    text,
                    color=rx.cond(AppState.dark_mode, "#f472b6", "#c7254e"),
                    background=rx.cond(AppState.dark_mode, "#374151", "#f9f2f4"),
                    padding="0.05rem 0.15rem",
                    border_radius="0.15rem",
                    font_size="0.75rem",
                ),
                "ul": lambda children: rx.box(
                    children,
                    as_="ul",
                    padding_left="1rem",
                    margin_bottom="0.375rem",
                    font_size="0.8rem",
                    color=rx.cond(AppState.dark_mode, "#d1d5db", "#374151"),
                ),
                "ol": lambda children: rx.box(
                    children,
                    as_="ol",
                    padding_left="1rem",
                    margin_bottom="0.375rem",
                    font_size="0.8rem",
                    color=rx.cond(AppState.dark_mode, "#d1d5db", "#374151"),
                ),
                "li": lambda text: rx.box(
                    text,
                    as_="li",
                    margin_bottom="0.125rem",
                    line_height="1.4",
                    color=rx.cond(AppState.dark_mode, "#d1d5db", "#374151"),
                ),
                "table": lambda children: rx.box(
                    children,
                    as_="table",
                    width="100%",
                    margin_y="0.5rem",
                    border_collapse="collapse",
                    font_size="0.75rem",
                ),
                "thead": lambda children: rx.box(
                    children,
                    as_="thead",
                    background=rx.cond(AppState.dark_mode, "#374151", "#f3f4f6"),
                ),
                "tbody": lambda children: rx.box(
                    children,
                    as_="tbody",
                ),
                "tr": lambda children: rx.box(
                    children,
                    as_="tr",
                    border_bottom=rx.cond(
                        AppState.dark_mode,
                        "1px solid #4b5563",
                        "1px solid #e5e7eb",
                    ),
                ),
                "th": lambda text: rx.box(
                    text,
                    as_="th",
                    padding="0.375rem 0.5rem",
                    text_align="left",
                    font_weight="600",
                    color=rx.cond(AppState.dark_mode, "#f3f4f6", "#1f2937"),
                ),
                "td": lambda text: rx.box(
                    text,
                    as_="td",
                    padding="0.375rem 0.5rem",
                    color=rx.cond(AppState.dark_mode, "#d1d5db", "#374151"),
                ),
            },
        ),
        width="100%",
        padding="0.75rem",
        background=rx.cond(AppState.dark_mode, "#1e293b", "white"),
        border_radius="0.375rem",
        box_shadow="0 1px 2px rgba(0, 0, 0, 0.05)",
    )


def lesson_header(
    title: str, description: str, lesson_number: int, total_lessons: int
) -> rx.Component:
    """Create the lesson header component.

    Args:
        title: Lesson title.
        description: Lesson description.
        lesson_number: Current lesson number (1-indexed).
        total_lessons: Total number of lessons in module.

    Returns:
        Lesson header component.
    """
    return rx.vstack(
        rx.hstack(
            rx.badge(
                f"Lesson {lesson_number} of {total_lessons}",
                color_scheme="blue",
                size="1",
            ),
            width="100%",
        ),
        rx.heading(
            title,
            size="3",
            color=rx.cond(AppState.dark_mode, "#f3f4f6", "#1f2937"),
        ),
        rx.cond(
            description != "",
            rx.text(
                description,
                color=rx.cond(AppState.dark_mode, "#9ca3af", "#6b7280"),
                font_size="0.75rem",
            ),
            rx.fragment(),
        ),
        width="100%",
        spacing="1",
        align="start",
        padding_bottom="0.5rem",
        border_bottom=rx.cond(
            AppState.dark_mode,
            "1px solid #374151",
            "1px solid #e5e7eb",
        ),
        margin_bottom="0.5rem",
    )
