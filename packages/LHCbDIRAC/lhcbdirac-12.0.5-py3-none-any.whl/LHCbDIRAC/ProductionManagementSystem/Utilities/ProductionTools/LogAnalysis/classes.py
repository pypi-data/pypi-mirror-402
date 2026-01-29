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

import re
import json
import xml.etree.ElementTree as ET
import fnmatch
from collections import defaultdict
from collections.abc import Sequence
from functools import cached_property
from typing import Any

RE_STEP_ARTIFACT_NAME = re.compile(
    r"(?P<prefix>[A-Za-z0-9_-]+)_(?P<transform_id>[\d]{8})_(?P<task_id>[\d]{8})_(?P<step_idx>[\d]+)\.(?P<suffix>[a-z]+)"
)


class StepArtifacts:
    """A collection of artifacts which all correspond to a single step inside a job"""

    def __init__(self, files: dict[str, bytes]):
        self._files = files

    def get_file(self, pattern: str) -> bytes | None:
        matches = fnmatch.filter(self._files, pattern)
        if len(matches) == 0:
            return None
        elif len(matches) > 1:
            raise NotImplementedError(f"Multiple matches for {pattern}: {matches}")
        return self._files[matches[0]]

    @property
    def application_log(self) -> bytes | None:
        return self.get_file("*.log")

    @property
    def summary_xml(self) -> ET.ElementTree | None:
        if not hasattr(self, "_summary_xml"):
            xml_content = self.get_file("summary*.xml")
            if xml_content:
                self._summary_xml = ET.ElementTree(ET.fromstring(xml_content.decode("utf-8")))
            else:
                self._summary_xml = None
        return self._summary_xml

    @property
    def prodrun_config(self) -> dict[str, Any] | None:
        if not hasattr(self, "_prodrun_config"):
            json_content = self.get_file("prodConf*.json")
            if json_content is None:
                self._prodrun_config = None
            else:
                self._prodrun_config = json.loads(json_content.decode("utf-8"))
        return self._prodrun_config

    @cached_property
    def prmon_data(self) -> dict[str, Sequence[int]] | None:
        raw_data = self.get_file("prmon_*.txt")
        if raw_data is None:
            return None
        headings, *data = raw_data.decode().splitlines()
        headings = headings.split("\t")
        data = dict(zip(headings, zip(*(list(map(int, x.split("\t"))) for x in data))))
        if data:
            data["rss+swap"] = [r + s for r, s in zip(data["rss"], data["swap"])]
        return data

    @property
    def bk_xml(self) -> ET.ElementTree | None:
        if not hasattr(self, "_bk_xml"):
            xml_content = self.get_file("bookkeeping*.xml")
            if xml_content is None:
                self._bk_xml = None
            else:
                self._bk_xml = ET.ElementTree(ET.fromstring(xml_content.decode("utf-8")))
        return self._bk_xml


class JobArtifactConsistencyError(ValueError):
    """Raised when the artifacts of a job are inconsistent"""


class JobArtifacts:
    """A collection of artifacts which all correspond to a single job"""

    @classmethod
    def from_files(cls, files: dict[str, bytes], *, transform_id: int, task_id: int):
        job_files = {}
        steps = defaultdict(dict)
        for filename, contents in files.items():
            if match := RE_STEP_ARTIFACT_NAME.fullmatch(filename):
                steps[match.group("step_idx")][filename] = contents

                # Sanity check that all files in a step have the expected transform and task IDs
                if transform_id != int(match.group("transform_id")):
                    raise JobArtifactConsistencyError("Transformation ID mismatch")
                if task_id != int(match.group("task_id")):
                    raise JobArtifactConsistencyError("Task ID mismatch")
            else:
                job_files[filename] = contents

        steps = [StepArtifacts(files) for _, files in sorted(steps.items(), key=lambda x: x[0])]
        return cls(steps, job_files)

    def __init__(self, steps: list[StepArtifacts], files: dict[str, bytes]):
        self.steps = steps
        self._files = files

    @property
    def dirac_log(self) -> bytes | None:
        return self._files.get("std.out")

    @property
    def workflow(self) -> ET.ElementTree:
        """Parse and return the workflow XML from the job description."""
        if not hasattr(self, "_workflow"):
            job_description = self._files.get("jobDescription.xml")
            if job_description is None:
                self._workflow = None
            else:
                self._workflow = ET.fromstring(job_description.decode("utf-8"))
        return self._workflow

    @property
    def xml_catalog(self) -> ET.ElementTree | None:
        if not hasattr(self, "_xml_catalog"):
            xml_content = self._files.get("pool_xml_catalog.xml")
            if xml_content is None:
                self._xml_catalog = None
            else:
                self._xml_catalog = ET.ElementTree(ET.fromstring(xml_content.decode("utf-8")))
        return self._xml_catalog
