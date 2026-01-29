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
from __future__ import annotations

import functools
import re
import sys
from collections.abc import Callable, Collection
from dataclasses import dataclass
from itertools import pairwise
from typing import TYPE_CHECKING, Generic, TypeVar

import hyperscan


if TYPE_CHECKING:
    from .job_analyzer import Job


T = TypeVar("T")


@dataclass
class LogFileMatches:
    init: list[LogFileMatch]
    by_lfn: dict[str, list[LogFileMatch]]
    finalize: list[LogFileMatch]

    def __init__(self, lfns: Collection[str]) -> None:
        self.init = []
        self.by_lfn = {lfn: [] for lfn in lfns}
        self.finalize = []

    def apply_sorting(self):
        self.init = sorted(self.init)
        self.by_lfn = {k: sorted(v) for k, v in self.by_lfn.items()}
        self.finalize = sorted(self.finalize)


class classproperty(Generic[T]):
    def __init__(self, method: Callable[..., T]):
        self.method = method
        functools.update_wrapper(self, method)  # type: ignore

    def __get__(self, obj, cls=None) -> T:
        if cls is None:
            cls = type(obj)
        return self.method(cls)


class ReasonMixin:
    """Base class for mixins that customize failure reason behavior.

    Mixins can override specific methods to provide custom implementations
    for failure reason classes. Only the methods defined here can be overridden.
    """

    @property
    def match_string(self) -> str:
        """Return the string representation of the match.

        Override this to customize how the matched portion of the log is extracted
        and formatted. The default implementation returns the matched bytes decoded
        as a string.
        """
        raise NotImplementedError("Subclasses must implement match_string")


class LogFileMatch:
    pattern_flags: int = hyperscan.HS_FLAG_SOM_LEFTMOST
    explanation: str | None = None
    _db: hyperscan.Database | None = None

    _reasons = []
    id_to_pattern: dict[int, str] = {}
    id_to_reason: dict[int, type[LogFileMatch]] = {}

    def __init__(self, job: Job, start: int, end: int) -> None:
        """Initialize a specific occurrence of this failure."""
        self._job = job
        self._start = start
        self._end = end

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(job, {self._start}, {self._end})"

    def __hash__(self) -> int:
        return hash((self.__class__, self._job, self.match_string))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self._job == other._job and self.match_string == other.match_string

    @property
    def match_string(self) -> str:
        return self._job.files.steps[-1].application_log[self._start : self._end].decode(errors="backslashreplace")

    @classproperty
    def reason_to_id(cls) -> dict[type[LogFileMatch], int]:  # pylint: disable=no-self-argument
        if not hasattr(cls, "_reason_to_id"):
            # Trigger the initialization of the database
            cls.db
        return cls._reason_to_id

    @classproperty
    def name_to_id(cls) -> dict[str, int]:  # pylint: disable=no-self-argument
        if not hasattr(cls, "_name_to_id"):
            # Trigger the initialization of the database
            cls.db
        return cls._name_to_id

    @classproperty
    def name_to_reason(cls) -> dict[str, type[LogFileMatch]]:  # pylint: disable=no-self-argument
        if not hasattr(cls, "_name_to_reason"):
            cls._name_to_reason = {name: cls.id_to_reason[i] for name, i in cls.name_to_id.items()}
        return cls._name_to_reason

    # pylint: disable=no-self-argument
    @classproperty
    def db(cls) -> hyperscan.Database:
        if cls._db is None:
            i = 0
            for reason in cls._reasons:
                if not reason.patterns:
                    cls.id_to_reason[i] = reason
                    i += 1
                    continue
                for pattern in reason.patterns:
                    cls.id_to_pattern[i] = pattern
                    cls.id_to_reason[i] = reason
                    i += 1
            cls._reason_to_id = {reason: i for i, reason in cls.id_to_reason.items()}
            cls._name_to_id = {reason.__name__: i for i, reason in cls.id_to_reason.items()}
            if len(cls.reason_to_id) != len(cls.name_to_id):
                raise NotImplementedError()

            ids, expressions = zip(*cls.id_to_pattern.items())
            flags = [cls.id_to_reason[i].pattern_flags for i in ids]
            db = hyperscan.Database()
            db.compile(expressions=expressions, ids=ids, elements=len(expressions), flags=flags)
            cls._db = db
        return cls._db

    @classmethod
    def _match_event_handler(
        cls, id: int, start: int, end: int, flags: int, context: tuple[Job, list[LogFileMatch]]
    ) -> bool | None:
        job, results = context
        reason_cls = cls.id_to_reason[id]
        kwargs = {}
        if issubclass(reason_cls, AppLogFailureReason):
            kwargs["priority"] = id
        results.append(cls.id_to_reason[id](job, start, end, **kwargs))

    @classmethod
    def scan_job_log(cls, job: Job) -> LogFileMatches:
        log_analysis_results = []
        if job.files.steps[-1].application_log is not None:
            cls.db.scan(  # pylint: disable=no-member
                job.files.steps[-1].application_log,
                context=(job, log_analysis_results),
                match_event_handler=cls._match_event_handler,
            )

        problems = []
        log_pos_to_file_open: dict[int, tuple[bool, str]] = {}
        # first_print_per_stream = {}
        # failed_to_open_events = {}
        event_loop_end = sys.maxsize
        application_manager_start = None
        for match in log_analysis_results:
            if isinstance(match, AppLogFailureReason):
                problems.append(match)
            elif isinstance(match, ConnectToFileEvent):
                log_pos_to_file_open[match._start] = (False, match.lfn)
            elif isinstance(match, (EndEventLoopEvent, ApplicationManagerStopEvent)):
                event_loop_end = min(event_loop_end, match._end)
            elif isinstance(match, EventSelectorPrintEvent):
                input_lfns = job.files.steps[-1].prodrun_config["input"]["files"]
                log_pos_to_file_open[match._start] = (False, input_lfns[match.stream_index - 1])
                # if match.stream_index not in first_print_per_stream.values():
                #     first_print_per_stream[match._start] = match.stream_index
            elif isinstance(match, FailedToOpenFileEvent):
                lfn = job.files.xml_catalog.find(f".//File[@ID='{match.guid}']").find(".//logical/lfn").attrib["name"]
                if not lfn.startswith("LFN:"):
                    lfn = f"LFN:{lfn}"
                log_pos_to_file_open[match._start] = (True, lfn)
            elif isinstance(match, ApplicationManagerStartEvent):
                application_manager_start = match._start
            elif isinstance(match, NewEventSelectorPrintEvent):
                log_pos_to_file_open[match._start] = (False, match.lfn)

        if log_pos_to_file_open:
            # Simplify log_pos_to_file_open to only contain the file start positions.
            # For files where we only have end positions, replaced them with a best
            # guess of when that file starts
            to_iter = sorted(log_pos_to_file_open.items())
            (b_idx, (b_end, b_lfn)) = to_iter[0]
            log_pos_to_file_open: dict[int, str] = {application_manager_start + 1 if b_end else b_idx: b_lfn}
            for (a_idx, (a_end, a_lfn)), (b_idx, (b_end, b_lfn)) in pairwise(to_iter):
                if a_end == b_end and a_lfn == b_lfn:
                    continue
                log_pos_to_file_open[a_idx + 1 if b_end else b_idx] = b_lfn

        boundaries = sorted(log_pos_to_file_open)
        result = LogFileMatches(log_pos_to_file_open.values())
        for problem in problems:
            if not boundaries or problem._start < boundaries[0]:
                result.init.append(problem)
            elif problem._start > event_loop_end:
                result.finalize.append(problem)
            else:
                for boundary in boundaries:
                    if problem._start < boundary:
                        break
                    lfn = log_pos_to_file_open[boundary]
                result.by_lfn[lfn].append(problem)

        if log_pos_to_file_open:
            input_lfns = job.files.steps[-1].prodrun_config["input"]["files"]
            last_found_lfn = log_pos_to_file_open[max(log_pos_to_file_open)]
            last_found_lfn_idx = input_lfns.index(last_found_lfn)
            if len(input_lfns) > last_found_lfn_idx + 1:
                next_lfn = input_lfns[last_found_lfn_idx + 1]
                if (
                    job.pre_analysis[last_found_lfn] == "probably_ok"
                    and job.pre_analysis[next_lfn] == "needs_log_analysis"
                ):
                    result.by_lfn[next_lfn] = result.by_lfn.pop(last_found_lfn)
                    result.by_lfn[last_found_lfn] = []

        result.apply_sorting()
        return result

    def __init_subclass__(cls, *, abstract=False) -> None:
        """Register a new failure reason"""
        if cls._db is not None:
            raise TypeError("Cannot register a new reason after the database has been compiled!")

        patterns = None
        if hasattr(cls, "pattern") and hasattr(cls, "patterns"):
            raise TypeError("LogFileMatch subclasses must not have both pattern and patterns!")
        elif hasattr(cls, "pattern"):
            patterns = [cls.pattern]
        elif hasattr(cls, "patterns"):
            patterns = cls.patterns

        if abstract:
            if patterns is not None:
                raise TypeError("LogFileMatch subclasses must not have a pattern or patterns!", cls)
        elif patterns is None:
            raise TypeError("LogFileMatch subclasses must have a pattern or patterns!", cls)
        else:
            cls._reasons.append(cls)
            if not hasattr(cls, "patterns"):
                cls.patterns = patterns

        return super().__init_subclass__()


class AppLogFailureReason(LogFileMatch, abstract=True):
    """Describes a part of the application log which indicates a problem."""

    def __init__(self, job: Job, start: int, end: int, *, priority: int) -> None:
        super().__init__(job, start, end)
        self.priority = priority

    def __len__(self) -> int:
        return self._end - self._start

    def __lt__(self, other):
        return (self.priority, -len(self)) < (other.priority, -len(other))


class RecoverableFailure(AppLogFailureReason, abstract=True): ...


class RecoverableFailureWithManualIntervention(RecoverableFailure, abstract=True): ...


class KnownUnrecoverableFailure(AppLogFailureReason, abstract=True):
    issue_url: str


class WorkerNodeIssue(RecoverableFailure, abstract=True): ...


class EventTimeout(AppLogFailureReason, abstract=True): ...


class UnknownFailure(AppLogFailureReason, abstract=True): ...


class Event(LogFileMatch, abstract=True):
    """Describes a part of the application log which indicates an event like connecting to a file."""


class ConnectToFileEvent(Event):
    pattern = rb"(?:RootIOAlg|Stream:EventSelector).+DATAFILE='(LFN:[^']+)'"
    RE_PATTERN = re.compile(pattern)

    @property
    def lfn(self) -> str:
        return self.RE_PATTERN.search(self.match_string.encode()).group(1).decode()


class DisconnectFromFileEvent(Event):
    pattern = rb"Disconnect from dataset.+\n"


class EndEventLoopEvent(Event):
    pattern = rb"No more events in event selection"


class EventSelectorPrintEvent(Event):
    pattern = rb"Record number within stream (\d+):"
    RE_PATTERN = re.compile(pattern)

    @property
    def stream_index(self) -> int:
        return int(self.RE_PATTERN.search(self.match_string.encode()).group(1))


class NewEventSelectorPrintEvent(Event):
    pattern = rb"Reading Event record (\d+) within ([^\s]+?),?\s"
    RE_PATTERN = re.compile(pattern)

    @property
    def stream_index(self) -> int:
        return int(self.RE_PATTERN.search(self.match_string.encode()).group(1))

    @property
    def lfn(self) -> str:
        return self.RE_PATTERN.search(self.match_string.encode()).group(2).decode()


class FailedToOpenFileEvent(Event):
    pattern = rb"Failed to open dsn:([^ ]+) "
    RE_PATTERN = re.compile(pattern)

    @property
    def guid(self) -> str:
        return self.RE_PATTERN.search(self.match_string.encode()).group(1).decode()


class ApplicationManagerStartEvent(Event):
    pattern = rb"Application Manager Started successfully"


class ApplicationManagerStopEvent(Event):
    pattern = rb"Application Manager Stopped successfully"
