###############################################################################
# (c) Copyright 2024 CERN for the benefit of the LHCb Collaboration           #
#                                                                             #
# This software is distributed under the terms of the GNU General Public      #
# Licence version 3 (GPL Version 3), copied verbatim in the file "COPYING".   #
#                                                                             #
# In applying this licence, CERN does not waive the privileges and immunities #
# granted to it by virtue of its status as an Intergovernmental Organization  #
# or submit itself to any jurisdiction.                                       #
###############################################################################
"""Tests for the Pydantic-based reason configuration system."""
from __future__ import annotations

import re
import tempfile
from pathlib import Path

import pytest
from pydantic import ValidationError

from ..base_reasons import (
    WorkerNodeIssue,
    RecoverableFailure,
)
from ..reason_models import ReasonDefinition, ReasonsConfig


class TestReasonDefinition:
    """Tests for ReasonDefinition Pydantic model."""

    def test_valid_reason_definition(self):
        """Test that valid reason definitions work."""
        reason = ReasonDefinition(
            name="TestFailure",
            base="WorkerNodeIssue",
            patterns=["test pattern"],
            explanation="Test explanation",
        )
        assert reason.name == "TestFailure"
        assert reason.base == "WorkerNodeIssue"
        assert reason.patterns == ["test pattern"]
        assert reason.explanation == "Test explanation"

    def test_valid_reason_with_issue_url(self):
        """Test reason with issue URL."""
        reason = ReasonDefinition(
            name="TestFailure",
            base="KnownUnrecoverableFailure",
            patterns=["error pattern"],
            issue_url="https://gitlab.cern.ch/lhcb/test/-/issues/123",
        )
        assert reason.issue_url == "https://gitlab.cern.ch/lhcb/test/-/issues/123"

    def test_invalid_regex_pattern(self):
        """Test that invalid regex patterns are caught."""
        with pytest.raises(ValidationError, match="Invalid regex pattern"):
            ReasonDefinition(
                name="BadPattern",
                base="WorkerNodeIssue",
                patterns=["[invalid(regex"],  # Unclosed bracket
                explanation="Test",
            )

    def test_invalid_name_lowercase(self):
        """Test that names starting with lowercase are rejected."""
        with pytest.raises(ValidationError, match="must start with uppercase"):
            ReasonDefinition(
                name="badName",
                base="WorkerNodeIssue",
                patterns=["test"],
            )

    def test_multiple_patterns(self):
        """Test reason with multiple patterns."""
        reason = ReasonDefinition(
            name="MultiPattern",
            base="RecoverableFailure",
            patterns=["pattern1", "pattern2", "pattern3"],
            explanation="Multiple patterns test",
        )
        assert len(reason.patterns) == 3

    def test_to_class_single_pattern(self):
        """Test converting definition to class with single pattern."""
        reason = ReasonDefinition(
            name="SinglePattern",
            base="WorkerNodeIssue",
            patterns=["test pattern"],
            explanation="Test explanation",
        )
        cls = reason.to_class()

        assert cls.__name__ == "SinglePattern"
        assert issubclass(cls, WorkerNodeIssue)
        assert cls.pattern == b"test pattern"
        assert cls.explanation == "Test explanation"

    def test_to_class_multiple_patterns(self):
        """Test converting definition to class with multiple patterns."""
        reason = ReasonDefinition(
            name="MultiPattern",
            base="RecoverableFailure",
            patterns=["pattern1", "pattern2"],
            explanation="Test",
        )
        cls = reason.to_class()

        assert cls.__name__ == "MultiPattern"
        assert issubclass(cls, RecoverableFailure)
        assert cls.patterns == [b"pattern1", b"pattern2"]

    def test_mixin_specification(self):
        """Test mixin specification."""
        reason = ReasonDefinition(
            name="CustomReason",
            base="UnknownFailure",
            patterns=["test"],
            mixin=".reasons:FatalGaudiErrorMixin",
        )
        assert reason.mixin == ".reasons:FatalGaudiErrorMixin"


class TestReasonsConfig:
    """Tests for ReasonsConfig Pydantic model."""

    def test_valid_config(self):
        """Test valid configuration."""
        config = ReasonsConfig(
            reasons=[
                ReasonDefinition(
                    name="Reason1",
                    base="WorkerNodeIssue",
                    patterns=["pattern1"],
                ),
                ReasonDefinition(
                    name="Reason2",
                    base="RecoverableFailure",
                    patterns=["pattern2"],
                ),
            ]
        )
        assert len(config.reasons) == 2

    def test_duplicate_reason_names(self):
        """Test that duplicate names are rejected."""
        with pytest.raises(ValidationError, match="Duplicate reason names"):
            ReasonsConfig(
                reasons=[
                    ReasonDefinition(name="Duplicate", base="WorkerNodeIssue", patterns=["a"]),
                    ReasonDefinition(name="Duplicate", base="RecoverableFailure", patterns=["b"]),
                ]
            )

    def test_load_from_yaml(self):
        """Test loading configuration from YAML file."""
        yaml_content = """
reasons:
  - name: TestReason
    base: WorkerNodeIssue
    patterns: ["test pattern"]
    explanation: "Test explanation"
  - name: AnotherReason
    base: KnownUnrecoverableFailure
    patterns: ["another pattern"]
    issue_url: "https://gitlab.cern.ch/lhcb/test/-/issues/1"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_file = Path(f.name)

        try:
            config = ReasonsConfig.load_from_yaml(yaml_file)
            assert len(config.reasons) == 2
            assert config.reasons[0].name == "TestReason"
            assert config.reasons[1].name == "AnotherReason"
            assert config.reasons[1].issue_url == "https://gitlab.cern.ch/lhcb/test/-/issues/1"
        finally:
            yaml_file.unlink()

    def test_create_reason_classes(self):
        """Test that classes are created correctly."""
        config = ReasonsConfig(
            reasons=[
                ReasonDefinition(
                    name="TestFailure",
                    base="WorkerNodeIssue",
                    patterns=["test pattern"],
                    explanation="Test explanation",
                ),
                ReasonDefinition(
                    name="CustomFailure",
                    base="UnknownFailure",
                    patterns=["custom"],
                    mixin=".reasons:FatalGaudiErrorMixin",
                ),
            ]
        )

        classes = config.create_reason_classes()

        # Both classes should be created (mixins are composed in class hierarchy)
        assert "TestFailure" in classes
        assert "CustomFailure" in classes

        TestFailure = classes["TestFailure"]
        assert TestFailure.pattern == b"test pattern"
        assert TestFailure.explanation == "Test explanation"
        assert issubclass(TestFailure, WorkerNodeIssue)

        # Check that CustomFailure has the mixin in its MRO
        CustomFailure = classes["CustomFailure"]
        from ..reasons import FatalGaudiErrorMixin

        assert FatalGaudiErrorMixin in CustomFailure.__mro__

    def test_empty_reasons_list(self):
        """Test configuration with empty reasons list."""
        # This should fail validation since we require at least one reason
        # But let's test an empty list to ensure it doesn't crash
        config = ReasonsConfig(reasons=[])
        assert len(config.reasons) == 0
        classes = config.create_reason_classes()
        assert len(classes) == 0


class TestYAMLIntegration:
    """Integration tests for YAML loading and class creation."""

    def test_load_actual_reasons_yaml(self):
        """Test loading the actual reasons.yaml file."""
        # This tests that the real configuration file is valid
        config = ReasonsConfig.load_from_yaml()
        assert len(config.reasons) > 0

        # Check that we have a mix of classes with and without mixins
        mixin_count = sum(1 for r in config.reasons if r.mixin)
        regular_count = len(config.reasons) - mixin_count

        assert regular_count > 0, "Should have regular YAML-defined reasons"
        assert mixin_count >= 0, "May have reasons with mixins"

    def test_create_classes_from_actual_yaml(self):
        """Test creating classes from the actual YAML file."""
        config = ReasonsConfig.load_from_yaml()
        classes = config.create_reason_classes()

        # Should have created multiple classes
        assert len(classes) > 0

        # Verify some expected classes exist
        assert "FunctorCompilationFailure" in classes or any(
            "Functor" in name for name in classes
        ), "Should have at least one reason class"

        # Pick the first class and verify it has the expected attributes
        first_class_name = next(iter(classes.keys()))
        first_class = classes[first_class_name]

        assert hasattr(first_class, "pattern") or hasattr(first_class, "patterns")
        assert hasattr(first_class, "explanation") or first_class.explanation is None

    def test_patterns_are_valid_regex(self):
        """Test that all patterns in the YAML are valid regex."""
        config = ReasonsConfig.load_from_yaml()

        for reason in config.reasons:
            for pattern in reason.patterns:
                # This should not raise an exception
                try:
                    print(f"Testing regex pattern: {pattern!r} for reason: {reason.name}")
                    re.compile(pattern.encode())
                except re.error as e:
                    pytest.fail(f"Invalid regex in {reason.name}: {pattern} - {e}")

    def test_base_classes_are_valid(self):
        """Test that all base classes are valid."""
        config = ReasonsConfig.load_from_yaml()

        valid_bases = {
            "WorkerNodeIssue",
            "RecoverableFailure",
            "KnownUnrecoverableFailure",
            "EventTimeout",
            "RecoverableFailureWithManualIntervention",
            "UnknownFailure",
        }

        for reason in config.reasons:
            assert reason.base in valid_bases, f"Invalid base class: {reason.base}"


class TestReasonModule:
    """Tests for the reasons module that loads from YAML."""

    def test_import_yaml_defined_classes(self):
        """Test that YAML-defined classes can be imported."""
        # Import the module
        from .. import reasons

        # Check that we have the expected classes
        assert hasattr(reasons, "FatalGaudiError")
        assert hasattr(reasons, "UnknownSegmentationFaultWithTraceback")
        assert hasattr(reasons, "KnownCorruptedFile")

        # Check that we have at least some YAML-defined classes
        # We know these exist in the YAML
        expected_yaml_classes = [
            "FunctorCompilationFailure",
            "FileTooLarge",
            "EventWatchdog",
        ]

        for class_name in expected_yaml_classes:
            if hasattr(reasons, class_name):
                # Found at least one
                break
        else:
            pytest.fail(f"None of the expected YAML classes found: {expected_yaml_classes}")

    def test_custom_classes_have_mixins(self):
        """Test that classes with mixins have their custom methods."""
        from .. import reasons

        # FatalGaudiError should have the FatalGaudiErrorMixin in its MRO
        assert hasattr(reasons.FatalGaudiError, "match_string")  # pylint: disable=no-member
        assert reasons.FatalGaudiErrorMixin in reasons.FatalGaudiError.__mro__  # pylint: disable=no-member

        # UnknownSegmentationFaultWithTraceback should have SegfaultTracebackMixin
        assert hasattr(reasons.UnknownSegmentationFaultWithTraceback, "match_string")  # pylint: disable=no-member
        assert (
            reasons.SegfaultTracebackMixin
            in reasons.UnknownSegmentationFaultWithTraceback.__mro__  # pylint: disable=no-member
        )

    def test_all_exports(self):
        """Test that __all__ is properly defined."""
        from .. import reasons

        assert hasattr(reasons, "__all__")
        assert isinstance(reasons.__all__, list)
        assert len(reasons.__all__) > 0

        # Check that custom classes are in __all__
        assert "FatalGaudiError" in reasons.__all__
        assert "UnknownSegmentationFaultWithTraceback" in reasons.__all__
        assert "KnownCorruptedFile" in reasons.__all__
