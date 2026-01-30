# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
""" Tests for ansible-doc-legalese """

import pytest

from ansible_doc_legalese.formatter import DocFragmentLegalese, transform_role_argument_spec


class TestDocFragmentLegalese:
    """ Tests for the DocFragmentLegalese formatter """

    def test_transform_basic_module(self):
        """ Test basic module transformation """
        formatter = DocFragmentLegalese()
        doc_data = {
            "short_description": "Test module",
            "description": ["A test module for testing."],
            "options": {
                "name": {
                    "description": "The name parameter",
                    "type": "str",
                    "required": True,
                }
            },
        }

        result = formatter.transform("test_module", doc_data)

        assert "IN THE SUPREME COURT OF ANSIBLE" in result
        assert "TEST_MODULE" in result
        assert "STIPULATION I" in result
        assert "NAME" in result
        assert "MANDATORY" in result

    def test_transform_with_choices(self):
        """ Test transformation with choices """
        formatter = DocFragmentLegalese()
        doc_data = {
            "short_description": "Test module",
            "options": {
                "state": {
                    "description": "Desired state",
                    "type": "str",
                    "choices": ["present", "absent"],
                    "default": "present",
                }
            },
        }

        result = formatter.transform("test_module", doc_data)

        assert "LIMITED TO" in result
        assert '"present"' in result
        assert '"absent"' in result

    def test_transform_with_examples(self):
        """ Test transformation with examples """
        formatter = DocFragmentLegalese()
        doc_data = {
            "short_description": "Test module",
            "examples": "- name: Example task\n  test_module:\n    name: test",
        }

        result = formatter.transform("test_module", doc_data)

        assert "EXHIBIT A" in result
        assert "DEMONSTRATIVE EVIDENCE" in result

    def test_transform_with_return_values(self):
        """ Test transformation with return values """
        formatter = DocFragmentLegalese()
        doc_data = {
            "short_description": "Test module",
            "return": {
                "result": {
                    "description": "The result of the operation",
                    "type": "str",
                    "returned": "always",
                    "sample": "success",
                }
            },
        }

        result = formatter.transform("test_module", doc_data)

        assert "FINDING 1" in result
        assert "result" in result

    def test_type_translations(self):
        """ Test that types are translated to legal terminology """
        formatter = DocFragmentLegalese()
        doc_data = {
            "short_description": "Test module",
            "options": {
                "string_param": {"description": "A string", "type": "str"},
                "int_param": {"description": "An int", "type": "int"},
                "bool_param": {"description": "A bool", "type": "bool"},
                "list_param": {"description": "A list", "type": "list"},
                "dict_param": {"description": "A dict", "type": "dict"},
                "path_param": {"description": "A path", "type": "path"},
            },
        }

        result = formatter.transform("test_module", doc_data)

        assert "alphanumeric testimony" in result
        assert "numerical evidence (whole)" in result
        assert "boolean affirmation" in result
        assert "enumerated articles" in result
        assert "associative memorandum" in result
        assert "filesystem domicile" in result

    def test_roman_numerals(self):
        """ Test Roman numeral generation """
        formatter = DocFragmentLegalese()

        assert formatter._roman_numeral(1) == "I"
        assert formatter._roman_numeral(4) == "IV"
        assert formatter._roman_numeral(9) == "IX"
        assert formatter._roman_numeral(14) == "XIV"
        assert formatter._roman_numeral(50) == "L"

    def test_case_number_generation(self):
        """ Test that case numbers are deterministic """
        formatter = DocFragmentLegalese()

        case1 = formatter._generate_case_number("test_module")
        case2 = formatter._generate_case_number("test_module")
        case3 = formatter._generate_case_number("other_module")

        assert case1 == case2  # Same module = same case number
        assert case1 != case3  # Different module = different case number
        assert case1.startswith("ANS-")


class TestTransformRoleArgumentSpec:
    """ Tests for role argument spec transformation """

    def test_transform_role_basic(self):
        """ Test basic role transformation """
        arg_spec = {
            "argument_specs": {
                "main": {
                    "short_description": "Test role",
                    "options": {
                        "role_var": {
                            "description": "A role variable",
                            "type": "str",
                            "default": "default_value",
                        }
                    },
                }
            }
        }

        result = transform_role_argument_spec("test_role", arg_spec)

        assert "TEST_ROLE" in result
        assert "ROLE_VAR" in result
        assert "default_value" in result

    def test_transform_role_multiple_entrypoints(self):
        """ Test role with multiple entrypoints """
        arg_spec = {
            "argument_specs": {
                "main": {
                    "short_description": "Main entrypoint",
                    "options": {},
                },
                "backup": {
                    "short_description": "Backup entrypoint",
                    "options": {},
                },
            }
        }

        result = transform_role_argument_spec("test_role", arg_spec)

        # Main entrypoint should just use role name
        assert "TEST_ROLE" in result
        # Backup entrypoint should include entrypoint name
        assert "TEST_ROLE::BACKUP" in result
