"""Git operations for ralph-coding application."""

import subprocess
from pathlib import Path


class GitError(Exception):
    """Exception raised for git operation failures."""
    pass


class GitManager:
    """Manages git operations for a project."""

    def __init__(self, project_dir: Path) -> None:
        self.project_dir = project_dir

    def _run_git(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        """Run a git command in the project directory."""
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                check=check,
            )
            return result
        except subprocess.CalledProcessError as e:
            raise GitError(f"Git command failed: git {' '.join(args)}\n{e.stderr}")

    def is_git_repo(self) -> bool:
        """Check if the project directory is a git repository."""
        result = self._run_git("rev-parse", "--is-inside-work-tree", check=False)
        return result.returncode == 0

    def init_repo(self) -> None:
        """Initialize a new git repository."""
        if not self.is_git_repo():
            self._run_git("init")

    def get_current_branch(self) -> str:
        """Get the name of the current branch."""
        result = self._run_git("branch", "--show-current")
        return str(result.stdout).strip()

    def branch_exists(self, branch_name: str) -> bool:
        """Check if a branch exists (local or remote)."""
        # Check local branches
        result = self._run_git("branch", "--list", branch_name, check=False)
        if result.stdout.strip():
            return True
        # Check remote branches
        result = self._run_git("branch", "-r", "--list", f"*/{branch_name}", check=False)
        return bool(result.stdout.strip())

    def create_branch(self, branch_name: str) -> None:
        """Create a new branch if it doesn't exist."""
        if not self.branch_exists(branch_name):
            self._run_git("branch", branch_name)

    def _has_conflicting_branch(self, branch_name: str) -> str | None:
        """Check if there's a branch that conflicts with the given name.

        Git can't have both 'foo' and 'foo/bar' as branch names because
        they conflict in the refs namespace.

        Returns the conflicting branch name if found, None otherwise.
        """
        # Check if any existing branch is a prefix of the new branch
        # e.g., 'ralph' conflicts with 'ralph/feature'
        parts = branch_name.split("/")
        for i in range(1, len(parts)):
            prefix = "/".join(parts[:i])
            if self.branch_exists(prefix):
                return prefix

        # Check if the new branch would be a prefix of existing branches
        # e.g., 'ralph/feature' conflicts with existing 'ralph/feature/sub'
        result = self._run_git("branch", "--list", f"{branch_name}/*", check=False)
        if result.stdout.strip():
            return branch_name

        return None

    def checkout_branch(self, branch_name: str) -> None:
        """Checkout a branch, creating it if necessary."""
        if self.branch_exists(branch_name):
            self._run_git("checkout", branch_name)
            return

        # Check for conflicting branch names before creating
        conflict = self._has_conflicting_branch(branch_name)
        if conflict:
            # Check if this is the ralph prefix conflict
            parts = branch_name.split("/")
            if len(parts) > 1 and parts[0] == conflict:
                raise GitError(
                    f"Cannot create branch '{branch_name}': a branch named '{conflict}' already exists.\n\n"
                    f"Git cannot have both '{conflict}' and '{branch_name}' as branch names.\n\n"
                    f"To fix this, rename the '{conflict}' branch:\n"
                    f"  git branch -m {conflict} main\n\n"
                    f"Or change the branch prefix in Settings > Branch prefix."
                )
            raise GitError(
                f"Cannot create branch '{branch_name}': conflicts with existing branch '{conflict}'. "
                f"Git cannot have both '{conflict}' and '{branch_name}' as branch names."
            )

        self._run_git("checkout", "-b", branch_name)

    def ensure_on_branch(self, branch_name: str) -> None:
        """Ensure we're on the specified branch, creating it if needed."""
        self.init_repo()
        current = self.get_current_branch()
        if current != branch_name:
            self.checkout_branch(branch_name)

    def has_changes(self) -> bool:
        """Check if there are uncommitted changes (excluding ralph files)."""
        return bool(self.get_stageable_files())

    def get_status(self) -> str:
        """Get the current git status."""
        result = self._run_git("status", "--short")
        return str(result.stdout)

    # Files/patterns that should never be committed by ralph
    EXCLUDE_PATTERNS = [
        ".ralph/",
        ".claude/",
        "progress.md",
        "learnings.md",
        "*.log",
        "*.pyc",
        "__pycache__/",
        ".env",
        ".DS_Store",
    ]

    def _is_gitignored(self, filepath: str) -> bool:
        """Check if a file is ignored by .gitignore."""
        result = self._run_git("check-ignore", "-q", filepath, check=False)
        return result.returncode == 0

    def _should_stage(self, filepath: str) -> bool:
        """Check if a file should be staged (not in exclude patterns or .gitignore)."""
        # Check hardcoded exclude patterns first
        for pattern in self.EXCLUDE_PATTERNS:
            if pattern.endswith("/"):
                # Directory pattern
                if filepath.startswith(pattern) or f"/{pattern}" in filepath:
                    return False
            elif pattern.startswith("*"):
                # Wildcard pattern
                if filepath.endswith(pattern[1:]):
                    return False
            else:
                # Exact match
                if filepath == pattern or filepath.endswith(f"/{pattern}"):
                    return False

        # Also check .gitignore
        if self._is_gitignored(filepath):
            return False

        return True

    def get_stageable_files(self) -> list[str]:
        """Get list of changed files that should be staged (excluding ralph files)."""
        result = self._run_git("status", "--porcelain")
        files = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            # Status is first 2 chars, filename starts at position 3
            filepath = line[3:].strip()
            # Handle renamed files (old -> new)
            if " -> " in filepath:
                filepath = filepath.split(" -> ")[1]
            if self._should_stage(filepath):
                files.append(filepath)
        return files

    def stage_all(self) -> None:
        """Stage all changes except excluded patterns."""
        files = self.get_stageable_files()
        if files:
            self._stage_files_in_batches(files)

    def stage_files(self, files: list[str]) -> None:
        """Stage specific files (filtered through exclusions)."""
        filtered = [f for f in files if self._should_stage(f)]
        if filtered:
            self._stage_files_in_batches(filtered)

    def _stage_files_in_batches(self, files: list[str], batch_size: int = 50) -> None:
        """Stage files in batches to avoid command line length limits."""
        for i in range(0, len(files), batch_size):
            batch = files[i:i + batch_size]
            self._run_git("add", *batch)

    def commit(self, message: str) -> str:
        """Create a commit with the given message and return the commit hash."""
        self._run_git("commit", "-m", message)
        result = self._run_git("rev-parse", "HEAD")
        return str(result.stdout).strip()

    def commit_all(self, message: str) -> str | None:
        """Stage all changes and commit with the given message."""
        if not self.has_changes():
            return None

        self.stage_all()
        return self.commit(message)

    def has_staged_changes(self) -> bool:
        """Check if there are any staged changes ready to commit."""
        result = self._run_git("diff", "--cached", "--quiet", check=False)
        return result.returncode != 0

    def commit_staged(self, message: str) -> str | None:
        """Commit only staged changes (doesn't stage anything new).

        Returns the commit hash if a commit was made, None if nothing was staged.
        """
        if not self.has_staged_changes():
            return None

        return self.commit(message)

    def get_unstaged_files(self) -> list[str]:
        """Get list of files with unstaged changes (modified + untracked).

        Returns files that have changes not yet added to the staging area.
        This includes both modified tracked files and new untracked files.
        """
        files = []

        # Get modified but unstaged files
        result = self._run_git("diff", "--name-only")
        for f in result.stdout.strip().split("\n"):
            if f:
                files.append(f)

        # Get untracked files
        result = self._run_git("ls-files", "--others", "--exclude-standard")
        for f in result.stdout.strip().split("\n"):
            if f:
                files.append(f)

        return files

    def get_last_commit_message(self) -> str:
        """Get the message of the last commit."""
        result = self._run_git("log", "-1", "--pretty=%B", check=False)
        return str(result.stdout).strip()

    def get_diff(self, staged: bool = False) -> str:
        """Get the current diff for stageable files only."""
        files = self.get_stageable_files()
        if not files:
            return ""

        # Process files in batches to avoid command line length limits
        batch_size = 50
        diff_parts = []
        for i in range(0, len(files), batch_size):
            batch = files[i:i + batch_size]
            args = ["diff"]
            if staged:
                args.append("--staged")
            args.append("--")
            args.extend(batch)
            result = self._run_git(*args, check=False)
            if result.stdout:
                diff_parts.append(str(result.stdout))

        return "\n".join(diff_parts)

    def get_untracked_files(self) -> list[str]:
        """Get a list of untracked files."""
        result = self._run_git("ls-files", "--others", "--exclude-standard")
        return [f for f in result.stdout.strip().split("\n") if f]

    def get_modified_files(self) -> list[str]:
        """Get a list of modified files."""
        result = self._run_git("diff", "--name-only")
        return [f for f in result.stdout.strip().split("\n") if f]

    def reset_file(self, filepath: str) -> None:
        """Reset a specific file to the last committed state."""
        self._run_git("checkout", "--", filepath)

    def stash(self, message: str = "") -> None:
        """Stash current changes."""
        if message:
            self._run_git("stash", "push", "-m", message)
        else:
            self._run_git("stash")

    def stash_pop(self) -> None:
        """Pop the most recent stash."""
        self._run_git("stash", "pop")
