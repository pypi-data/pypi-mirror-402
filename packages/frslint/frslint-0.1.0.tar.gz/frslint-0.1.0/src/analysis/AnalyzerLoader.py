import os
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape as xml_escape

from discovery.FileNode import FileNode
from discovery.FreeswitchFileDiscovery import FreeswitchFileDiscovery


class AnalyzerLoader(FreeswitchFileDiscovery):
    """Internal loader for the analyzer - loads and expands XML without all the printing."""

    def _validate_xml_file(self, file_path: str) -> tuple:
        content = ""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
            wrapped = f"<_root_>{content}</_root_>"
            ET.fromstring(wrapped)
            return (True, content, None)
        except ET.ParseError as e:
            return (False, content, str(e))
        except Exception as e:
            return (False, content, str(e))

    def _inject_source_file_attr(self, content: str, file_path: str) -> str:
        """Inject _source_file attribute into top-level XML elements."""
        import re

        # Escape file path for use in XML attribute (handle &, <, >, ", ')
        escaped_path = xml_escape(file_path, {'"': "&quot;"})

        # More robust regex that handles quoted attribute values properly
        # This matches tag name, then any attributes (properly handling quotes), then > or />
        # Pattern for attributes: word="value" or word='value' with possible spaces
        attr_pattern = r'(?:\s+[\w:-]+\s*=\s*(?:"[^"]*"|\'[^\']*\'))*'

        def add_attr(match):
            tag = match.group(1)
            attrs = match.group(2) or ""
            closing = match.group(3)  # captures "\s*/>" or ">"
            # Don't add if already has _source_file
            if "_source_file=" in attrs:
                return match.group(0)
            # Add attribute before the closing > or />
            if closing.strip() == "/>":
                return f'<{tag}{attrs} _source_file="{escaped_path}"/>'
            else:
                return f'<{tag}{attrs} _source_file="{escaped_path}">'

        # Match tags we care about for source tracking
        # Capture the closing part including optional whitespace before />
        pattern = rf"<(context|extension|condition|action|anti-action)({attr_pattern})(\s*/?>)"
        return re.sub(pattern, add_attr, content)

    def _expand_file(self, file_path: str, file_node: FileNode) -> str:
        abs_path = os.path.abspath(file_path)

        if abs_path in self._visited_files:
            return "<!-- CIRCULAR -->"

        self._visited_files.add(abs_path)

        if not os.path.exists(abs_path):
            return "<!-- NOT FOUND -->"

        base_dir = os.path.dirname(abs_path)

        with open(abs_path, encoding="utf-8") as f:
            content = f.read()

        result_lines = []

        for line in content.split("\n"):
            match = self.PREPROCESS_PATTERN.search(line)

            if match:
                cmd = match.group(1).lower()
                data = match.group(2)

                if cmd == "set":
                    self.process_set(data)
                    result_lines.append(f"<!-- set: {data} -->")
                elif cmd == "include":
                    include_paths = self.resolve_include_paths(data, base_dir)
                    for inc_path in include_paths:
                        is_valid, _, error = self._validate_xml_file(inc_path)
                        if not is_valid:
                            file_node.children.append(FileNode(path=inc_path, skipped=True, error=error))
                            continue
                        child_node = FileNode(path=inc_path)
                        file_node.children.append(child_node)
                        expanded = self._expand_file(inc_path, child_node)
                        result_lines.append(expanded)
                else:
                    result_lines.append(line)
            else:
                result_lines.append(line)

        self._visited_files.discard(abs_path)

        # Inject source file attribute into elements from this file
        result = "\n".join(result_lines)
        return self._inject_source_file_attr(result, abs_path)

    def load_for_analysis(self, file_path: str) -> tuple:
        """Load and return (root_element, variables) for analysis."""
        abs_path = os.path.abspath(file_path)

        self._visited_files.clear()
        self.variables.clear()
        self._pre_load_variables()

        root_node = FileNode(path=abs_path)
        expanded_content = self._expand_file(abs_path, root_node)

        try:
            root = ET.fromstring(expanded_content)
            return (root, dict(self.variables))
        except ET.ParseError as e:
            print(f"[ERROR] Failed to parse XML: {e}")
            return (None, {})
