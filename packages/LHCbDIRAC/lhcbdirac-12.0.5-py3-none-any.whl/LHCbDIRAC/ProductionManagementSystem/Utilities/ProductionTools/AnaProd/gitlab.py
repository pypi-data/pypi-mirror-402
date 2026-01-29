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

from ..integrations import RepoIssueMetadataBase, RepoIssueBase, GitlabRepoBase


class APIssueMetadata(RepoIssueMetadataBase):
    # [discussion_id] = b64encode(zstd.compress(RequestFeedbackAction))
    open_discussions: dict[str, str] = {}


class APRepoIssue(RepoIssueBase, metadata_model=APIssueMetadata):
    pass


class APGitlabRepo(GitlabRepoBase, project_slug="lhcb-datapkg/AnalysisProductions"):
    pass
