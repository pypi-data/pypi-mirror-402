"""Module detail page - displays lessons within a module."""

import reflex as rx

from ..components.navbar import navbar
from ..state.app_state import AppState, LessonInfo


def lesson_row(lesson: LessonInfo) -> rx.Component:
    """Create a lesson row component.

    Args:
        lesson: LessonInfo object.

    Returns:
        Lesson row component.
    """
    return rx.link(
        rx.hstack(
            rx.hstack(
                rx.icon(
                    "circle",
                    size=16,
                    color=rx.cond(AppState.dark_mode, "#4b5563", "#d1d5db"),
                ),
                rx.text(
                    f"{lesson.order + 1}.",
                    color=rx.cond(AppState.dark_mode, "#6b7280", "#9ca3af"),
                    font_size="0.8rem",
                    min_width="1.5rem",
                ),
                rx.vstack(
                    rx.text(
                        lesson.title,
                        font_weight="500",
                        font_size="0.85rem",
                        color=rx.cond(AppState.dark_mode, "#f3f4f6", "#1f2937"),
                    ),
                    spacing="0",
                    align="start",
                ),
                spacing="2",
                align="center",
            ),
            rx.spacer(),
            rx.hstack(
                rx.badge("Start", color_scheme="blue", size="1"),
                rx.icon(
                    "chevron-right",
                    size=14,
                    color=rx.cond(AppState.dark_mode, "#6b7280", "#9ca3af"),
                ),
                spacing="2",
                align="center",
            ),
            width="100%",
            padding="0.75rem 1rem",
            background=rx.cond(AppState.dark_mode, "#1e293b", "white"),
            border_radius="0.375rem",
            border=rx.cond(
                AppState.dark_mode,
                "1px solid #374151",
                "1px solid #e5e7eb",
            ),
            _hover={
                "border_color": "#3b82f6",
                "box_shadow": "0 2px 8px rgba(59, 130, 246, 0.1)",
            },
            transition="all 0.2s ease",
            align="center",
        ),
        href=f"/lesson/{AppState.current_module_id}/{lesson.id}",
        _hover={"text_decoration": "none"},
        width="100%",
    )


def module_page() -> rx.Component:
    """Module detail page component.

    Returns:
        Module page component.
    """
    return rx.box(
        navbar(),
        rx.box(
            rx.vstack(
                # Back link
                rx.link(
                    rx.hstack(
                        rx.icon("arrow-left", size=14, color="#3b82f6"),
                        rx.text("Back to Modules", color="#3b82f6", font_size="0.85rem"),
                        spacing="1",
                        align="center",
                    ),
                    href="/",
                    _hover={"opacity": "0.8"},
                ),
                # Module header
                rx.box(
                    rx.vstack(
                        rx.hstack(
                            rx.icon("book-open", size=24, color="#3b82f6"),
                            rx.badge(
                                f"{AppState.current_module_lesson_count} lessons",
                                color_scheme="blue",
                                size="1",
                            ),
                            spacing="2",
                            align="center",
                        ),
                        rx.heading(
                            AppState.current_module_name,
                            size="6",
                            color=rx.cond(AppState.dark_mode, "#f3f4f6", "#1f2937"),
                        ),
                        rx.text(
                            AppState.current_module_description,
                            color=rx.cond(AppState.dark_mode, "#9ca3af", "#6b7280"),
                            font_size="0.9rem",
                        ),
                        spacing="1",
                        align="start",
                        width="100%",
                    ),
                    width="100%",
                    padding_bottom="1rem",
                    border_bottom=rx.cond(
                        AppState.dark_mode,
                        "1px solid #374151",
                        "1px solid #e5e7eb",
                    ),
                ),
                # Lesson list
                rx.vstack(
                    rx.foreach(
                        AppState.current_module_lessons,
                        lesson_row,
                    ),
                    width="100%",
                    spacing="2",
                    padding_top="0.75rem",
                ),
                width="100%",
                max_width="800px",
                margin="0 auto",
                padding="1.5rem",
                spacing="3",
                align="start",
            ),
            width="100%",
            min_height="calc(100vh - 44px)",
            background=rx.cond(AppState.dark_mode, "#0f172a", "#f9fafb"),
        ),
        width="100%",
    )
