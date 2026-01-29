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
import json
import sys
import re
from datetime import UTC
from typing import Any

from DIRAC import gLogger
from DIRAC.Core.Utilities.ReturnValues import returnValueOrRaise, convertToReturnValue
from DIRAC.Core.Base.Script import Script

from LHCbDIRAC.ProductionManagementSystem.Utilities.Models import DataProduction, SimulationProduction, ProductionBase

REQUEST_COLUMNS = [
    "RequestID",
    "ParentID",
    "MasterID",
    "RequestAuthor",
    "RequestName",
    "RequestType",
    "RequestState",
    "RequestPriority",
    "RequestPDG",
    "RequestWG",
    "SimCondition",
    "SimCondID",
    "SimCondDetail",
    "ProPath",
    "ProID",
    "ProDetail",
    "EventType",
    "NumberOfEvents",
    "Description",
    "Comments",
    "Inform",
    "RealNumberOfEvents",
    "IsModel",
    "Extra",
    "RawRequest",
    "RetentionRate",
    "FastSimulationType",
    "HasSubrequest",
]

TRANSFORM_COLUMNS = [
    "TransformationID",
    "TransformationFamily",
    "TransformationName",
    "Status",
]

IGNORE_TRANSFORM_STATES = {"Cleaning", "Cleaned"}


def parseArgs():
    doForReal = False
    validation = False

    @convertToReturnValue
    def enableDoForReal(_):
        nonlocal doForReal
        doForReal = True

    @convertToReturnValue
    def enableValidation(_):
        nonlocal validation
        validation = True

    switches = [
        ("", "do-for-real", "Actually create steps and submit productions", enableDoForReal),
        ("", "validation", "Run validation production", enableValidation),
    ]
    Script.registerSwitches(switches)
    Script.registerArgument("yaml_path: Path to the YAML file containing productions to submit")
    Script.parseCommandLine(ignoreErrors=False)
    requestIDs = [int(x) for x in Script.getPositionalArgs()]
    return requestIDs, doForReal, validation


@Script()
def main():
    from LHCbDIRAC.ProductionManagementSystem.Client.ProductionRequestClient import ProductionRequestClient
    from LHCbDIRAC.TransformationSystem.Client.TransformationClient import TransformationClient
    from LHCbDIRAC.ProductionManagementSystem.Utilities.Models import parse_obj as parse_request_dict

    requestIDs, doForReal, validation = parseArgs()

    if not requestIDs:
        raise ValueError("No request IDs provided. Please provide at least one request ID.")

    requests = returnValueOrRaise(ProductionRequestClient().getProductionRequest(requestIDs, columns=REQUEST_COLUMNS))
    if missing := set(requestIDs).symmetric_difference(requests.keys()):
        gLogger.error(f"Some of the provided request IDs were not found in the system. Missing IDs: {missing}")
        sys.exit(1)

    transforms = returnValueOrRaise(
        TransformationClient().getTransformations(
            {"TransformationFamily": list(requestIDs)}, columns=TRANSFORM_COLUMNS
        ),
    )
    # By default, the TransformationFamily is returned as a string, but we need it as an int to match the request IDs.
    for transform in transforms:
        transform["TransformationFamily"] = int(transform["TransformationFamily"])

    transforms_by_family = {}
    family_to_generations = {}
    for transform in transforms:
        if match := re.search(r"_(\d+)\.xml$", transform["TransformationName"]):
            family_to_generations.setdefault(transform["TransformationFamily"], set()).add(int(match.group(1)))
        else:
            raise NotImplementedError(
                f"Transformation {transform['TransformationName']} does not have a valid name suffix. "
                "Expected the transformation name to end with _<int>.xml"
            )
        if transform["Status"] in IGNORE_TRANSFORM_STATES:
            continue
        transforms_by_family.setdefault(transform["TransformationFamily"], []).append(transform)

    if transforms_by_family:
        msg = f"Found transformations for the provided request IDs: {transforms_by_family!r}."
        msg += " If you want to launch the requests, please clean them up first."
        if doForReal:
            raise NotImplementedError(msg)
        gLogger.error(msg)

    for request_id, data in requests.items():
        append_name = str(max(family_to_generations.get(request_id, {0})) + 1)
        request = parse_request_dict(json.loads(data["RawRequest"]))

        subrequests = []
        result = returnValueOrRaise(ProductionRequestClient().getProductionRequestList(request_id, "", "ASC", 0, 0, {}))
        for row in result["Rows"]:
            subrequests.append((row["RequestID"], row["ParentID"] or None, row["EventType"]))
        if not subrequests:
            subrequests.append((request_id, None, None))

        set_state(request_id, "Accepted", dryRun=not doForReal)
        for request_id, parent_id, event_type in subrequests:
            gLogger.info(f"Launching production for request ({parent_id}) with append name {append_name}.")
            _launch_production(
                request_id,
                parent_id,
                request,
                data,
                append_name,
                event_type,
                dryRun=not doForReal,
                validation=validation,
            )
        # Simulation productions stay in Accepted until testing is done.
        if not isinstance(request, SimulationProduction):
            set_state(request_id, "Active", dryRun=not doForReal)


def set_state(request_id: int, state: str, dryRun: bool = False) -> bool:
    """Set the state of a production request."""
    from LHCbDIRAC.ProductionManagementSystem.Client.ProductionRequestClient import ProductionRequestClient

    if dryRun:
        gLogger.info(f"Dry run mode enabled, not changing state of request {request_id} to {state}.")
        return True

    gLogger.info(f"Changing state of request {request_id} to {state}.")
    return returnValueOrRaise(ProductionRequestClient().updateProductionRequest(request_id, {"RequestState": state}))


def _launch_production(
    request_id: int,
    parent_id: int | None,
    request: ProductionBase,
    data: dict[str, Any],
    append_name: str,
    event_type: None | str,
    validation: bool,
    dryRun: bool,
) -> list[int]:
    from LHCbDIRAC.ProductionManagementSystem.Client.ProductionRequest import (
        ProductionRequest,
    )
    from LHCbDIRAC.ProductionManagementSystem.Utilities.ModelCompatibility import (
        configure_input,
    )
    from LHCbDIRAC.TransformationSystem.Client.TransformationClient import (
        TransformationClient,
    )

    pr = ProductionRequest()
    pr.requestID = str(request_id)
    pr.appendName = append_name
    pr.visibility = "Yes"
    pr.disableOptionalCorrections = True
    pr.bkSampleMax = request.input_dataset.launch_parameters.sample_max_md5
    pr.bkSampleSeed = request.input_dataset.launch_parameters.sample_seed_md5
    if isinstance(request, DataProduction):
        assert event_type is None, event_type
        assert parent_id is None, parent_id
        configure_input(
            pr,
            data,
            runs=request.input_dataset.launch_parameters.run_numbers,
            startRun=request.input_dataset.launch_parameters.start_run,
            endRun=request.input_dataset.launch_parameters.end_run,
        )
        pr.prodGroup = f"{pr.processingPass}/{json.loads(data['ProDetail'])['pDsc']}"[:50]
        pr.extraModulesList = ["FileUsage"]
    elif isinstance(request, SimulationProduction):
        pr.eventType = request.event_types
        pr.requestID = request_id
        pr.parentRequestID = parent_id
        pr.prodGroup = json.loads(data["ProDetail"])["pDsc"]
    else:
        raise NotImplementedError(request)
    pr.outConfigName = pr.configName

    if validation:
        if not isinstance(request, SimulationProduction):
            if request.input_dataset.launch_parameters.start_run is not None:
                raise ValueError("Expected start_run to be None for validation requests")
            if request.input_dataset.launch_parameters.end_run is not None:
                raise ValueError("Expected end_run to be None for validation requests")
            if not request.input_dataset.launch_parameters.run_numbers:
                raise ValueError("Expected run_numbers to be provided for validation requests")
        pr.outConfigName = "validation"

    configure_steps(pr, data, request)
    ourStepsInProds = pr.stepsInProds

    if dryRun:
        gLogger.info(
            "Dry run mode enabled, to actually launch the production, pass --do-for-real",
        )
        return []

    transform_ids = returnValueOrRaise(pr.buildAndLaunchRequest())
    name = f"{request_id} ({parent_id})" if parent_id else str(request_id)
    gLogger.info(f"Production for request {name} launched successfully.")

    if ourStepsInProds != pr.stepsInProds:
        raise ValueError(
            "Something went horribly wrong: stepsInProds was changed after buildAndLaunchRequest. "
            "Check that applyOptionalCorrections didn't meddle in our business!\n"
            f"The following transformations should be stopped and cleaned: {transform_ids!r}"
        )

    if isinstance(request, DataProduction):
        # If keep_running is False, we need to update the end date of the transformation
        # so files are only added if they exist at the time of launching the request
        new_query = None
        tid = transform_ids[0]
        if end_date := request.input_dataset.launch_parameters.end_date:
            # If the input dataset has an end date, we use that as the end date for the transformation
            new_query = {"EndDate": end_date.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S")}

        if request.input_dataset.launch_parameters.sample_max_md5:
            new_query = (new_query or {}) | {
                "SampleMax": request.input_dataset.launch_parameters.sample_max_md5,
                "SampleSeedMD5": request.input_dataset.launch_parameters.sample_seed_md5,
            }

        if new_query is not None:
            tc = TransformationClient()
            new_query = returnValueOrRaise(tc.getBookkeepingQuery(tid)) | new_query
            returnValueOrRaise(tc.deleteBookkeepingQuery(tid))
            returnValueOrRaise(tc.addBookkeepingQuery(tid, new_query))
            print(f"Modified input query for transformation {tid} to: {new_query}")

    return transform_ids


def find_previousProds(trf_idx, request: ProductionBase, stepsInProds):
    trf = request.submission_info.processing_transforms[trf_idx]
    if trf_idx == 0:
        return None
    from_step_idxs = {x.step_idx for x in request.steps[trf.steps[0]].input}
    if len(from_step_idxs) != 1:
        raise NotImplementedError("Please don't")
    from_step_idx = from_step_idxs.pop()
    for trf_idx_, stepsInProd in enumerate(stepsInProds):
        if from_step_idx + 1 in stepsInProd:
            return trf_idx_ + 1
    raise NotImplementedError("Something went very wrong")


def configure_steps(pr, data, request: ProductionBase):
    pd = json.loads(data["ProDetail"])
    steps_stepIDs = {int(k[1 : -len("Step")]): int(v) for k, v in pd.items() if k.endswith("Step")}
    pr.stepsList = [int(v) for k, v in sorted(steps_stepIDs.items())]

    # The EventTimeout isn't actually stored in the bookkeeping so take it from the raw request
    for dirac_step in request.steps:
        assert dirac_step.id is not None, "All steps must have an ID assigned before launching the production"
        if dirac_step.event_timeout is not None:
            pr.eventTimeouts[dirac_step.id] = dirac_step.event_timeout

    pr.previousProds = []
    for trf_idx, trf in enumerate(request.submission_info.processing_transforms):
        pr.prodsTypeList += [trf.type]
        # which stepIDs are in this transform
        pr.stepsInProds += [[x + 1 for x in trf.steps]]  # this is actually 1-indexed in DIRAC 😱😭
        # where do the outputs get uploaded to
        pr.outputSEs += [trf.output_se]
        # specifies how we access our input files in the transform
        pr.inputDataPolicies += [trf.input_data_policy]
        # the input file plugin to use for the transform
        pr.plugins += [trf.input_plugin]
        # Just the number of steps in this transform.
        pr.outputFileSteps += [len(trf.steps)]
        # the input file group size to the transform.
        pr.groupSizes += [trf.group_size]
        # whether the output is going to be saved?
        output_visibilities = {}
        for trf_step_idx in trf.steps:
            visibilities = {x.visible for x in request.steps[trf_step_idx].output}
            if len(visibilities) != 1:
                raise NotImplementedError("No idea how to make this work...")
            output_visibilities[str(trf_step_idx + 1)] = {True: "Y", False: "N"}[visibilities.pop()]
        pr.outputVisFlag.append(output_visibilities)

        # previousProds is a list of indices (ONE-INDEXED!!!)
        # each pointing to the transformation to take input from
        # referenced in the stepsInProds list.
        # we need to do this otherwise the transforms will not find the correct
        # output to use as input.
        # e.g.
        # 1 = take input from (1-1=0)th transform referenced in stepsInProds
        # 2 = take input from (2-1=1)st transform referenced in stepsInProds
        # 3 = take input from (3-1=2)st transform referenced in stepsInProds
        # n = take input from (n-1)th transform referenced in stepsInProds
        pr.previousProds.append(find_previousProds(trf_idx, request, pr.stepsInProds))
        if trf_idx > 0:
            pr.bkQueries.append("fromPreviousProd")
        elif not pr.bkQueries:
            # Only set the first bkQuery if not already set by configure_input
            # (DataProduction sets it to "Full" or "fromPreviousProd", SimulationProduction leaves it empty)
            pr.bkQueries.append("")

        # left blank
        pr.targets += [""]
        # left blank
        pr.specialOutputSEs += [{}]
        # whether the input files should be removed when used by
        # the transform - need to be very careful with this
        pr.removeInputsFlags += [trf.remove_inputs_flags]
        # leave as is
        pr.priorities += [trf.priority]
        # left blank
        pr.inputs += [[]]
        # ???
        pr.outputFileMasks += [trf.output_file_mask]
        # left as is
        pr.multicore += [str(trf.multicore)]
        # ???
        pr.outputModes += [trf.output_mode]
        # we process all events
        pr.events += [trf.events]
        # leave as is as not relevant
        pr.ancestorDepths += [trf.ancestor_depth]
        # extra input sandboxes to be used in the transform
        pr.inputSandboxes += [trf.extra_sandboxes or []]
        # compression is not handled at this point but in our
        # application config
        pr.compressionLvl += ["LOW"]
        # left as is
        pr.cpus += [trf.cpu]
        # processors
        pr.processors += [trf.processors]

    # DO NOT REMOVE THIS!
    if pr.removeInputsFlags[0] is not False:
        raise NotImplementedError("The first transformation should never remove inputs...")
    if len(pr.previousProds) != len(pr.prodsTypeList):
        raise ValueError("The number of previous productions does not match the number of production types.")


if __name__ == "__main__":
    main()
