"""Progress badge component."""

import reflex as rx


def progress_badge(completed: int, total: int) -> rx.Component:
    """Create a progress badge showing completion status.

    Args:
        completed: Number of completed items.
        total: Total number of items.

    Returns:
        Progress badge component.
    """
    is_complete = completed == total
    percentage = (completed / total * 100) if total > 0 else 0

    return rx.hstack(
        rx.cond(
            is_complete,
            rx.icon("circle-check", size=16, color="#10b981"),
            rx.icon("circle", size=16, color="#9ca3af"),
        ),
        rx.text(
            f"{completed}/{total}",
            font_size="0.875rem",
            color=rx.cond(is_complete, "#065f46", "#6b7280"),
        ),
        spacing="1",
        align="center",
    )


def progress_bar(completed: int, total: int) -> rx.Component:
    """Create a progress bar showing completion percentage.

    Args:
        completed: Number of completed items.
        total: Total number of items.

    Returns:
        Progress bar component.
    """
    percentage = (completed / total * 100) if total > 0 else 0

    return rx.vstack(
        rx.hstack(
            rx.text(
                f"{completed} of {total} lessons completed",
                font_size="0.875rem",
                color="#6b7280",
            ),
            rx.spacer(),
            rx.text(
                f"{percentage:.0f}%",
                font_size="0.875rem",
                font_weight="500",
                color="#374151",
            ),
            width="100%",
        ),
        rx.box(
            rx.box(
                width=f"{percentage}%",
                height="100%",
                background="#3b82f6",
                border_radius="9999px",
                transition="width 0.3s ease",
            ),
            width="100%",
            height="8px",
            background="#e5e7eb",
            border_radius="9999px",
            overflow="hidden",
        ),
        width="100%",
        spacing="1",
    )


def completion_status(is_completed: bool) -> rx.Component:
    """Create a completion status indicator.

    Args:
        is_completed: Whether the item is completed.

    Returns:
        Completion status component.
    """
    return rx.cond(
        is_completed,
        rx.badge(
            rx.hstack(
                rx.icon("check", size=12),
                rx.text("Completed"),
                spacing="1",
            ),
            color_scheme="green",
            variant="soft",
            size="1",
        ),
        rx.badge(
            "In Progress",
            color_scheme="gray",
            variant="soft",
            size="1",
        ),
    )
