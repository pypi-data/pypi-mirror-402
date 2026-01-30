# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
""" Command-line interface for ansible-doc-legalese """

import argparse
import json
import os
import subprocess
import sys

from .formatter import DocFragmentLegalese, transform_role_argument_spec


def load_role_from_directory(role_path):
    """
    Load role documentation from a role directory structure.

    Looks for:
    - meta/argument_specs.yml (Ansible 2.11+)
    - defaults/main.yml (fallback for variable docs)

    Returns:
        Formatted legalese string
    """
    try:
        import yaml
    except ImportError:
        print("Error: PyYAML is required for role parsing.", file=sys.stderr)
        print("Install it with: pip install pyyaml", file=sys.stderr)
        sys.exit(1)

    role_name = os.path.basename(os.path.normpath(role_path))

    # Try argument_specs.yml first (preferred)
    arg_spec_path = os.path.join(role_path, "meta", "argument_specs.yml")
    if os.path.exists(arg_spec_path):
        with open(arg_spec_path) as f:
            arg_spec_data = yaml.safe_load(f)
        return transform_role_argument_spec(role_name, arg_spec_data)

    # Also check for argument_specs.yaml
    arg_spec_path_yaml = os.path.join(role_path, "meta", "argument_specs.yaml")
    if os.path.exists(arg_spec_path_yaml):
        with open(arg_spec_path_yaml) as f:
            arg_spec_data = yaml.safe_load(f)
        return transform_role_argument_spec(role_name, arg_spec_data)

    # Fallback: try to parse defaults/main.yml
    defaults_path = os.path.join(role_path, "defaults", "main.yml")
    if not os.path.exists(defaults_path):
        defaults_path = os.path.join(role_path, "defaults", "main.yaml")

    if os.path.exists(defaults_path):
        with open(defaults_path) as f:
            content = f.read()

        # Try to extract documentation from comments
        options = {}
        lines = content.split("\n")
        current_comment = []

        for line in lines:
            if line.strip().startswith("#"):
                current_comment.append(line.strip().lstrip("#").strip())
            elif ":" in line and not line.strip().startswith("-"):
                var_name = line.split(":")[0].strip()
                if var_name and not var_name.startswith("#"):
                    value_part = ":".join(line.split(":")[1:]).strip()
                    options[var_name] = {
                        "description": (
                            " ".join(current_comment)
                            if current_comment
                            else f"Variable {var_name}"
                        ),
                        "default": value_part if value_part else None,
                        "required": False,
                    }
                    current_comment = []
            else:
                current_comment = []

        doc_data = {
            "short_description": f"Role: {role_name}",
            "description": [f"Configuration role for {role_name}"],
            "options": options,
        }

        formatter = DocFragmentLegalese()
        return formatter.transform(role_name, doc_data)

    raise FileNotFoundError(f"No documentation found in {role_path}")


def process_module(module_name):
    """
    Process a module using ansible-doc.

    Returns:
        Formatted legalese string
    """
    try:
        result = subprocess.run(
            ["ansible-doc", "-t", "module", "--json", module_name],
            capture_output=True,
            text=True,
            check=True,
        )
        doc_data = json.loads(result.stdout)

        # ansible-doc returns {module_name: {doc: {...}}}
        if module_name in doc_data:
            module_doc = doc_data[module_name].get("doc", {})
            module_doc["return"] = doc_data[module_name].get("return", {})
            module_doc["examples"] = doc_data[module_name].get("examples", "")
        else:
            print(f"Error: Module '{module_name}' not found", file=sys.stderr)
            sys.exit(1)

        formatter = DocFragmentLegalese()
        return formatter.transform(module_name, module_doc)

    except FileNotFoundError:
        print("Error: ansible-doc not found. Is Ansible installed?", file=sys.stderr)
        print(
            "You can still use this tool with role directories (--role).",
            file=sys.stderr,
        )
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error running ansible-doc: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}", file=sys.stderr)
        sys.exit(1)


def run_demo():
    """ Run demonstration with sample data """
    demo_role = {
        "argument_specs": {
            "main": {
                "short_description": "Install and configure a message of the day",
                "description": [
                    "This role manages the /etc/motd file on target hosts.",
                ],
                "author": ["Your Name (@yourhandle)"],
                "options": {
                    "motd_content": {
                        "description": "The message to display when users log in.",
                        "type": "str",
                        "required": True,
                    },
                    "motd_path": {
                        "description": "Path to the motd file.",
                        "type": "path",
                        "default": "/etc/motd",
                    },
                    "motd_backup": {
                        "description": "Create a backup of the existing file.",
                        "type": "bool",
                        "default": True,
                    },
                },
            }
        }
    }

    print("=" * 80)
    print("ANSIBLE-DOC-LEGALESE DEMONSTRATION")
    print("=" * 80)
    print()

    output = transform_role_argument_spec("motd", demo_role)
    print(output)


def main():
    """ Main entry point """
    parser = argparse.ArgumentParser(
        prog="ansible-doc-legalese",
        description="Transform Ansible documentation into legal court documents.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a module via ansible-doc
  ansible-doc-legalese ansible.builtin.copy

  # Process a role directory
  ansible-doc-legalese --role ./roles/my_role

  # Show demonstration output
  ansible-doc-legalese --demo

  # Save output to file
  ansible-doc-legalese ansible.builtin.file > file_module.txt
""",
    )

    parser.add_argument(
        "target",
        nargs="?",
        help="Module name (e.g., ansible.builtin.copy) or role path with --role",
    )

    parser.add_argument(
        "-r",
        "--role",
        action="store_true",
        help="Treat target as a role directory path",
    )

    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run demonstration with sample data",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output file (default: stdout)",
    )

    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )

    args = parser.parse_args()

    # Handle demo mode
    if args.demo:
        run_demo()
        return

    # Require target if not demo
    if not args.target:
        parser.print_help()
        sys.exit(1)

    # Process based on type
    if args.role or os.path.isdir(args.target):
        try:
            output = load_role_from_directory(args.target)
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        output = process_module(args.target)

    # Write output
    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Output written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
