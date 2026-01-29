"""Release management commands for aiterm."""

import subprocess
import sys
from pathlib import Path

import typer
from rich import print
from rich.panel import Panel
from rich.table import Table

app = typer.Typer(
    name="release",
    help="Release management commands for PyPI and Homebrew.",
    no_args_is_help=True,
)


def get_project_root() -> Path:
    """Find the project root by looking for pyproject.toml."""
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        if (parent / "pyproject.toml").exists():
            return parent
    return cwd


def get_version_from_pyproject(root: Path) -> str | None:
    """Extract version from pyproject.toml."""
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        return None

    content = pyproject.read_text()
    for line in content.splitlines():
        if line.strip().startswith("version"):
            # Parse: version = "0.4.0"
            parts = line.split("=", 1)
            if len(parts) == 2:
                return parts[1].strip().strip('"').strip("'")
    return None


def get_version_from_init(root: Path) -> str | None:
    """Extract version from __init__.py."""
    # Try common locations
    locations = [
        root / "src" / "aiterm" / "__init__.py",
        root / "aiterm" / "__init__.py",
    ]

    for init_file in locations:
        if init_file.exists():
            content = init_file.read_text()
            for line in content.splitlines():
                if line.strip().startswith("__version__"):
                    parts = line.split("=", 1)
                    if len(parts) == 2:
                        return parts[1].strip().strip('"').strip("'")
    return None


def get_changelog_version(root: Path) -> str | None:
    """Extract latest version from CHANGELOG.md."""
    changelog = root / "CHANGELOG.md"
    if not changelog.exists():
        return None

    content = changelog.read_text()
    # Look for pattern like ## [0.4.0] or ## [0.4.0] - 2025-12-30
    import re
    match = re.search(r"##\s*\[(\d+\.\d+\.\d+)\]", content)
    if match:
        return match.group(1)
    return None


def run_command(cmd: list[str], capture: bool = True) -> tuple[int, str]:
    """Run a command and return exit code and output."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture,
            text=True,
            timeout=300,
        )
        output = result.stdout + result.stderr if capture else ""
        return result.returncode, output.strip()
    except subprocess.TimeoutExpired:
        return 1, "Command timed out"
    except FileNotFoundError:
        return 1, f"Command not found: {cmd[0]}"


def check_git_status(root: Path) -> tuple[bool, str]:
    """Check for uncommitted changes."""
    code, output = run_command(["git", "status", "--porcelain"], capture=True)
    if code != 0:
        return False, "Failed to check git status"
    if output:
        return False, f"Uncommitted changes:\n{output}"
    return True, "No uncommitted changes"


def check_git_branch() -> tuple[bool, str, str]:
    """Check current git branch."""
    code, branch = run_command(["git", "branch", "--show-current"])
    if code != 0:
        return False, "Failed to get branch", ""
    return True, branch, branch


def check_tag_exists(version: str) -> bool:
    """Check if a git tag exists."""
    code, _ = run_command(["git", "tag", "-l", f"v{version}"])
    # Check if the tag is in the list
    code, output = run_command(["git", "tag", "-l", f"v{version}"])
    return f"v{version}" in output.splitlines()


def run_tests(root: Path) -> tuple[bool, str]:
    """Run pytest and return success status."""
    code, output = run_command(["pytest", "--tb=no", "-q"], capture=True)
    if code == 0:
        # Extract pass count from output
        lines = output.strip().splitlines()
        for line in reversed(lines):
            if "passed" in line:
                return True, line
        return True, "Tests passed"
    return False, output


@app.command("check")
def release_check(
    skip_tests: bool = typer.Option(False, "--skip-tests", "-s", help="Skip running tests"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
) -> None:
    """
    Validate release readiness.

    Checks version consistency, tests, git status, and more.

    Examples:
        ait release check
        ait release check --skip-tests
        ait release check --verbose
    """
    root = get_project_root()

    print(Panel.fit("[bold]Release Check[/bold]", style="blue"))
    print()

    checks: list[tuple[str, bool, str]] = []
    all_passed = True

    # 1. Version consistency
    pyproject_ver = get_version_from_pyproject(root)
    init_ver = get_version_from_init(root)
    changelog_ver = get_changelog_version(root)

    versions_match = (
        pyproject_ver is not None
        and pyproject_ver == init_ver
        and pyproject_ver == changelog_ver
    )

    if versions_match:
        checks.append(("Version consistency", True, f"{pyproject_ver}"))
        if verbose:
            print(f"  pyproject.toml: {pyproject_ver}")
            print(f"  __init__.py: {init_ver}")
            print(f"  CHANGELOG.md: {changelog_ver}")
    else:
        all_passed = False
        details = []
        if pyproject_ver:
            details.append(f"pyproject.toml: {pyproject_ver}")
        if init_ver:
            details.append(f"__init__.py: {init_ver}")
        if changelog_ver:
            details.append(f"CHANGELOG.md: {changelog_ver}")
        checks.append(("Version consistency", False, ", ".join(details) if details else "Missing version"))

    version = pyproject_ver or init_ver or changelog_ver or "unknown"

    # 2. Tests
    if not skip_tests:
        print("[dim]Running tests...[/dim]", end="\r")
        test_passed, test_msg = run_tests(root)
        checks.append(("Tests", test_passed, test_msg))
        if not test_passed:
            all_passed = False
    else:
        checks.append(("Tests", True, "Skipped"))

    # 3. Git status (uncommitted changes)
    git_clean, git_msg = check_git_status(root)
    checks.append(("Clean working tree", git_clean, git_msg if not git_clean else "No uncommitted changes"))
    if not git_clean:
        all_passed = False

    # 4. Git branch
    branch_ok, branch_name, _ = check_git_branch()
    is_main = branch_name in ("main", "master")
    checks.append(("On main branch", is_main, f"Current: {branch_name}"))
    if not is_main:
        all_passed = False

    # 5. Tag exists check
    tag_exists = check_tag_exists(version)
    if tag_exists:
        checks.append(("Tag available", False, f"v{version} already exists"))
        all_passed = False
    else:
        checks.append(("Tag available", True, f"v{version} not yet tagged"))

    # Display results
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Status", width=3)
    table.add_column("Check", width=25)
    table.add_column("Details")

    for check_name, passed, details in checks:
        status = "[green]✓[/green]" if passed else "[red]✗[/red]"
        detail_style = "" if passed else "[dim]"
        table.add_row(status, check_name, f"{detail_style}{details}")

    print(table)
    print()

    if all_passed:
        print(f"[bold green]Ready to release v{version}[/bold green]")
        print()
        print("[dim]Next steps:[/dim]")
        print(f"  ait release tag {version}")
        print(f"  ait release pypi")
    else:
        print("[bold yellow]Not ready for release[/bold yellow]")
        print("[dim]Fix the issues above and run again.[/dim]")
        raise typer.Exit(1)


@app.command("status")
def release_status() -> None:
    """
    Show current release state and pending changes.

    Examples:
        ait release status
    """
    root = get_project_root()

    print(Panel.fit("[bold]Release Status[/bold]", style="blue"))
    print()

    # Current version
    version = get_version_from_pyproject(root) or "unknown"
    print(f"[bold]Current version:[/bold] {version}")

    # Latest tag
    code, tags = run_command(["git", "tag", "--sort=-v:refname"])
    if code == 0 and tags:
        latest_tag = tags.splitlines()[0]
        print(f"[bold]Latest tag:[/bold] {latest_tag}")

        # Commits since tag
        code, commits = run_command(["git", "rev-list", f"{latest_tag}..HEAD", "--count"])
        if code == 0:
            count = int(commits) if commits.isdigit() else 0
            print(f"[bold]Commits since tag:[/bold] {count}")

            if count > 0:
                print()
                print("[bold]Pending changes:[/bold]")
                code, log = run_command([
                    "git", "log", f"{latest_tag}..HEAD",
                    "--oneline", "--no-decorate"
                ])
                if code == 0:
                    for line in log.splitlines()[:10]:
                        print(f"  [dim]•[/dim] {line}")
                    if count > 10:
                        print(f"  [dim]... and {count - 10} more[/dim]")
    else:
        print("[dim]No tags found[/dim]")

    # Suggest next version
    print()
    if version != "unknown":
        parts = version.split(".")
        if len(parts) == 3:
            major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
            print("[bold]Suggested next versions:[/bold]")
            print(f"  Patch: {major}.{minor}.{patch + 1}")
            print(f"  Minor: {major}.{minor + 1}.0")
            print(f"  Major: {major + 1}.0.0")


def check_tool_available(tool: str) -> bool:
    """Check if a command-line tool is available."""
    code, _ = run_command(["which", tool])
    return code == 0


def build_package(root: Path) -> tuple[bool, str, list[Path]]:
    """Build the package using uv or pip."""
    dist_dir = root / "dist"

    # Clean old builds
    if dist_dir.exists():
        import shutil
        shutil.rmtree(dist_dir)

    # Try uv first
    if check_tool_available("uv"):
        code, output = run_command(["uv", "build"], capture=True)
        if code == 0:
            # Find built files
            built = list(dist_dir.glob("*.whl")) + list(dist_dir.glob("*.tar.gz"))
            return True, "Built with uv", built
        return False, f"uv build failed: {output}", []

    # Fallback to pip/build
    code, output = run_command(["python", "-m", "build"], capture=True)
    if code == 0:
        built = list(dist_dir.glob("*.whl")) + list(dist_dir.glob("*.tar.gz"))
        return True, "Built with python -m build", built
    return False, f"Build failed: {output}", []


def publish_to_pypi(root: Path, test: bool = False) -> tuple[bool, str]:
    """Publish package to PyPI."""
    dist_dir = root / "dist"

    if not dist_dir.exists():
        return False, "No dist/ directory found. Run build first."

    files = list(dist_dir.glob("*.whl")) + list(dist_dir.glob("*.tar.gz"))
    if not files:
        return False, "No distribution files found in dist/"

    # Determine repository
    repo_args = ["--index-url", "https://test.pypi.org/simple/"] if test else []

    # Try uv publish first
    if check_tool_available("uv"):
        cmd = ["uv", "publish"]
        if test:
            cmd.extend(["--publish-url", "https://test.pypi.org/legacy/"])
        code, output = run_command(cmd, capture=True)
        if code == 0:
            return True, "Published with uv"
        # Check if it's an "already exists" error (not a failure)
        if "already exists" in output.lower() or "409" in output:
            return True, "Package already exists on PyPI"
        return False, f"uv publish failed: {output}"

    # Fallback to twine
    if check_tool_available("twine"):
        repo = "testpypi" if test else "pypi"
        cmd = ["twine", "upload", "--repository", repo] + [str(f) for f in files]
        code, output = run_command(cmd, capture=True)
        if code == 0:
            return True, "Published with twine"
        if "already exists" in output.lower():
            return True, "Package already exists on PyPI"
        return False, f"twine upload failed: {output}"

    return False, "Neither uv nor twine found. Install with: pip install twine"


def verify_on_pypi(package: str, version: str, test: bool = False) -> tuple[bool, str]:
    """Verify specific version of package is available on PyPI."""
    import urllib.request
    import json

    base_url = "https://test.pypi.org/pypi" if test else "https://pypi.org/pypi"
    # Use version-specific URL to verify exact version exists
    url = f"{base_url}/{package}/{version}/json"

    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            pypi_version = data.get("info", {}).get("version", "")
            if pypi_version == version:
                return True, f"Verified: {package} {version} on PyPI"
            return False, f"Version mismatch: PyPI has {pypi_version}, expected {version}"
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False, f"Version {version} of {package} not found on PyPI"
        return False, f"HTTP error: {e.code}"
    except Exception as e:
        return False, f"Verification failed: {e}"


@app.command("pypi")
def release_pypi(
    skip_build: bool = typer.Option(False, "--skip-build", help="Skip building, use existing dist/"),
    skip_verify: bool = typer.Option(False, "--skip-verify", help="Skip PyPI verification"),
    test: bool = typer.Option(False, "--test", "-t", help="Publish to TestPyPI instead"),
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Build but don't publish"),
) -> None:
    """
    Build and publish package to PyPI.

    Examples:
        ait release pypi
        ait release pypi --test          # Publish to TestPyPI
        ait release pypi --dry-run       # Build only
        ait release pypi --skip-build    # Use existing dist/
    """
    root = get_project_root()
    version = get_version_from_pyproject(root) or "unknown"
    pypi_target = "TestPyPI" if test else "PyPI"

    print(Panel.fit(f"[bold]Publish to {pypi_target}[/bold]", style="blue"))
    print()

    # Get package name from pyproject.toml
    pyproject = root / "pyproject.toml"
    package_name = "aiterm-dev"  # Default
    if pyproject.exists():
        content = pyproject.read_text()
        for line in content.splitlines():
            if line.strip().startswith("name"):
                parts = line.split("=", 1)
                if len(parts) == 2:
                    package_name = parts[1].strip().strip('"').strip("'")
                    break

    print(f"[bold]Package:[/bold] {package_name}")
    print(f"[bold]Version:[/bold] {version}")
    print()

    # Step 1: Build
    if not skip_build:
        print("[dim]Building package...[/dim]")
        success, msg, files = build_package(root)
        if success:
            print(f"[green]✓[/green] {msg}")
            for f in files:
                print(f"  [dim]•[/dim] {f.name}")
        else:
            print(f"[red]✗[/red] {msg}")
            raise typer.Exit(1)
        print()

    if dry_run:
        print("[yellow]Dry run - skipping publish[/yellow]")
        return

    # Step 2: Publish
    print(f"[dim]Publishing to {pypi_target}...[/dim]")
    success, msg = publish_to_pypi(root, test=test)
    if success:
        print(f"[green]✓[/green] {msg}")
    else:
        print(f"[red]✗[/red] {msg}")
        raise typer.Exit(1)
    print()

    # Step 3: Verify
    if not skip_verify:
        print("[dim]Verifying on PyPI (may take a moment)...[/dim]")
        import time
        time.sleep(3)  # Give PyPI a moment to update
        success, msg = verify_on_pypi(package_name, version, test=test)
        if success:
            print(f"[green]✓[/green] {msg}")
        else:
            print(f"[yellow]![/yellow] {msg}")
            print("[dim]Note: PyPI index may take a few minutes to update[/dim]")

    print()
    print(f"[bold green]Published {package_name} {version} to {pypi_target}![/bold green]")

    if not test:
        print()
        print("[dim]Install with:[/dim]")
        print(f"  pip install {package_name}=={version}")


def get_commits_since_tag(tag: str) -> list[dict]:
    """Get commits since a given tag."""
    code, output = run_command([
        "git", "log", f"{tag}..HEAD",
        "--pretty=format:%H|%s|%an|%ai"
    ])
    if code != 0 or not output:
        return []

    commits = []
    for line in output.splitlines():
        if "|" not in line:
            continue
        parts = line.split("|", 3)
        if len(parts) >= 2:
            commits.append({
                "hash": parts[0][:8],
                "subject": parts[1],
                "author": parts[2] if len(parts) > 2 else "",
                "date": parts[3] if len(parts) > 3 else "",
            })
    return commits


def categorize_commits(commits: list[dict]) -> dict[str, list[dict]]:
    """Categorize commits by conventional commit type."""
    categories = {
        "feat": [],
        "fix": [],
        "docs": [],
        "refactor": [],
        "test": [],
        "chore": [],
        "other": [],
    }

    for commit in commits:
        subject = commit["subject"]
        categorized = False
        for cat in ["feat", "fix", "docs", "refactor", "test", "chore", "ci", "build", "perf", "style"]:
            if subject.startswith(f"{cat}:") or subject.startswith(f"{cat}("):
                key = cat if cat in categories else "other"
                categories.get(key, categories["other"]).append(commit)
                categorized = True
                break
        if not categorized:
            categories["other"].append(commit)

    return {k: v for k, v in categories.items() if v}


def generate_release_notes(version: str, commits: list[dict]) -> str:
    """Generate markdown release notes from commits."""
    categories = categorize_commits(commits)

    lines = [f"# Release v{version}", ""]

    category_titles = {
        "feat": "✨ Features",
        "fix": "🐛 Bug Fixes",
        "docs": "📚 Documentation",
        "refactor": "♻️ Refactoring",
        "test": "🧪 Tests",
        "chore": "🔧 Chores",
        "other": "📝 Other Changes",
    }

    for cat, title in category_titles.items():
        if cat in categories:
            lines.append(f"## {title}")
            lines.append("")
            for commit in categories[cat]:
                # Clean up the subject (remove type prefix)
                subject = commit["subject"]
                if ":" in subject:
                    subject = subject.split(":", 1)[1].strip()
                lines.append(f"- {subject}")
            lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(f"**Full Changelog**: https://github.com/Data-Wise/aiterm/compare/v{version}...HEAD")

    return "\n".join(lines)


@app.command("notes")
def release_notes(
    version: str = typer.Argument(None, help="Version for release notes header"),
    since: str = typer.Option(None, "--since", "-s", help="Tag to compare from (default: latest)"),
    output_file: str = typer.Option(None, "--output", "-o", help="Write to file instead of stdout"),
    clipboard: bool = typer.Option(False, "--clipboard", "-c", help="Copy to clipboard"),
) -> None:
    """
    Generate release notes from commits since last tag.

    Examples:
        ait release notes
        ait release notes 0.5.0
        ait release notes --since v0.4.0
        ait release notes -o RELEASE_NOTES.md
        ait release notes --clipboard
    """
    root = get_project_root()

    # Get version if not specified
    if version is None:
        version = get_version_from_pyproject(root) or "next"

    # Get tag to compare from
    if since is None:
        code, tags = run_command(["git", "tag", "--sort=-v:refname"])
        if code == 0 and tags:
            since = tags.splitlines()[0]
        else:
            print("[red]No tags found. Use --since to specify a starting point.[/red]")
            raise typer.Exit(1)

    # Get commits
    commits = get_commits_since_tag(since)
    if not commits:
        print(f"[yellow]No commits found since {since}[/yellow]")
        return

    # Generate notes
    notes = generate_release_notes(version, commits)

    # Output
    if output_file:
        Path(output_file).write_text(notes)
        print(f"[green]✓[/green] Written to {output_file}")
    elif clipboard:
        try:
            import subprocess
            process = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
            process.communicate(notes.encode())
            print(f"[green]✓[/green] Copied to clipboard ({len(commits)} commits)")
        except Exception:
            print("[yellow]Could not copy to clipboard. Here are the notes:[/yellow]")
            print()
            print(notes)
    else:
        print(notes)


@app.command("tag")
def release_tag(
    version: str = typer.Argument(None, help="Version to tag (e.g., 0.5.0)"),
    message: str = typer.Option(None, "--message", "-m", help="Tag message"),
    push: bool = typer.Option(False, "--push", "-p", help="Push tag to origin"),
) -> None:
    """
    Create an annotated git tag.

    Examples:
        ait release tag 0.5.0
        ait release tag 0.5.0 -m "Release v0.5.0"
        ait release tag 0.5.0 --push
    """
    root = get_project_root()

    # Use current version if not specified
    if version is None:
        version = get_version_from_pyproject(root)
        if not version:
            print("[red]Could not detect version. Please specify explicitly.[/red]")
            raise typer.Exit(1)

    tag_name = f"v{version}" if not version.startswith("v") else version

    # Check if tag exists
    if check_tag_exists(version.lstrip("v")):
        print(f"[red]Tag {tag_name} already exists[/red]")
        raise typer.Exit(1)

    # Create tag
    tag_message = message or f"Release {tag_name}"
    code, output = run_command(["git", "tag", "-a", tag_name, "-m", tag_message])

    if code != 0:
        print(f"[red]Failed to create tag: {output}[/red]")
        raise typer.Exit(1)

    print(f"[green]✓[/green] Created tag {tag_name}")

    if push:
        code, output = run_command(["git", "push", "origin", tag_name])
        if code != 0:
            print(f"[red]Failed to push tag: {output}[/red]")
            raise typer.Exit(1)
        print(f"[green]✓[/green] Pushed {tag_name} to origin")
    else:
        print(f"[dim]Push with: git push origin {tag_name}[/dim]")


def get_pypi_sha256(package: str, version: str) -> str | None:
    """Get SHA256 hash for a package from PyPI."""
    import urllib.request
    import json

    url = f"https://pypi.org/pypi/{package}/{version}/json"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            urls = data.get("urls", [])
            for file_info in urls:
                if file_info.get("packagetype") == "sdist":
                    digests = file_info.get("digests", {})
                    return digests.get("sha256")
    except Exception:
        pass
    return None


def update_homebrew_formula(
    tap_path: Path, package: str, version: str, sha256: str
) -> tuple[bool, str]:
    """Update the Homebrew formula with new version and hash."""
    formula_path = tap_path / "Formula" / f"{package}.rb"

    if not formula_path.exists():
        # Try without the -dev suffix
        alt_name = package.replace("-dev", "")
        formula_path = tap_path / "Formula" / f"{alt_name}.rb"

    if not formula_path.exists():
        return False, f"Formula not found at {formula_path}"

    content = formula_path.read_text()

    # Update version in URL
    import re
    new_content = re.sub(
        r'url "https://files\.pythonhosted\.org/.*?/[^/]+\.tar\.gz"',
        f'url "https://files.pythonhosted.org/packages/source/{package[0]}/{package}/{package}-{version}.tar.gz"',
        content,
    )

    # Update sha256
    new_content = re.sub(
        r'sha256 "[a-f0-9]{64}"',
        f'sha256 "{sha256}"',
        new_content,
    )

    if new_content == content:
        return False, "No changes detected in formula"

    formula_path.write_text(new_content)
    return True, f"Updated {formula_path.name}"


@app.command("homebrew")
def release_homebrew(
    tap_path: str = typer.Option(
        None, "--tap", "-t",
        help="Path to homebrew-tap repo (default: ~/projects/dev-tools/homebrew-tap)"
    ),
    version: str = typer.Option(None, "--version", "-v", help="Version to update to"),
    commit: bool = typer.Option(False, "--commit", "-c", help="Commit changes"),
    push: bool = typer.Option(False, "--push", "-p", help="Push changes to origin"),
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Show what would be done"),
) -> None:
    """
    Update Homebrew formula in tap.

    Examples:
        ait release homebrew
        ait release homebrew --tap ~/homebrew-tap
        ait release homebrew --commit --push
        ait release homebrew --dry-run
    """
    root = get_project_root()

    # Determine version
    if version is None:
        version = get_version_from_pyproject(root)
        if not version:
            print("[red]Could not detect version. Use --version to specify.[/red]")
            raise typer.Exit(1)

    print(Panel.fit("[bold]Update Homebrew Formula[/bold]", style="blue"))
    print()

    # Get package name
    package_name = "aiterm-dev"
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text()
        for line in content.splitlines():
            if line.strip().startswith("name"):
                parts = line.split("=", 1)
                if len(parts) == 2:
                    package_name = parts[1].strip().strip('"').strip("'")
                    break

    print(f"[bold]Package:[/bold] {package_name}")
    print(f"[bold]Version:[/bold] {version}")
    print()

    # Get SHA256 from PyPI
    print("[dim]Fetching SHA256 from PyPI...[/dim]")
    sha256 = get_pypi_sha256(package_name, version)
    if not sha256:
        print(f"[red]Could not get SHA256 for {package_name} {version} from PyPI[/red]")
        print("[dim]Make sure the package is published first.[/dim]")
        raise typer.Exit(1)

    print(f"[green]✓[/green] SHA256: {sha256[:16]}...")
    print()

    # Find tap path
    if tap_path is None:
        # Try common locations
        possible_paths = [
            Path.home() / "projects" / "dev-tools" / "homebrew-tap",
            Path.home() / "homebrew-tap",
            Path.home() / "dev" / "homebrew-tap",
        ]
        for p in possible_paths:
            if p.exists():
                tap_path = str(p)
                break

    if tap_path is None:
        print("[red]Could not find homebrew-tap. Use --tap to specify path.[/red]")
        raise typer.Exit(1)

    tap = Path(tap_path)
    if not tap.exists():
        print(f"[red]Tap path does not exist: {tap}[/red]")
        raise typer.Exit(1)

    if dry_run:
        print(f"[yellow]Dry run - would update formula in {tap}[/yellow]")
        return

    # Update formula
    print("[dim]Updating formula...[/dim]")
    success, msg = update_homebrew_formula(tap, package_name, version, sha256)
    if success:
        print(f"[green]✓[/green] {msg}")
    else:
        print(f"[red]✗[/red] {msg}")
        raise typer.Exit(1)

    # Commit if requested
    if commit:
        code, _ = run_command(
            ["git", "-C", str(tap), "add", "-A"],
            capture=True
        )
        code, _ = run_command(
            ["git", "-C", str(tap), "commit", "-m", f"Update {package_name} to {version}"],
            capture=True
        )
        if code == 0:
            print("[green]✓[/green] Committed changes")
        else:
            print("[yellow]![/yellow] No changes to commit")

    # Push if requested
    if push:
        code, _ = run_command(
            ["git", "-C", str(tap), "push"],
            capture=True
        )
        if code == 0:
            print("[green]✓[/green] Pushed to origin")
        else:
            print("[red]✗[/red] Failed to push")

    print()
    print(f"[bold green]Homebrew formula updated for {package_name} {version}![/bold green]")
    print()
    print("[dim]Test with:[/dim]")
    print(f"  brew update && brew upgrade {package_name.replace('-dev', '')}")


@app.command("full")
def release_full(
    version: str = typer.Argument(..., help="Version to release (e.g., 0.5.0)"),
    skip_tests: bool = typer.Option(False, "--skip-tests", help="Skip running tests"),
    skip_homebrew: bool = typer.Option(False, "--skip-homebrew", help="Skip Homebrew update"),
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Show what would be done"),
) -> None:
    """
    Full release workflow: check → tag → push → pypi → homebrew.

    This command orchestrates the complete release process:
    1. Validate release readiness
    2. Create annotated git tag
    3. Push tag to origin
    4. Publish to PyPI (via CI or directly)
    5. Update Homebrew formula

    Examples:
        ait release full 0.5.0
        ait release full 0.5.0 --dry-run
        ait release full 0.5.0 --skip-homebrew
    """
    from rich.progress import Progress, SpinnerColumn, TextColumn

    root = get_project_root()

    print(Panel.fit(f"[bold]Full Release: v{version}[/bold]", style="blue"))
    print()

    steps = [
        ("check", "Validate release readiness"),
        ("tag", "Create git tag"),
        ("push", "Push tag to origin"),
        ("pypi", "Publish to PyPI"),
    ]
    if not skip_homebrew:
        steps.append(("homebrew", "Update Homebrew formula"))

    if dry_run:
        print("[yellow]Dry run mode - showing planned steps:[/yellow]")
        print()
        for i, (step, desc) in enumerate(steps, 1):
            print(f"  {i}. {desc}")
        print()
        print("[dim]Run without --dry-run to execute.[/dim]")
        return

    # Step 1: Check
    print("[bold]Step 1/{}:[/bold] Validate release readiness".format(len(steps)))
    current_version = get_version_from_pyproject(root)
    if current_version != version:
        print(f"[red]Version mismatch: pyproject.toml has {current_version}, expected {version}[/red]")
        print("[dim]Update version in pyproject.toml and __init__.py first.[/dim]")
        raise typer.Exit(1)

    # Version consistency
    init_ver = get_version_from_init(root)
    changelog_ver = get_changelog_version(root)
    if not (current_version == init_ver == changelog_ver):
        print("[red]Version mismatch across files:[/red]")
        print(f"  pyproject.toml: {current_version}")
        print(f"  __init__.py: {init_ver}")
        print(f"  CHANGELOG.md: {changelog_ver}")
        raise typer.Exit(1)

    # Git status
    git_clean, _ = check_git_status(root)
    if not git_clean:
        print("[red]Uncommitted changes detected. Commit or stash them first.[/red]")
        raise typer.Exit(1)

    # Tests
    if not skip_tests:
        print("[dim]Running tests...[/dim]")
        test_passed, test_msg = run_tests(root)
        if not test_passed:
            print(f"[red]Tests failed:[/red] {test_msg}")
            raise typer.Exit(1)

    print("[green]✓[/green] Ready for release")
    print()

    # Step 2: Tag
    print("[bold]Step 2/{}:[/bold] Create git tag".format(len(steps)))
    tag_name = f"v{version}"
    if check_tag_exists(version):
        print(f"[yellow]Tag {tag_name} already exists - skipping[/yellow]")
    else:
        code, _ = run_command(["git", "tag", "-a", tag_name, "-m", f"Release {tag_name}"])
        if code != 0:
            print("[red]Failed to create tag[/red]")
            raise typer.Exit(1)
        print(f"[green]✓[/green] Created {tag_name}")
    print()

    # Step 3: Push
    print("[bold]Step 3/{}:[/bold] Push tag to origin".format(len(steps)))
    code, _ = run_command(["git", "push", "origin", tag_name])
    if code != 0:
        print("[yellow]Failed to push tag (may already exist remotely)[/yellow]")
    else:
        print(f"[green]✓[/green] Pushed {tag_name}")
    print()

    # Step 4: PyPI
    print("[bold]Step 4/{}:[/bold] Publish to PyPI".format(len(steps)))
    print("[dim]Building package...[/dim]")
    success, msg, _ = build_package(root)
    if not success:
        print(f"[red]Build failed:[/red] {msg}")
        raise typer.Exit(1)

    print("[dim]Publishing...[/dim]")
    success, msg = publish_to_pypi(root)
    if success:
        print(f"[green]✓[/green] {msg}")
    else:
        print(f"[red]✗[/red] {msg}")
        raise typer.Exit(1)
    print()

    # Step 5: Homebrew (optional)
    if not skip_homebrew:
        print("[bold]Step 5/{}:[/bold] Update Homebrew formula".format(len(steps)))
        print("[dim]Waiting for PyPI to update...[/dim]")
        import time
        time.sleep(5)

        package_name = "aiterm-dev"
        sha256 = get_pypi_sha256(package_name, version)
        if sha256:
            # Try to find tap
            possible_paths = [
                Path.home() / "projects" / "dev-tools" / "homebrew-tap",
                Path.home() / "homebrew-tap",
            ]
            tap_path = None
            for p in possible_paths:
                if p.exists():
                    tap_path = p
                    break

            if tap_path:
                success, msg = update_homebrew_formula(tap_path, package_name, version, sha256)
                if success:
                    print(f"[green]✓[/green] {msg}")
                    # Commit and push
                    run_command(["git", "-C", str(tap_path), "add", "-A"])
                    run_command(["git", "-C", str(tap_path), "commit", "-m", f"Update {package_name} to {version}"])
                    run_command(["git", "-C", str(tap_path), "push"])
                    print("[green]✓[/green] Pushed formula update")
                else:
                    print(f"[yellow]![/yellow] {msg}")
            else:
                print("[yellow]![/yellow] Homebrew tap not found - skipping")
        else:
            print("[yellow]![/yellow] Could not get SHA256 from PyPI yet")
        print()

    # Done!
    print(Panel.fit(
        f"[bold green]🎉 Released aiterm v{version}![/bold green]\n\n"
        f"PyPI: https://pypi.org/project/aiterm-dev/{version}/\n"
        f"GitHub: https://github.com/Data-Wise/aiterm/releases/tag/v{version}",
        style="green"
    ))


if __name__ == "__main__":
    app()
