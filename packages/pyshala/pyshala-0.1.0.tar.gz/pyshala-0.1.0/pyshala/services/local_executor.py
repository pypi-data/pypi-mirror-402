"""Local Python code executor - simpler alternative to Judge0."""

import asyncio
import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from typing import Optional

from ..models.lesson import DataFile


@dataclass
class ExecutionResult:
    """Result of code execution."""

    stdout: str = ""
    stderr: str = ""
    return_code: int = 0
    timed_out: bool = False

    @property
    def is_success(self) -> bool:
        """Check if execution was successful."""
        return self.return_code == 0 and not self.timed_out

    @property
    def error_message(self) -> str:
        """Get error message if any."""
        if self.timed_out:
            return "Execution timed out"
        if self.stderr:
            return self.stderr
        if self.return_code != 0:
            return f"Process exited with code {self.return_code}"
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
    hidden: bool = False


@dataclass
class TestRunResults:
    """Results of running code against all test cases."""

    test_results: list[TestResult] = field(default_factory=list)
    all_passed: bool = False
    total_tests: int = 0
    passed_count: int = 0


class LocalExecutor:
    """Execute Python code locally using subprocess."""

    def __init__(
        self,
        timeout: float = 10.0,
        python_path: Optional[str] = None,
    ):
        """Initialize the local executor.

        Args:
            timeout: Maximum execution time in seconds.
            python_path: Path to Python interpreter. Defaults to 'python3'.
        """
        self.timeout = float(os.getenv("MAX_EXECUTION_TIME", str(timeout)))
        self.python_path = python_path or os.getenv("PYTHON_PATH", "python3")

    async def execute(
        self,
        source_code: str,
        stdin: str = "",
        data_files: Optional[list[DataFile]] = None,
    ) -> ExecutionResult:
        """Execute Python code and return the result.

        Args:
            source_code: Python source code to execute.
            stdin: Standard input for the program.
            data_files: Additional data files to make available.

        Returns:
            ExecutionResult object.
        """
        # Create a temporary directory for execution
        with tempfile.TemporaryDirectory() as tmpdir:
            # Write the source code
            script_path = os.path.join(tmpdir, "script.py")
            with open(script_path, "w") as f:
                f.write(source_code)

            # Write any data files
            if data_files:
                for df in data_files:
                    if df.content:
                        file_path = os.path.join(tmpdir, df.name)
                        # Ensure parent directory exists (for nested paths like "data/file.csv")
                        file_dir = os.path.dirname(file_path)
                        if file_dir:
                            os.makedirs(file_dir, exist_ok=True)
                        # Write as binary since content is loaded as bytes
                        with open(file_path, "wb") as f:
                            f.write(df.content)

            # Run the code
            try:
                process = await asyncio.create_subprocess_exec(
                    self.python_path,
                    script_path,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=tmpdir,
                )

                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(input=stdin.encode()),
                        timeout=self.timeout,
                    )
                    return ExecutionResult(
                        stdout=stdout.decode("utf-8", errors="replace"),
                        stderr=stderr.decode("utf-8", errors="replace"),
                        return_code=process.returncode or 0,
                    )
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()
                    return ExecutionResult(
                        timed_out=True,
                        return_code=-1,
                    )

            except Exception as e:
                return ExecutionResult(
                    stderr=str(e),
                    return_code=-1,
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

            exec_result = await self.execute(
                source_code=source_code,
                stdin=stdin,
                data_files=data_files,
            )

            # Normalize output for comparison (strip trailing whitespace)
            actual = exec_result.stdout.rstrip()
            expected_normalized = expected.rstrip()

            passed = exec_result.is_success and actual == expected_normalized

            test_result = TestResult(
                test_index=i,
                description=description,
                passed=passed,
                stdin=stdin,
                expected_output=expected,
                actual_output=exec_result.stdout,
                error_message=exec_result.error_message if not passed else "",
                hidden=hidden,
            )

            results.test_results.append(test_result)
            if test_result.passed:
                results.passed_count += 1

        results.all_passed = results.passed_count == results.total_tests
        return results


# Global instance
_executor: Optional[LocalExecutor] = None


def get_local_executor() -> LocalExecutor:
    """Get the global local executor instance."""
    global _executor
    if _executor is None:
        _executor = LocalExecutor()
    return _executor
