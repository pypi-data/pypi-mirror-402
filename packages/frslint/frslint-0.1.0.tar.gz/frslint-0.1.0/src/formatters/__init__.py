from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from analysis.FreeswitchAnalyzer import AnalysisResult
    from lint.FreeswitchCodeStyleChecker import LintResult


class LintFormatter(ABC):
    @abstractmethod
    def format(self, result: "LintResult", fix_mode: bool = False) -> str:
        """Format lint result and return as string."""
        pass

    def print(self, result: "LintResult", fix_mode: bool = False) -> None:
        """Format and print to stdout."""
        print(self.format(result, fix_mode))


class AnalyzeFormatter(ABC):
    @abstractmethod
    def format(self, result: "AnalysisResult") -> str:
        """Format analysis result and return as string."""
        pass

    def print(self, result: "AnalysisResult") -> None:
        """Format and print to stdout."""
        print(self.format(result))


# Import concrete formatters
from formatters.console import ConsoleAnalyzeFormatter, ConsoleLintFormatter
from formatters.json_formatter import JsonAnalyzeFormatter, JsonLintFormatter

# Explicit formatter mappings
LINT_FORMATTERS = {
    "console": ConsoleLintFormatter,
    "json": JsonLintFormatter,
}

ANALYZE_FORMATTERS = {
    "console": ConsoleAnalyzeFormatter,
    "json": JsonAnalyzeFormatter,
}


def get_lint_formatter(name: str) -> LintFormatter:
    """Get a lint formatter by name."""
    if name not in LINT_FORMATTERS:
        available = ", ".join(LINT_FORMATTERS.keys())
        raise ValueError(f"Unknown lint formatter: {name}. Available: {available}")
    return LINT_FORMATTERS[name]()


def get_analyze_formatter(name: str) -> AnalyzeFormatter:
    """Get an analyze formatter by name."""
    if name not in ANALYZE_FORMATTERS:
        available = ", ".join(ANALYZE_FORMATTERS.keys())
        raise ValueError(f"Unknown analyze formatter: {name}. Available: {available}")
    return ANALYZE_FORMATTERS[name]()


def available_formats() -> list:
    """Return list of available format names."""
    return list(LINT_FORMATTERS.keys())
