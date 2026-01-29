from pathlib import Path


def get_project_path_by_name(project_name: str) -> str:
    current_path = Path(__file__).parent
    while current_path != current_path.parent:  # pylint: disable=W0149
        if str(current_path).endswith(f"/{project_name}"):
            return str(current_path)
        current_path = current_path.parent
    raise FileNotFoundError(
        f'Project "{project_name}" not found in any parent directories.\n' f"Current path: {Path(__file__)}",
    )


def get_project_path_by_file(markers: set[str] | None = None) -> Path:
    markers = markers or {".git", "setup.py", "pyproject.toml", "LICENSE", "README.md"}
    path = Path(__file__).resolve() if "__file__" in globals() else Path.cwd().resolve()

    for marker in markers:
        if (path / marker).exists():
            return path

    for parent in path.parents:
        for marker in markers:
            if (parent / marker).exists():
                return parent
    raise RuntimeError(f'Project root with one of the markers: "{markers}" not found.')
