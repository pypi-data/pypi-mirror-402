###############################################################################
# (c) Copyright 2025 CERN for the benefit of the LHCb Collaboration           #
#                                                                             #
# This software is distributed under the terms of the GNU General Public      #
# Licence version 3 (GPL Version 3), copied verbatim in the file "COPYING".   #
#                                                                             #
# In applying this licence, CERN does not waive the privileges and immunities #
# granted to it by virtue of its status as an Intergovernmental Organization  #
# or submit itself to any jurisdiction.                                       #
###############################################################################
from __future__ import annotations

__all__ = ["analyse_log"]

import hyperscan

from .reasons import GenericPythonCrash  # pylint: disable=no-name-in-module
from .job_analyzer import ReasonInfo


db = hyperscan.Database()
patterns = ((GenericPythonCrash.pattern, 0, GenericPythonCrash.pattern_flags),)
expressions, ids, flags = zip(*patterns)
db.compile(expressions=expressions, ids=ids, elements=len(patterns), flags=flags)


def analyse_log(log) -> list[ReasonInfo]:
    context = []
    db.scan(log, match_event_handler=_on_match, context=(log, context))
    return context


def _on_match(id: int, start: int, end: int, flags: int, context: tuple[bytes, list[ReasonInfo]]) -> bool | None:
    reason_info = ReasonInfo(
        type="GenericPythonCrash",
        match=context[0][start:end].decode(errors="backslashreplace"),
        explanation=GenericPythonCrash.explanation,
    )
    context[1].append(reason_info)
