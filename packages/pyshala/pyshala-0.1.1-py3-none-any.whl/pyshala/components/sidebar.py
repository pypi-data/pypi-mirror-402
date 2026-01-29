"""Sidebar navigation component for lesson navigation."""

import reflex as rx

from ..state.app_state import AppState, LessonInfo


def lesson_item(
    lesson: LessonInfo,
    module_id: rx.Var[str],
    current_lesson_id: rx.Var[str],
    completed_lessons: rx.Var[list[str]],
) -> rx.Component:
    """Create a single lesson item in the sidebar.

    Args:
        lesson: LessonInfo object.
        module_id: Parent module ID.
        current_lesson_id: Currently active lesson ID.
        completed_lessons: List of completed lesson IDs.

    Returns:
        Lesson item component.
    """
    full_id = module_id + "/" + lesson.id
    is_current = lesson.id == current_lesson_id
    is_completed = completed_lessons.contains(full_id)

    return rx.link(
        rx.hstack(
            rx.cond(
                is_completed,
                rx.icon("circle-check", size=14, color="#10b981"),
                rx.icon(
                    "circle",
                    size=14,
                    color=rx.cond(AppState.dark_mode, "#6b7280", "#9ca3af"),
                ),
            ),
            rx.text(
                lesson.title,
                font_size="0.8rem",
                font_weight=rx.cond(is_current, "600", "400"),
                color=rx.cond(
                    is_current,
                    "#3b82f6",
                    rx.cond(AppState.dark_mode, "#e5e7eb", "#374151"),
                ),
            ),
            spacing="2",
            width="100%",
            padding="0.4rem 0.6rem",
            border_radius="0.375rem",
            background=rx.cond(
                is_current,
                rx.cond(AppState.dark_mode, "rgba(59, 130, 246, 0.2)", "rgba(59, 130, 246, 0.1)"),
                "transparent",
            ),
            _hover={"background": rx.cond(AppState.dark_mode, "rgba(59, 130, 246, 0.15)", "rgba(59, 130, 246, 0.05)")},
        ),
        href="/lesson/" + module_id + "/" + lesson.id,
        width="100%",
        _hover={"text_decoration": "none"},
    )


def sidebar(
    module_name: rx.Var[str],
    lessons: rx.Var[list[LessonInfo]],
    module_id: rx.Var[str],
    current_lesson_id: rx.Var[str],
    completed_lessons: rx.Var[list[str]],
) -> rx.Component:
    """Create the sidebar navigation component.

    Args:
        module_name: Name of the current module.
        lessons: List of LessonInfo objects.
        module_id: Current module ID.
        current_lesson_id: Currently active lesson ID.
        completed_lessons: List of completed lesson IDs.

    Returns:
        Sidebar component.
    """
    return rx.box(
        rx.vstack(
            # Header: different layout for expanded vs collapsed
            rx.cond(
                AppState.sidebar_collapsed == False,
                # Expanded: back arrow, module name, collapse button
                rx.hstack(
                    rx.link(
                        rx.icon("arrow-left", size=16, color="#3b82f6"),
                        href="/",
                    ),
                    rx.text(
                        module_name,
                        font_size="0.8rem",
                        font_weight="600",
                        color=rx.cond(AppState.dark_mode, "#f3f4f6", "#1f2937"),
                        overflow="hidden",
                        text_overflow="ellipsis",
                        white_space="nowrap",
                        flex="1",
                    ),
                    rx.icon_button(
                        rx.icon(
                            "panel-left-close",
                            size=14,
                            color=rx.cond(AppState.dark_mode, "#9ca3af", "inherit"),
                        ),
                        variant="ghost",
                        size="1",
                        on_click=AppState.toggle_sidebar,
                        cursor="pointer",
                    ),
                    spacing="2",
                    align="center",
                    width="100%",
                    padding_bottom="0.5rem",
                    border_bottom=rx.cond(
                        AppState.dark_mode,
                        "1px solid #374151",
                        "1px solid #e5e7eb",
                    ),
                ),
                # Collapsed: only expand button, centered
                rx.hstack(
                    rx.icon_button(
                        rx.icon(
                            "panel-left-open",
                            size=14,
                            color=rx.cond(AppState.dark_mode, "#9ca3af", "inherit"),
                        ),
                        variant="ghost",
                        size="1",
                        on_click=AppState.toggle_sidebar,
                        cursor="pointer",
                    ),
                    justify="center",
                    width="100%",
                    padding_bottom="0.5rem",
                    border_bottom=rx.cond(
                        AppState.dark_mode,
                        "1px solid #374151",
                        "1px solid #e5e7eb",
                    ),
                ),
            ),
            # Lesson list
            rx.cond(
                AppState.sidebar_collapsed == False,
                # Expanded: show full lesson items
                rx.vstack(
                    rx.foreach(
                        lessons,
                        lambda lesson: lesson_item(
                            lesson, module_id, current_lesson_id, completed_lessons
                        ),
                    ),
                    width="100%",
                    spacing="1",
                    padding_top="0.5rem",
                ),
                # Collapsed: show only status icons
                rx.vstack(
                    rx.foreach(
                        lessons,
                        lambda lesson: rx.link(
                            rx.cond(
                                completed_lessons.contains(module_id + "/" + lesson.id),
                                rx.icon("circle-check", size=14, color="#10b981"),
                                rx.cond(
                                    lesson.id == current_lesson_id,
                                    rx.icon("circle-dot", size=14, color="#3b82f6"),
                                    rx.icon(
                                        "circle",
                                        size=14,
                                        color=rx.cond(AppState.dark_mode, "#6b7280", "#9ca3af"),
                                    ),
                                ),
                            ),
                            href="/lesson/" + module_id + "/" + lesson.id,
                            padding="0.4rem",
                            _hover={"background": rx.cond(AppState.dark_mode, "rgba(59, 130, 246, 0.15)", "rgba(59, 130, 246, 0.05)")},
                            border_radius="0.375rem",
                        ),
                    ),
                    spacing="1",
                    align="center",
                    width="100%",
                    padding_top="0.5rem",
                ),
            ),
            width="100%",
            spacing="0",
            align="start",
        ),
        width=rx.cond(AppState.sidebar_collapsed, "52px", "220px"),
        min_width=rx.cond(AppState.sidebar_collapsed, "52px", "220px"),
        height="calc(100vh - 44px)",
        padding="0.75rem",
        background=rx.cond(AppState.dark_mode, "#1e293b", "#fafafa"),
        border_right=rx.cond(
            AppState.dark_mode,
            "1px solid #374151",
            "1px solid #e5e7eb",
        ),
        overflow_y="auto",
        position="sticky",
        top="44px",
        transition="width 0.2s ease, min-width 0.2s ease",
    )
