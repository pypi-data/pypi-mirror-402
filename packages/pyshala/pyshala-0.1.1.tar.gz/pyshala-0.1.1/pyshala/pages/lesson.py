"""Lesson viewer page - displays lesson content and code editor."""

import reflex as rx

from ..components.code_editor import code_editor, editor_toolbar
from ..components.lesson_content import lesson_content, lesson_header
from ..components.navbar import navbar
from ..components.quiz_form import quiz_form, quiz_results_summary
from ..components.quiz_toolbar import quiz_toolbar
from ..components.sidebar import sidebar
from ..components.test_results import test_results
from ..state.app_state import AppState


def lesson_navigation() -> rx.Component:
    """Create the lesson navigation buttons.

    Returns:
        Navigation component.
    """
    return rx.hstack(
        rx.cond(
            AppState.has_previous_lesson,
            rx.link(
                rx.button(
                    rx.hstack(
                        rx.icon("arrow-left", size=14),
                        rx.text("Previous", font_size="0.8rem"),
                        spacing="1",
                    ),
                    variant="outline",
                    color_scheme="gray",
                    size="1",
                ),
                href=AppState.previous_lesson_url,
            ),
            rx.box(),
        ),
        rx.spacer(),
        rx.cond(
            AppState.lesson_completed & AppState.has_next_lesson,
            rx.link(
                rx.button(
                    rx.hstack(
                        rx.text("Next Lesson", font_size="0.8rem"),
                        rx.icon("arrow-right", size=14),
                        spacing="1",
                    ),
                    color_scheme="green",
                    size="1",
                ),
                href=AppState.next_lesson_url,
            ),
            rx.cond(
                AppState.has_next_lesson,
                rx.button(
                    rx.hstack(
                        rx.text("Next Lesson", font_size="0.8rem"),
                        rx.icon("arrow-right", size=14),
                        spacing="1",
                    ),
                    variant="outline",
                    color_scheme="gray",
                    size="1",
                    disabled=True,
                ),
                rx.box(),
            ),
        ),
        width="100%",
        padding_y="0.5rem",
    )


def lesson_page() -> rx.Component:
    """Lesson viewer page component.

    Returns:
        Lesson page component.
    """
    return rx.box(
        navbar(),
        rx.hstack(
            # Sidebar
            sidebar(
                module_name=AppState.current_module_name,
                lessons=AppState.current_module_lessons,
                module_id=AppState.current_module_id,
                current_lesson_id=AppState.current_lesson_id,
                completed_lessons=AppState.completed_lessons,
            ),
            # Main content area
            rx.box(
                rx.hstack(
                    # Left column - Instructions
                    rx.box(
                        rx.vstack(
                            lesson_header(
                                title=AppState.current_lesson_title,
                                description=AppState.current_lesson_description,
                                lesson_number=AppState.lesson_number,
                                total_lessons=AppState.current_lesson_total,
                            ),
                            lesson_content(AppState.current_lesson_instructions),
                            width="100%",
                            spacing="2",
                            align="start",
                        ),
                        width="50%",
                        padding="0.75rem",
                        overflow_y="auto",
                        height="calc(100vh - 44px)",
                        background=rx.cond(AppState.dark_mode, "#0f172a", "white"),
                    ),
                    # Right column - Code editor/Quiz and results
                    rx.box(
                        rx.cond(
                            AppState.current_lesson_type == "quiz",
                            # Quiz content
                            rx.vstack(
                                quiz_toolbar(),
                                quiz_form(),
                                quiz_results_summary(),
                                lesson_navigation(),
                                width="100%",
                                spacing="2",
                                align="start",
                            ),
                            # Code content
                            rx.vstack(
                                editor_toolbar(
                                    on_run=AppState.run_code,
                                    on_reset=AppState.reset_code,
                                    is_running=AppState.is_running,
                                ),
                                code_editor(
                                    code=AppState.current_code,
                                    on_change=AppState.set_code,
                                    height="280px",
                                    editor_key=AppState.editor_key,
                                ),
                                test_results(
                                    results=AppState.test_results,
                                    is_running=AppState.is_running,
                                    all_passed=AppState.tests_all_passed,
                                    passed_count=AppState.tests_passed_count,
                                    total_count=AppState.tests_total_count,
                                ),
                                lesson_navigation(),
                                width="100%",
                                spacing="2",
                                align="start",
                            ),
                        ),
                        width="50%",
                        padding="0.75rem",
                        overflow_y="auto",
                        height="calc(100vh - 44px)",
                        background=rx.cond(AppState.dark_mode, "#1e293b", "#f9fafb"),
                    ),
                    width="100%",
                    spacing="0",
                    align="start",
                ),
                flex="1",
                width="100%",
            ),
            width="100%",
            spacing="0",
            align="start",
        ),
        width="100%",
        height="100vh",
        overflow="hidden",
    )
