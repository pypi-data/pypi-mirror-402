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

import pytest

from LHCbDIRAC.ProductionManagementSystem.Utilities.ProductionTools.LogAnalysis.job_analyzer import (
    Job,
    PreAnalysisResult,
)

from . import load_example

TEST_CASES = {
    893788994: {
        "LFN:/lhcb/LHCb/Collision11/DIMUON.DST/00041838/0000/00041838_00003339_1.dimuon.dst": (
            PreAnalysisResult.NO_EVENTS_SELECTED
        ),
    },
    957694667: {
        "LFN:/lhcb/MC/2018/ALLSTREAMS.MDST/00097909/0000/00097909_00000169_7.AllStreams.mdst": (
            PreAnalysisResult.NEEDS_LOG_ANALYSIS
        )
    },
    893543510: {
        "LFN:/lhcb/LHCb/Collision12/LEPTONIC.MDST/00094006/0001/00094006_00018816_1.leptonic.mdst": (
            PreAnalysisResult.NO_XML_SUMMARY
        ),
        "LFN:/lhcb/LHCb/Collision12/LEPTONIC.MDST/00094006/0001/00094006_00019023_1.leptonic.mdst": (
            PreAnalysisResult.NO_XML_SUMMARY
        ),
        "LFN:/lhcb/LHCb/Collision12/LEPTONIC.MDST/00094006/0001/00094006_00019076_1.leptonic.mdst": (
            PreAnalysisResult.NO_XML_SUMMARY
        ),
        "LFN:/lhcb/LHCb/Collision12/LEPTONIC.MDST/00094006/0001/00094006_00019480_1.leptonic.mdst": (
            PreAnalysisResult.NO_XML_SUMMARY
        ),
        "LFN:/lhcb/LHCb/Collision12/LEPTONIC.MDST/00094006/0001/00094006_00019651_1.leptonic.mdst": (
            PreAnalysisResult.NO_XML_SUMMARY
        ),
        "LFN:/lhcb/LHCb/Collision12/LEPTONIC.MDST/00094006/0002/00094006_00020251_1.leptonic.mdst": (
            PreAnalysisResult.NO_XML_SUMMARY
        ),
        "LFN:/lhcb/LHCb/Collision12/LEPTONIC.MDST/00094006/0002/00094006_00020785_1.leptonic.mdst": (
            PreAnalysisResult.NO_XML_SUMMARY
        ),
        "LFN:/lhcb/LHCb/Collision12/LEPTONIC.MDST/00094006/0002/00094006_00021863_1.leptonic.mdst": (
            PreAnalysisResult.NO_XML_SUMMARY
        ),
        "LFN:/lhcb/LHCb/Collision12/LEPTONIC.MDST/00094006/0002/00094006_00024696_1.leptonic.mdst": (
            PreAnalysisResult.NO_XML_SUMMARY
        ),
        "LFN:/lhcb/LHCb/Collision12/LEPTONIC.MDST/00094006/0002/00094006_00024886_1.leptonic.mdst": (
            PreAnalysisResult.NO_XML_SUMMARY
        ),
    },
    957012280: {
        "LFN:/lhcb/MC/2016/ALLRADIATIVE.STRIP.DST/00154282/0000/00154282_00000001_1.allradiative.strip.dst": (
            PreAnalysisResult.MAYBE_POST_APPLICATION_FAILURE
        ),
    },
    893803907: {
        "LFN:/lhcb/LHCb/Collision24/CHARM.DST/00226358/0012/00226358_00121543_1.charm.dst": PreAnalysisResult.NO_XML_SUMMARY,
        "LFN:/lhcb/LHCb/Collision24/CHARM.DST/00226358/0012/00226358_00121830_1.charm.dst": PreAnalysisResult.NO_XML_SUMMARY,
        "LFN:/lhcb/LHCb/Collision24/CHARM.DST/00226358/0012/00226358_00121831_1.charm.dst": PreAnalysisResult.NO_XML_SUMMARY,
        "LFN:/lhcb/LHCb/Collision24/CHARM.DST/00226358/0012/00226358_00121838_1.charm.dst": PreAnalysisResult.NO_XML_SUMMARY,
        "LFN:/lhcb/LHCb/Collision24/CHARM.DST/00226358/0012/00226358_00121839_1.charm.dst": PreAnalysisResult.NO_XML_SUMMARY,
        "LFN:/lhcb/LHCb/Collision24/CHARM.DST/00226358/0012/00226358_00122140_1.charm.dst": PreAnalysisResult.NO_XML_SUMMARY,
        "LFN:/lhcb/LHCb/Collision24/CHARM.DST/00226358/0012/00226358_00122141_1.charm.dst": PreAnalysisResult.NO_XML_SUMMARY,
        "LFN:/lhcb/LHCb/Collision24/CHARM.DST/00226358/0012/00226358_00122151_1.charm.dst": PreAnalysisResult.NO_XML_SUMMARY,
        "LFN:/lhcb/LHCb/Collision24/CHARM.DST/00226358/0012/00226358_00122471_1.charm.dst": PreAnalysisResult.NO_XML_SUMMARY,
        "LFN:/lhcb/LHCb/Collision24/CHARM.DST/00226358/0012/00226358_00122484_1.charm.dst": PreAnalysisResult.NO_XML_SUMMARY,
    },
    940635849: {
        "LFN:/lhcb/data/2023/RAW/BEAMGAS/LHCb/VDM23/275640/275640_00090015_0000.raw": (
            PreAnalysisResult.UNKNOWN_ERROR_ON_JOB_SUCCESS
        ),
        "LFN:/lhcb/data/2023/RAW/BEAMGAS/LHCb/VDM23/275640/275640_00090009_0000.raw": (
            PreAnalysisResult.UNKNOWN_ERROR_ON_JOB_SUCCESS
        ),
    },
    886255904: {
        "LFN:/lhcb/MC/2018/ALLSTREAMS.DST/00173490/0000/00173490_00001002_7.AllStreams.dst": PreAnalysisResult.NO_EVENTS_SELECTED,
        "LFN:/lhcb/MC/2018/ALLSTREAMS.DST/00173490/0000/00173490_00001009_7.AllStreams.dst": PreAnalysisResult.NO_EVENTS_SELECTED,
    },
    929522350: {
        "LFN:/lhcb/LHCb/Collision24/B2CC.DST/00231024/0009/00231024_00092637_1.b2cc.dst": (
            PreAnalysisResult.MAYBE_POST_APPLICATION_FAILURE
        ),
        "LFN:/lhcb/LHCb/Collision24/B2CC.DST/00231024/0009/00231024_00098545_1.b2cc.dst": (
            PreAnalysisResult.MAYBE_POST_APPLICATION_FAILURE
        ),
        "LFN:/lhcb/LHCb/Collision24/B2CC.DST/00231024/0009/00231024_00098828_1.b2cc.dst": (
            PreAnalysisResult.MAYBE_POST_APPLICATION_FAILURE
        ),
        "LFN:/lhcb/LHCb/Collision24/B2CC.DST/00231024/0009/00231024_00098974_1.b2cc.dst": (
            PreAnalysisResult.MAYBE_POST_APPLICATION_FAILURE
        ),
        "LFN:/lhcb/LHCb/Collision24/B2CC.DST/00231024/0009/00231024_00099072_1.b2cc.dst": (
            PreAnalysisResult.MAYBE_POST_APPLICATION_FAILURE
        ),
        "LFN:/lhcb/LHCb/Collision24/B2CC.DST/00231024/0009/00231024_00099474_1.b2cc.dst": (
            PreAnalysisResult.MAYBE_POST_APPLICATION_FAILURE
        ),
        "LFN:/lhcb/LHCb/Collision24/B2CC.DST/00231024/0010/00231024_00104352_1.b2cc.dst": (
            PreAnalysisResult.MAYBE_POST_APPLICATION_FAILURE
        ),
        "LFN:/lhcb/LHCb/Collision24/B2CC.DST/00231024/0010/00231024_00104414_1.b2cc.dst": (
            PreAnalysisResult.MAYBE_POST_APPLICATION_FAILURE
        ),
        "LFN:/lhcb/LHCb/Collision24/B2CC.DST/00231024/0010/00231024_00105096_1.b2cc.dst": (
            PreAnalysisResult.MAYBE_POST_APPLICATION_FAILURE
        ),
        "LFN:/lhcb/LHCb/Collision24/B2CC.DST/00231024/0015/00231024_00156493_1.b2cc.dst": (
            PreAnalysisResult.MAYBE_POST_APPLICATION_FAILURE
        ),
    },
    895008813: {
        "LFN:/lhcb/LHCb/Collision24/BANDQ.DST/00227656/0007/00227656_00075025_1.bandq.dst": PreAnalysisResult.PROBABLY_OK,
        "LFN:/lhcb/LHCb/Collision24/BANDQ.DST/00227656/0007/00227656_00074480_1.bandq.dst": PreAnalysisResult.PROBABLY_OK,
        "LFN:/lhcb/LHCb/Collision24/BANDQ.DST/00227656/0006/00227656_00067693_1.bandq.dst": PreAnalysisResult.PROBABLY_OK,
        "LFN:/lhcb/LHCb/Collision24/BANDQ.DST/00227656/0006/00227656_00067922_1.bandq.dst": PreAnalysisResult.PROBABLY_OK,
        "LFN:/lhcb/LHCb/Collision24/BANDQ.DST/00227656/0006/00227656_00068205_1.bandq.dst": PreAnalysisResult.PROBABLY_OK,
        "LFN:/lhcb/LHCb/Collision24/BANDQ.DST/00227656/0006/00227656_00068589_1.bandq.dst": PreAnalysisResult.PROBABLY_OK,
        "LFN:/lhcb/LHCb/Collision24/BANDQ.DST/00227656/0006/00227656_00068624_1.bandq.dst": PreAnalysisResult.NOT_IN_SUMMARY_XML,
        "LFN:/lhcb/LHCb/Collision24/BANDQ.DST/00227656/0006/00227656_00068625_1.bandq.dst": PreAnalysisResult.NOT_IN_SUMMARY_XML,
        "LFN:/lhcb/LHCb/Collision24/BANDQ.DST/00227656/0006/00227656_00068843_1.bandq.dst": PreAnalysisResult.NOT_IN_SUMMARY_XML,
        "LFN:/lhcb/LHCb/Collision24/BANDQ.DST/00227656/0006/00227656_00068623_1.bandq.dst": PreAnalysisResult.NEEDS_LOG_ANALYSIS,
    },
    # TODO: Add a case of PreAnalysisResult.NEEDS_GROUP_SIZE_REDUCTION
}


@pytest.mark.parametrize("job_id, expected_result", TEST_CASES.items())
def test_pre_analysis(job_id: int, expected_result: dict[str, set[str]]):
    transform_id, task_id, files = load_example(job_id)
    job = Job(transform_id, task_id, files)
    assert job.pre_analysis == expected_result
