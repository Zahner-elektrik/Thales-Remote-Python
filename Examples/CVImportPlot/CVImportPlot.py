import sys
from thales_remote.connection import ThalesRemoteConnection
from thales_remote.script_wrapper import ThalesRemoteScriptWrapper
from thales_remote.file_interface import ThalesFileInterface

from zahner_analysis.file_import.isc_import import IscImport

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import EngFormatter


if __name__ == "__main__":
    zenniumConnection = ThalesRemoteConnection()
    zenniumConnection.connectToTerm("localhost", "ScriptRemote")

    zahnerZennium = ThalesRemoteScriptWrapper(zenniumConnection)
    zahnerZennium.forceThalesIntoRemoteScript()

    zahnerZennium.calibrateOffsets()

    fileInterface = ThalesFileInterface("localhost")
    fileInterface.disableSaveReceivedFilesToDisk()
    fileInterface.enableKeepReceivedFilesInObject()
    fileInterface.enableAutomaticFileExchange(fileExtensions="*.isc")

    zahnerZennium.setCVStartPotential(0)
    zahnerZennium.setCVUpperReversingPotential(0.2)
    zahnerZennium.setCVLowerReversingPotential(-0.2)
    zahnerZennium.setCVEndPotential(0)

    zahnerZennium.setCVStartHoldTime(2)
    zahnerZennium.setCVEndHoldTime(2)

    zahnerZennium.setCVCycles(1.5)
    zahnerZennium.setCVSamplesPerCycle(400)

    zahnerZennium.setCVMaximumCurrent(0.0002)
    zahnerZennium.setCVMinimumCurrent(-0.0002)

    zahnerZennium.setCVOhmicDrop(0)

    zahnerZennium.disableCVAutoRestartAtCurrentOverflow()
    zahnerZennium.disableCVAutoRestartAtCurrentUnderflow()
    zahnerZennium.disableCVAnalogFunctionGenerator()

    zahnerZennium.setCVNaming("individual")
    zahnerZennium.setCVOutputPath(r"C:\THALES\temp\cv")

    scanRatesForMeasurement = [0.5, 1, 2]

    for scanRate in scanRatesForMeasurement:
        zahnerZennium.setCVOutputFileName("cv_{:d}mVs".format(int(scanRate * 1000)))
        zahnerZennium.setCVScanRate(scanRate)

        zahnerZennium.checkCVSetup()

        zahnerZennium.measureCV()

        """
        Determine the maximum current for the next measurement
        from the maximum current of the last CV measurement.
        """
        latestMeasurement = IscImport(fileInterface.getLatestReceivedFile().binaryData)
        maximumCurrent = max(abs(latestMeasurement.getCurrentArray()))

        zahnerZennium.setCVMaximumCurrent(maximumCurrent * 3)
        zahnerZennium.setCVMinimumCurrent(maximumCurrent * -3)

    zenniumConnection.disconnectFromTerm()
    fileInterface.close()

    iscFileFromDisc = IscImport(r"C:\THALES\temp\cv\cv_1000mVs.isc")

    iscFiles = [IscImport(file.binaryData) for file in fileInterface.getReceivedFiles()]

    for iscFile in iscFiles:
        print(
            f"{iscFile.getScanRate()} V/s\tmeasurement finished at {iscFile.getMeasurementEndDateTime()}"
        )

    figCV, (axis) = plt.subplots(1, 1)
    figCV.suptitle("Cyclic Voltammetry at different scan rates")

    for iscFile in iscFiles:
        axis.plot(
            iscFile.getVoltageArray(),
            iscFile.getCurrentArray(),
            label=f"{iscFile.getScanRate()} $\\frac{{V}}{{s}}$",
        )

    axis.grid(which="both")
    axis.xaxis.set_major_formatter(EngFormatter(unit="$V$"))
    axis.yaxis.set_major_formatter(EngFormatter(unit="$A$"))
    axis.set_xlabel(r"$Voltage$")
    axis.set_ylabel(r"$Current$")
    axis.legend()

    figCV.set_size_inches(18, 18)
    plt.show()
    figCV.savefig("CV.svg")
