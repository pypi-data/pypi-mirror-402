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

from collections import defaultdict
from datetime import datetime, timedelta
from functools import cached_property

import pytz
from pydantic import BaseModel

from .constants import ACTIVE_TRANSFORMATION_STATES
from .gitlab import APGitlabRepo
from ..integrations import OperationsLogbook
from ..LogAnalysis.prod_analyzer import GroupedProblems


class APTransformDebugInfo(BaseModel):
    transform_id: int
    state: str
    type: str
    group_size: int
    active_inputs: set[int]
    file_counts: dict[str, int] | None = None
    problems: GroupedProblems | None = None


class APRequestDebugInfo(BaseModel):
    request_id: int
    transforms: list[APTransformDebugInfo] = []

    @cached_property
    def long_running(self):
        for transform in self.transforms:
            if transform.state not in ACTIVE_TRANSFORMATION_STATES:
                continue
            return bool(transform.active_inputs)
        return False


class APBaseDebugInfo(BaseModel):
    version: str
    issue_url: str | None
    requests: list[APRequestDebugInfo] = []


class APDebugInfo(APBaseDebugInfo):
    wg: str
    analysis: str
    created: datetime

    @cached_property
    def time_since_creation(self) -> timedelta:
        timezone = pytz.timezone("Europe/Zurich")
        return datetime.now(tz=timezone) - self.created

    @property
    def key(self):
        return (self.wg, self.analysis, self.version)


class APOverview(BaseModel):
    missing: list[int] = []
    recent: list[APDebugInfo] = []
    stuck: list[APDebugInfo] = []
    to_archive: list[APBaseDebugInfo] = []

    active: list[APDebugInfo] = []
    transform_ids_to_check: set[int] = set()

    @cached_property
    def running(self) -> list[APDebugInfo]:
        result = []
        for ap in self.active:
            requests = [req for req in ap.requests if not req.long_running]
            if not requests:
                continue
            ap = ap.model_copy(deep=True)
            ap.requests = requests
            result.append(ap)
        return result

    @cached_property
    def long_running(self) -> list[APDebugInfo]:
        result = []
        for ap in self.active:
            requests = [req for req in ap.requests if req.long_running]
            if not requests:
                continue
            ap = ap.model_copy(deep=True)
            ap.requests = requests
            result.append(ap)
        return result

    @cached_property
    def key_to_ap(self) -> dict[tuple[str, str, str], APDebugInfo]:
        result = {ap.key: ap for ap in self.active}
        assert len(self.active) == len(result)
        return result

    @cached_property
    def request_id_to_aps(self) -> dict[int, list[APDebugInfo]]:
        result = defaultdict(list)
        for ap in self.active:
            for req in ap.requests:
                result[req.request_id].append(ap)
        return dict(result)

    @cached_property
    def transform_id_to_request_id(self) -> dict[int, int]:
        result = {t.transform_id: req.request_id for ap in self.active for req in ap.requests for t in req.transforms}
        return result

    @cached_property
    def transform_id_to_transform(self) -> dict[int, APTransformDebugInfo]:
        result = {t.transform_id: t for ap in self.active for req in ap.requests for t in req.transforms}
        return result

    @cached_property
    def repo(self):
        return APGitlabRepo(with_auth=True)

    @cached_property
    def logbook(self):
        return OperationsLogbook()
