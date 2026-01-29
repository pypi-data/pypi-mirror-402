import os
import sys
import shutil
import subprocess
from pathlib import Path
from typing import Optional
from jinja2 import Environment, PackageLoader, select_autoescape
from datetime import datetime
from rich.console import Console

from .constants import (
    DEFAULT_VERSION,
    DEFAULT_PYTHON_VERSION,
    DEFAULT_LICENSE,
    DEFAULT_BUILDER,
    TYPE_CLASSIC,
    TYPE_ML,
    TYPE_DL,
    SRC_DIR,
    NOTEBOOKS_DIR,
    TESTS_DIR,
)
from .utils import sanitize_project_name, get_author_from_git
from .licenses import LICENSES

console = Console()

class ProjectGenerator:
    def __init__(self, name: str, description: str, type: str, 
                  author: str, 
                  use_env: bool, use_config: bool, 
                 use_readme: bool = True,
                 license: str = DEFAULT_LICENSE, 
                 builder: str = DEFAULT_BUILDER, 
                 framework: str = "pytorch",
                 verbose: bool = False):
        self.raw_name = name
        self.project_name = sanitize_project_name(name)
        self.description = description or name
        self.type = type
        self.framework = framework
        self.author = author
        if not self.author or self.author == "Your Name":
             self.author, self.author_email = get_author_from_git()
        else:
             self.author_email = "your.email@example.com"
        
        self.license = license
        self.builder = builder
        self.use_env = use_env
        self.use_config = use_config
        self.use_readme = use_readme
        self.verbose = verbose
        
        # Detect System Python
        self.python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        
        # Jinja Setup
        self.env = Environment(
            loader=PackageLoader("pypro", "templates"),
            autoescape=select_autoescape()
        )

    def log(self, message: str, style: str = "dim"):
        if self.verbose:
            console.print(f"  [{style}]{message}[/{style}]")

    def generate(self, target_dir: Optional[Path] = None):
        """Main generation flow using uv init."""
        if target_dir is None:
            target_dir = Path.cwd()

        project_dir = target_dir / self.raw_name
        
        if project_dir.exists():
            console.print(f"[bold red]Error:[/bold red] Directory {project_dir} already exists.")
            return

        console.print(f"[bold green]Creating project {self.raw_name} ({self.type})...[/bold green]")
        
        self.log(f"Target directory: {project_dir}")
        self.log(f"Python version: {self.python_version}")


    def generate(self, target_dir: Path):
        """Main generation flow using uv init."""
        project_dir = target_dir / self.raw_name
        
        if project_dir.exists():
            console.print(f"[bold red]Error:[/bold red] Directory {project_dir} already exists.")
            return

        console.print(f"[bold green]Creating project {self.raw_name} ({self.type})...[/bold green]")
        
        # 1. Scaffolding with uv init
        try:
            # We use --package as requested for a general package structure
            subprocess.run(
                ["uv", "init", "--package", "--no-workspace", self.raw_name], 
                check=True, cwd=target_dir, capture_output=True
            )
            console.print("  [blue]✓ Scaffolding created with uv init --package[/blue]")
        except subprocess.CalledProcessError as e:
             console.print(f"[bold red]Error running uv init:[/bold red] {e}")
             return

        # 2. Restructure / Clean up
        # uv init creates src/project_name/
        
        # 3. Create extra directories (First, so templates have target dirs)
        self._create_extra_dirs(project_dir)
        
        # 4. Overwrite/Add Files
        self._generate_files(project_dir)
        
        # 5. Git & Final Steps
        # uv init already initialized git, we might want to amend/commit
        console.print(f"\n[bold green]✓ Project {self.raw_name} created successfully![/bold green]")
        console.print(f"  [dim]cd {self.raw_name} && uv sync[/dim]")

    def _create_extra_dirs(self, root: Path):
        # Notebooks for ML/DL
        if self.type in [TYPE_ML, TYPE_DL]:
            (root / NOTEBOOKS_DIR).mkdir(exist_ok=True)
            self.log("Created notebooks directory")
            # Note: 'data/' directory is created lazily by data_loader when needed (local=True)
            
        # Tests inside package (future proofing as requested)
        src_pkg = root / SRC_DIR / self.project_name
        (src_pkg / TESTS_DIR).mkdir(exist_ok=True)
        # Create a dummy test file
        with open(src_pkg / TESTS_DIR / "__init__.py", "w") as f:
            pass
        with open(src_pkg / TESTS_DIR / "test_core.py", "w") as f:
            f.write("def test_dummy():\n    assert True\n")
        self.log("Created internal tests directory")

    def _generate_files(self, root: Path):
        self.log(f"Generating files for {self.project_name}...")
        context = {
            "project_name": self.raw_name,
            "package_name": self.project_name,
            "description": self.description,
            "version": DEFAULT_VERSION,
            "python_version": self.python_version or DEFAULT_PYTHON_VERSION,
            "author_name": self.author,
            "author_email": self.author_email,
            "license": self.license,
            "project_type": self.type,
            "use_uv": self.builder == "uv",
            "has_config": self.use_config,
            "framework": self.framework,
        }
        
        # pyproject.toml (Overwrite uv's basic one to add our specific deps)
        self._render("pyproject.toml.j2", root / "pyproject.toml", context)
        
        # src/... files
        pkg_root = root / SRC_DIR / self.project_name
        
        # Ensure pkg root exists
        if not pkg_root.exists():
             self.log(f"Warning: Package root {pkg_root} expected but not found. Check uv init output.", "yellow")

        # __init__.py
        self._render("__init__.py.j2", pkg_root / "__init__.py", context)
        
        # README.md
        if self.use_readme:
             self._render("README.md.j2", root / "README.md", context)
        else:
             if (root / "README.md").exists():
                 (root / "README.md").unlink()
                 self.log("Removed default README.md (requested --no-readme)")
        
        # LICENSE
        license_text = LICENSES.get(self.license, LICENSES["MIT"])
        license_text = license_text.format(year=datetime.now().year, author=self.author)
        with open(root / "LICENSE", "w") as f:
            f.write(license_text)
        self.log(f"Generated LICENSE ({self.license})")

        # Config files
        if self.use_config:
            self._render("config.yaml.j2", pkg_root / "config.yaml", context)
            self._render("config.py.j2", pkg_root / "config.py", context)
            
        # Entry points & Logic
        if self.type == TYPE_CLASSIC:
             self._render("main.py.j2", pkg_root / "main.py", context)
        elif self.type in [TYPE_ML, TYPE_DL]:
             # Render Notebooks
             self._render("Base_Kaggle.ipynb.j2", root / NOTEBOOKS_DIR / "Base_Kaggle.ipynb", context)
             self._render("Base_General.ipynb.j2", root / NOTEBOOKS_DIR / "Base_General.ipynb", context)
             # Render Data Loader
             self._render("data_loader.py.j2", pkg_root / "data_loader.py", context)
             self.log("Generated wrappers: Base_Kaggle.ipynb, Base_General.ipynb, data_loader.py")
             
        # .env (Strict Isolation: In pkg_root)
        if self.use_env:
            with open(pkg_root / ".env", "w") as f:
                f.write("# Environment Variables (Isolated)\n")
            with open(pkg_root / ".env.example", "w") as f:
                f.write("# Environment Variables Example\n")
            self.log(f"Created .env and .env.example in {pkg_root.relative_to(root)}")
                
        # .gitignore
        with open(root / ".gitignore", "a") as f:
            # Add data/ to gitignore but allow .gitkeep
            f.write("\n# PyPro specific\n.ipynb_checkpoints/\n# Isolated Env\nsrc/**/.env\n# Data (Local)\ndata/*\n!data/.gitkeep\n")
        self.log("Updated .gitignore")

    def _render(self, template_name: str, target_path: Path, context: dict):
        template = self.env.get_template(template_name)
        content = template.render(**context)
        with open(target_path, "w") as f:
            f.write(content)
        self.log(f"Rendered {target_path.name}")

    def add_to_workspace(self, workspace_root: Path):
        """Add a new package to an existing workspace."""
        console.print(f"[bold green]Adding package {self.raw_name} to workspace...[/bold green]")
        
        pyproject_path = workspace_root / "pyproject.toml"
        if not pyproject_path.exists():
            console.print("[red]Error: Not in a valid project root (pyproject.toml missing).[/red]")
            return
            
        # Read pyproject.toml
        with open(pyproject_path, "r") as f:
            content = f.read()

        # Check if it's already a workspace
        is_workspace = "[tool.uv.workspace]" in content
        
        if not is_workspace:
            console.print("[yellow]Upgrading project to Workspace...[/yellow]")
            # Append workspace definition
            with open(pyproject_path, "a") as f:
                f.write(f"\n[tool.uv.workspace]\nmembers = [\"{self.raw_name}\"]\n")
            self.log("Added [tool.uv.workspace] section")
        else:
            # Add member to specific list if it exists
            # We use a simple regex approach to find 'members = [...]'
            import re
            members_pattern = r'members\s*=\s*\[(.*?)\]'
            match = re.search(members_pattern, content, re.DOTALL)
            
            if match:
                current_members = match.group(1)
                # Check if already present
                if f'"{self.raw_name}"' in current_members or f"'{self.raw_name}'" in current_members:
                    self.log(f"Package {self.raw_name} is already in workspace members.")
                else:
                    # Append new member
                    # We inject it into the list
                    self.log("Adding member to existing workspace list")
                    # Naively replace the closing bracket
                    # Better: parse, but for now robust string insertion
                    # Cleanest way without breaking formatting involves finding the last element
                    new_member = f', "{self.raw_name}"'
                    # Warning: This regex replace is basic. `uv` handles toml well, maybe we should just edit safely.
                    # Let's try to append to the end of the content of the list
                    new_content = re.sub(members_pattern, lambda m: f'members = [{m.group(1)}{new_member}]', content, flags=re.DOTALL)
                    with open(pyproject_path, "w") as f:
                        f.write(new_content)
            else:
                 # Section exists but members key might be missing? Or weird formatting.
                 # Append to section?
                 # Safe fallback
                 console.print("[yellow]Warning: Could not parse members list. Adding manually at end.[/yellow]")
                 with open(pyproject_path, "a") as f:
                     f.write(f"\n# Added by pypro\n[tool.uv.workspace]\nmembers = [\"{self.raw_name}\"]\n")

        # Generate the package in the root
        # We reuse generate logic but strictly in the current dir
        self.generate(workspace_root)
        
        # Post-generation: Ensure root knows about it
        console.print(f"[bold green]✓ Added {self.raw_name} to workspace successfully.[/bold green]")
        console.print(f"  Run [bold]uv sync[/bold] to link the new package.")

    def delete_from_workspace(self, workspace_root: Path):
        """Remove a package from the workspace."""
        console.print(f"[bold red]Removing package {self.raw_name} from workspace...[/bold red]")
        
        target_dir = workspace_root / self.raw_name
        pyproject_path = workspace_root / "pyproject.toml"

        # 1. Remove directory
        if target_dir.exists():
            import shutil
            shutil.rmtree(target_dir)
            self.log(f"Removed directory {target_dir}")
        else:
            console.print(f"[yellow]Directory {target_dir} not found.[/yellow]")

        # 2. Update pyproject.toml
        if pyproject_path.exists():
            with open(pyproject_path, "r") as f:
                content = f.read()
            
            # Regex to remove member
            # This handles "member", 'member' and checks for commas
            import re
            # Patter matches the member string with optional surrounding whitespace and optional following comma
            # It's tricky to be perfect with regex on TOML logic, but reasonably safe for standard lists
            # We look for the exact string inside the brackets
            
            # Simple approach: Load content, replace the specific member string literal with empty
            # But we need to handle commas.
            # Let's try to just remove the string and cleanup commas? 
            # Or better: specific regex for the element.
            
            member_str_double = f'"{self.raw_name}"'
            member_str_single = f"'{self.raw_name}'"
            
            new_content = content
            if member_str_double in new_content:
                new_content = new_content.replace(member_str_double, "")
            elif member_str_single in new_content:
                new_content = new_content.replace(member_str_single, "")
            else:
                self.log("Member not found in pyproject.toml list string")
                return

            # Cleanup double commas or trailing commas/empty items inside the list [ , , ]
            # This is "dirty" but works for simple lists
            new_content = re.sub(r'\[\s*,', '[', new_content) # Leading comma
            new_content = re.sub(r',\s*,', ',', new_content) # Double comma
            new_content = re.sub(r',\s*\]', ']', new_content) # Trailing comma
            
            with open(pyproject_path, "w") as f:
                f.write(new_content)
            self.log("Removed member from pyproject.toml")
        
        console.print(f"[bold green]✓ Removed {self.raw_name} successfully.[/bold green]")

    def update_package(self, workspace_root: Path):
        """Update a package (dependencies)."""
        console.print(f"[bold blue]Updating package {self.raw_name}...[/bold blue]")
        
        target_dir = workspace_root / self.raw_name
        if not target_dir.exists():
            console.print(f"[red]Error: Package {self.raw_name} does not exist.[/red]")
            return

        # Run uv lock --upgrade
        # Actually in a workspace, usually we run sync from root or lock from root?
        # If it's a workspace member, `uv lock` at root updates everything.
        # But maybe we want specific update?
        # Let's run `uv lock --upgrade-package name` if supported or just universal update.
        # For now, let's assume we run `uv lock --upgrade` inside the package or root.
        # Running inside the package dir usually affects the workspace lock if using "workspaces".
        
        import subprocess
        try:
            cmd = ["uv", "lock", "--upgrade"]
            self.log(f"Running {' '.join(cmd)}")
            subprocess.run(cmd, cwd=target_dir, check=True)
            console.print(f"[bold green]✓ Updated {self.raw_name} dependencies.[/bold green]")
        except subprocess.CalledProcessError:
            console.print(f"[red]Failed to update {self.raw_name}.[/red]")


