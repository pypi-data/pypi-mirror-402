"""Judge0 API client for code execution."""

import asyncio
import base64
import io
import os
import zipfile
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional

import httpx

from ..models.lesson import DataFile


class SubmissionStatus(IntEnum):
    """Judge0 submission status codes."""

    IN_QUEUE = 1
    PROCESSING = 2
    ACCEPTED = 3
    WRONG_ANSWER = 4
    TIME_LIMIT_EXCEEDED = 5
    COMPILATION_ERROR = 6
    RUNTIME_ERROR_SIGSEGV = 7
    RUNTIME_ERROR_SIGXFSZ = 8
    RUNTIME_ERROR_SIGFPE = 9
    RUNTIME_ERROR_SIGABRT = 10
    RUNTIME_ERROR_NZEC = 11
    RUNTIME_ERROR_OTHER = 12
    INTERNAL_ERROR = 13
    EXEC_FORMAT_ERROR = 14


@dataclass
class ExecutionResult:
    """Result of code execution."""

    status_id: int
    status_description: str
    stdout: str = ""
    stderr: str = ""
    compile_output: str = ""
    message: str = ""
    time: Optional[float] = None
    memory: Optional[int] = None

    @property
    def is_accepted(self) -> bool:
        """Check if execution was accepted (ran without errors)."""
        return self.status_id == SubmissionStatus.ACCEPTED

    @property
    def is_pending(self) -> bool:
        """Check if execution is still pending."""
        return self.status_id in (
            SubmissionStatus.IN_QUEUE,
            SubmissionStatus.PROCESSING,
        )

    @property
    def is_error(self) -> bool:
        """Check if execution resulted in an error."""
        return self.status_id >= SubmissionStatus.COMPILATION_ERROR

    @property
    def error_message(self) -> str:
        """Get a human-readable error message."""
        if self.compile_output:
            return f"Compilation Error:\n{self.compile_output}"
        if self.stderr:
            return f"Error:\n{self.stderr}"
        if self.message:
            return self.message
        if self.is_error:
            return f"Execution failed: {self.status_description}"
        return ""


@dataclass
class TestResult:
    """Result of running code against a single test case."""

    test_index: int
    description: str
    passed: bool
    stdin: str = ""
    expected_output: str = ""
    actual_output: str = ""
    error_message: str = ""
    execution_time: Optional[float] = None
    memory_used: Optional[int] = None
    hidden: bool = False


@dataclass
class TestRunResults:
    """Results of running code against all test cases."""

    test_results: list[TestResult] = field(default_factory=list)
    all_passed: bool = False
    total_tests: int = 0
    passed_count: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "test_results": [
                {
                    "test_index": tr.test_index,
                    "description": tr.description,
                    "passed": tr.passed,
                    "stdin": tr.stdin if not tr.hidden else "[hidden]",
                    "expected_output": (
                        tr.expected_output if not tr.hidden else "[hidden]"
                    ),
                    "actual_output": tr.actual_output,
                    "error_message": tr.error_message,
                    "execution_time": tr.execution_time,
                    "memory_used": tr.memory_used,
                }
                for tr in self.test_results
            ],
            "all_passed": self.all_passed,
            "total_tests": self.total_tests,
            "passed_count": self.passed_count,
        }


class Judge0Client:
    """Client for Judge0 code execution API."""

    # Python 3 language ID in Judge0
    PYTHON3_LANGUAGE_ID = 71

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        max_execution_time: float = 10.0,
        max_memory_kb: int = 128000,
    ):
        """Initialize the Judge0 client.

        Args:
            base_url: Judge0 API base URL.
                     Defaults to JUDGE0_URL env var or http://localhost:2358
            timeout: HTTP request timeout in seconds.
            max_execution_time: Maximum code execution time in seconds.
            max_memory_kb: Maximum memory allocation in kilobytes.
        """
        self.base_url = (
            base_url
            or os.getenv("JUDGE0_URL", "http://localhost:2358")
        ).rstrip("/")
        self.timeout = timeout
        self.max_execution_time = float(
            os.getenv("MAX_EXECUTION_TIME", str(max_execution_time))
        )
        self.max_memory_kb = int(
            os.getenv("MAX_MEMORY_KB", str(max_memory_kb))
        )

    def _create_additional_files_zip(
        self, data_files: list[DataFile]
    ) -> Optional[str]:
        """Create a base64-encoded ZIP of additional files.

        Args:
            data_files: List of DataFile objects.

        Returns:
            Base64-encoded ZIP content or None if no files.
        """
        if not data_files:
            return None

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(
            zip_buffer, "w", zipfile.ZIP_DEFLATED
        ) as zip_file:
            for df in data_files:
                if df.content:
                    zip_file.writestr(df.name, df.content)

        zip_buffer.seek(0)
        return base64.b64encode(zip_buffer.read()).decode("utf-8")

    async def submit_code(
        self,
        source_code: str,
        stdin: str = "",
        data_files: Optional[list[DataFile]] = None,
    ) -> str:
        """Submit code for execution and return the submission token.

        Args:
            source_code: Python source code to execute.
            stdin: Standard input for the program.
            data_files: Additional files to include.

        Returns:
            Submission token string.

        Raises:
            httpx.HTTPError: If the API request fails.
        """
        payload = {
            "source_code": base64.b64encode(
                source_code.encode("utf-8")
            ).decode("utf-8"),
            "language_id": self.PYTHON3_LANGUAGE_ID,
            "stdin": base64.b64encode(stdin.encode("utf-8")).decode("utf-8"),
            "cpu_time_limit": self.max_execution_time,
            "memory_limit": self.max_memory_kb,
        }

        # Add additional files if present
        if data_files:
            additional_files = self._create_additional_files_zip(data_files)
            if additional_files:
                payload["additional_files"] = additional_files

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/submissions",
                json=payload,
                params={"base64_encoded": "true"},
            )
            response.raise_for_status()
            return response.json()["token"]

    async def get_submission(self, token: str) -> ExecutionResult:
        """Get the result of a submission.

        Args:
            token: Submission token.

        Returns:
            ExecutionResult object.

        Raises:
            httpx.HTTPError: If the API request fails.
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/submissions/{token}",
                params={"base64_encoded": "true"},
            )
            response.raise_for_status()
            data = response.json()

        # Decode base64 fields
        def decode_field(value: Optional[str]) -> str:
            if not value:
                return ""
            try:
                return base64.b64decode(value).decode("utf-8")
            except Exception:
                return value

        status = data.get("status", {})

        return ExecutionResult(
            status_id=status.get("id", 0),
            status_description=status.get("description", "Unknown"),
            stdout=decode_field(data.get("stdout")),
            stderr=decode_field(data.get("stderr")),
            compile_output=decode_field(data.get("compile_output")),
            message=decode_field(data.get("message")),
            time=float(data["time"]) if data.get("time") else None,
            memory=int(data["memory"]) if data.get("memory") else None,
        )

    async def execute_and_wait(
        self,
        source_code: str,
        stdin: str = "",
        data_files: Optional[list[DataFile]] = None,
        poll_interval: float = 0.5,
        max_wait: float = 60.0,
    ) -> ExecutionResult:
        """Submit code and wait for the result.

        Args:
            source_code: Python source code to execute.
            stdin: Standard input for the program.
            data_files: Additional files to include.
            poll_interval: Time between status checks in seconds.
            max_wait: Maximum time to wait for completion in seconds.

        Returns:
            ExecutionResult object.
        """
        token = await self.submit_code(source_code, stdin, data_files)

        elapsed = 0.0
        while elapsed < max_wait:
            result = await self.get_submission(token)
            if not result.is_pending:
                return result
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        # Timeout
        return ExecutionResult(
            status_id=SubmissionStatus.TIME_LIMIT_EXCEEDED,
            status_description="Execution timed out waiting for results",
        )

    async def run_tests(
        self,
        source_code: str,
        test_cases: list[dict],
        data_files: Optional[list[DataFile]] = None,
    ) -> TestRunResults:
        """Run code against multiple test cases.

        Args:
            source_code: Python source code to execute.
            test_cases: List of test case dictionaries with stdin,
                       expected_output, description, and hidden.
            data_files: Additional files to include.

        Returns:
            TestRunResults object.
        """
        results = TestRunResults(total_tests=len(test_cases))

        for i, tc in enumerate(test_cases):
            stdin = tc.get("stdin", "")
            expected = tc.get("expected_output", "")
            description = tc.get("description", f"Test {i + 1}")
            hidden = tc.get("hidden", False)

            try:
                exec_result = await self.execute_and_wait(
                    source_code=source_code,
                    stdin=stdin,
                    data_files=data_files,
                )

                # Normalize output for comparison (strip trailing whitespace)
                actual = exec_result.stdout.rstrip()
                expected_normalized = expected.rstrip()

                passed = (
                    exec_result.is_accepted
                    and actual == expected_normalized
                )

                test_result = TestResult(
                    test_index=i,
                    description=description,
                    passed=passed,
                    stdin=stdin,
                    expected_output=expected,
                    actual_output=exec_result.stdout,
                    error_message=exec_result.error_message if not passed else "",
                    execution_time=exec_result.time,
                    memory_used=exec_result.memory,
                    hidden=hidden,
                )

            except Exception as e:
                test_result = TestResult(
                    test_index=i,
                    description=description,
                    passed=False,
                    stdin=stdin,
                    expected_output=expected,
                    actual_output="",
                    error_message=f"Execution failed: {str(e)}",
                    hidden=hidden,
                )

            results.test_results.append(test_result)
            if test_result.passed:
                results.passed_count += 1

        results.all_passed = results.passed_count == results.total_tests

        return results


# Global instance
_client: Optional[Judge0Client] = None


def get_judge0_client() -> Judge0Client:
    """Get the global Judge0 client instance."""
    global _client
    if _client is None:
        _client = Judge0Client()
    return _client
