"""
FreeSWITCH configuration static analyzer.

Performs static analysis checks similar to PHPStan for PHP:
- Variable usage analysis
- Dialplan logic validation
- Attribute validation
- Duplicate detection
- Application validation
"""

import os
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set

from analysis.AnalyzerLoader import AnalyzerLoader
from discovery.FreeswitchFileDiscovery import FreeswitchFileDiscovery
from log.Loggable import Loggable


class IssueSeverity(Enum):
    """Severity levels for analysis issues."""

    ERROR = "error"  # Definitely wrong, will cause problems
    WARNING = "warning"  # Likely wrong or bad practice
    INFO = "info"  # Informational, may be intentional


class IssueType(Enum):
    """Types of analysis issues."""

    UNDEFINED_VARIABLE = "undefined-variable"
    UNCLOSED_VARIABLE = "unclosed-variable"
    EMPTY_EXTENSION = "empty-extension"
    UNREACHABLE_ACTION = "unreachable-action"
    INVALID_REGEX = "invalid-regex"
    UNKNOWN_APPLICATION = "unknown-application"
    DUPLICATE_CONTEXT = "duplicate-context"
    MISSING_REQUIRED_ATTRIBUTE = "missing-required-attribute"
    INVALID_ATTRIBUTE_VALUE = "invalid-attribute-value"


@dataclass
class AnalysisIssue:
    """Represents a single analysis issue."""

    issue_type: IssueType
    severity: IssueSeverity
    message: str
    location: str  # e.g., "context:default > extension:test > condition:1"
    element_tag: str
    suggestion: Optional[str] = None
    file_path: Optional[str] = None

    def __str__(self):
        sev = self.severity.value.upper()
        file_info = f"\n  File: {self.file_path}" if self.file_path else ""
        return f"[{sev}] {self.issue_type.value}: {self.message}\n  Location: {self.location}{file_info}"


@dataclass
class AnalysisResult:
    """Result of an analysis operation."""

    issues: List[AnalysisIssue] = field(default_factory=list)

    @property
    def total_count(self) -> int:
        return len(self.issues)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == IssueSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == IssueSeverity.WARNING)

    @property
    def info_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == IssueSeverity.INFO)

    @property
    def has_errors(self) -> bool:
        return self.error_count > 0


# Known FreeSWITCH dialplan applications
# This is not exhaustive but covers common ones
KNOWN_APPLICATIONS = {
    # Core applications
    "answer",
    "pre_answer",
    "ring_ready",
    "hangup",
    "sleep",
    "bridge",
    "transfer",
    "set",
    "unset",
    "export",
    "log",
    "info",
    "event",
    "playback",
    "play_and_get_digits",
    "read",
    "say",
    "speak",
    "record",
    "record_session",
    "stop_record_session",
    "conference",
    "fifo",
    "voicemail",
    "ivr",
    "menu",
    "park",
    "valet_park",
    "hold",
    "unhold",
    "att_xfer",
    "blind_xfer",
    "intercept",
    "eavesdrop",
    "three_way",
    "execute_extension",
    "socket",
    "lua",
    "python",
    "javascript",
    "perl",
    "echo",
    "delay_echo",
    "tone_detect",
    "spandsp_detect_tdd",
    "bind_digit_action",
    "clear_digit_action",
    "digit_action_set_realm",
    "privacy",
    "cng_plc",
    "jitterbuffer",
    "limit",
    "limit_execute",
    "hash",
    "group",
    "db",
    "httapi",
    "cidlookup",
    "fax_detect",
    "spandsp_start_fax_detect",
    "spandsp_stop_fax_detect",
    "rxfax",
    "txfax",
    "t38_gateway",
    "sched_hangup",
    "sched_transfer",
    "sched_broadcast",
    "uuid_broadcast",
    "uuid_bridge",
    "uuid_transfer",
    "deflect",
    "respond",
    "redirect",
    "send_display",
    "endless_playback",
    "loop_playback",
    "file_string",
    "gentones",
    "displace_session",
    "stop_displace_session",
    "start_dtmf",
    "stop_dtmf",
    "start_dtmf_generate",
    "stop_dtmf_generate",
    "queue_dtmf",
    "send_dtmf",
    "flush_dtmf",
    "multiset",
    "push",
    "rename",
    "soft_hold",
    "bind_meta_app",
    "unbind_meta_app",
    "session_loglevel",
    "sched_heartbeat",
    "enable_heartbeat",
    "disable_heartbeat",
    "strftime",
    "strepoch",
    "chat",
    "presence",
    "allow_hierarchical_logging_to_be_disabled_per_channel",
    "check_acl",
    "early_hangup",
    "mkdir",
    "system",
    "bg_system",
    "curl",
    # mod_dptools
    "busy",
    "send_info",
    "wait_for_answer",
    "wait_for_silence",
    "detect_speech",
    "stop_detect_speech",
    "play_and_detect_speech",
    "capture",
    "clear_speech_cache",
    "media_reset",
    "deduplicate_dtmf",
    "sound_test",
    "stop_and_forward_list_sounds",
    # Video
    "video_refresh",
    "video_write_overlay",
    # Variables
    "set_global",
    "set_profile_var",
    "set_user",
    "set_zombie_exec",
    "unshift",
    "local_stream",
    "phrase",
    "play_fsv",
    # Mod specific
    "sofia",
    "verto",
    "rtc",
    "skinny",
    "loopback",
    "portaudio",
    "dingaling",
    "enum",
    "lcr",
    "easyroute",
    "distributor",
    "spy",
    "callcenter",
    "mod_commands",
    "originate",
    "recovery_refresh",
    "recovery_send_event",
    "send_bye",
    "verbose_events",
    "cluechoo",
    "counter",
}

# Valid values for break attribute
VALID_BREAK_VALUES = {"on-true", "on-false", "always", "never"}

# Valid values for continue attribute (on extension)
VALID_CONTINUE_VALUES = {"true", "false"}


class FreeswitchAnalyzer(Loggable):
    """
    Static analyzer for FreeSWITCH XML configuration.

    Checks for common issues like undefined variables, empty extensions,
    invalid regex patterns, unknown applications, etc.
    """

    def __init__(self, verbose: bool = False):
        super().__init__(verbose=verbose)
        self._discovery = FreeswitchFileDiscovery(verbose=verbose)
        self.issues: List[AnalysisIssue] = []
        self._defined_variables: Set[str] = set()
        self._used_variables: Set[str] = set()
        self._context_names: Dict[str, int] = {}  # name -> count

    def _add_issue(
        self,
        issue_type: IssueType,
        severity: IssueSeverity,
        message: str,
        location: str,
        element_tag: str,
        suggestion: Optional[str] = None,
        file_path: Optional[str] = None,
    ):
        self.issues.append(
            AnalysisIssue(
                issue_type=issue_type,
                severity=severity,
                message=message,
                location=location,
                element_tag=element_tag,
                suggestion=suggestion,
                file_path=file_path,
            )
        )

    def _build_location(self, path: List[str]) -> str:
        """Build a human-readable location string."""
        return " > ".join(path)

    def _get_source_file(self, element: ET.Element) -> Optional[str]:
        """Extract source file from element's _source_file attribute."""
        return element.attrib.get("_source_file")

    def _extract_variables(self, text: str) -> Set[str]:
        """Extract all $${var} references from text."""
        pattern = r"\$\$\{([^}]+)\}"
        return set(re.findall(pattern, text))

    def _check_unclosed_variables(self, text: str, location: str, element_tag: str, file_path: Optional[str] = None):
        """
        Check for unclosed variable references like ${ or $${ without closing }.

        Handles nested variables like: ${hash(select/callnum/${yd_cc_key})}
        """
        i = 0
        while i < len(text):
            # Check for $${ first (longer match) - global variable
            if text[i : i + 3] == "$${":
                var_type = "global"
                start_pos = i
                i += 3  # Skip past $${
                brace_count = 1

                # Scan for matching closing brace, counting nested braces
                while i < len(text) and brace_count > 0:
                    if text[i] == "{":
                        brace_count += 1
                    elif text[i] == "}":
                        brace_count -= 1
                    i += 1

                if brace_count > 0:
                    # Unclosed - didn't find matching }
                    snippet = text[start_pos : min(start_pos + 30, len(text))]
                    if len(text) > start_pos + 30:
                        snippet += "..."
                    self._add_issue(
                        IssueType.UNCLOSED_VARIABLE,
                        IssueSeverity.WARNING,
                        f"Unclosed global variable reference: '{snippet}'",
                        location,
                        element_tag,
                        suggestion="Add closing } to complete the variable reference",
                        file_path=file_path,
                    )

            # Check for ${ (channel variable)
            elif text[i : i + 2] == "${":
                var_type = "channel"
                start_pos = i
                i += 2  # Skip past ${
                brace_count = 1

                # Scan for matching closing brace, counting nested braces
                while i < len(text) and brace_count > 0:
                    if text[i] == "{":
                        brace_count += 1
                    elif text[i] == "}":
                        brace_count -= 1
                    i += 1

                if brace_count > 0:
                    # Unclosed - didn't find matching }
                    snippet = text[start_pos : min(start_pos + 30, len(text))]
                    if len(text) > start_pos + 30:
                        snippet += "..."
                    self._add_issue(
                        IssueType.UNCLOSED_VARIABLE,
                        IssueSeverity.WARNING,
                        f"Unclosed channel variable reference: '{snippet}'",
                        location,
                        element_tag,
                        suggestion="Add closing } to complete the variable reference",
                        file_path=file_path,
                    )
            else:
                i += 1

    def _check_regex(self, pattern: str) -> Optional[str]:
        """Check if regex is valid. Returns error message or None."""
        try:
            re.compile(pattern)
            return None
        except re.error as e:
            return str(e)

    def _analyze_condition(self, condition: ET.Element, path: List[str]):
        """Analyze a single condition element."""
        cond_path = path + ["condition"]
        location = self._build_location(cond_path)
        source_file = self._get_source_file(condition)

        field = condition.attrib.get("field")
        expression = condition.attrib.get("expression")
        break_val = condition.attrib.get("break")

        # Check for required attributes (unless it's an unconditional condition)
        # An unconditional condition has neither field nor expression
        has_field = field is not None
        has_expression = expression is not None

        if has_field != has_expression:
            # One is set but not the other
            if has_field and not has_expression:
                self._add_issue(
                    IssueType.MISSING_REQUIRED_ATTRIBUTE,
                    IssueSeverity.ERROR,
                    "Condition has 'field' but missing 'expression'",
                    location,
                    "condition",
                    suggestion="Add expression attribute or remove field",
                    file_path=source_file,
                )
            elif has_expression and not has_field:
                self._add_issue(
                    IssueType.MISSING_REQUIRED_ATTRIBUTE,
                    IssueSeverity.ERROR,
                    "Condition has 'expression' but missing 'field'",
                    location,
                    "condition",
                    suggestion="Add field attribute or remove expression",
                    file_path=source_file,
                )

        # Check break attribute value
        if break_val is not None and break_val not in VALID_BREAK_VALUES:
            self._add_issue(
                IssueType.INVALID_ATTRIBUTE_VALUE,
                IssueSeverity.ERROR,
                f"Invalid break value: '{break_val}'",
                location,
                "condition",
                suggestion=f"Valid values: {', '.join(sorted(VALID_BREAK_VALUES))}",
                file_path=source_file,
            )

        # Validate regex if expression is present
        if expression:
            # Check for unclosed variable references
            self._check_unclosed_variables(expression, location, "condition", source_file)

            # Extract variables used in expression
            self._used_variables.update(self._extract_variables(expression))

            # Check regex validity
            regex_error = self._check_regex(expression)
            if regex_error:
                self._add_issue(
                    IssueType.INVALID_REGEX,
                    IssueSeverity.ERROR,
                    f"Invalid regex '{expression}': {regex_error}",
                    location,
                    "condition",
                    file_path=source_file,
                )

        # Analyze actions
        actions = list(condition.findall("action")) + list(condition.findall("anti-action"))
        self._analyze_actions(actions, cond_path)

    def _analyze_actions(self, actions: List[ET.Element], path: List[str]):
        """Analyze a list of actions, checking for unreachable code."""
        found_terminating = False
        terminating_app = None

        for i, action in enumerate(actions):
            action_type = action.tag  # "action" or "anti-action"
            app = action.attrib.get("application", "")
            data = action.attrib.get("data", "")
            source_file = self._get_source_file(action)

            action_path = path + [f"{action_type}:{app}"]
            location = self._build_location(action_path)

            # Check if this action is unreachable
            if found_terminating:
                self._add_issue(
                    IssueType.UNREACHABLE_ACTION,
                    IssueSeverity.WARNING,
                    f"Action '{app}' is unreachable after '{terminating_app}'",
                    location,
                    action_type,
                    suggestion=f"Remove this action or move it before '{terminating_app}'",
                    file_path=source_file,
                )

            # Check for unknown application
            if app and app.lower() not in KNOWN_APPLICATIONS:
                # Check if it might be a custom app (contains underscore, likely module-specific)
                if not app.startswith("mod_") and "_" not in app:
                    self._add_issue(
                        IssueType.UNKNOWN_APPLICATION,
                        IssueSeverity.WARNING,
                        f"Unknown application: '{app}'",
                        location,
                        action_type,
                        suggestion="Check spelling or ensure the module is loaded",
                        file_path=source_file,
                    )

            # Check for missing application attribute
            if not app:
                self._add_issue(
                    IssueType.MISSING_REQUIRED_ATTRIBUTE,
                    IssueSeverity.ERROR,
                    "Action missing 'application' attribute",
                    location,
                    action_type,
                    file_path=source_file,
                )

            # Extract variables from data and check for unclosed references
            if data:
                self._check_unclosed_variables(data, location, action_type, source_file)
                self._used_variables.update(self._extract_variables(data))

            # Check for terminating applications
            terminating_apps = {"hangup", "transfer", "redirect", "deflect"}
            if app.lower() in terminating_apps:
                # transfer with inline dialplan may not be terminating
                # but we'll flag it anyway as it usually is
                found_terminating = True
                terminating_app = app

    def _analyze_extension(self, extension: ET.Element, path: List[str]):
        """Analyze a single extension element."""
        ext_name = extension.attrib.get("name", "(unnamed)")
        continue_val = extension.attrib.get("continue")
        source_file = self._get_source_file(extension)

        ext_path = path + [f"extension:{ext_name}"]
        location = self._build_location(ext_path)

        # Check continue attribute value
        if continue_val is not None and continue_val not in VALID_CONTINUE_VALUES:
            self._add_issue(
                IssueType.INVALID_ATTRIBUTE_VALUE,
                IssueSeverity.ERROR,
                f"Invalid continue value: '{continue_val}'",
                location,
                "extension",
                suggestion=f"Valid values: {', '.join(sorted(VALID_CONTINUE_VALUES))}",
                file_path=source_file,
            )

        # Check for empty extension
        conditions = list(extension.findall("condition"))
        if not conditions:
            self._add_issue(
                IssueType.EMPTY_EXTENSION,
                IssueSeverity.WARNING,
                f"Extension '{ext_name}' has no conditions",
                location,
                "extension",
                suggestion="Add at least one condition element",
                file_path=source_file,
            )

        # Analyze each condition
        for i, condition in enumerate(conditions):
            self._analyze_condition(condition, ext_path)

    def _analyze_context(self, context: ET.Element, path: List[str]):
        """Analyze a single context element."""
        ctx_name = context.attrib.get("name", "(unnamed)")
        ctx_path = path + [f"context:{ctx_name}"]
        location = self._build_location(ctx_path)

        # Track context names for duplicate detection
        self._context_names[ctx_name] = self._context_names.get(ctx_name, 0) + 1

        # Find all extensions (may be nested in <include> tags)
        extensions = []
        for child in context:
            if child.tag == "extension":
                extensions.append(child)
            elif child.tag == "include":
                extensions.extend(child.findall("extension"))

        # Analyze each extension
        for extension in extensions:
            self._analyze_extension(extension, ctx_path)

    def _analyze_dialplan_section(self, section: ET.Element, path: List[str]):
        """Analyze the dialplan section."""
        dialplan_path = path + ["section:dialplan"]

        # Find all contexts (may be nested in <include> tags)
        contexts = []
        for child in section:
            if child.tag == "context":
                contexts.append(child)
            elif child.tag == "include":
                contexts.extend(child.findall("context"))

        for context in contexts:
            self._analyze_context(context, dialplan_path)

    def _analyze_xml(self, root: ET.Element):
        """Analyze the full XML tree."""
        path = ["document"]

        # Find dialplan section
        for section in root.findall(".//section"):
            section_name = section.attrib.get("name", "")
            if section_name == "dialplan":
                self._analyze_dialplan_section(section, path)

    def _check_undefined_variables(self):
        """Check for variables used but never defined."""
        # Pre-defined variables that FreeSWITCH always has
        builtin_vars = {
            "hostname",
            "local_ip_v4",
            "local_mask_v4",
            "local_ip_v6",
            "switch_serial",
            "base_dir",
            "recordings_dir",
            "sound_prefix",
            "sounds_dir",
            "conf_dir",
            "log_dir",
            "run_dir",
            "db_dir",
            "mod_dir",
            "htdocs_dir",
            "script_dir",
            "temp_dir",
            "grammar_dir",
            "certs_dir",
            "storage_dir",
            "cache_dir",
            "core_uuid",
            "zrtp_enabled",
            "nat_public_addr",
            "nat_private_addr",
            "nat_type",
        }

        undefined = self._used_variables - self._defined_variables - builtin_vars

        for var in sorted(undefined):
            self._add_issue(
                IssueType.UNDEFINED_VARIABLE,
                IssueSeverity.ERROR,
                f"Variable '${{{{{var}}}}}' is used but never defined",
                "global",
                "variable",
                suggestion=f'Add: <X-PRE-PROCESS cmd="set" data="{var}=value"/>',
            )

    def _check_duplicate_contexts(self):
        """Check for duplicate context names."""
        for name, count in self._context_names.items():
            if count > 1:
                self._add_issue(
                    IssueType.DUPLICATE_CONTEXT,
                    IssueSeverity.WARNING,
                    f"Context '{name}' is defined {count} times",
                    "global",
                    "context",
                    suggestion="Merge contexts or use unique names",
                )

    def analyze(self, file_path: str) -> AnalysisResult:
        """
        Analyze a FreeSWITCH configuration file.

        Args:
            file_path: Path to the main configuration file

        Returns:
            AnalysisResult containing all issues found
        """
        abs_path = os.path.abspath(file_path)

        # Reset state
        self.issues = []
        self._defined_variables = set()
        self._used_variables = set()
        self._context_names = {}

        self._log(f"Analyzing file: {abs_path}")

        # Use the discovery/loader to get expanded XML
        loader = AnalyzerLoader(verbose=self.verbose)
        root, variables = loader.load_for_analysis(file_path)

        if root is None:
            return AnalysisResult(issues=self.issues)

        # Track defined variables
        self._defined_variables = set(variables.keys())

        # Analyze the XML tree
        self._analyze_xml(root)

        # Post-analysis checks
        self._check_undefined_variables()
        self._check_duplicate_contexts()

        return AnalysisResult(issues=self.issues)
