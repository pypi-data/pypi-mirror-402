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

from LHCbDIRAC.ProductionManagementSystem.Utilities.ProductionTools.LogAnalysis.classes import (
    JobArtifacts,
    JobArtifactConsistencyError,
)

from . import load_example


@pytest.mark.parametrize(
    "in_files, out_keys, out_steps_keys",
    [
        ({}, {}, []),
        (
            {
                "DaVinci_00244431_00000106_1.log": b"DAVINCI_00244431_00000106_1.LOG",
                "jobDescription.xml": b"JOBDESCRIPTION.XML",
                "job.info": b"JOB.INFO",
                "pool_xml_catalog.xml": b"POOL_XML_CATALOG.XML",
                "prmon_00244431_00000106_1.txt": b"PRMON_00244431_00000106_1.TXT",
                "prmon.log": b"PRMON.LOG",
                "prodConf_00244431_00000106_1.py": b"PRODCONF_00244431_00000106_1.PY",
                "prodConf_DaVinci_00244431_00000106_1.json": b"PRODCONF_DAVINCI_00244431_00000106_1.JSON",
                "std.out": b"STD.OUT",
                "summaryDaVinci_00244431_00000106_1.xml": b"SUMMARYDAVINCI_00244431_00000106_1.XML",
            },
            {
                "jobDescription.xml",
                "job.info",
                "pool_xml_catalog.xml",
                "prmon.log",
                "std.out",
            },
            [
                {
                    "DaVinci_00244431_00000106_1.log",
                    "prmon_00244431_00000106_1.txt",
                    "prodConf_00244431_00000106_1.py",
                    "prodConf_DaVinci_00244431_00000106_1.json",
                    "summaryDaVinci_00244431_00000106_1.xml",
                }
            ],
        ),
        (
            {
                "Moore_00244431_00000106_2.log": b"MOORE_00244431_00000106_2.LOG",
                "Boole_00244431_00000106_1.log": b"BOOLE_00244431_00000106_1.LOG",
                "bookkeeping_00244431_00000106_1.xml": b"BOOKKEEPING_00244431_00000106_1.XML",
                "bookkeeping_00244431_00000106_2.xml": b"BOOKKEEPING_00244431_00000106_2.XML",
                "job.info": b"JOB.INFO",
                "jobDescription.xml": b"JOBDESCRIPTION.XML",
                "pool_xml_catalog.xml": b"POOL_XML_CATALOG.XML",
                "prmon.log": b"PRMON.LOG",
                "prmon_00244431_00000106_1.txt": b"PRMON_00244431_00000106_1.TXT",
                "prmon_00244431_00000106_2.txt": b"PRMON_00244431_00000106_2.TXT",
                "prodConf_00244431_00000106_1.py": b"PRODCONF_00244431_00000106_1.PY",
                "prodConf_Boole_00244431_00000106_1.json": b"PRODCONF_BOOLE_00244431_00000106_1.JSON",
                "prodConf_Moore_00244431_00000106_2.json": b"PRODCONF_MOORE_00244431_00000106_2.JSON",
                "std.out": b"STD.OUT",
                "summaryBoole_00244431_00000106_1.xml": b"SUMMARYBOOLE_00244431_00000106_1.XML",
                "summaryMoore_00244431_00000106_2.xml": b"SUMMARYMOORE_00244431_00000106_2.XML",
            },
            {
                "std.out",
                "job.info",
                "jobDescription.xml",
                "pool_xml_catalog.xml",
                "prmon.log",
            },
            [
                {
                    "Boole_00244431_00000106_1.log",
                    "bookkeeping_00244431_00000106_1.xml",
                    "prmon_00244431_00000106_1.txt",
                    "prodConf_00244431_00000106_1.py",
                    "prodConf_Boole_00244431_00000106_1.json",
                    "summaryBoole_00244431_00000106_1.xml",
                },
                {
                    "Moore_00244431_00000106_2.log",
                    "bookkeeping_00244431_00000106_2.xml",
                    "prmon_00244431_00000106_2.txt",
                    "prodConf_Moore_00244431_00000106_2.json",
                    "summaryMoore_00244431_00000106_2.xml",
                },
            ],
        ),
    ],
)
def test_artifact_loading(in_files, out_keys, out_steps_keys):
    # Add the expected output keys
    out_job_files = {k: in_files[k] for k in out_keys}
    out_steps_files = [{k: in_files[k] for k in v} for v in out_steps_keys]
    # Parse the file list
    job_artifacts = JobArtifacts.from_files(in_files, transform_id=244431, task_id=106)
    # Check the output is as expected
    assert out_job_files == job_artifacts._files
    assert out_steps_files == [step._files for step in job_artifacts.steps]


def test_inconsistent_artifact_loading():
    files = {
        "Moore_00241881_00001234_2.log": b"MOORE_00241881_00001234_2.LOG",
        "Boole_00241881_00001234_1.log": b"BOOLE_00241881_00001234_1.LOG",
        "bookkeeping_00241881_00001234_1.xml": b"BOOKKEEPING_00241881_00001234_1.XML",
        "bookkeeping_00241881_00001234_2.xml": b"BOOKKEEPING_00241881_00001234_2.XML",
        "job.info": b"JOB.INFO",
        "jobDescription.xml": b"JOBDESCRIPTION.XML",
        "pool_xml_catalog.xml": b"POOL_XML_CATALOG.XML",
        "prmon.log": b"PRMON.LOG",
        "prmon_00241881_00001234_1.txt": b"PRMON_00241881_00001234_1.TXT",
        "prmon_00241881_00001234_2.txt": b"PRMON_00241881_00001234_2.TXT",
        "prodConf_00241881_00001234_1.py": b"PRODCONF_00241881_00001234_1.PY",
        "prodConf_Boole_00241881_00001234_1.json": b"PRODCONF_BOOLE_00241881_00001234_1.JSON",
        "prodConf_Moore_00241881_00001234_2.json": b"PRODCONF_MOORE_00241881_00001234_2.JSON",
        "std.out": b"STD.OUT",
        "summaryBoole_00241881_00001234_1.xml": b"SUMMARYBOOLE_00241881_00001234_1.XML",
        "summaryMoore_00241881_00001234_2.xml": b"SUMMARYMOORE_00241881_00001234_2.XML",
    }
    # Make sure this works as expected
    JobArtifacts.from_files(files, transform_id=241881, task_id=1234)
    # Check the various error cases
    with pytest.raises(JobArtifactConsistencyError, match="Transformation ID mismatch"):
        JobArtifacts.from_files(files, transform_id=241882, task_id=1234)
    with pytest.raises(JobArtifactConsistencyError, match="Task ID mismatch"):
        JobArtifacts.from_files(files, transform_id=241881, task_id=106)
    bad_files = files | {"prodConf_Boole_12345678_00001234_1.json": b"AAA"}
    with pytest.raises(JobArtifactConsistencyError, match="Transformation ID mismatch"):
        JobArtifacts.from_files(bad_files, transform_id=241881, task_id=1234)
    bad_files = files | {"prodConf_Boole_00241881_00000001_1.json": b"AAA"}
    with pytest.raises(JobArtifactConsistencyError, match="Task ID mismatch"):
        JobArtifacts.from_files(bad_files, transform_id=241881, task_id=1234)


def test_parsing():
    transform_id, task_id, files = load_example(957694667)
    job_artifacts = JobArtifacts.from_files(files, transform_id=transform_id, task_id=task_id)

    assert b"957694667" in job_artifacts.dirac_log
    assert job_artifacts.workflow.find(".//StepInstance/Parameter[@name='applicationVersion']/value").text == "v46r8"

    assert len(job_artifacts.steps) == 1

    assert b"DaVinciInitAlg    SUCCESS" in job_artifacts.steps[0].application_log
    assert job_artifacts.steps[0].prodrun_config["input"]["files"] == [
        "LFN:/lhcb/MC/2018/ALLSTREAMS.MDST/00097909/0000/00097909_00000169_7.AllStreams.mdst"
    ]
    assert job_artifacts.steps[0].summary_xml.findall(".//input/file")[0].attrib["status"] == "part"
