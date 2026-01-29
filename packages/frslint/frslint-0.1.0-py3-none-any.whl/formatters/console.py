import os
from typing import TYPE_CHECKING, Dict, List

from formatters import AnalyzeFormatter, LintFormatter

if TYPE_CHECKING:
    from analysis.FreeswitchAnalyzer import AnalysisIssue, AnalysisResult, IssueType
    from lint.FreeswitchCodeStyleChecker import LintResult, Violation, ViolationType


class ConsoleLintFormatter(LintFormatter):
    """Human-readable console output for lint results."""

    def format(self, result: "LintResult", fix_mode: bool = False) -> str:
        from lint.FreeswitchCodeStyleChecker import FIXABLE_VIOLATION_TYPES

        lines = []

        if not result.violations:
            lines.append("✓ No style violations found!")
            return "\n".join(lines)

        # Group violations by file
        by_file: Dict[str, List[Violation]] = {}
        for v in result.violations:
            by_file.setdefault(v.file_path, []).append(v)

        # Header
        lines.append("")
        lines.append("=" * 70)
        if fix_mode:
            lines.append(f"LINT RESULTS: {result.fixed_count} fixed, {result.unfixed_count} remaining")
            lines.append(f"Files: {result.files_checked} checked, {result.files_modified} modified")
        else:
            lines.append(f"LINT RESULTS: {result.total_count} issues in {len(by_file)} files")
        lines.append("=" * 70)
        lines.append("")

        # Fixed violations
        if fix_mode and result.fixed_count > 0:
            lines.append("FIXED ISSUES:")
            lines.append("-" * 40)
            for fp, file_violations in sorted(by_file.items()):
                fixed_in_file = [v for v in file_violations if v.fixed]
                if fixed_in_file:
                    lines.append(f"\n{os.path.basename(fp)} ({len(fixed_in_file)} fixed)")
                    lines.append(f"   {fp}")
                    for v in sorted(fixed_in_file, key=lambda x: (x.line, x.column)):
                        lines.append(f"   {v.line:4d}:{v.column:<3d} ✓ [{v.violation_type.value}] {v.message}")
            lines.append("")

        # Unfixed violations
        if result.unfixed_count > 0:
            if fix_mode:
                lines.append("REMAINING UNFIXED ISSUES:")
                lines.append("-" * 40)

            for fp, file_violations in sorted(by_file.items()):
                unfixed_in_file = [v for v in file_violations if not v.fixed]
                if unfixed_in_file:
                    lines.append(f"\n{os.path.basename(fp)} ({len(unfixed_in_file)} issues)")
                    lines.append(f"   {fp}")
                    for v in sorted(unfixed_in_file, key=lambda x: (x.line, x.column)):
                        lines.append(f"   {v.line:4d}:{v.column:<3d} [{v.violation_type.value}] {v.message}")
            lines.append("")

        # Summary by type
        by_type_fixed: Dict[ViolationType, int] = {}
        by_type_unfixed: Dict[ViolationType, int] = {}
        for v in result.violations:
            if v.fixed:
                by_type_fixed[v.violation_type] = by_type_fixed.get(v.violation_type, 0) + 1
            else:
                by_type_unfixed[v.violation_type] = by_type_unfixed.get(v.violation_type, 0) + 1

        lines.append("=" * 70)
        lines.append("SUMMARY BY TYPE:")
        lines.append("=" * 70)

        all_types = set(by_type_fixed.keys()) | set(by_type_unfixed.keys())
        for vtype in sorted(all_types, key=lambda x: -(by_type_fixed.get(x, 0) + by_type_unfixed.get(x, 0))):
            fixed = by_type_fixed.get(vtype, 0)
            unfixed = by_type_unfixed.get(vtype, 0)
            fixable = "fixable" if vtype in FIXABLE_VIOLATION_TYPES else "manual fix required"

            if fix_mode and fixed > 0:
                lines.append(f"  {fixed:4d} fixed, {unfixed:4d} remaining  {vtype.value} ({fixable})")
            else:
                lines.append(f"  {unfixed:4d}  {vtype.value} ({fixable})")

        # Hint about --fix
        if not fix_mode and result.unfixed_count > 0:
            fixable_count = sum(1 for v in result.violations if v.is_fixable)
            if fixable_count > 0:
                lines.append(f"\n💡 Run with --fix to auto-fix {fixable_count} issues")

        return "\n".join(lines)


class ConsoleAnalyzeFormatter(AnalyzeFormatter):
    """Human-readable console output for analysis results."""

    def format(self, result: "AnalysisResult") -> str:
        from analysis.FreeswitchAnalyzer import IssueSeverity

        lines = []

        if not result.issues:
            lines.append("✓ No issues found!")
            return "\n".join(lines)

        # Group by severity
        by_severity: Dict[IssueSeverity, List[AnalysisIssue]] = {}
        for issue in result.issues:
            by_severity.setdefault(issue.severity, []).append(issue)

        # Group by type
        by_type: Dict[IssueType, int] = {}
        for issue in result.issues:
            by_type[issue.issue_type] = by_type.get(issue.issue_type, 0) + 1

        # Count by severity
        error_count = len(by_severity.get(IssueSeverity.ERROR, []))
        warning_count = len(by_severity.get(IssueSeverity.WARNING, []))
        info_count = len(by_severity.get(IssueSeverity.INFO, []))

        lines.append("")
        lines.append("=" * 70)
        lines.append(f"ANALYSIS RESULTS: {error_count} errors, {warning_count} warnings, {info_count} info")
        lines.append("=" * 70)
        lines.append("")

        # Print by severity
        for severity in [IssueSeverity.ERROR, IssueSeverity.WARNING, IssueSeverity.INFO]:
            severity_issues = by_severity.get(severity, [])
            if not severity_issues:
                continue

            icon = {"error": "✗", "warning": "⚠", "info": "ℹ"}[severity.value]
            lines.append(f"{icon} {severity.value.upper()}S ({len(severity_issues)}):")
            lines.append("-" * 70)

            for issue in severity_issues:
                lines.append(f"  [{issue.issue_type.value}] {issue.message}")
                lines.append(f"    Location: {issue.location}")
                if issue.file_path:
                    lines.append(f"    File: {issue.file_path}")
                if issue.suggestion:
                    lines.append(f"    Suggestion: {issue.suggestion}")
                lines.append("")

        lines.append("=" * 70)
        lines.append("SUMMARY BY TYPE:")
        lines.append("=" * 70)
        for itype, count in sorted(by_type.items(), key=lambda x: -x[1]):
            lines.append(f"  {count:4d}  {itype.value}")

        return "\n".join(lines)
