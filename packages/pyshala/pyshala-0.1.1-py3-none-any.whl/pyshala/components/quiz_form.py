"""Quiz form component for MCQ and text questions."""

import reflex as rx

from ..state.app_state import AppState, QuestionInfo, QuestionOptionInfo, QuestionResultInfo


def get_result_for_question(question_id: str) -> QuestionResultInfo | None:
    """Helper to find result for a question."""
    for result in AppState.quiz_results:
        if result.question_id == question_id:
            return result
    return None


def mcq_option_item_single(
    question_id: rx.Var[str],
    option: QuestionOptionInfo,
) -> rx.Component:
    """Single MCQ option for single-select (radio style)."""
    is_selected = AppState.quiz_responses.get(question_id, []).contains(option.id)

    return rx.box(
        rx.hstack(
            rx.box(
                rx.cond(
                    is_selected,
                    rx.box(
                        width="10px",
                        height="10px",
                        border_radius="50%",
                        background="#3b82f6",
                    ),
                    rx.box(),
                ),
                width="18px",
                height="18px",
                border_radius="50%",
                border=rx.cond(
                    is_selected,
                    "2px solid #3b82f6",
                    rx.cond(AppState.dark_mode, "2px solid #6b7280", "2px solid #d1d5db"),
                ),
                display="flex",
                align_items="center",
                justify_content="center",
            ),
            rx.text(
                option.id.upper() + ". " + option.text,
                font_size="0.85rem",
                color=rx.cond(AppState.dark_mode, "#e5e7eb", "#374151"),
            ),
            spacing="2",
            align="center",
            width="100%",
            cursor=rx.cond(AppState.quiz_submitted, "default", "pointer"),
            on_click=AppState.set_mcq_response_single(question_id, option.id),
        ),
        padding="0.5rem",
        border_radius="0.375rem",
        background=rx.cond(
            is_selected,
            rx.cond(AppState.dark_mode, "rgba(59, 130, 246, 0.2)", "rgba(59, 130, 246, 0.1)"),
            "transparent",
        ),
        _hover=rx.cond(
            AppState.quiz_submitted,
            {},
            {"background": rx.cond(AppState.dark_mode, "rgba(59, 130, 246, 0.1)", "rgba(59, 130, 246, 0.05)")},
        ),
        width="100%",
    )


def mcq_option_item_multi(
    question_id: rx.Var[str],
    option: QuestionOptionInfo,
) -> rx.Component:
    """Single MCQ option for multi-select (checkbox style)."""
    is_selected = AppState.quiz_responses.get(question_id, []).contains(option.id)

    return rx.box(
        rx.hstack(
            rx.checkbox(
                checked=is_selected,
                on_change=lambda _: AppState.set_mcq_response_multi(
                    question_id, option.id
                ),
                disabled=AppState.quiz_submitted,
            ),
            rx.text(
                option.id.upper() + ". " + option.text,
                font_size="0.85rem",
                color=rx.cond(AppState.dark_mode, "#e5e7eb", "#374151"),
            ),
            spacing="2",
            align="center",
            width="100%",
        ),
        padding="0.5rem",
        border_radius="0.375rem",
        background=rx.cond(
            is_selected,
            rx.cond(AppState.dark_mode, "rgba(59, 130, 246, 0.2)", "rgba(59, 130, 246, 0.1)"),
            "transparent",
        ),
        _hover=rx.cond(
            AppState.quiz_submitted,
            {},
            {"background": rx.cond(AppState.dark_mode, "rgba(59, 130, 246, 0.1)", "rgba(59, 130, 246, 0.05)")},
        ),
        width="100%",
    )


def result_feedback(question_id: rx.Var[str]) -> rx.Component:
    """Show correct/incorrect feedback after submission."""
    # Get the result for this question from the dictionary
    result = AppState.quiz_results.get(question_id, QuestionResultInfo())

    return rx.cond(
        result.question_id != "",
        rx.cond(
            result.correct,
            rx.hstack(
                rx.icon("circle-check", size=16, color="#10b981"),
                rx.text("Correct!", color="#10b981", font_size="0.8rem", font_weight="500"),
                spacing="1",
                align="center",
                padding="0.5rem",
                background=rx.cond(AppState.dark_mode, "#064e3b", "#d1fae5"),
                border_radius="0.25rem",
                width="100%",
            ),
            rx.vstack(
                rx.hstack(
                    rx.icon("circle-x", size=16, color="#ef4444"),
                    rx.text("Incorrect", color="#ef4444", font_size="0.8rem", font_weight="500"),
                    spacing="1",
                    align="center",
                ),
                rx.text(
                    "Correct answer: " + result.correct_answer.join(", "),
                    color=rx.cond(AppState.dark_mode, "#9ca3af", "#6b7280"),
                    font_size="0.75rem",
                ),
                padding="0.5rem",
                background=rx.cond(AppState.dark_mode, "#7f1d1d", "#fef2f2"),
                border_radius="0.25rem",
                width="100%",
                spacing="1",
                align="start",
            ),
        ),
        rx.fragment(),
    )


def mcq_question(question: QuestionInfo, index: rx.Var[int]) -> rx.Component:
    """MCQ question component."""
    return rx.box(
        rx.vstack(
            rx.text(
                (index + 1).to_string() + ". " + question.text,
                font_weight="500",
                font_size="0.9rem",
                color=rx.cond(AppState.dark_mode, "#f3f4f6", "#1f2937"),
            ),
            rx.cond(
                question.multi_select,
                # Multi-select: use checkbox options
                rx.vstack(
                    rx.foreach(
                        question.options,
                        lambda opt: mcq_option_item_multi(question.id, opt),
                    ),
                    width="100%",
                    spacing="1",
                    padding_left="0.5rem",
                ),
                # Single-select: use radio options
                rx.vstack(
                    rx.foreach(
                        question.options,
                        lambda opt: mcq_option_item_single(question.id, opt),
                    ),
                    width="100%",
                    spacing="1",
                    padding_left="0.5rem",
                ),
            ),
            rx.cond(
                AppState.quiz_submitted,
                result_feedback(question.id),
                rx.fragment(),
            ),
            width="100%",
            spacing="2",
            align="start",
        ),
        padding="1rem",
        background=rx.cond(AppState.dark_mode, "#1e293b", "white"),
        border_radius="0.5rem",
        border=rx.cond(AppState.dark_mode, "1px solid #374151", "1px solid #e5e7eb"),
        width="100%",
    )


def text_question(question: QuestionInfo, index: rx.Var[int]) -> rx.Component:
    """Text input question component."""
    current_value = AppState.quiz_responses.get(question.id, [""])

    return rx.box(
        rx.vstack(
            rx.text(
                (index + 1).to_string() + ". " + question.text,
                font_weight="500",
                font_size="0.9rem",
                color=rx.cond(AppState.dark_mode, "#f3f4f6", "#1f2937"),
            ),
            rx.input(
                placeholder="Type your answer...",
                value=rx.cond(current_value.length() > 0, current_value[0], ""),
                on_change=lambda val: AppState.set_text_response(question.id, val),
                disabled=AppState.quiz_submitted,
                width="100%",
                background=rx.cond(AppState.dark_mode, "#0f172a", "white"),
                color=rx.cond(AppState.dark_mode, "#f3f4f6", "#1f2937"),
                border=rx.cond(AppState.dark_mode, "1px solid #374151", "1px solid #d1d5db"),
            ),
            rx.cond(
                AppState.quiz_submitted,
                result_feedback(question.id),
                rx.fragment(),
            ),
            width="100%",
            spacing="2",
            align="start",
        ),
        padding="1rem",
        background=rx.cond(AppState.dark_mode, "#1e293b", "white"),
        border_radius="0.5rem",
        border=rx.cond(AppState.dark_mode, "1px solid #374151", "1px solid #e5e7eb"),
        width="100%",
    )


def quiz_form() -> rx.Component:
    """Main quiz form component displaying all questions."""
    return rx.vstack(
        rx.foreach(
            AppState.current_questions,
            lambda q, idx: rx.cond(
                q.type == "mcq",
                mcq_question(q, idx),
                text_question(q, idx),
            ),
        ),
        width="100%",
        spacing="3",
    )


def quiz_results_summary() -> rx.Component:
    """Display quiz results summary after submission."""
    return rx.cond(
        AppState.quiz_submitted,
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.text(
                        "Quiz Results",
                        font_weight="600",
                        font_size="0.85rem",
                        color=rx.cond(AppState.dark_mode, "#f3f4f6", "#1f2937"),
                    ),
                    rx.spacer(),
                    rx.badge(
                        AppState.quiz_correct_count.to_string() + "/" + AppState.quiz_total_count.to_string(),
                        color_scheme=rx.cond(AppState.quiz_all_correct, "green", "orange"),
                        size="1",
                    ),
                    width="100%",
                    align="center",
                ),
                rx.cond(
                    AppState.quiz_all_correct,
                    rx.box(
                        rx.hstack(
                            rx.icon("party-popper", size=16, color="#10b981"),
                            rx.text(
                                "All questions correct!",
                                font_weight="500",
                                font_size="0.8rem",
                                color=rx.cond(AppState.dark_mode, "#34d399", "#065f46"),
                            ),
                            spacing="1",
                            align="center",
                        ),
                        padding="0.5rem",
                        background=rx.cond(AppState.dark_mode, "#064e3b", "#d1fae5"),
                        border_radius="0.25rem",
                        border=rx.cond(
                            AppState.dark_mode,
                            "1px solid #065f46",
                            "1px solid #a7f3d0",
                        ),
                        width="100%",
                    ),
                    rx.fragment(),
                ),
                width="100%",
                spacing="2",
            ),
            width="100%",
            padding="0.75rem",
            background=rx.cond(AppState.dark_mode, "#1e293b", "white"),
            border_radius="0.375rem",
            box_shadow="0 1px 2px rgba(0, 0, 0, 0.05)",
        ),
        rx.fragment(),
    )
