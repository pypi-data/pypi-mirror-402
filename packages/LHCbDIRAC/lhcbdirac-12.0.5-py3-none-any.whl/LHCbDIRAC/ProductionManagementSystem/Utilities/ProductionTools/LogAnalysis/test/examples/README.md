# Information for adding new log analysis tests

```fish
set jid 965859769; lb-dirac dirac-wms-job-parameters $jid | rg lhcb-dirac-logse | cut -d '"' -f 2 | cut -d '/' -f 4- | string trim -c / && xrdcp root://eoslhcb.cern.ch//eos/lhcb/grid/prod/lhcb/logSE/(lb-dirac dirac-wms-job-parameters $jid | rg lhcb-dirac-logse | cut -d '"' -f 2 | cut -d '/' -f 4- | string trim -c /).zip $jid.zip && mkdir -p src/LHCbDIRAC/ProductionManagementSystem/Utilities/ProductionTools/LogAnalysis/test/examples/logs/$jid-raw/ && unzip $jid.zip -d src/LHCbDIRAC/ProductionManagementSystem/Utilities/ProductionTools/LogAnalysis/test/examples/logs/$jid-raw/ && mv src/LHCbDIRAC/ProductionManagementSystem/Utilities/ProductionTools/LogAnalysis/test/examples/logs/$jid{-raw/*,} && rm -rf $jid.zip src/LHCbDIRAC/ProductionManagementSystem/Utilities/ProductionTools/LogAnalysis/test/examples/logs/$jid-raw
```

```
python src/LHCbDIRAC/ProductionManagementSystem/Utilities/ProductionTools/LogAnalysis/test/Test_log_analysis.py
```

```
set tid 249324; rm -rf /scratching/.cache/$tid.json /home/cburr/Development/DIRAC-dev/LHCbDIRAC/src/LHCbDIRAC/ProductionManagementSystem/Utilities/ProductionTools/LogAnalysis/test/examples/prods/$tid; DIRACSYSCONFIG=/cvmfs/lhcb.cern.ch/lhcbdirac/etc/dirac.cfg python src/LHCbDIRAC/ProductionManagementSystem/Utilities/ProductionTools/LogAnalysis/test/Test_prod_analysis.py $tid /lhcb/MC/2012/ALLSTREAMS.DST/00149387/0000/00149387_00000091_5.AllStreams.dst /lhcb/MC/2012/ALLSTREAMS.DST/00149387/0000/00149387_00000099_5.AllStreams.dst /lhcb/MC/2012/ALLSTREAMS.DST/00149387/0000/00149387_00000103_5.AllStreams.dst /lhcb/MC/2012/ALLSTREAMS.DST/00149387/0000/00149387_00000105_5.AllStreams.dst /lhcb/MC/2012/ALLSTREAMS.DST/00149387/0000/00149387_00000108_5.AllStreams.dst /lhcb/MC/2012/ALLSTREAMS.DST/00149387/0000/00149387_00000116_5.AllStreams.dst /lhcb/MC/2012/ALLSTREAMS.DST/00149387/0000/00149387_00000122_5.AllStreams.dst /lhcb/MC/2012/ALLSTREAMS.DST/00149387/0000/00149387_00000126_5.AllStreams.dst
```

