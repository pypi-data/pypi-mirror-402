# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
""" Core formatting logic for legalese document generation """

import hashlib
import textwrap
from datetime import datetime


class DocFragmentLegalese:
    """ Transforms ansible-doc JSON output into legalese format """

    PREAMBLE = """
═══════════════════════════════════════════════════════════════════════════════
                    IN THE SUPREME COURT OF ANSIBLE
                        INFRASTRUCTURE DIVISION
═══════════════════════════════════════════════════════════════════════════════

                            Case No. {case_number}

═══════════════════════════════════════════════════════════════════════════════
                    IN THE MATTER OF THE MODULE KNOWN AS

                              "{module_name}"

                           OFFICIAL DOCUMENTATION
                        AND BINDING SPECIFICATIONS
═══════════════════════════════════════════════════════════════════════════════

Filed this {date}

BEFORE THE HONORABLE ANSIBLE ENGINE, PRESIDING

───────────────────────────────────────────────────────────────────────────────
"""

    SECTION_HEADER = """
───────────────────────────────────────────────────────────────────────────────
                            {title}
───────────────────────────────────────────────────────────────────────────────
"""

    def __init__(self):
        self.case_number = None
        self.exhibit_counter = 0

    def _generate_case_number(self, module_name):
        """ Generate a pseudo-legal case number """
        hash_val = hashlib.md5(module_name.encode()).hexdigest()[:6].upper()
        year = datetime.now().year
        return f"ANS-{year}-{hash_val}"

    def _wrap_text(self, text, indent=0, width=78):
        """ Wrap text with proper indentation """
        if not text:
            return ""
        wrapper = textwrap.TextWrapper(
            width=width - indent,
            initial_indent=" " * indent,
            subsequent_indent=" " * indent,
        )
        return wrapper.fill(str(text))

    def _format_type(self, type_val):
        """ Convert Python types to legal terminology """
        type_map = {
            "str": "alphanumeric testimony",
            "string": "alphanumeric testimony",
            "int": "numerical evidence (whole)",
            "integer": "numerical evidence (whole)",
            "float": "numerical evidence (fractional)",
            "bool": "boolean affirmation",
            "boolean": "boolean affirmation",
            "list": "enumerated articles",
            "dict": "associative memorandum",
            "dictionary": "associative memorandum",
            "path": "filesystem domicile",
            "raw": "unprocessed material evidence",
        }
        if isinstance(type_val, list):
            types = [type_map.get(t, t) for t in type_val]
            return " OR ".join(types)
        return type_map.get(str(type_val).lower(), str(type_val))

    def _format_choices(self, choices):
        """ Format choices as legal options """
        if not choices:
            return ""
        choice_strs = [f'"{c}"' for c in choices]
        return f"WHEREAS the admissible values are LIMITED TO: {', '.join(choice_strs)}"

    def _roman_numeral(self, num):
        """ Convert integer to Roman numeral """
        val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
        syms = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"]
        roman_num = ""
        i = 0
        while num > 0:
            for _ in range(num // val[i]):
                roman_num += syms[i]
                num -= val[i]
            i += 1
        return roman_num

    def _format_parameter(self, name, details, index):
        """ Format a single parameter as a legal stipulation """
        roman = self._roman_numeral(index)

        lines = []
        lines.append(f'\n  STIPULATION {roman}: "{name.upper()}"')
        lines.append("  " + "─" * 60)

        # Description
        desc = details.get("description", "")
        if isinstance(desc, list):
            desc = " ".join(desc)
        if desc:
            lines.append(
                f"\n  LET IT BE KNOWN that this parameter shall be understood as:"
            )
            lines.append(self._wrap_text(desc, indent=4))

        # Type
        param_type = details.get("type", "str")
        lines.append(
            f"\n  THE COURT RECOGNIZES the evidence type as: {self._format_type(param_type)}"
        )

        # Required
        required = details.get("required", False)
        if required:
            lines.append("\n  THIS STIPULATION IS HEREBY DECLARED **MANDATORY**.")
            lines.append(
                "  FAILURE TO PROVIDE shall result in IMMEDIATE MISTRIAL (task failure)."
            )
        else:
            lines.append(
                "\n  This stipulation is OPTIONAL and may be omitted without prejudice."
            )

        # Default
        default = details.get("default")
        if default is not None:
            lines.append(
                f"\n  IN THE ABSENCE of explicit declaration, the Court shall assume"
            )
            lines.append(f"  the DEFAULT VALUE of: {repr(default)}")

        # Choices
        choices = details.get("choices")
        if choices:
            lines.append(f"\n  {self._format_choices(choices)}")
            lines.append(
                "  Any value not enumerated above shall be STRICKEN from the record."
            )

        # Aliases
        aliases = details.get("aliases", [])
        if aliases:
            alias_str = ", ".join([f'"{a}"' for a in aliases])
            lines.append(
                f"\n  THE COURT SHALL ALSO RECOGNIZE the following aliases: {alias_str}"
            )

        # Version added
        version = details.get("version_added")
        if version:
            lines.append(
                f"\n  This stipulation entered into law as of Ansible version {version}."
            )

        return "\n".join(lines)

    def _format_example(self, example_text):
        """ Format an example as a legal exhibit """
        self.exhibit_counter += 1
        letter = chr(64 + self.exhibit_counter)  # A, B, C, etc.

        lines = []
        lines.append(f"\n  ┌{'─' * 68}┐")
        lines.append(f"  │{'EXHIBIT ' + letter:^68}│")
        lines.append(f"  │{'DEMONSTRATIVE EVIDENCE':^68}│")
        lines.append(f"  └{'─' * 68}┘")
        lines.append("")

        # Indent the example code
        for line in example_text.strip().split("\n"):
            lines.append(f"      {line}")

        lines.append("")
        lines.append(f"  [END EXHIBIT {letter}]")

        return "\n".join(lines)

    def _format_return_value(self, name, details, index):
        """ Format a return value as a legal finding """
        lines = []
        lines.append(f'\n  FINDING {index}: "{name}"')
        lines.append("  " + "─" * 60)

        desc = details.get("description", "")
        if isinstance(desc, list):
            desc = " ".join(desc)
        if desc:
            lines.append(
                f"\n  THE COURT FINDS that upon successful execution, this value represents:"
            )
            lines.append(self._wrap_text(desc, indent=4))

        returned = details.get("returned", "always")
        lines.append(f"\n  CONDITIONS FOR DISCLOSURE: {returned}")

        ret_type = details.get("type", "string")
        lines.append(f"  EVIDENTIARY FORMAT: {self._format_type(ret_type)}")

        sample = details.get("sample")
        if sample is not None:
            lines.append(f"  SAMPLE EVIDENCE: {repr(sample)}")

        return "\n".join(lines)

    def transform(self, module_name, doc_data):
        """ Transform module documentation into legalese format """
        self.case_number = self._generate_case_number(module_name)
        self.exhibit_counter = 0

        output = []

        # Preamble
        output.append(
            self.PREAMBLE.format(
                case_number=self.case_number,
                module_name=module_name.upper(),
                date=datetime.now().strftime("%B %d, %Y"),
            )
        )

        # Opening statement (short description)
        short_desc = doc_data.get("short_description", "No description provided")
        output.append(self.SECTION_HEADER.format(title="ARTICLE I: STATEMENT OF PURPOSE"))
        output.append(
            f"""
COMES NOW the module "{module_name}", hereinafter referred to as "THE MODULE,"
and respectfully submits to this Court the following declaration of purpose:

    "{short_desc}"

"""
        )

        # Full description
        description = doc_data.get("description", [])
        if description:
            if isinstance(description, list):
                description = "\n\n".join(description)
            output.append(
                self.SECTION_HEADER.format(title="ARTICLE II: DETAILED SPECIFICATIONS")
            )
            output.append(
                f"""
THE MODULE, being of sound logic and stable code, hereby elaborates upon
its stated purpose with the following detailed specifications:

{self._wrap_text(description, indent=4)}

"""
            )

        # Parameters
        options = doc_data.get("options", {})
        if options:
            output.append(
                self.SECTION_HEADER.format(
                    title="ARTICLE III: BINDING STIPULATIONS (PARAMETERS)"
                )
            )
            output.append(
                """
THE FOLLOWING STIPULATIONS are hereby entered into the record. The operator
("THE USER") is bound to comply with all MANDATORY stipulations. Failure to
adhere to these requirements shall result in sanctions up to and including
complete task failure.

"""
            )
            for i, (param_name, param_details) in enumerate(options.items(), 1):
                output.append(self._format_parameter(param_name, param_details, i))
            output.append("\n")

        # Examples
        examples = doc_data.get("examples", "")
        if examples:
            output.append(
                self.SECTION_HEADER.format(title="ARTICLE IV: EXHIBITS (USAGE EXAMPLES)")
            )
            output.append(
                """
THE FOLLOWING EXHIBITS are submitted as demonstrative evidence of proper
module invocation. These examples are provided for illustrative purposes
and do not constitute legal advice regarding your specific infrastructure.

"""
            )
            output.append(self._format_example(examples))
            output.append("\n")

        # Return values
        return_docs = doc_data.get("return", {})
        if return_docs:
            output.append(
                self.SECTION_HEADER.format(
                    title="ARTICLE V: FINDINGS OF FACT (RETURN VALUES)"
                )
            )
            output.append(
                """
UPON SUCCESSFUL EXECUTION, the Court shall issue the following findings.
These return values constitute the official record of module execution.

"""
            )
            for i, (ret_name, ret_details) in enumerate(return_docs.items(), 1):
                output.append(self._format_return_value(ret_name, ret_details, i))
            output.append("\n")

        # Notes
        notes = doc_data.get("notes", [])
        if notes:
            output.append(
                self.SECTION_HEADER.format(title="ARTICLE VI: ADVISORY OPINIONS (NOTES)")
            )
            output.append(
                """
THE COURT ISSUES the following non-binding advisory opinions:

"""
            )
            for i, note in enumerate(notes, 1):
                output.append(f"  {i}. {self._wrap_text(note, indent=5).strip()}\n")
            output.append("\n")

        # See also
        see_also = doc_data.get("seealso", [])
        if see_also:
            output.append(
                self.SECTION_HEADER.format(title="ARTICLE VII: RELATED PROCEEDINGS")
            )
            output.append(
                """
FOR FURTHER JURISPRUDENCE, the Court directs attention to the following
related matters:

"""
            )
            for item in see_also:
                if isinstance(item, dict):
                    if "module" in item:
                        output.append(f"  • Module: {item['module']}")
                        if "description" in item:
                            output.append(f"    ({item['description']})")
                    elif "link" in item:
                        output.append(f"  • External Reference: {item['link']}")
                        if "description" in item:
                            output.append(f"    ({item['description']})")
                else:
                    output.append(f"  • {item}")
                output.append("")

        # Author attribution
        author = doc_data.get("author", [])
        if author:
            if isinstance(author, str):
                author = [author]
            output.append(
                self.SECTION_HEADER.format(title="ARTICLE VIII: ATTESTATION")
            )
            output.append(
                """
THIS DOCUMENT has been prepared and attested to by the following parties:

"""
            )
            for auth in author:
                output.append(f"    ✓ {auth}")
            output.append("\n")

        # Closing
        output.append(
            """
═══════════════════════════════════════════════════════════════════════════════
                              CERTIFICATION
═══════════════════════════════════════════════════════════════════════════════

I, ANSIBLE-DOC, Clerk of the Supreme Court of Ansible, do hereby certify
that the foregoing is a true and complete documentation of the module
referenced herein.

                                        _____________________________
                                        ANSIBLE-DOC, Court Clerk
                                        Infrastructure Division

                              [SEAL OF THE COURT]

                                    ⚖️  ANSIBLE  ⚖️

═══════════════════════════════════════════════════════════════════════════════
           This document generated pursuant to the Ansible Documentation Act
                            All rights reserved under the GPL v3
═══════════════════════════════════════════════════════════════════════════════
"""
        )

        return "\n".join(output)


def transform_role_argument_spec(role_name, arg_spec_data):
    """
    Transform a role's argument_specs.yml into legalese format.

    Args:
        role_name: Name of the role
        arg_spec_data: Dict from argument_specs.yml (has 'argument_specs' key with entrypoints)

    Returns:
        Formatted legalese string
    """
    formatter = DocFragmentLegalese()
    outputs = []

    argument_specs = arg_spec_data.get("argument_specs", arg_spec_data)

    for entrypoint, spec in argument_specs.items():
        # Convert role argument_spec format to module doc format
        doc_data = {
            "short_description": spec.get(
                "short_description", f"{role_name} - {entrypoint} entrypoint"
            ),
            "description": spec.get("description", []),
            "options": spec.get("options", {}),
            "author": spec.get("author", []),
            "notes": [],
        }

        full_name = f"{role_name}::{entrypoint}" if entrypoint != "main" else role_name
        outputs.append(formatter.transform(full_name, doc_data))

    return "\n\n".join(outputs)
