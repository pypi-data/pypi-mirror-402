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

__all__ = ["presorted_groupby", "unsorted_groupby", "call_dirac", "old_to_new_log_url", "ProgressUpdater", "Progress"]

import asyncio
from dataclasses import dataclass
from functools import partial
from itertools import groupby as _groupby
from urllib.parse import urlencode, urlparse

from DIRAC.Core.Utilities.ReturnValues import returnValueOrRaise
from rich.progress import Progress as _Progress, MofNCompleteColumn, TimeElapsedColumn, TaskID as ProgressBarTaskID


@dataclass
class ProgressUpdater:
    progress: _Progress | None = None
    task: ProgressBarTaskID | None = None

    def advance(self):
        if self.progress is None or self.task is None:
            return
        self.progress.update(self.task, advance=1)

    def advance_total(self, n: int):
        if self.progress is None or self.task is None:
            return
        total = self.progress.tasks[self.progress.task_ids.index(self.task)].total
        total = total + n if total else n
        self.progress.update(self.task, total=total)


Progress = partial(_Progress, MofNCompleteColumn(), *_Progress.get_default_columns(), TimeElapsedColumn())


def presorted_groupby(iterable, key=None):
    return _groupby(iterable, key=key)


def unsorted_groupby(iterable, key=None):
    return _groupby(sorted(iterable, key=key), key=key)


async def call_dirac(func, *args, **kwargs):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, partial(func, *args, **kwargs))
    return returnValueOrRaise(result)


def old_to_new_log_url(url):
    if not url or "lhcb-productions.web.cern.ch" in url:
        return url
    path = urlparse(url).path.split("/")
    lfn = "/".join(path[:7])
    task_id = path[7]
    query = urlencode({"lfn": lfn, "task_name": task_id})
    return f"https://lhcb-productions.web.cern.ch/logs/?{query}"
