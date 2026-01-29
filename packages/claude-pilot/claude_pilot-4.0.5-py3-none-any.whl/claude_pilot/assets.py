"""Asset manifest and build-time generation for claude-pilot.

This module defines the Single Source of Truth (SSOT) for curated Claude Code
assets that should be packaged in the wheel. It provides functionality to:

1. Define which files from .claude/** should be included in the package
2. Exclude generated/downloaded content (external skills)
3. Exclude repo-dev-only files (999_publish command)
4. Handle special cases like settings.json (merge-only policy)

The manifest is used both at build time (Hatchling hook) and runtime
(init/update operations).
"""

from __future__ import annotations

import fnmatch
import shutil
import stat
from pathlib import Path
from typing import Final

# Special file policies
POLICY_MERGE_ONLY = "merge-only"
POLICY_OVERWRITE = "overwrite"
POLICY_SKIP = "skip"


class AssetManifest:
    """
    Manifest defining the curated subset of Claude Code assets to package.

    This class defines include/exclude patterns and special file policies
    for determining which .claude/** files should be shipped in the wheel.
    """

    # Include patterns: core Claude Code assets
    # These patterns use glob syntax to match files for inclusion
    INCLUDE_PATTERNS: Final[list[str]] = [
        # Core commands (0x and 9x prefix - claude-pilot specific)
        ".claude/commands/00_plan.md",
        ".claude/commands/01_confirm.md",
        ".claude/commands/02_execute.md",
        ".claude/commands/03_close.md",
        ".claude/commands/90_review.md",
        ".claude/commands/91_document.md",
        ".claude/commands/92_init.md",
        # Commands CONTEXT file
        ".claude/commands/CONTEXT.md",
        # Agents (all agents are curated)
        ".claude/agents/*.md",
        ".claude/agents/CONTEXT.md",
        # Core skills (excluding external - those are generated/downloaded)
        ".claude/skills/tdd/SKILL.md",
        ".claude/skills/tdd/REFERENCE.md",
        ".claude/skills/ralph-loop/SKILL.md",
        ".claude/skills/ralph-loop/REFERENCE.md",
        ".claude/skills/vibe-coding/SKILL.md",
        ".claude/skills/vibe-coding/REFERENCE.md",
        ".claude/skills/git-master/SKILL.md",
        ".claude/skills/git-master/REFERENCE.md",
        ".claude/skills/documentation-best-practices/SKILL.md",
        ".claude/skills/documentation-best-practices/REFERENCE.md",
        # Skills CONTEXT file
        ".claude/skills/CONTEXT.md",
        # Guides (all guides are curated)
        ".claude/guides/*.md",
        ".claude/guides/CONTEXT.md",
        # Templates (all templates are curated)
        ".claude/templates/*.template",
        ".claude/templates/gap-checklist.md",
        # Hooks
        ".claude/scripts/hooks/*.sh",
        # Utility scripts
        ".claude/scripts/statusline.sh",
        ".claude/scripts/worktree-utils.sh",
        ".claude/scripts/codex-sync.sh",
        # Rules (all rules are curated)
        ".claude/rules/**",
        # Version file
        ".claude/.pilot-version",
        # Settings file (special handling: merge-only)
        ".claude/settings.json",
        # Local directory placeholder
        ".claude/local/.gitkeep",
    ]

    # Exclude patterns: generated, repo-only, or user-owned files
    EXCLUDE_PATTERNS: Final[list[str]] = [
        # External skills (generated/downloaded - never ship)
        ".claude/skills/external/**",
        ".claude/skills/external/**/*",
        # External skills version file (generated state)
        ".claude/.external-skills-version",
        # Repo-dev-only commands
        ".claude/commands/999_publish.md",
        ".claude/commands/999_*",
        # .pilot directory runtime state (user-owned)
        ".pilot/**",
        ".pilot/**/*",
        # User-owned files (handled separately)
        "CLAUDE.md",
        ".claude/local/**/*",
    ]

    # Special case files with specific policies
    SPECIAL_CASE_FILES: Final[dict[str, str]] = {
        ".claude/settings.json": POLICY_MERGE_ONLY,
    }

    def __init__(
        self,
        include_patterns: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
        special_case_files: dict[str, str] | None = None,
    ) -> None:
        """
        Initialize the asset manifest.

        Args:
            include_patterns: Optional custom include patterns.
            exclude_patterns: Optional custom exclude patterns.
            special_case_files: Optional custom special case files.
        """
        self.include_patterns = include_patterns or self.INCLUDE_PATTERNS
        self.exclude_patterns = exclude_patterns or self.EXCLUDE_PATTERNS
        self.special_case_files = special_case_files or self.SPECIAL_CASE_FILES

    def should_include(self, file_path: str) -> bool:
        """
        Determine if a file should be included based on manifest patterns.

        Args:
            file_path: Relative file path (e.g., ".claude/commands/00_plan.md").

        Returns:
            True if file should be included, False otherwise.
        """
        # Check exclude patterns first (exclusion takes priority)
        for pattern in self.exclude_patterns:
            if self._match_pattern(file_path, pattern):
                return False

        # Check include patterns
        for pattern in self.include_patterns:
            if self._match_pattern(file_path, pattern):
                return True

        # Not explicitly included
        return False

    def _match_pattern(self, file_path: str, pattern: str) -> bool:
        """
        Match a file path against a glob pattern.

        Uses pathlib.Path.match() for proper ** pattern handling.

        Args:
            file_path: File path to match.
            pattern: Glob pattern.

        Returns:
            True if pattern matches, False otherwise.
        """
        try:
            return Path(file_path).match(pattern)
        except (ValueError, TypeError):
            return fnmatch.fnmatch(file_path, pattern)

    def is_special_case(self, file_path: str) -> bool:
        """
        Check if a file has special handling policy.

        Args:
            file_path: Relative file path.

        Returns:
            True if file has special policy, False otherwise.
        """
        return file_path in self.special_case_files

    def get_policy(self, file_path: str) -> str | None:
        """
        Get the policy for a special case file.

        Args:
            file_path: Relative file path.

        Returns:
            Policy string (e.g., "merge-only") or None if not special.
        """
        return self.special_case_files.get(file_path)


# Singleton manifest instance
_manifest: AssetManifest | None = None


def get_asset_manifest() -> AssetManifest:
    """
    Get the singleton asset manifest instance.

    Returns:
        The canonical AssetManifest instance.
    """
    global _manifest
    if _manifest is None:
        _manifest = AssetManifest()
    return _manifest


def generate_assets(
    source_dir: Path,
    dest_dir: Path,
    manifest: AssetManifest | None = None,
) -> int:
    """
    Generate packaged assets from source directory based on manifest.

    This function copies files from source_dir to dest_dir, filtering
    according to the manifest's include/exclude patterns.

    Args:
        source_dir: Source directory containing .claude/** files.
        dest_dir: Destination directory for generated assets.
        manifest: Optional manifest instance (uses singleton if not provided).

    Returns:
        Number of files copied.
    """
    if manifest is None:
        manifest = get_asset_manifest()

    count = 0

    # Walk through source directory
    for item in source_dir.rglob("*"):
        if not item.is_file():
            continue

        # Get relative path from source_dir
        try:
            rel_path = item.relative_to(source_dir)
        except ValueError:
            # Item is not relative to source_dir (shouldn't happen)
            continue

        rel_path_str = str(rel_path)

        # Check if file should be included
        if not manifest.should_include(rel_path_str):
            continue

        # Create destination path
        dest_path = dest_dir / rel_path
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # Copy file, preserving permissions for scripts
        shutil.copy2(item, dest_path)

        # Ensure shell scripts are executable
        if str(item).endswith('.sh'):
            dest_path.chmod(dest_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        count += 1

    return count
