"""
Shared FileNode class for tracking file include trees in FreeSWITCH configuration.
"""

import os
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class FileNode:
    """Represents a file in the include tree."""

    path: str
    children: list = field(default_factory=list)
    skipped: bool = False
    error: Optional[str] = None

    def print_tree(self, indent: int = 0):
        """Print a visual tree representation."""
        marker = " [SKIPPED]" if self.skipped else ""
        print("  " * indent + os.path.basename(self.path) + marker)
        for child in self.children:
            child.print_tree(indent + 1)

    def get_skipped_files(self) -> List[Tuple[str, Optional[str]]]:
        """Return list of (path, error) for all skipped files in this tree."""
        skipped = []
        if self.skipped:
            skipped.append((self.path, self.error))
        for child in self.children:
            skipped.extend(child.get_skipped_files())
        return skipped

    def get_all_files(self) -> List[str]:
        """Return list of all file paths in this tree (non-skipped only)."""
        files = []
        if not self.skipped:
            files.append(self.path)
        for child in self.children:
            files.extend(child.get_all_files())
        return files

    def count_files(self) -> int:
        """Return total count of files (including skipped)."""
        count = 1
        for child in self.children:
            count += child.count_files()
        return count
