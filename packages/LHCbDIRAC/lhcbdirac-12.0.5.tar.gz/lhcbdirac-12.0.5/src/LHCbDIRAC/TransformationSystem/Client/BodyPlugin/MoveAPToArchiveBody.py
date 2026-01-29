###############################################################################
# (c) Copyright 2021 CERN for the benefit of the LHCb Collaboration           #
#                                                                             #
# This software is distributed under the terms of the GNU General Public      #
# Licence version 3 (GPL Version 3), copied verbatim in the file "COPYING".   #
#                                                                             #
# In applying this licence, CERN does not waive the privileges and immunities #
# granted to it by virtue of its status as an Intergovernmental Organization  #
# or submit itself to any jurisdiction.                                       #
###############################################################################

from DIRAC.RequestManagementSystem.Client.Request import Request
from DIRAC.RequestManagementSystem.Client.Operation import Operation
from DIRAC.RequestManagementSystem.Client.File import File

from DIRAC.TransformationSystem.Client.BodyPlugin.BaseBody import BaseBody

BUFFER_TYPE = "-BUFFER"
DST_TYPE = "-DST"


ALREADY_REPLICATED_TARGET = "ALREADY_REPLICATED"


class MoveAPToArchiveBody(BaseBody):
    """
    This body is to be used for the MoveAPToArchive plugin:

    The file either needs to be replicated to an archive and then removed from CERN-ANAPROD,
    or it has already been replicated and only the removal is needed.
    In the later case, the TargetSE will be

    This workflow now also works with DST instead of buffer
    """

    # This is needed to know how to serialize the object
    _attrToSerialize = []

    @staticmethod
    def _createOperation(operationType, lfns, targetSE, sourceSE=None):
        """
        Generate an Operation object of the given Type, with the
        specified targetSE and sourceSE. Associate to it File objects
        from the lfns list

        :param str operationType: Type of the operation (RemoveReplica, ReplicateAndRegister, etc)
        :param list lfns: list of LFNs on which to perform the operation
        :param str targetSE: SE name(s) targeted by the ops
        :param str sourceSE: SE name of the source
        """
        newOp = Operation()
        newOp.Type = operationType
        newOp.TargetSE = targetSE
        if sourceSE:
            newOp.SourceSE = sourceSE
        for lfn in lfns:
            opFile = File()
            opFile.LFN = lfn
            newOp.addFile(opFile)
        return newOp

    def taskToRequest(self, taskID, task, transID):
        """
        Create the request object from the task Dict


        """

        if isinstance(task["InputData"], list):
            lfns = task["InputData"]
        elif isinstance(task["InputData"], str):
            lfns = task["InputData"].split(";")
        else:
            raise ValueError(f"InputData must be a list or a string, not {type(task['InputData'])}")

        req = Request()

        targetSEs = task["TargetSE"].split(",")
        assert len(targetSEs) == 1, targetSEs

        # If not already replicated, replicate to the Archive
        if targetSEs[0] != ALREADY_REPLICATED_TARGET:
            repArchive = self._createOperation("ReplicateAndRegister", lfns, targetSEs)
            req.addOperation(repArchive)

        # Finally, remove the replicas from CERN-DAQ-EXPORT
        anaProdRemoval = self._createOperation("RemoveReplica", lfns, "CERN-ANAPROD")
        req.addOperation(anaProdRemoval)

        return req
