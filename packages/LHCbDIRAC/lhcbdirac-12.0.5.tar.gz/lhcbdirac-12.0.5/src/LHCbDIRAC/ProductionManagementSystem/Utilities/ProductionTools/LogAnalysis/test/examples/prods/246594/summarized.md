# Summary of 5 files

### needs_download_input_data in 2 LFNs

| Transform | LFN | Job ID | Site | Peak Mem | Log URL(s) | Occurrences |
| --------- | --- | ------ | ---- | -------- | ---------- | ----------- |
| `246594` | `LFN:/lhcb/LHCb/Collision17/BHADRONCOMPLETEEVENT.DST/00071499/0001/00071499_00012339_1.bhadroncompleteevent.dst` | 962292618 | **LCG.Glasgow.uk** (5) |  | [here](https://lhcb-productions.web.cern.ch/logs/?lfn=%2Flhcb%2FLHCb%2FCollision17%2FLOG%2F00246594%2F0000&task_name=00003594) [here](https://lhcb-productions.web.cern.ch/logs/?lfn=%2Flhcb%2FLHCb%2FCollision17%2FLOG%2F00246594%2F0000&task_name=00003446) [here](https://lhcb-productions.web.cern.ch/logs/?lfn=%2Flhcb%2FLHCb%2FCollision17%2FLOG%2F00246594%2F0000&task_name=00002641) | 5 / 13 |
|  | `LFN:/lhcb/LHCb/Collision17/BHADRONCOMPLETEEVENT.DST/00071957/0002/00071957_00020949_1.bhadroncompleteevent.dst` | 962293815 | **LCG.Glasgow.uk** (7) |  | [here](https://lhcb-productions.web.cern.ch/logs/?lfn=%2Flhcb%2FLHCb%2FCollision17%2FLOG%2F00246594%2F0000&task_name=00003675) [here](https://lhcb-productions.web.cern.ch/logs/?lfn=%2Flhcb%2FLHCb%2FCollision17%2FLOG%2F00246594%2F0000&task_name=00003584) [here](https://lhcb-productions.web.cern.ch/logs/?lfn=%2Flhcb%2FLHCb%2FCollision17%2FLOG%2F00246594%2F0000&task_name=00003371) | 7 / 12 |

### stalled in 2 LFNs

| Transform | LFN | Job ID | Site | Peak Mem | Log URL(s) | Occurrences |
| --------- | --- | ------ | ---- | -------- | ---------- | ----------- |
| `246594` | `LFN:/lhcb/LHCb/Collision17/BHADRONCOMPLETEEVENT.DST/00071499/0001/00071499_00012654_1.bhadroncompleteevent.dst` | 962294828 | **LCG.Glasgow.uk** (13) |  |  | 13 / 13 |
|  | `LFN:/lhcb/LHCb/Collision17/BHADRONCOMPLETEEVENT.DST/00071957/0002/00071957_00022211_1.bhadroncompleteevent.dst` | 962295626 | **LCG.Glasgow.uk** (12) |  |  | 12 / 12 |

## KnownCorruptedFile

```
Error in <TBranchElement::GetBasket>: File: root://proxy@xrootd.grid.surfsara.nl//pnfs/grid.sara.nl/data/lhcb/LHCb-Disk/lhcb/LHCb/Collision17/BHADRONCOMPLETEEVENT.DST/00071499/0001/00071499_00015440_1.bhadroncompleteevent.dst at byte:1248758341, branch:_Event_pRec_Track_Best., entry:14147, badread=1, nerrors=1, basketnumber=3960

```

This file is known to contain some corrupt events. It likely cannot be recovered for this production however we typically don't delete these files as other analyses might not depend on the bad branches.

| Transform | LFN | Job ID | Site | Peak Mem | Log URL(s) | Occurrences |
| --------- | --- | ------ | ---- | -------- | ---------- | ----------- |
| `246594` | `LFN:/lhcb/LHCb/Collision17/BHADRONCOMPLETEEVENT.DST/00071499/0001/00071499_00015440_1.bhadroncompleteevent.dst` | 958395203 | **LCG.NIKHEF.nl;LCG.SARA.nl** (1) |  | [here](https://lhcb-productions.web.cern.ch/logs/?lfn=%2Flhcb%2FLHCb%2FCollision17%2FLOG%2F00246594%2F0000&task_name=00001695) | 1 / 5 |
