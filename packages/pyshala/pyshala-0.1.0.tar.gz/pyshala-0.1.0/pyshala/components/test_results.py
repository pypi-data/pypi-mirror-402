"""Test results display component."""

import reflex as rx

from ..state.app_state import AppState, TestResultInfo


def test_result_item(result: TestResultInfo) -> rx.Component:
    """Create a single test result item.

    Args:
        result: TestResultInfo object.

    Returns:
        Test result item component.
    """
    return rx.box(
        rx.vstack(
            # Header with pass/fail
            rx.hstack(
                rx.cond(
                    result.passed,
                    rx.icon("circle-check", size=16, color="#10b981"),
                    rx.icon("circle-x", size=16, color="#ef4444"),
                ),
                rx.text(
                    result.description,
                    font_weight="500",
                    font_size="0.8rem",
                    color=rx.cond(
                        result.passed,
                        rx.cond(AppState.dark_mode, "#34d399", "#065f46"),
                        rx.cond(AppState.dark_mode, "#fca5a5", "#991b1b"),
                    ),
                ),
                rx.spacer(),
                rx.badge(
                    rx.cond(result.passed, "PASSED", "FAILED"),
                    color_scheme=rx.cond(result.passed, "green", "red"),
                    size="1",
                ),
                width="100%",
                align="center",
            ),
            # Show details on failure
            rx.cond(
                ~result.passed,
                rx.vstack(
                    # Expected output
                    rx.cond(
                        result.expected_output != "",
                        rx.box(
                            rx.text(
                                "Expected:",
                                font_size="0.7rem",
                                color=rx.cond(AppState.dark_mode, "#9ca3af", "#6b7280"),
                                margin_bottom="0.125rem",
                            ),
                            rx.code(
                                result.expected_output,
                                display="block",
                                white_space="pre-wrap",
                                padding="0.375rem",
                                background=rx.cond(AppState.dark_mode, "#064e3b", "#f0fdf4"),
                                border_radius="0.25rem",
                                font_size="0.7rem",
                                color=rx.cond(AppState.dark_mode, "#a7f3d0", "inherit"),
                                width="100%",
                            ),
                            width="100%",
                        ),
                        rx.fragment(),
                    ),
                    # Actual output
                    rx.cond(
                        result.actual_output != "",
                        rx.box(
                            rx.text(
                                "Your output:",
                                font_size="0.7rem",
                                color=rx.cond(AppState.dark_mode, "#9ca3af", "#6b7280"),
                                margin_bottom="0.125rem",
                            ),
                            rx.code(
                                result.actual_output,
                                display="block",
                                white_space="pre-wrap",
                                padding="0.375rem",
                                background=rx.cond(AppState.dark_mode, "#7f1d1d", "#fef2f2"),
                                border_radius="0.25rem",
                                font_size="0.7rem",
                                color=rx.cond(AppState.dark_mode, "#fecaca", "inherit"),
                                width="100%",
                            ),
                            width="100%",
                        ),
                        rx.fragment(),
                    ),
                    # Error message
                    rx.cond(
                        result.error_message != "",
                        rx.box(
                            rx.text(
                                "Error:",
                                font_size="0.7rem",
                                color=rx.cond(AppState.dark_mode, "#9ca3af", "#6b7280"),
                                margin_bottom="0.125rem",
                            ),
                            rx.code(
                                result.error_message,
                                display="block",
                                white_space="pre-wrap",
                                padding="0.375rem",
                                background=rx.cond(AppState.dark_mode, "#7f1d1d", "#fef2f2"),
                                border_radius="0.25rem",
                                font_size="0.7rem",
                                color=rx.cond(AppState.dark_mode, "#fca5a5", "#991b1b"),
                                width="100%",
                            ),
                            width="100%",
                        ),
                        rx.fragment(),
                    ),
                    width="100%",
                    spacing="1",
                    padding_top="0.375rem",
                ),
                rx.fragment(),
            ),
            width="100%",
            spacing="1",
        ),
        padding="0.5rem",
        background=rx.cond(
            result.passed,
            rx.cond(AppState.dark_mode, "#064e3b", "#f0fdf4"),
            rx.cond(AppState.dark_mode, "#7f1d1d", "#fef2f2"),
        ),
        border_radius="0.25rem",
        border=rx.cond(
            result.passed,
            rx.cond(AppState.dark_mode, "1px solid #065f46", "1px solid #bbf7d0"),
            rx.cond(AppState.dark_mode, "1px solid #991b1b", "1px solid #fecaca"),
        ),
        width="100%",
    )


def test_results(
    results: rx.Var[list[TestResultInfo]],
    is_running: rx.Var[bool],
    all_passed: rx.Var[bool],
    passed_count: rx.Var[int],
    total_count: rx.Var[int],
) -> rx.Component:
    """Create the test results display component.

    Args:
        results: List of TestResultInfo objects.
        is_running: Whether tests are currently running.
        all_passed: Whether all tests passed.
        passed_count: Number of passed tests.
        total_count: Total number of tests.

    Returns:
        Test results component.
    """
    return rx.box(
        rx.vstack(
            # Header
            rx.hstack(
                rx.text(
                    "Test Results",
                    font_weight="600",
                    font_size="0.85rem",
                    color=rx.cond(AppState.dark_mode, "#f3f4f6", "#1f2937"),
                ),
                rx.spacer(),
                rx.cond(
                    is_running,
                    rx.hstack(
                        rx.spinner(size="1"),
                        rx.text(
                            "Running...",
                            color=rx.cond(AppState.dark_mode, "#9ca3af", "#6b7280"),
                            font_size="0.75rem",
                        ),
                        spacing="1",
                    ),
                    rx.cond(
                        total_count > 0,
                        rx.badge(
                            passed_count.to_string() + "/" + total_count.to_string(),
                            color_scheme=rx.cond(all_passed, "green", "orange"),
                            size="1",
                        ),
                        rx.fragment(),
                    ),
                ),
                width="100%",
                align="center",
            ),
            # Results list or placeholder
            rx.cond(
                is_running,
                rx.center(
                    rx.vstack(
                        rx.spinner(size="2"),
                        rx.text(
                            "Executing...",
                            color=rx.cond(AppState.dark_mode, "#9ca3af", "#6b7280"),
                            font_size="0.75rem",
                        ),
                        spacing="1",
                    ),
                    padding="1rem",
                    width="100%",
                ),
                rx.cond(
                    total_count > 0,
                    rx.vstack(
                        rx.foreach(
                            results,
                            test_result_item,
                        ),
                        width="100%",
                        spacing="1",
                    ),
                    rx.center(
                        rx.vstack(
                            rx.icon(
                                "circle-play",
                                size=24,
                                color=rx.cond(AppState.dark_mode, "#6b7280", "#9ca3af"),
                            ),
                            rx.text(
                                "Click 'Run Code' to test your solution",
                                color=rx.cond(AppState.dark_mode, "#9ca3af", "#6b7280"),
                                font_size="0.75rem",
                            ),
                            spacing="1",
                            align="center",
                        ),
                        padding="1rem",
                        width="100%",
                    ),
                ),
            ),
            # Success message
            rx.cond(
                all_passed & (total_count > 0) & ~is_running,
                rx.box(
                    rx.hstack(
                        rx.icon("party-popper", size=16, color="#10b981"),
                        rx.text(
                            "All tests passed!",
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
                    margin_top="0.25rem",
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
    )
