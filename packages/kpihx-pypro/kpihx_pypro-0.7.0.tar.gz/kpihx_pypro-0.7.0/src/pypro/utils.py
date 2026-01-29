import re
import git
from rich.console import Console

console = Console()

def sanitize_project_name(name: str) -> str:
    """
    Sanitize the project name to be a valid Python package name.
    Replaces hyphens with underscores and removes invalid characters.
    """
    # Replace - with _
    name = name.replace("-", "_")
    # Remove any characters that aren't alphanumerics or underscores
    name = re.sub(r"[^a-zA-Z0-9_]", "", name)
    # Ensure it starts with a letter or underscore
    if not re.match(r"^[a-zA-Z_]", name):
        name = f"_{name}"
    return name.lower()

def get_author_from_git() -> tuple[str, str]:
    """
    Attempt to get author name and email from git config.
    Returns (name, email) or defaults.
    """
    try:
        import git
        config = git.GitConfigParser(git.GitConfigParser.get_global_config(), read_only=True)
        name = config.get("user", "name", fallback="Your Name")
        email = config.get("user", "email", fallback="your.email@example.com")
        return name, email
    except Exception:
        return "Your Name", "your.email@example.com"
