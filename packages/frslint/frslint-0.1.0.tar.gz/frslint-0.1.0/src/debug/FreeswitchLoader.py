"""
FreeSWITCH configuration loader that properly handles recursive X-PRE-PROCESS includes.

The key insight: process includes at the TEXT level before XML parsing.
This avoids complications with modifying XML trees during iteration.
"""

import os
import xml.etree.ElementTree as ET

from debug.Freeswitch import Freeswitch
from debug.FreeswitchConfigurationParser import FreeswitchConfigurationParser
from debug.FreeswitchInstructionParser import FreeswitchInstructionParser
from discovery.FileNode import FileNode
from discovery.FreeswitchFileDiscovery import FreeswitchFileDiscovery


class FreeswitchLoader(FreeswitchFileDiscovery):
    """
    Loads FreeSWITCH XML configuration with full support for recursive includes.

    Extends FreeswitchFileDiscovery to add XML expansion and parsing.
    """

    def __init__(self, verbose: bool = False):
        super().__init__(verbose=verbose)

    def _validate_xml_file(self, file_path: str) -> tuple:
        """
        Validate that a file contains parseable XML.

        Since included files are often XML fragments (not complete documents),
        we wrap the content in a root element before parsing.

        Returns:
            Tuple of (is_valid: bool, content: str, error: Optional[str])
        """
        content = ""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Wrap in root element to handle fragments
            wrapped = f"<_root_>{content}</_root_>"
            ET.fromstring(wrapped)
            return (True, content, None)
        except ET.ParseError as e:
            return (False, content, str(e))
        except Exception as e:
            return (False, content, str(e))

    def _expand_file(self, file_path: str, file_node: FileNode) -> str:
        """
        Read a file and recursively expand all X-PRE-PROCESS directives.

        Returns:
            The fully expanded content as a string
        """
        abs_path = os.path.abspath(file_path)

        # Cycle detection
        if abs_path in self._visited_files:
            self._log(f"  [WARN] Skipping circular include: {abs_path}")
            return f"<!-- CIRCULAR INCLUDE SKIPPED: {abs_path} -->"

        self._visited_files.add(abs_path)

        if not os.path.exists(abs_path):
            self._log(f"  [WARN] File not found: {abs_path}")
            return f"<!-- FILE NOT FOUND: {abs_path} -->"

        base_dir = os.path.dirname(abs_path)

        self._log(f"Processing: {abs_path}")

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
                    result_lines.append(f"<!-- X-PRE-PROCESS set: {data} -->")

                elif cmd == "include":
                    self._log(f"  INCLUDE: {data}")
                    include_paths = self.resolve_include_paths(data, base_dir)

                    if not include_paths:
                        self._log(f"  [WARN] No files matched pattern: {data} (from {base_dir})")
                        result_lines.append(f"<!-- NO FILES MATCHED: {data} -->")
                    else:
                        for inc_path in include_paths:
                            # Validate the file parses as XML BEFORE including
                            is_valid, _, error = self._validate_xml_file(inc_path)

                            if not is_valid:
                                self._log(f"  [SKIP] Unparseable XML in {inc_path}: {error}")
                                result_lines.append(
                                    f"<!-- SKIPPED UNPARSEABLE FILE: {os.path.basename(inc_path)} - {error} -->"
                                )
                                file_node.children.append(FileNode(path=inc_path, skipped=True, error=error))
                                continue

                            child_node = FileNode(path=inc_path)
                            file_node.children.append(child_node)

                            expanded = self._expand_file(inc_path, child_node)
                            result_lines.append(f"<!-- BEGIN INCLUDE: {os.path.basename(inc_path)} -->")
                            result_lines.append(expanded)
                            result_lines.append(f"<!-- END INCLUDE: {os.path.basename(inc_path)} -->")
                else:
                    self._log(f"  [WARN] Unknown X-PRE-PROCESS cmd: {cmd}")
                    result_lines.append(line)
            else:
                result_lines.append(line)

        self._visited_files.discard(abs_path)
        return "\n".join(result_lines)

    def load(self, file_path: str) -> Freeswitch:
        """
        Load and parse a FreeSWITCH configuration file.

        Args:
            file_path: Path to the main configuration file (usually freeswitch.xml)

        Returns:
            Freeswitch object with parsed configuration
        """
        abs_path = os.path.abspath(file_path)

        print(f"\n{'='*60}")
        print(f"Loading FreeSWITCH configuration: {abs_path}")
        print(f"{'='*60}\n")

        # Reset state
        self._visited_files.clear()
        self.variables.clear()
        self._pre_load_variables()

        # Build the include tree
        root_node = FileNode(path=abs_path)

        # Expand all includes
        expanded_content = self._expand_file(abs_path, root_node)

        # Parse the expanded XML
        try:
            root = ET.fromstring(expanded_content)
        except ET.ParseError as e:
            print(f"\n[ERROR] Failed to parse expanded XML: {e}")
            debug_path = "/tmp/freeswitch_expanded.xml"
            with open(debug_path, "w") as f:
                f.write(expanded_content)
            print(f"[DEBUG] Expanded content saved to: {debug_path}")
            raise

        # Validate document type
        if root.tag != "document":
            print(f"[WARN] Expected <document> root, got <{root.tag}>")
        elif root.attrib.get("type") != "freeswitch/xml":
            print(f"[WARN] Expected type='freeswitch/xml', got '{root.attrib.get('type')}'")

        # Print the include tree
        print(f"\n{'='*60}")
        print("INCLUDE TREE:")
        print(f"{'='*60}")
        root_node.print_tree()

        # Print the XML structure tree
        print(f"\n{'='*60}")
        print("XML STRUCTURE:")
        print(f"{'='*60}")
        self._print_xml_tree(root)

        # Print variables
        print(f"\n{'='*60}")
        print("VARIABLES:")
        print(f"{'='*60}")
        for key, value in sorted(self.variables.items()):
            print(f"  {key} = {value}")

        # Print skipped files summary
        skipped_files = root_node.get_skipped_files()
        if skipped_files:
            print(f"\n{'='*60}")
            print(f"SKIPPED FILES ({len(skipped_files)}):")
            print(f"{'='*60}")
            for path, error in skipped_files:
                print(f"  {path}")
                print(f"    Error: {error}")

        # Build Freeswitch object
        configurations = FreeswitchConfigurationParser().parse(root)
        context_instructions = FreeswitchInstructionParser().parse(root)
        return Freeswitch(
            verbose=self.verbose,
            variables=self.variables,
            configurations=configurations,
            context_instructions=context_instructions,
        )

    def _print_xml_tree(self, element: ET.Element, indent: int = 0, max_depth: int = 4):
        """Print a tree representation of the XML structure."""
        prefix = "  " * indent

        attrs: list[str] = []
        for key in ["name", "type", "description"]:
            if key in element.attrib:
                attrs.append(f'{key}="{element.attrib[key]}"')

        attr_str = f" ({', '.join(attrs)})" if attrs else ""

        child_tags: dict[str, int] = {}
        for child in element:
            child_tags[child.tag] = child_tags.get(child.tag, 0) + 1

        if child_tags and indent < max_depth:
            print(f"{prefix}<{element.tag}>{attr_str}")
            for child in element:
                self._print_xml_tree(child, indent + 1, max_depth)
        elif child_tags:
            summary = ", ".join(f"{count}x {tag}" for tag, count in child_tags.items())
            print(f"{prefix}<{element.tag}>{attr_str} [{summary}]")
        else:
            print(f"{prefix}<{element.tag}>{attr_str}")
