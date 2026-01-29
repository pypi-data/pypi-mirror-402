import argparse
import shutil
import sys
import tempfile
from pathlib import Path

from .create_project import (
    ReactRouterSetup,
    fancy_print,
    resolve_project_name,
    show_banner,
)
from .extract_canvas_content import extract_canvas_content


def _ensure_required_commands():
    required_commands = ["npx", "npm"]
    missing = [cmd for cmd in required_commands if shutil.which(cmd) is None]
    if missing:
        fancy_print(f"❌ Required commands not found: {', '.join(missing)}", style="red")
        fancy_print("Please install Node.js and npm", style="yellow")
        sys.exit(1)


def _write_canvas_to_temp_jsx(content: str) -> Path:
    temp_file = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".jsx",
        delete=False,
        encoding="utf-8",
    )
    try:
        temp_file.write(content)
        temp_file.flush()
    finally:
        temp_file.close()
    return Path(temp_file.name)


def _load_jsx_from_input(input_value: str) -> tuple[Path, bool]:
    if input_value.startswith("http://") or input_value.startswith("https://"):
        try:
            canvas_content = extract_canvas_content(input_value)
        except Exception:
            fancy_print("❌ Failed to fetch or parse canvas content", style="red")
            sys.exit(1)
        return _write_canvas_to_temp_jsx(canvas_content), True

    input_path = Path(input_value)
    if not input_path.exists():
        fancy_print(f"❌ JSX file not found: {input_value}", style="red")
        sys.exit(1)
    return input_path, False


def main():
    parser = argparse.ArgumentParser(
        description="Create a React Router project from a canvas URL or a local JSX file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s https://chatgpt.com/canvas/shared/abc123
  %(prog)s https://chatgpt.com/canvas/shared/abc123 -n my-app
  %(prog)s ./component.jsx -n my-app
        """,
    )
    parser.add_argument("input", help="Canvas URL or local .jsx file")
    parser.add_argument(
        "-n",
        "--name",
        help="Project name (if not provided, will prompt interactively)",
    )

    args = parser.parse_args()

    show_banner()
    _ensure_required_commands()

    jsx_path, is_temp = _load_jsx_from_input(args.input)
    try:
        project_name = resolve_project_name(args.name, jsx_path)

        fancy_print(f"🎯 Project name: {project_name}", style="bold cyan")
        fancy_print(f"📄 JSX file: {jsx_path.name}", style="bold cyan")

        setup = ReactRouterSetup(project_name, str(jsx_path))
        setup.setup_project()
    finally:
        if is_temp and jsx_path.exists():
            jsx_path.unlink()


if __name__ == "__main__":
    main()
