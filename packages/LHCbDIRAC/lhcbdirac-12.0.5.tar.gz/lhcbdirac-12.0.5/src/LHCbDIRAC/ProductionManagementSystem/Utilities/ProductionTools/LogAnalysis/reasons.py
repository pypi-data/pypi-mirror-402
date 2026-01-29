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
"""Defines patterns for errors that can be found in LHCb jobs.

NOTE: The order of classes is important for defining the priorities between them.
All reason classes are now defined in reasons.yaml and loaded dynamically.
Classes with custom behavior use mixin classes defined in this module.

The order in reasons.yaml determines the priority of pattern matching.
"""
from __future__ import annotations

import re

from .base_reasons import KnownUnrecoverableFailure, ReasonMixin
from .reason_models import ReasonsConfig

RE_MEMORY_ADDRESS = re.compile(r"(0x[0-9a-f]{4,})(?=[^\w])")


# Mixin classes for customizing failure reason behavior
class FatalGaudiErrorMixin(ReasonMixin):
    """Mixin for FatalGaudiError to extract full error context."""

    @property
    def match_string(self) -> str:
        """Extract FATAL/ERROR lines leading up to the match."""
        log = self._job.files.steps[-1].application_log
        old_start = log.rfind(b"\n", 0, self._start)
        maybe_skip = None
        while (start := log.rfind(b"\n", 0, old_start)) > 0:
            line = log[start:old_start]
            if b"FATAL" in line or b"ERROR" in line:
                old_start = start
                maybe_skip = None
            elif maybe_skip is None:
                maybe_skip = old_start
                old_start = start
            else:
                start = maybe_skip
                break
        else:
            start = 0

        return log[start : self._end].decode(errors="backslashreplace")


class SegfaultTracebackMixin(ReasonMixin):
    """Mixin for UnknownSegmentationFaultWithTraceback to filter and anonymize traceback."""

    @property
    def match_string(self) -> str:
        """Extract traceback with memory addresses masked and Python internals filtered."""
        log = self._job.files.steps[-1].application_log
        match_string = log[self._start : self._end].decode(errors="backslashreplace")

        # Replace anything which looks like a memory address
        match_string = RE_MEMORY_ADDRESS.sub(
            lambda match: "0x" + "X" * len(match.group(0)),
            match_string,
        )
        # Try to remove superfluous parts of the match
        raw_lines = match_string.splitlines(keepends=True)
        filtered_lines = None
        for line in raw_lines:
            if filtered_lines is None:
                # Remove everything before the first line of ====
                if line.startswith("===="):
                    filtered_lines = []
            elif line.startswith("====") or "in _Py" in line or "in Py" in line:
                # Only keep parts of the traceback which are LHCb specific
                # If we reach the second line of ==== we're also done
                break
            else:
                filtered_lines.append(line)
        return "".join(filtered_lines) if filtered_lines else match_string


# Special case: KnownCorruptedFile has empty patterns, needs to be defined manually
class KnownCorruptedFile(KnownUnrecoverableFailure):
    # This is a dummy reason that can only be manually initialised
    patterns = []
    explanation = "This file is known contain some corrupted data."


def _load_reasons_from_yaml() -> dict[str, type]:
    """Load and instantiate all reason classes defined in YAML.

    This function loads the reasons.yaml configuration file and dynamically
    creates Python classes for each reason definition. Classes with mixins
    are automatically composed with the mixin class in the MRO.

    Returns:
        dict: Mapping of reason class names to their class objects
    """
    try:
        config = ReasonsConfig.load_from_yaml()

        # Create all classes from YAML (mixins are handled in to_class())
        all_classes = {}
        for reason_def in config.reasons:
            reason_class = reason_def.to_class()
            all_classes[reason_def.name] = reason_class

        return all_classes

    except Exception as e:
        # If YAML loading fails, provide a helpful error message
        import sys

        print(f"ERROR: Failed to load reasons from YAML: {e}", file=sys.stderr)
        print("Make sure reasons.yaml exists and is valid.", file=sys.stderr)
        raise


# Load all YAML-defined reason classes and add them to the module namespace
# This makes them available for import like: from .reasons import FunctorCompilationFailure
_yaml_reason_classes = _load_reasons_from_yaml()
globals().update(_yaml_reason_classes)

# Export all reason class names and mixins for `from .reasons import *`
__all__ = [
    "RE_MEMORY_ADDRESS",
    "KnownCorruptedFile",
    "FatalGaudiErrorMixin",
    "SegfaultTracebackMixin",
] + list(_yaml_reason_classes.keys())
