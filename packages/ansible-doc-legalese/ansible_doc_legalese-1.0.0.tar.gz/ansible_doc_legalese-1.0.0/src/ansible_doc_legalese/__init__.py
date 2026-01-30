# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
"""
ansible-doc-legalese: Transform Ansible documentation into legal court documents.

This tool renders Ansible module and role documentation in the style of formal
legal proceedings, complete with stipulations, exhibits, and findings of fact.
"""

__version__ = "0.1.0"
__author__ = "FrozenFOXX"
__license__ = "Apache-2.0"

from .formatter import DocFragmentLegalese, transform_role_argument_spec
from .cli import main

__all__ = ["DocFragmentLegalese", "transform_role_argument_spec", "main"]
