"""PyShala application class for programmatic usage."""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional


class PyShala:
    """PyShala application for running interactive Python lessons.

    Example usage:
        ```python
        from pyshala import PyShala

        app = PyShala(lessons_path="./my_lessons")
        app.run()
        ```
    """

    def __init__(
        self,
        lessons_path: str = "./lessons",
        host: str = "0.0.0.0",
        port: int = 3000,
        backend_port: int = 8000,
        max_execution_time: float = 10.0,
        python_path: Optional[str] = None,
        loglevel: str = "info",
        app_name: str = "Learn Python",
        app_description: str = "Interactive lessons with hands-on coding exercises and instant feedback",
    ):
        """Initialize the PyShala application.

        Args:
            lessons_path: Path to the directory containing lesson YAML files.
            host: Host address to bind the frontend server.
            port: Port for the frontend server.
            backend_port: Port for the backend API server.
            max_execution_time: Maximum time in seconds for code execution.
            python_path: Path to Python interpreter for code execution.
                        Defaults to the current Python interpreter.
            loglevel: Logging level (debug, info, warning, error).
            app_name: Application name displayed in the UI.
            app_description: Application description displayed on the home page.
        """
        self.lessons_path = str(Path(lessons_path).resolve())
        self.host = host
        self.port = port
        self.backend_port = backend_port
        self.max_execution_time = max_execution_time
        self.python_path = python_path or sys.executable
        self.loglevel = loglevel
        self.app_name = app_name
        self.app_description = app_description

        # Validate lessons path
        if not Path(self.lessons_path).exists():
            raise ValueError(f"Lessons path does not exist: {self.lessons_path}")

    def _setup_environment(self) -> dict:
        """Set up environment variables for the app."""
        env = os.environ.copy()
        env["LESSONS_PATH"] = self.lessons_path
        env["MAX_EXECUTION_TIME"] = str(self.max_execution_time)
        env["PYTHON_PATH"] = self.python_path
        env["APP_NAME"] = self.app_name
        env["APP_DESCRIPTION"] = self.app_description
        return env

    def _get_pyshala_dir(self) -> Path:
        """Get the pyshala package directory."""
        return Path(__file__).parent

    def run(self, env: Optional[str] = None) -> None:
        """Run the PyShala application.

        This starts the Reflex development server. For production deployments,
        use the `export` method followed by running the exported app.

        Args:
            env: Environment mode ('dev' or 'prod'). Defaults to 'dev'.
        """
        env_vars = self._setup_environment()
        pyshala_dir = self._get_pyshala_dir()

        cmd = [
            sys.executable, "-m", "reflex", "run",
            "--frontend-port", str(self.port),
            "--backend-port", str(self.backend_port),
            "--loglevel", self.loglevel,
        ]

        if env == "prod":
            cmd.append("--env")
            cmd.append("prod")

        print(f"Starting {self.app_name}...")
        print(f"  Lessons: {self.lessons_path}")
        print(f"  Frontend: http://{self.host}:{self.port}")
        print(f"  Backend: http://{self.host}:{self.backend_port}")
        print()

        # Run from the project root (parent of pyshala package) where rxconfig.py is located
        subprocess.run(
            cmd,
            cwd=pyshala_dir.parent,
            env=env_vars,
        )

    def export(self, output_dir: str = "./build") -> None:
        """Export the application for production deployment.

        Args:
            output_dir: Directory to export the built application to.
        """
        env_vars = self._setup_environment()
        pyshala_dir = self._get_pyshala_dir()

        cmd = [
            sys.executable, "-m", "reflex", "export",
            "--no-zip",
        ]

        print(f"Exporting PyShala to {output_dir}...")

        subprocess.run(
            cmd,
            cwd=pyshala_dir.parent,
            env=env_vars,
        )

        print(f"Export complete. Files are in {output_dir}")


def create_app(
    lessons_path: str = "./lessons",
    **kwargs,
) -> PyShala:
    """Create a PyShala application instance.

    This is a convenience function for creating a PyShala instance.

    Args:
        lessons_path: Path to the lessons directory.
        **kwargs: Additional arguments passed to PyShala constructor.

    Returns:
        PyShala application instance.

    Example:
        ```python
        from pyshala import create_app

        app = create_app(lessons_path="./my_lessons", port=8080)
        app.run()
        ```
    """
    return PyShala(lessons_path=lessons_path, **kwargs)
