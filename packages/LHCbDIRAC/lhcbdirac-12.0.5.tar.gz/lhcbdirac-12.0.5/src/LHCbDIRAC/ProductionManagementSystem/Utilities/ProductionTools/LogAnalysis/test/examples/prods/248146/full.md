# Summary of 1 files

## UnknownSegmentationFaultWithTraceback

```
#7  0xXXXXXXXXXXXXXXXXXX in GaudiCommon<Algorithm>::releaseTool(IAlgTool const*) const () from /cvmfs/lhcb.cern.ch/lib/lhcb/GAUDI/GAUDI_v36r2/InstallArea/x86_64_v2-centos7-gcc11-opt/lib/libGaudiAlgLib.so
#8  0xXXXXXXXXXXXXXXXXXX in GaudiCommon<Algorithm>::finalize() () from /cvmfs/lhcb.cern.ch/lib/lhcb/GAUDI/GAUDI_v36r2/InstallArea/x86_64_v2-centos7-gcc11-opt/lib/libGaudiAlgLib.so
#9  0xXXXXXXXXXXXXXXXXXX in Gaudi::Algorithm::sysFinalize() () from /cvmfs/lhcb.cern.ch/lib/lhcb/GAUDI/GAUDI_v36r2/InstallArea/x86_64_v2-centos7-gcc11-opt/lib/libGaudiKernel.so
#10 0xXXXXXXXXXXXXXXXXXX in AlgorithmManager::finalize() () from /cvmfs/lhcb.cern.ch/lib/lhcb/GAUDI/GAUDI_v36r2/InstallArea/x86_64_v2-centos7-gcc11-opt/lib/libGaudiCoreSvc.so
#11 0xXXXXXXXXXXXXXXXXXX in ApplicationMgr::finalize() () from /cvmfs/lhcb.cern.ch/lib/lhcb/GAUDI/GAUDI_v36r2/InstallArea/x86_64_v2-centos7-gcc11-opt/lib/libGaudiCoreSvc.so
#12 0xXXXXXXXXXXXXXXXXXX in Gaudi::Application::run() () from /cvmfs/lhcb.cern.ch/lib/lhcb/GAUDI/GAUDI_v36r2/InstallArea/x86_64_v2-centos7-gcc11-opt/lib/libGaudiKernel.so
#13 0xXXXXXXXXXXXXXXXXXX in ffi_call_unix64 () from /cvmfs/lhcb.cern.ch/lib/lcg/releases/libffi/3.2.1-26487/x86_64-centos7-gcc11-opt/lib64/libffi.so.6
#14 0xXXXXXXXXXXXXXXXXXX in ffi_call () from /cvmfs/lhcb.cern.ch/lib/lcg/releases/libffi/3.2.1-26487/x86_64-centos7-gcc11-opt/lib64/libffi.so.6
#15 0xXXXXXXXXXXXXXXXXXX in _call_function_pointer (argtypecount=<optimized out>, argcount=1, resmem=0xXXXXXXXXXXXXXX, restype=<optimized out>, atypes=<optimized out>, avalues=0xXXXXXXXXXXXXXX, pProc=0xXXXXXXXXXXXXXX <_py_Gaudi__Application__run>, flags=4357) at /build/jenkins/workspace/lcg_release_pipeline/build/externals/Python-3.9.6/src/Python/3.9.6/Modules/_ctypes/callproc.c:920
#16 _ctypes_callproc (pProc=pProc
entry=0xXXXXXXXXXXXXXX <_py_Gaudi__Application__run>, argtuple=argtuple
entry=0xXXXXXXXXXXXXXX, flags=4357, argtypes=argtypes
entry=0xXXXXXXXXXXXXXX, restype=restype
entry=0xXXXXXXXXX, checker=checker
entry=0x0) at /build/jenkins/workspace/lcg_release_pipeline/build/externals/Python-3.9.6/src/Python/3.9.6/Modules/_ctypes/callproc.c:1263

```

A segmentation fault occurred

| Transform | LFN | Job ID | Site | Peak Mem | Log URL(s) |
| --------- | --- | ------ | ---- | -------- | ---------- |
| `248146` | `LFN:/lhcb/MC/2017/ALLRADIATIVE.STRIP.DST/00154513/0000/00154513_00000008_1.allradiative.strip.dst` | 980553429 | LCG.CERN.cern | 2.7 GiB | [here](https://lhcb-productions.web.cern.ch/logs/?lfn=%2Flhcb%2FMC%2F2017%2FLOG%2F00248146%2F0000&task_name=00000010) |
