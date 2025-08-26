from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # adjust depth if needed

def here(*parts: str) -> str:
    """Resolve a path relative to the project root."""
    return (BASE_DIR.joinpath(*parts)).as_posix()

print(here())