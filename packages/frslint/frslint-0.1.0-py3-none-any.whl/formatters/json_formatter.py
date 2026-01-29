import json
from typing import TYPE_CHECKING

from formatters import AnalyzeFormatter, LintFormatter

if TYPE_CHECKING:
    from analysis.FreeswitchAnalyzer import AnalysisResult
    from lint.FreeswitchCodeStyleChecker import LintResult


class JsonLintFormatter(LintFormatter):
    """JSON output for lint results."""

    def format(self, result: "LintResult", fix_mode: bool = False) -> str:
        from lint.FreeswitchCodeStyleChecker import FIXABLE_VIOLATION_TYPES

        violations = []
        for v in result.violations:
            violations.append(
                {
                    "file": v.file_path,
                    "line": v.line,
                    "column": v.column,
                    "rule": v.violation_type.value,
                    "message": v.message,
                    "fixable": v.violation_type in FIXABLE_VIOLATION_TYPES,
                    "fixed": v.fixed,
                }
            )

        output = {
            "summary": {
                "total": result.total_count,
                "fixed": result.fixed_count,
                "unfixed": result.unfixed_count,
                "files_checked": result.files_checked,
                "files_modified": result.files_modified,
            },
            "violations": violations,
        }

        return json.dumps(output, indent=2)


class JsonAnalyzeFormatter(AnalyzeFormatter):
    """JSON output for analysis results."""

    def format(self, result: "AnalysisResult") -> str:
        issues = []
        for issue in result.issues:
            issues.append(
                {
                    "type": issue.issue_type.value,
                    "severity": issue.severity.value,
                    "message": issue.message,
                    "location": issue.location,
                    "element": issue.element_tag,
                    "file": issue.file_path,
                    "suggestion": issue.suggestion,
                }
            )

        output = {
            "summary": {
                "total": result.total_count,
                "errors": result.error_count,
                "warnings": result.warning_count,
                "info": result.info_count,
            },
            "issues": issues,
        }

        return json.dumps(output, indent=2)
