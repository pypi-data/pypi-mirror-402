"""PyShala command-line interface."""

import argparse
import sys

from .app import PyShala


def main() -> int:
    """Main entry point for the PyShala CLI."""
    parser = argparse.ArgumentParser(
        prog="pyshala",
        description="PyShala - A self-hosted interactive Python training platform",
    )

    parser.add_argument(
        "lessons_path",
        nargs="?",
        default="./lessons",
        help="Path to the lessons directory (default: ./lessons)",
    )

    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host address to bind (default: 0.0.0.0)",
    )

    parser.add_argument(
        "--port", "-p",
        type=int,
        default=3000,
        help="Frontend port (default: 3000)",
    )

    parser.add_argument(
        "--backend-port",
        type=int,
        default=8000,
        help="Backend API port (default: 8000)",
    )

    parser.add_argument(
        "--max-execution-time",
        type=float,
        default=10.0,
        help="Maximum code execution time in seconds (default: 10.0)",
    )

    parser.add_argument(
        "--python-path",
        default=None,
        help="Python interpreter path for code execution (default: current interpreter)",
    )

    parser.add_argument(
        "--loglevel",
        choices=["debug", "info", "warning", "error"],
        default="info",
        help="Logging level (default: info)",
    )

    parser.add_argument(
        "--app-name",
        default="Learn Python",
        help="Application name displayed in the UI (default: Learn Python)",
    )

    parser.add_argument(
        "--app-description",
        default="Interactive lessons with hands-on coding exercises and instant feedback",
        help="Application description displayed on the home page",
    )

    parser.add_argument(
        "--env",
        choices=["dev", "prod"],
        default=None,
        help="Environment mode (default: dev)",
    )

    parser.add_argument(
        "--version", "-v",
        action="store_true",
        help="Show version and exit",
    )

    args = parser.parse_args()

    if args.version:
        from . import __version__
        print(f"pyshala {__version__}")
        return 0

    try:
        app = PyShala(
            lessons_path=args.lessons_path,
            host=args.host,
            port=args.port,
            backend_port=args.backend_port,
            max_execution_time=args.max_execution_time,
            python_path=args.python_path,
            loglevel=args.loglevel,
            app_name=args.app_name,
            app_description=args.app_description,
        )
        app.run(env=args.env)
        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nShutting down...")
        return 0


if __name__ == "__main__":
    sys.exit(main())
