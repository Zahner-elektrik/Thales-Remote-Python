import sys
from thales_remote.connection import ThalesRemoteConnection
from thales_remote.script_wrapper import ThalesRemoteScriptWrapper

from zahner_analysis.file_import.iss_import import IssImport

import matplotlib.pyplot as plt
from matplotlib.ticker import EngFormatter

if __name__ == "__main__":
    zenniumConnection = ThalesRemoteConnection()
    zenniumConnection.connectToTerm("localhost", "ScriptRemote")

    zahnerZennium = ThalesRemoteScriptWrapper(zenniumConnection)
    zahnerZennium.forceThalesIntoRemoteScript()

    zahnerZennium.setIEOutputPath(r"C:\THALES\temp\ie")

    zahnerZennium.setIENaming("individual")

    zahnerZennium.calibrateOffsets()

    zahnerZennium.setIEFirstEdgePotential(0)
    zahnerZennium.setIEFirstEdgePotentialRelation("absolute")
    zahnerZennium.setIESecondEdgePotential(0.4)
    zahnerZennium.setIESecondEdgePotentialRelation("absolute")
    zahnerZennium.setIEThirdEdgePotential(-0.4)
    zahnerZennium.setIEThirdEdgePotentialRelation("absolute")
    zahnerZennium.setIEFourthEdgePotential(0)
    zahnerZennium.setIEFourthEdgePotentialRelation("absolute")

    zahnerZennium.setIEPotentialResolution(0.005)
    zahnerZennium.setIEMinimumWaitingTime(0.1)
    zahnerZennium.setIEMaximumWaitingTime(3)
    zahnerZennium.setIERelativeTolerance(0.01)  # 1 %
    zahnerZennium.setIEAbsoluteTolerance(0.001)  # 1 mA
    zahnerZennium.setIEOhmicDrop(0)

    zahnerZennium.setIEScanRate(0.05)
    zahnerZennium.setIEMaximumCurrent(3)
    zahnerZennium.setIEMinimumCurrent(-3)

    zahnerZennium.setIESweepMode("steady state")
    zahnerZennium.setIEOutputFileName("ie_steady")

    zahnerZennium.checkIESetup()
    print(zahnerZennium.readIESetup())

    zahnerZennium.measureIE()

    zahnerZennium.setIESweepMode("dynamic scan")
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

    measurementData = IssImport(r"C:\THALES\temp\ie\ie_steady.iss")

    fig, (axis) = plt.subplots(1, 1)
    axis.semilogy(
        measurementData.getVoltageArray(),
        abs(measurementData.getCurrentArray()),
        color="red",
    )

    axis.grid(which="both")
    axis.xaxis.set_major_formatter(EngFormatter(unit="V"))
    axis.yaxis.set_major_formatter(EngFormatter(unit="A"))
    axis.set_xlabel(r"Voltage")
    axis.set_ylabel(r"Current")
    fig.set_size_inches(10, 10)
    plt.show()

    print("finish")
