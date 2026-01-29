from pathlib import Path


def get_project_root(start: Path | None = None) -> Path:
    """
    Resolve the project root dynamically by walking upward
    until pyproject.toml / .git / src folder is found.
    """

    if start is None:
        start = Path(__file__).resolve()

    for parent in [start, *start.parents]:
        if (parent / "pyproject.toml").exists():
            return parent
        if (parent / ".git").exists():
            return parent

    return start.parents[-1]
