"""
FreeSWITCH XML configuration code style checker.

Checks for:
- Indentation issues
- Trailing whitespace
- Too many consecutive blank lines
- Missing newline at end of file
- Lines that are too long
- Mixed line endings (CRLF vs LF)
"""

import re
from dataclasses import dataclass, field
from enum import Enum

from discovery.FreeswitchFileDiscovery import FreeswitchFileDiscovery
from log.Loggable import Loggable


class ViolationType(Enum):
    """Types of style violations."""

    TRAILING_WHITESPACE = "trailing-whitespace"
    TABS_INSTEAD_OF_SPACES = "tabs-instead-of-spaces"
    TOO_MANY_BLANK_LINES = "too-many-blank-lines"
    NO_NEWLINE_AT_EOF = "no-newline-at-eof"
    MULTIPLE_NEWLINES_AT_EOF = "multiple-newlines-at-eof"
    LINE_TOO_LONG = "line-too-long"
    MIXED_LINE_ENDINGS = "mixed-line-endings"
    LEADING_WHITESPACE_ON_BLANK = "leading-whitespace-on-blank"
    WRONG_INDENT_SIZE = "wrong-indent-size"


# Violation types that can be auto-fixed
FIXABLE_VIOLATION_TYPES = {
    ViolationType.TRAILING_WHITESPACE,
    ViolationType.TABS_INSTEAD_OF_SPACES,
    ViolationType.TOO_MANY_BLANK_LINES,
    ViolationType.NO_NEWLINE_AT_EOF,
    ViolationType.MULTIPLE_NEWLINES_AT_EOF,
    ViolationType.MIXED_LINE_ENDINGS,
    ViolationType.LEADING_WHITESPACE_ON_BLANK,
    ViolationType.WRONG_INDENT_SIZE,
}


@dataclass
class Violation:
    """Represents a single code style violation."""

    file_path: str
    line: int
    column: int
    violation_type: ViolationType
    message: str
    fixed: bool = False

    @property
    def is_fixable(self) -> bool:
        """Whether this violation type can be auto-fixed."""
        return self.violation_type in FIXABLE_VIOLATION_TYPES

    def __str__(self):
        status = " [FIXED]" if self.fixed else ""
        return f"{self.file_path}:{self.line}:{self.column}: [{self.violation_type.value}] {self.message}{status}"


@dataclass
class LintResult:
    """Result of a lint operation on one or more files."""

    violations: list[Violation] = field(default_factory=list)
    fixed_count: int = 0
    unfixed_count: int = 0
    files_checked: int = 0
    files_modified: int = 0

    @property
    def total_count(self) -> int:
        return len(self.violations)

    @property
    def has_issues(self) -> bool:
        return self.unfixed_count > 0

    def get_fixed(self) -> list[Violation]:
        """Get all fixed violations."""
        return [v for v in self.violations if v.fixed]

    def get_unfixed(self) -> list[Violation]:
        """Get all unfixed violations."""
        return [v for v in self.violations if not v.fixed]


class FreeswitchCodeStyleChecker(Loggable):
    """
    Checks and optionally fixes FreeSWITCH XML configuration files for code style violations.

    Recursively discovers all included files and checks each one.

    Usage:
        checker = FreeswitchCodeStyleChecker()

        # Check only (report issues)
        result = checker.lint('/path/to/freeswitch.xml')

        # Check and fix
        result = checker.lint('/path/to/freeswitch.xml', fix=True)
    """

    def __init__(
        self,
        indent_size: int = 2,
        max_line_length: int = 120,
        max_consecutive_blank_lines: int = 2,
        allow_tabs: bool = False,
        line_ending: str = "\n",
        verbose: bool = False,
    ):
        super().__init__(verbose=verbose)
        self.indent_size = indent_size
        self.max_line_length = max_line_length
        self.max_consecutive_blank_lines = max_consecutive_blank_lines
        self.allow_tabs = allow_tabs
        self.line_ending = line_ending
        self._discovery = FreeswitchFileDiscovery(verbose=verbose)

    def _analyze_line_xml(self, line: str) -> tuple[int, int]:
        """
        Analyze a line for XML tag structure and return indent adjustments.

        Returns:
            Tuple of (indent_before, indent_after):
            - indent_before: adjustment to apply BEFORE this line (for closing tags)
            - indent_after: adjustment to apply AFTER this line (for opening tags)
        """
        stripped = line.strip()

        # Skip empty lines, comments, and non-XML content
        if not stripped or stripped.startswith("<!--") or not stripped.startswith("<"):
            return (0, 0)

        # Skip XML declarations and processing instructions
        if stripped.startswith("<?") or stripped.startswith("<!"):
            return (0, 0)

        indent_before = 0
        indent_after = 0

        # Check if line starts with a closing tag
        if stripped.startswith("</"):
            indent_before = -1

        # Count opening and closing tags to determine indent change after this line
        # Remove strings/attributes to avoid counting < > inside them
        clean = re.sub(r'"[^"]*"', "", stripped)
        clean = re.sub(r"'[^']*'", "", clean)

        # self-closing tags don't change indent

        # Count opening tags (not closing, not self-closing)
        opening = len(re.findall(r"<(?!/)[^>]*(?<!/)>", clean))

        # Count closing tags
        closing = len(re.findall(r"</[^>]+>", clean))

        # Net change after this line (opening adds, closing subtracts, self-closing neutral)
        indent_after = opening - closing

        # If line starts with closing tag, we already subtracted 1 before
        if stripped.startswith("</"):
            indent_after += 1

        return (indent_before, indent_after)

    def _check_file(self, file_path: str) -> list[Violation]:
        """Check a single file for style violations (without fixing)."""
        violations = []

        try:
            with open(file_path, "rb") as f:
                raw_content = f.read()
        except Exception as e:
            violations.append(
                Violation(
                    file_path=file_path,
                    line=0,
                    column=0,
                    violation_type=ViolationType.TRAILING_WHITESPACE,
                    message=f"Could not read file: {e}",
                )
            )
            return violations

        # Check for mixed line endings
        has_crlf = b"\r\n" in raw_content
        has_lf_only = b"\n" in raw_content.replace(b"\r\n", b"")
        has_cr_only = b"\r" in raw_content.replace(b"\r\n", b"")

        if sum([has_crlf, has_lf_only, has_cr_only]) > 1:
            violations.append(
                Violation(
                    file_path=file_path,
                    line=1,
                    column=1,
                    violation_type=ViolationType.MIXED_LINE_ENDINGS,
                    message="File has mixed line endings (CRLF and LF)",
                )
            )

        # Decode content
        try:
            content = raw_content.decode("utf-8")
        except UnicodeDecodeError:
            content = raw_content.decode("latin-1")

        lines = content.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        consecutive_blank_lines = 0
        current_depth = 0

        for line_num, line in enumerate(lines, start=1):
            # Trailing whitespace (not on blank lines)
            if line.rstrip() != line and line.strip():
                violations.append(
                    Violation(
                        file_path=file_path,
                        line=line_num,
                        column=len(line.rstrip()) + 1,
                        violation_type=ViolationType.TRAILING_WHITESPACE,
                        message=f"Trailing whitespace ({len(line) - len(line.rstrip())} characters)",
                    )
                )

            # Whitespace on blank lines
            if not line.strip() and line:
                violations.append(
                    Violation(
                        file_path=file_path,
                        line=line_num,
                        column=1,
                        violation_type=ViolationType.LEADING_WHITESPACE_ON_BLANK,
                        message=f"Blank line contains whitespace ({len(line)} characters)",
                    )
                )

            # Tabs
            if "\t" in line and not self.allow_tabs:
                violations.append(
                    Violation(
                        file_path=file_path,
                        line=line_num,
                        column=line.index("\t") + 1,
                        violation_type=ViolationType.TABS_INSTEAD_OF_SPACES,
                        message="Tab character found (use spaces instead)",
                    )
                )

            # Line length
            if len(line) > self.max_line_length:
                violations.append(
                    Violation(
                        file_path=file_path,
                        line=line_num,
                        column=self.max_line_length + 1,
                        violation_type=ViolationType.LINE_TOO_LONG,
                        message=f"Line too long ({len(line)} > {self.max_line_length})",
                    )
                )

            # Consecutive blank lines
            if not line.strip():
                consecutive_blank_lines += 1
            else:
                if consecutive_blank_lines > self.max_consecutive_blank_lines:
                    violations.append(
                        Violation(
                            file_path=file_path,
                            line=line_num - 1,
                            column=1,
                            violation_type=ViolationType.TOO_MANY_BLANK_LINES,
                            message=f"Too many consecutive blank lines ({consecutive_blank_lines} > {self.max_consecutive_blank_lines})",
                        )
                    )
                consecutive_blank_lines = 0

            # Indentation check based on XML nesting depth
            stripped = line.strip()
            if stripped and not stripped.startswith("<!--"):
                indent_before, indent_after = self._analyze_line_xml(line)
                expected_depth = max(0, current_depth + indent_before)
                expected_indent = expected_depth * self.indent_size
                leading_spaces = len(line) - len(line.lstrip(" "))

                if stripped.startswith("<") and "\t" not in line[:leading_spaces] and leading_spaces != expected_indent:
                    violations.append(
                        Violation(
                            file_path=file_path,
                            line=line_num,
                            column=1,
                            violation_type=ViolationType.WRONG_INDENT_SIZE,
                            message=f"Wrong indentation: expected {expected_indent} spaces (depth {expected_depth}), got {leading_spaces}",
                        )
                    )

                current_depth = max(0, current_depth + indent_before + indent_after)

        # Newline at end of file
        if content and not content.endswith("\n"):
            violations.append(
                Violation(
                    file_path=file_path,
                    line=len(lines),
                    column=len(lines[-1]) + 1 if lines else 1,
                    violation_type=ViolationType.NO_NEWLINE_AT_EOF,
                    message="No newline at end of file",
                )
            )

        # Multiple newlines at end of file
        if content.endswith("\n\n"):
            trailing = len(content) - len(content.rstrip("\n\r"))
            if trailing > 1:
                violations.append(
                    Violation(
                        file_path=file_path,
                        line=len(lines),
                        column=1,
                        violation_type=ViolationType.MULTIPLE_NEWLINES_AT_EOF,
                        message=f"Multiple newlines at end of file ({trailing})",
                    )
                )

        return violations

    def _fix_file(self, file_path: str) -> tuple[list[Violation], list[Violation], bool]:
        """
        Fix a single file and return violations.

        Returns:
            Tuple of (fixed_violations, remaining_violations, file_was_modified)
        """
        fixed_violations = []
        remaining_violations = []

        try:
            with open(file_path, "rb") as f:
                raw_content = f.read()
        except Exception as e:
            remaining_violations.append(
                Violation(
                    file_path=file_path,
                    line=0,
                    column=0,
                    violation_type=ViolationType.TRAILING_WHITESPACE,
                    message=f"Could not read file: {e}",
                )
            )
            return [], remaining_violations, False

        # Decode content
        try:
            content = raw_content.decode("utf-8")
            encoding = "utf-8"
        except UnicodeDecodeError:
            content = raw_content.decode("latin-1")
            encoding = "latin-1"

        # Track original issues before fixing
        original_violations = self._check_file(file_path)

        # Apply fixes
        fixed_content = content

        # Fix mixed line endings
        has_crlf = "\r\n" in fixed_content
        has_cr = "\r" in fixed_content.replace("\r\n", "")
        if has_crlf or has_cr:
            fixed_content = fixed_content.replace("\r\n", "\n").replace("\r", "\n")

        lines = fixed_content.split("\n")
        fixed_lines = []
        current_depth = 0
        consecutive_blank_count = 0

        for line in lines:
            # Fix tabs
            if "\t" in line and not self.allow_tabs:
                line = line.replace("\t", " " * self.indent_size)

            # Fix trailing whitespace on non-blank lines
            if line.strip() and line.rstrip() != line:
                line = line.rstrip()

            # Fix whitespace on blank lines
            if not line.strip() and line:
                line = ""

            # Handle consecutive blank lines
            if not line.strip():
                consecutive_blank_count += 1
                if consecutive_blank_count > self.max_consecutive_blank_lines:
                    continue  # Skip excess blank line
            else:
                consecutive_blank_count = 0

            # Fix indentation for XML lines
            stripped = line.strip()
            if stripped and stripped.startswith("<") and not stripped.startswith("<!--"):
                indent_before, indent_after = self._analyze_line_xml(line)
                expected_depth = max(0, current_depth + indent_before)
                expected_indent = expected_depth * self.indent_size
                leading_spaces = len(line) - len(line.lstrip())

                if leading_spaces != expected_indent:
                    line = " " * expected_indent + stripped

                current_depth = max(0, current_depth + indent_before + indent_after)

            fixed_lines.append(line)

        # Remove trailing blank lines
        while len(fixed_lines) > 1 and not fixed_lines[-1].strip():
            fixed_lines.pop()

        # Join and ensure single newline at EOF
        fixed_content = self.line_ending.join(fixed_lines)
        if fixed_content and not fixed_content.endswith(self.line_ending):
            fixed_content += self.line_ending

        # Check if content changed
        original_normalized = content.replace("\r\n", "\n").replace("\r", "\n")
        file_modified = fixed_content != original_normalized

        # Write fixed content
        if file_modified:
            try:
                with open(file_path, "w", encoding=encoding, newline="") as f:
                    f.write(fixed_content)
            except Exception as e:
                remaining_violations.append(
                    Violation(
                        file_path=file_path,
                        line=0,
                        column=0,
                        violation_type=ViolationType.TRAILING_WHITESPACE,
                        message=f"Could not write file: {e}",
                    )
                )
                return [], remaining_violations, False

        # Re-check file to find remaining issues
        post_fix_violations = self._check_file(file_path)

        # Categorize violations as fixed or remaining
        post_fix_set = {(v.line, v.column, v.violation_type) for v in post_fix_violations}

        for v in original_violations:
            key = (v.line, v.column, v.violation_type)
            if key in post_fix_set:
                # Still exists after fix - it's unfixable (like LINE_TOO_LONG)
                remaining_violations.append(v)
            else:
                # No longer exists - it was fixed
                v.fixed = True
                fixed_violations.append(v)

        return fixed_violations, remaining_violations, file_modified

    def lint(self, file_path: str, fix: bool = False) -> LintResult:
        """
        Lint a FreeSWITCH configuration and all includes.

        Args:
            file_path: Path to the root configuration file
            fix: If True, automatically fix fixable issues

        Returns:
            LintResult with all violations (both fixed and unfixed)
        """
        # Discover all files
        root_node = self._discovery.discover(file_path)
        all_files = root_node.get_all_files()

        self._log(f"Discovered {len(all_files)} files to lint")

        result = LintResult(files_checked=len(all_files))

        for file in all_files:
            self._log(f"Linting file: {file}")

            if fix:
                fixed, remaining, modified = self._fix_file(file)
                result.violations.extend(fixed)
                result.violations.extend(remaining)
                result.fixed_count += len(fixed)
                result.unfixed_count += len(remaining)
                if modified:
                    result.files_modified += 1
            else:
                violations = self._check_file(file)
                result.violations.extend(violations)
                result.unfixed_count += len(violations)

        return result
