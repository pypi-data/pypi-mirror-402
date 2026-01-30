# ansible-doc-legalese

Transform Ansible module and role documentation into formal legal court documents.

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## Overview

Ever felt that your Ansible documentation lacked the gravitas of a Supreme Court filing? Looking to make a career pivot into policy but don't know how to answer questions about legal documents? Fear not, `ansible-doc-legalese` transforms your mundane module documentation into official-looking legal proceedings, complete with:

- **Stipulations** (parameters)
- **Exhibits** (examples)
- **Findings of Fact** (return values)
- **Advisory Opinions** (notes)
- Case numbers, attestations, and court seals

## Installation

```bash
# From PyPI
pip install ansible-doc-legalese

# From source
git clone https://github.com/frozenfoxx/ansible-doc-legalese.git
cd ansible-doc-legalese
pip install -e .

# With YAML support for role parsing
pip install -e ".[yaml]"
```

## Usage

### Process a Module

```bash
# Uses ansible-doc under the hood
ansible-doc-legalese ansible.builtin.copy
ansible-doc-legalese ansible.builtin.file
ansible-doc-legalese community.general.docker_container
```

### Process a Role

```bash
# Reads meta/argument_specs.yml or defaults/main.yml
ansible-doc-legalese --role ./roles/my_role
ansible-doc-legalese -r ~/ansible-bricksandblocks/roles/minecraft
```

### Save to File

```bash
ansible-doc-legalese ansible.builtin.copy -o copy_docs.txt
ansible-doc-legalese ansible.builtin.copy > copy_docs.txt
```

### Demo Mode

```bash
ansible-doc-legalese --demo
```

## Example Output

```
═══════════════════════════════════════════════════════════════════════════════
                    IN THE SUPREME COURT OF ANSIBLE
                        INFRASTRUCTURE DIVISION
═══════════════════════════════════════════════════════════════════════════════

                            Case No. ANS-2026-77D4C0

═══════════════════════════════════════════════════════════════════════════════
                    IN THE MATTER OF THE MODULE KNOWN AS

                              "ANSIBLE.BUILTIN.COPY"

                           OFFICIAL DOCUMENTATION
                        AND BINDING SPECIFICATIONS
═══════════════════════════════════════════════════════════════════════════════

Filed this January 21, 2026

BEFORE THE HONORABLE ANSIBLE ENGINE, PRESIDING

───────────────────────────────────────────────────────────────────────────────

  STIPULATION I: "DEST"
  ────────────────────────────────────────────────────────────

  LET IT BE KNOWN that this parameter shall be understood as:
    Remote absolute path where the file should be copied to.

  THE COURT RECOGNIZES the evidence type as: filesystem domicile

  THIS STIPULATION IS HEREBY DECLARED **MANDATORY**.
  FAILURE TO PROVIDE shall result in IMMEDIATE MISTRIAL (task failure).
```

## Type Translations

| Ansible Type | Legal Terminology |
|--------------|-------------------|
| `str` | alphanumeric testimony |
| `int` | numerical evidence (whole) |
| `float` | numerical evidence (fractional) |
| `bool` | boolean affirmation |
| `list` | enumerated articles |
| `dict` | associative memorandum |
| `path` | filesystem domicile |
| `raw` | unprocessed material evidence |

## Requirements

- Python 3.8+
- Ansible (for module documentation via `ansible-doc`)
- PyYAML (optional, for role parsing)

## Development

```bash
# Clone and install dev dependencies
git clone https://github.com/frozenfoxx/ansible-doc-legalese.git
cd ansible-doc-legalese
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/
ruff check src/ --fix
```

## License

Apache License 2.0. See [LICENSE](LICENSE) for details.

## Contributing

Pull requests welcome! Please ensure:

1. Code is formatted with `black`
2. Linting passes with `ruff`
3. Tests pass
4. New features include appropriate legal terminology

## Disclaimer

This tool is provided for entertainment purposes. The output does not constitute actual legal documentation and should not be submitted to any court, regulatory body, or compliance audit. Side effects may include excessive formality in commit messages and an urge to refer to your coworkers as "counsel."
