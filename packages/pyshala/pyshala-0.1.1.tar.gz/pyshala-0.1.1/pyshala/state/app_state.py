"""Application state management."""

from __future__ import annotations

import reflex as rx
from pydantic import BaseModel

from ..services.config_loader import get_app_config
from ..services.local_executor import get_local_executor
from ..services.lesson_loader import get_lesson_loader


class ModuleInfo(BaseModel):
    """Module information for display."""
    id: str = ""
    name: str = ""
    description: str = ""
    order: int = 0
    lesson_count: int = 0
    first_lesson_id: str = ""


class LessonInfo(BaseModel):
    """Lesson information for lists."""
    id: str = ""
    title: str = ""
    description: str = ""
    order: int = 0


class TestCaseInfo(BaseModel):
    """Test case information."""
    stdin: str = ""
    expected_output: str = ""
    description: str = ""
    hidden: bool = False


class TestResultInfo(BaseModel):
    """Test result information."""
    test_index: int = 0
    description: str = ""
    passed: bool = False
    stdin: str = ""
    expected_output: str = ""
    actual_output: str = ""
    error_message: str = ""


class QuestionOptionInfo(BaseModel):
    """Question option for display."""
    id: str = ""
    text: str = ""


class QuestionInfo(BaseModel):
    """Question information for display."""
    id: str = ""
    type: str = ""  # "mcq" or "text"
    text: str = ""
    options: list[QuestionOptionInfo] = []
    multi_select: bool = False


class QuestionResultInfo(BaseModel):
    """Result for a single question."""
    question_id: str = ""
    correct: bool = False
    user_answer: list[str] = []
    correct_answer: list[str] = []


class AppState(rx.State):
    """Global application state."""

    # Module list for home page
    modules: list[ModuleInfo] = []

    # Current module details
    current_module_id: str = ""
    current_module_name: str = ""
    current_module_description: str = ""
    current_module_lesson_count: int = 0
    current_module_lessons: list[LessonInfo] = []

    # Current lesson details
    current_lesson_id: str = ""
    current_lesson_title: str = ""
    current_lesson_description: str = ""
    current_lesson_instructions: str = ""
    current_lesson_order: int = 0
    current_lesson_index: int = 0
    current_lesson_total: int = 0
    current_lesson_test_cases: list[TestCaseInfo] = []

    # Progress tracking
    completed_lessons: list[str] = []

    # Code editor state
    current_code: str = ""
    starter_code: str = ""
    editor_reset_count: int = 0  # Increment to force editor re-mount on reset

    # Test execution state
    is_running: bool = False
    test_results: list[TestResultInfo] = []
    tests_all_passed: bool = False
    tests_passed_count: int = 0
    tests_total_count: int = 0

    # Error handling
    error_message: str = ""

    # UI state
    sidebar_collapsed: bool = False
    dark_mode: bool = False

    # Quiz state
    current_lesson_type: str = "code"  # "code" or "quiz"
    current_questions: list[QuestionInfo] = []
    quiz_responses: dict[str, list[str]] = {}  # {question_id: [selected_answers]}
    quiz_results: dict[str, QuestionResultInfo] = {}  # {question_id: result}
    quiz_submitted: bool = False
    quiz_all_correct: bool = False
    quiz_correct_count: int = 0
    quiz_total_count: int = 0

    # App config (loaded from config.yaml)
    app_title: str = "PyShala"
    app_subtitle: str = "Learn Python, One Lesson at a Time"
    app_description: str = "Interactive lessons with hands-on coding exercises and instant feedback"
    app_about_url: str = "https://github.com/dkedar7/pyshala"
    app_about_text: str = "About"
    app_icon: str = "graduation-cap"

    def load_config(self) -> None:
        """Load app configuration from config.yaml."""
        config = get_app_config()
        self.app_title = config.title
        self.app_subtitle = config.subtitle
        self.app_description = config.description
        self.app_about_url = config.about_url
        self.app_about_text = config.about_text
        self.app_icon = config.icon

    def toggle_theme(self) -> None:
        """Toggle between light and dark theme."""
        self.dark_mode = not self.dark_mode

    def load_modules(self) -> None:
        """Load all modules from the lesson loader."""
        loader = get_lesson_loader()
        modules = loader.get_all_modules()

        self.modules = [
            ModuleInfo(
                id=m.id,
                name=m.name,
                description=m.description,
                order=m.order,
                lesson_count=len(m.lessons),
                first_lesson_id=m.lessons[0].id if m.lessons else "",
            )
            for m in modules
        ]

    def load_progress(self) -> None:
        """Progress is session-based only, no database loading."""
        # Progress resets on browser refresh - each session starts fresh
        # This avoids conflicts between multiple users on shared deployments
        pass

    def _load_module(self, module_id: str) -> None:
        """Load a specific module by ID."""
        # Skip if already on this module
        if self.current_module_id == module_id and self.current_module_lessons:
            return

        loader = get_lesson_loader()
        module = loader.get_module(module_id)

        if module:
            self.current_module_id = module.id
            self.current_module_name = module.name
            self.current_module_description = module.description
            self.current_module_lesson_count = len(module.lessons)
            self.current_module_lessons = [
                LessonInfo(
                    id=lesson.id,
                    title=lesson.title,
                    description=lesson.description,
                    order=lesson.order,
                )
                for lesson in module.lessons
            ]
        else:
            self.current_module_id = ""
            self.current_module_name = ""
            self.current_module_description = ""
            self.current_module_lesson_count = 0
            self.current_module_lessons = []
            self.error_message = f"Module not found: {module_id}"

    def load_lesson_from_route(self) -> None:
        """Load lesson based on URL parameters."""
        # Using router.page.params despite deprecation warning
        # router.url doesn't support dynamic route params yet (Reflex issue #5689)
        module_id = self.router.page.params.get("module_id", "")
        lesson_id = self.router.page.params.get("lesson_id", "")
        if module_id and lesson_id:
            self._load_lesson(module_id, lesson_id)

    def _load_lesson(self, module_id: str, lesson_id: str) -> None:
        """Load a specific lesson by module and lesson ID."""
        # Skip if already on this lesson to preserve user's code and test results
        if self.current_module_id == module_id and self.current_lesson_id == lesson_id:
            return

        loader = get_lesson_loader()
        lesson = loader.get_lesson(module_id, lesson_id)
        module = loader.get_module(module_id)

        if lesson and module:
            # Find lesson index
            lesson_index = 0
            for i, l in enumerate(module.lessons):
                if l.id == lesson_id:
                    lesson_index = i
                    break

            # Set lesson details
            self.current_lesson_id = lesson.id
            self.current_lesson_title = lesson.title
            self.current_lesson_description = lesson.description
            self.current_lesson_instructions = lesson.instructions
            self.current_lesson_order = lesson.order
            self.current_lesson_index = lesson_index
            self.current_lesson_total = len(module.lessons)
            self.current_lesson_test_cases = [
                TestCaseInfo(
                    stdin=tc.stdin,
                    expected_output=tc.expected_output,
                    description=tc.description,
                    hidden=tc.hidden,
                )
                for tc in lesson.test_cases
            ]

            # Set module details
            self.current_module_id = module.id
            self.current_module_name = module.name
            self.current_module_description = module.description
            self.current_module_lessons = [
                LessonInfo(
                    id=l.id,
                    title=l.title,
                    description=l.description,
                    order=l.order,
                )
                for l in module.lessons
            ]

            # Set lesson type
            self.current_lesson_type = lesson.lesson_type

            # Set code editor content (for code lessons)
            self.starter_code = lesson.starter_code
            self.current_code = lesson.starter_code

            # Reset test results
            self.test_results = []
            self.tests_all_passed = False
            self.tests_passed_count = 0
            self.tests_total_count = 0
            self.error_message = ""

            # Load questions for quiz lessons
            self.current_questions = [
                QuestionInfo(
                    id=q.id,
                    type=q.type,
                    text=q.text,
                    options=[
                        QuestionOptionInfo(id=opt.id, text=opt.text)
                        for opt in q.options
                    ],
                    multi_select=q.multi_select,
                )
                for q in lesson.questions
            ]

            # Reset quiz state
            self.quiz_responses = {}
            self.quiz_results = {}
            self.quiz_submitted = False
            self.quiz_all_correct = False
            self.quiz_correct_count = 0
            self.quiz_total_count = 0
        else:
            self.current_lesson_id = ""
            self.current_lesson_title = ""
            self.error_message = f"Lesson not found: {module_id}/{lesson_id}"

    def set_code(self, code: str) -> None:
        """Update the current code in the editor."""
        self.current_code = code

    def toggle_sidebar(self) -> None:
        """Toggle sidebar visibility."""
        self.sidebar_collapsed = not self.sidebar_collapsed

    def reset_code(self) -> None:
        """Reset code to starter code."""
        self.current_code = self.starter_code
        self.editor_reset_count = self.editor_reset_count + 1  # Force editor re-mount
        self.test_results = []
        self.tests_all_passed = False
        self.tests_passed_count = 0
        self.tests_total_count = 0

    def set_mcq_response(self, question_id: str, option_id: str, multi_select: bool) -> None:
        """Handle MCQ option selection."""
        if multi_select:
            # Toggle selection for checkboxes
            current = self.quiz_responses.get(question_id, [])
            if option_id in current:
                current = [x for x in current if x != option_id]
            else:
                current = current + [option_id]
            self.quiz_responses = {**self.quiz_responses, question_id: current}
        else:
            # Replace selection for radio buttons
            self.quiz_responses = {**self.quiz_responses, question_id: [option_id]}

    def set_mcq_response_single(self, question_id: str, option_id: str) -> None:
        """Handle single-select MCQ option selection (radio buttons)."""
        if self.quiz_submitted:
            return
        self.quiz_responses = {**self.quiz_responses, question_id: [option_id]}

    def set_mcq_response_multi(self, question_id: str, option_id: str) -> None:
        """Handle multi-select MCQ option selection (checkboxes)."""
        if self.quiz_submitted:
            return
        current = self.quiz_responses.get(question_id, [])
        if option_id in current:
            current = [x for x in current if x != option_id]
        else:
            current = current + [option_id]
        self.quiz_responses = {**self.quiz_responses, question_id: current}

    def set_text_response(self, question_id: str, value: str) -> None:
        """Handle text input response."""
        self.quiz_responses = {**self.quiz_responses, question_id: [value]}

    def submit_quiz(self) -> None:
        """Validate quiz responses and show results."""
        loader = get_lesson_loader()
        lesson = loader.get_lesson(self.current_module_id, self.current_lesson_id)

        if not lesson:
            return

        results = {}
        correct_count = 0

        for question in lesson.questions:
            user_answer = self.quiz_responses.get(question.id, [])

            if question.type == "mcq":
                # Exact match of selected options
                is_correct = set(user_answer) == set(question.correct)
            else:  # text
                # Case-insensitive match against any acceptable answer
                user_text = user_answer[0].strip().lower() if user_answer else ""
                is_correct = user_text in [ans.strip().lower() for ans in question.correct]

            if is_correct:
                correct_count += 1

            results[question.id] = QuestionResultInfo(
                question_id=question.id,
                correct=is_correct,
                user_answer=user_answer,
                correct_answer=question.correct,
            )

        self.quiz_results = results
        self.quiz_submitted = True
        self.quiz_correct_count = correct_count
        self.quiz_total_count = len(lesson.questions)
        self.quiz_all_correct = correct_count == len(lesson.questions)

        # Mark as completed if all correct
        if self.quiz_all_correct:
            full_id = f"{self.current_module_id}/{self.current_lesson_id}"
            if full_id not in self.completed_lessons:
                self.completed_lessons = self.completed_lessons + [full_id]

    def reset_quiz(self) -> None:
        """Reset quiz state for retry."""
        self.quiz_responses = {}
        self.quiz_results = {}
        self.quiz_submitted = False
        self.quiz_all_correct = False
        self.quiz_correct_count = 0
        self.quiz_total_count = 0

    @rx.event(background=True)
    async def run_code(self) -> None:
        """Execute the current code against test cases."""
        # Check if already running and set running state
        async with self:
            if self.is_running:
                return
            self.is_running = True
            self.test_results = []
            # Capture values needed for the API call
            module_id = self.current_module_id
            lesson_id = self.current_lesson_id
            code = self.current_code
            test_cases_dict = [
                {
                    "stdin": tc.stdin,
                    "expected_output": tc.expected_output,
                    "description": tc.description,
                    "hidden": tc.hidden,
                }
                for tc in self.current_lesson_test_cases
            ]

        try:
            executor = get_local_executor()
            loader = get_lesson_loader()

            # Get lesson for data files
            lesson = loader.get_lesson(module_id, lesson_id)
            data_files = lesson.data_files if lesson else []

            # Run tests (this is the async operation outside state lock)
            results = await executor.run_tests(
                source_code=code,
                test_cases=test_cases_dict,
                data_files=data_files,
            )

            # Store results back in state
            async with self:
                self.test_results = [
                    TestResultInfo(
                        test_index=tr.test_index,
                        description=tr.description,
                        passed=tr.passed,
                        stdin=tr.stdin if not tr.hidden else "[hidden]",
                        expected_output=tr.expected_output if not tr.hidden else "[hidden]",
                        actual_output=tr.actual_output,
                        error_message=tr.error_message,
                    )
                    for tr in results.test_results
                ]
                self.tests_all_passed = results.all_passed
                self.tests_passed_count = results.passed_count
                self.tests_total_count = results.total_tests
                self.is_running = False

                # Mark as completed if all tests pass (session-only, not persisted)
                if results.all_passed and module_id and lesson_id:
                    full_id = f"{module_id}/{lesson_id}"
                    if full_id not in self.completed_lessons:
                        self.completed_lessons = self.completed_lessons + [full_id]

        except Exception as e:
            async with self:
                self.error_message = f"Error running code: {str(e)}"
                self.test_results = []
                self.tests_all_passed = False
                self.tests_passed_count = 0
                self.tests_total_count = 0
                self.is_running = False

    @rx.var
    def has_next_lesson(self) -> bool:
        """Check if there's a next lesson."""
        return self.current_lesson_index < self.current_lesson_total - 1

    @rx.var
    def has_previous_lesson(self) -> bool:
        """Check if there's a previous lesson."""
        return self.current_lesson_index > 0

    @rx.var
    def next_lesson_url(self) -> str:
        """Get the next lesson URL or empty string."""
        if not self.has_next_lesson:
            return ""
        next_idx = self.current_lesson_index + 1
        if next_idx < len(self.current_module_lessons):
            next_lesson = self.current_module_lessons[next_idx]
            return f"/lesson/{self.current_module_id}/{next_lesson.id}"
        return ""

    @rx.var
    def previous_lesson_url(self) -> str:
        """Get the previous lesson URL or empty string."""
        if not self.has_previous_lesson:
            return ""
        prev_idx = self.current_lesson_index - 1
        if prev_idx >= 0 and prev_idx < len(self.current_module_lessons):
            prev_lesson = self.current_module_lessons[prev_idx]
            return f"/lesson/{self.current_module_id}/{prev_lesson.id}"
        return ""

    @rx.var
    def lesson_number(self) -> int:
        """Get the current lesson number (1-indexed)."""
        return self.current_lesson_index + 1

    @rx.var
    def editor_key(self) -> str:
        """Get a unique key for the code editor to force re-mount on lesson change or reset."""
        return f"{self.current_module_id}-{self.current_lesson_id}-{self.editor_reset_count}"

    @rx.var
    def lesson_completed(self) -> bool:
        """Check if the current lesson is completed (code tests passed or quiz all correct)."""
        return self.tests_all_passed or self.quiz_all_correct
