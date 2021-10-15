import sys
from thales_remote.connection import ThalesRemoteConnection
from thales_remote.script_wrapper import ThalesRemoteScriptWrapper

from jupyter_utils import executionInNotebook, notebookCodeToPython

if __name__ == "__main__":
    zenniumConnection = ThalesRemoteConnection()
    connectionSuccessful = zenniumConnection.connectToTerm("localhost", "ScriptRemote")
    if connectionSuccessful:
        print("connection successfull")
    else:
        print("connection not possible")
        sys.exit()
        
    zahnerZennium = ThalesRemoteScriptWrapper(zenniumConnection)
    zahnerZennium.forceThalesIntoRemoteScript()

    zahnerZennium.setIEOutputPath(r"C:\THALES\temp\ie")

    zahnerZennium.setIENaming("counter")
    zahnerZennium.setIECounter(1)

    zahnerZennium.setIEFirstEdgePotential(1)
    zahnerZennium.setIEFirstEdgePotentialRelation("absolute")
    zahnerZennium.setIESecondEdgePotential(1.1)
    zahnerZennium.setIESecondEdgePotentialRelation("absolute")
    zahnerZennium.setIEThirdEdgePotential(0.9)
    zahnerZennium.setIEThirdEdgePotentialRelation("absolute")
    zahnerZennium.setIEFourthEdgePotential(1)
    zahnerZennium.setIEFourthEdgePotentialRelation("absolute")
    
    zahnerZennium.setIEPotentialResolution(0.02)
    zahnerZennium.setIEMinimumWaitingTime(1)
    zahnerZennium.setIEMaximumWaitingTime(15)
    zahnerZennium.setIERelativeTolerance(0.01)  #1 %
    zahnerZennium.setIEAbsoluteTolerance(0.001) #1 mA
    zahnerZennium.setIEOhmicDrop(0)
    
    zahnerZennium.setIEScanRate(0.05)
    zahnerZennium.setIEMaximumCurrent(0.01)
    zahnerZennium.setIEMinimumCurrent(-0.01)

    zahnerZennium.setIESweepMode("steady state")
    zahnerZennium.setIEOutputFileName("ie_steady")

    zahnerZennium.checkIESetup()
    print(zahnerZennium.readIESetup())
    
    zahnerZennium.measureIE()

    zahnerZennium.setIESweepMode("dynamic scan")
    zahnerZennium.setIENaming("dateTime")
    zahnerZennium.setIEOutputFileName("ie_dynamic")
    
    zahnerZennium.checkIESetup()
    print(zahnerZennium.readIESetup())
    
    zahnerZennium.measureIE()

    zahnerZennium.setIESweepMode("fixed sampling")
    zahnerZennium.setIEOutputFileName("ie_fixed")
    
    zahnerZennium.checkIESetup()
    print(zahnerZennium.readIESetup())
    
    zahnerZennium.measureIE()

    zenniumConnection.disconnectFromTerm()
    print("finish")

    if executionInNotebook() == True:
        notebookCodeToPython("CurrentVoltageCurve.ipynb")

