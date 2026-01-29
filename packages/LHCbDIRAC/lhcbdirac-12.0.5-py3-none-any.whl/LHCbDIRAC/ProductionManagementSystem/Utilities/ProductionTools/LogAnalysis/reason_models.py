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
"""Pydantic models for defining failure reasons via YAML configuration."""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

from .base_reasons import (
    WorkerNodeIssue,
    RecoverableFailure,
    KnownUnrecoverableFailure,
    EventTimeout,
    RecoverableFailureWithManualIntervention,
    UnknownFailure,
    AppLogFailureReason,
)


# Type mapping for base classes
BaseReasonType = Literal[
    "WorkerNodeIssue",
    "RecoverableFailure",
    "KnownUnrecoverableFailure",
    "EventTimeout",
    "RecoverableFailureWithManualIntervention",
    "UnknownFailure",
]

BASE_REASON_REGISTRY = {
    "WorkerNodeIssue": WorkerNodeIssue,
    "RecoverableFailure": RecoverableFailure,
    "KnownUnrecoverableFailure": KnownUnrecoverableFailure,
    "EventTimeout": EventTimeout,
    "RecoverableFailureWithManualIntervention": RecoverableFailureWithManualIntervention,
    "UnknownFailure": UnknownFailure,
}


class ReasonDefinition(BaseModel):
    """Pydantic model for a single reason definition from YAML."""

    name: str = Field(..., description="Class name for this reason")
    base: BaseReasonType = Field(..., description="Base class to inherit from")
    patterns: list[str] = Field(..., min_length=1, description="List of regex patterns (as strings)")
    explanation: str | None = Field(None, description="Human-readable explanation of the failure")
    issue_url: str | None = Field(None, description="URL to GitLab issue or documentation")
    mixin: str | None = Field(
        None,
        description="Mixin class to customize behavior (format: 'module.path:ClassName' or '.relative.module:ClassName')",
    )
    pattern_flags: int | None = Field(None, description="Optional hyperscan pattern flags")

    @field_validator("patterns")
    @classmethod
    def validate_patterns(cls, v: list[str]) -> list[str]:
        """Validate that patterns are valid regex and compile as bytes."""
        for i, pattern in enumerate(v, 1):
            try:
                # Compile as bytes since that's how they're used in the application
                re.compile(pattern.encode())
            except re.error as e:
                # Provide detailed error message with pattern preview
                pattern_preview = pattern[:100] + "..." if len(pattern) > 100 else pattern
                raise ValueError(f"Invalid regex pattern #{i}: {pattern_preview!r}\n" f"Regex error: {e}") from e
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensure name follows Python class naming conventions."""
        if not v[0].isupper():
            raise ValueError(f"Reason name must start with uppercase: {v}")
        if not v.replace("_", "").replace(".", "").isalnum():
            raise ValueError(f"Reason name must be alphanumeric: {v}")
        return v

    @model_validator(mode="after")
    def validate_issue_url_for_known_failures(self) -> ReasonDefinition:
        """Warn if KnownUnrecoverableFailure lacks an issue_url."""
        if self.base == "KnownUnrecoverableFailure" and not self.issue_url and not self.mixin:
            # This is a soft validation - just for awareness
            pass
        return self

    def to_class(self) -> type[AppLogFailureReason]:
        """Convert this definition to an actual Python class.

        If a mixin is specified, it will be loaded and included in the class hierarchy.
        The mixin is placed before the base class in the MRO to allow method overriding.
        """
        base_class = BASE_REASON_REGISTRY[self.base]

        # Build class attributes
        class_attrs = {}

        # Add patterns (convert strings to bytes)
        patterns_bytes = [p.encode() for p in self.patterns]
        if len(patterns_bytes) == 1:
            class_attrs["pattern"] = patterns_bytes[0]
        else:
            class_attrs["patterns"] = patterns_bytes

        # Add optional attributes
        if self.explanation is not None:
            class_attrs["explanation"] = self.explanation
        if self.issue_url is not None:
            class_attrs["issue_url"] = self.issue_url
        if self.pattern_flags is not None:
            class_attrs["pattern_flags"] = self.pattern_flags

        # Load mixin if specified
        if self.mixin:
            mixin_class = self._load_mixin(self.mixin)
            # Create class with mixin before base class in MRO
            return type(self.name, (mixin_class, base_class), class_attrs)
        else:
            # Create class without mixin
            return type(self.name, (base_class,), class_attrs)

    def _load_mixin(self, mixin_path: str) -> type:
        """Load a mixin class from a module path.

        Args:
            mixin_path: String in format "module.path:ClassName" or ".relative.module:ClassName"

        Returns:
            The mixin class

        Raises:
            ValueError: If the path format is invalid
            ImportError: If the module cannot be imported
            AttributeError: If the class doesn't exist in the module
        """
        if ":" not in mixin_path:
            raise ValueError(f"Invalid mixin path format: {mixin_path}. Expected 'module:ClassName'")

        module_path, class_name = mixin_path.rsplit(":", 1)

        # Import the module
        if module_path.startswith("."):
            from importlib import import_module

            module = import_module(
                module_path, package="LHCbDIRAC.ProductionManagementSystem.Utilities.ProductionTools.LogAnalysis"
            )
        else:
            import importlib

            module = importlib.import_module(module_path)

        # Get the mixin class
        mixin_class = getattr(module, class_name)

        # Validate that it's a class
        if not isinstance(mixin_class, type):
            raise TypeError(f"{mixin_path} is not a class")

        return mixin_class


class ReasonsConfig(BaseModel):
    """Root configuration model for all reasons."""

    reasons: list[ReasonDefinition] = Field(..., description="List of all reason definitions")

    @field_validator("reasons")
    @classmethod
    def validate_unique_names(cls, v: list[ReasonDefinition]) -> list[ReasonDefinition]:
        """Ensure all reason names are unique."""
        names = [r.name for r in v]
        if len(names) != len(set(names)):
            duplicates = [name for name in names if names.count(name) > 1]
            raise ValueError(f"Duplicate reason names found: {duplicates}")
        return v

    @classmethod
    def load_from_yaml(cls, path: Path | None = None) -> ReasonsConfig:
        """Load configuration from YAML file."""
        if path is None:
            path = Path(__file__).parent / "reasons.yaml"
            if "DIRAC_PROD_MANAGER_REASONS_PATH" in os.environ:
                path = Path(os.environ["DIRAC_PROD_MANAGER_REASONS_PATH"])

        with open(path) as f:
            data = yaml.safe_load(f)

        return cls.model_validate(data)

    def create_reason_classes(self) -> dict[str, type[AppLogFailureReason]]:
        """Create reason classes from this configuration.

        Returns:
            Dictionary mapping reason names to their class objects
        """
        return {reason_def.name: reason_def.to_class() for reason_def in self.reasons}
