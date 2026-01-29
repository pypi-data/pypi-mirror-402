import shutil

from python_base_toolkit.utils.path_utils import get_project_path_by_file


def clean_build_artifacts() -> None:
    ignore_dirs = {".git", ".github", ".venv", "__pycache__", ".idea", ".config"}
    build_dirs = ["build", "dist"]
    egg_info_suffix = ".egg-info"

    root_project_path = get_project_path_by_file()
    for p in root_project_path.iterdir():
        if p.name in ignore_dirs:
            continue

        if p.is_dir() and p.name.endswith(egg_info_suffix):
            shutil.rmtree(p, ignore_errors=True)
        elif p.is_dir() and p.name in build_dirs:
            shutil.rmtree(p, ignore_errors=True)


if __name__ == "__main__":
    clean_build_artifacts()
