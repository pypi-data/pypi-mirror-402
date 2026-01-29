"""
Shared file discovery logic for FreeSWITCH configuration.

Handles:
- X-PRE-PROCESS cmd="include" directive resolution
- X-PRE-PROCESS cmd="set" variable tracking
- Glob pattern expansion for includes
- Recursive file tree building
"""

import os
import re
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set

from discovery.FileNode import FileNode


class FreeswitchFileDiscovery:
    """
    Discovers all files in a FreeSWITCH configuration by following X-PRE-PROCESS includes.

    Can be used standalone or as a base for loaders and analyzers.
    """

    # Regex to match X-PRE-PROCESS tags (handles self-closing and with content)
    PREPROCESS_PATTERN = re.compile(
        r'<X-PRE-PROCESS\s+cmd=["\'](\w+)["\']\s+data=["\']([^"\']+)["\']\s*/?>', re.IGNORECASE
    )

    def __init__(self, verbose: bool = False):
        self.variables: Dict[str, str] = {}
        self.verbose = verbose
        self._visited_files: Set[str] = set()
        self._pre_load_variables()

    def _pre_load_variables(self):
        """Pre-populate commonly needed variables."""
        self.variables["hostname"] = "localhost"
        self.variables["local_ip_v4"] = "127.0.0.1"
        self.variables["local_ip_v6"] = "::1"
        self.variables["base_dir"] = "/etc/freeswitch"

    def _log(self, msg: str):
        if self.verbose:
            print(msg)

    def eval_value(self, value: str) -> str:
        """Expand $${var_name} references in a string."""
        pattern = r"\$\$\{([^}]+)\}"

        def replacer(match):
            var_name = match.group(1)
            if var_name in self.variables:
                return self.variables[var_name]
            self._log(f"  [WARN] Unknown variable: {var_name}")
            return match.group(0)  # Keep original if not found

        return re.sub(pattern, replacer, value)

    def process_set(self, data: str):
        """Handle X-PRE-PROCESS cmd="set" directive."""
        if "=" not in data:
            self._log(f"  [WARN] Invalid set directive (no '='): {data}")
            return

        key, value = data.split("=", 1)
        expanded_value = self.eval_value(value)
        self.variables[key] = expanded_value
        self._log(f"  SET: {key} = {expanded_value}")

    def resolve_include_paths(self, pattern: str, base_dir: str) -> List[str]:
        """
        Resolve include pattern to actual file paths.

        Args:
            pattern: The include pattern (may contain wildcards like *.xml)
            base_dir: Directory of the file containing the include

        Returns:
            Sorted list of matching absolute file paths
        """
        # Expand any variables in the pattern
        pattern = self.eval_value(pattern)

        # Use pathlib glob for pattern matching
        base_path = Path(base_dir)
        matches = list(base_path.glob(pattern))

        # Sort for deterministic order
        return sorted([str(p.resolve()) for p in matches if p.is_file()])

    def discover_files(
        self, file_path: str, file_node: FileNode, file_validator: Optional[Callable[[str], tuple]] = None
    ) -> None:
        """
        Recursively discover all included files starting from file_path.

        Args:
            file_path: Starting file path
            file_node: FileNode to populate with children
            file_validator: Optional callable(path) -> (is_valid, content, error)
                           to validate files before adding them
        """
        abs_path = os.path.abspath(file_path)

        # Cycle detection
        if abs_path in self._visited_files:
            self._log(f"  [WARN] Skipping circular include: {abs_path}")
            return

        self._visited_files.add(abs_path)

        if not os.path.exists(abs_path):
            file_node.skipped = True
            file_node.error = "File not found"
            self._log(f"  [WARN] File not found: {abs_path}")
            return

        base_dir = os.path.dirname(abs_path)

        self._log(f"Discovering: {abs_path}")

        try:
            with open(abs_path, encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            file_node.skipped = True
            file_node.error = str(e)
            self._log(f"  [WARN] Could not read file: {e}")
            return

        # Find all preprocessor directives
        for line in content.split("\n"):
            match = self.PREPROCESS_PATTERN.search(line)
            if match:
                cmd = match.group(1).lower()
                data = match.group(2)

                if cmd == "set":
                    self.process_set(data)

                elif cmd == "include":
                    self._log(f"  INCLUDE: {data}")
                    include_paths = self.resolve_include_paths(data, base_dir)

                    if not include_paths:
                        self._log(f"  [WARN] No files matched pattern: {data} (from {base_dir})")

                    for inc_path in include_paths:
                        # Optionally validate the file
                        if file_validator:
                            is_valid, _, error = file_validator(inc_path)
                            if not is_valid:
                                self._log(f"  [SKIP] Invalid file {inc_path}: {error}")
                                file_node.children.append(FileNode(path=inc_path, skipped=True, error=error))
                                continue

                        child_node = FileNode(path=inc_path)
                        file_node.children.append(child_node)
                        self.discover_files(inc_path, child_node, file_validator)

        # Remove from visited after processing (allows same file in different branches)
        self._visited_files.discard(abs_path)

    def discover(self, file_path: str, file_validator: Optional[Callable[[str], tuple]] = None) -> FileNode:
        """
        Discover all files starting from the given path.

        Args:
            file_path: Path to the root configuration file
            file_validator: Optional validator function

        Returns:
            Root FileNode containing the full include tree
        """
        abs_path = os.path.abspath(file_path)

        # Reset state
        self._visited_files.clear()
        self.variables.clear()
        self._pre_load_variables()

        root_node = FileNode(path=abs_path)
        self.discover_files(abs_path, root_node, file_validator)

        return root_node
