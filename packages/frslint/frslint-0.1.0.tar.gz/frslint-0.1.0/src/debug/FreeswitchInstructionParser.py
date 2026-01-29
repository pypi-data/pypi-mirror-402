import xml.etree.ElementTree as ET
from typing import Dict, List

from debug.Action import Action
from debug.Condition import Condition
from debug.Context import Context
from debug.Extension import Extension


class FreeswitchInstructionParser:
    """Parses FreeSWITCH XML dialplan into structured Context/Extension/Condition/Action objects."""

    def parse(self, element: ET.Element) -> Dict[str, Context]:
        """
        Parse an XML element tree and return contexts indexed by name.

        Args:
            element: The root XML element (typically the document or section element)

        Returns:
            Dictionary mapping context names to Context objects
        """
        contexts: Dict[str, Context] = {}

        # Find all context elements (may be nested under section/include tags)
        for context_elem in element.iter("context"):
            context = self._parse_context(context_elem)
            if context:
                # If context name already exists, merge extensions
                if context.name in contexts:
                    raise ValueError(f"Context {context.name} already exists")
                contexts[context.name] = context

        return contexts

    def _parse_context(self, context_elem: ET.Element) -> Context:
        """Parse a single context element."""
        name = context_elem.attrib.get("name", "(unnamed)")
        extensions: List[Extension] = []

        # Find extensions - they may be direct children or nested in <include> tags
        for child in context_elem:
            if child.tag == "extension":
                ext = self._parse_extension(child)
                if ext:
                    extensions.append(ext)
            elif child.tag == "include":
                # Extensions nested inside <include> tags
                for ext_elem in child.findall("extension"):
                    ext = self._parse_extension(ext_elem)
                    if ext:
                        extensions.append(ext)

        return Context(name=name, extensions=extensions)

    def _parse_extension(self, ext_elem: ET.Element) -> Extension:
        """Parse a single extension element."""
        name = ext_elem.attrib.get("name", "(unnamed)")
        continue_val = ext_elem.attrib.get("continue", "false").lower() == "true"

        extension = Extension(name=name, do_continue=continue_val)

        # Find all conditions
        for condition_elem in ext_elem.findall("condition"):
            condition = self._parse_condition(condition_elem)
            extension.add_condition(condition)

        return extension

    def _parse_condition(self, cond_elem: ET.Element) -> Condition:
        """Parse a single condition element."""
        # TODO: handle regex=any and regex child elements
        field = cond_elem.attrib.get("field")
        expression = cond_elem.attrib.get("expression")
        do_break = cond_elem.attrib.get("break", "on-false")

        # require_nested: if this is an unconditional condition (no field/expression),
        # nested conditions are typically required for matching
        require_nested = field is None and expression is None

        condition = Condition(field=field, expression=expression, do_break=do_break, require_nested=require_nested)

        # Parse actions and anti-actions
        for child in cond_elem:
            if child.tag == "action":
                action = self._parse_action(child)
                condition.add_action(action)
            elif child.tag == "anti-action":
                action = self._parse_action(child)
                condition.add_anti_action(action)

        return condition

    def _parse_action(self, action_elem: ET.Element) -> Action:
        """Parse a single action or anti-action element."""
        application = action_elem.attrib.get("application", "")
        data = action_elem.attrib.get("data")

        return Action(application=application, data=data)
