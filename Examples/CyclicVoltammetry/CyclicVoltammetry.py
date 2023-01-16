import sys
from thales_remote.connection import ThalesRemoteConnection
from thales_remote.script_wrapper import ThalesRemoteScriptWrapper

if __name__ == "__main__":
    zenniumConnection = ThalesRemoteConnection()
    zenniumConnection.connectToTerm("localhost", "ScriptRemote")

    zahnerZennium = ThalesRemoteScriptWrapper(zenniumConnection)
    zahnerZennium.forceThalesIntoRemoteScript()
    zahnerZennium.calibrateOffsets()

    zahnerZennium.setCVOutputPath(r"C:\THALES\temp\cv")

    zahnerZennium.setCVOutputFileName("cv_series")
    zahnerZennium.setCVNaming("counter")
    zahnerZennium.setCVCounter(1)

    zahnerZennium.setCVStartPotential(1)
    zahnerZennium.setCVUpperReversingPotential(2)
    zahnerZennium.setCVLowerReversingPotential(0)
    zahnerZennium.setCVEndPotential(1)

    zahnerZennium.setCVStartHoldTime(2)
    zahnerZennium.setCVEndHoldTime(2)

    zahnerZennium.setCVCycles(1.5)
    zahnerZennium.setCVSamplesPerCycle(400)
    zahnerZennium.setCVScanRate(0.5)

    zahnerZennium.setCVMaximumCurrent(0.03)
    zahnerZennium.setCVMinimumCurrent(-0.03)

    zahnerZennium.setCVOhmicDrop(0)

    zahnerZennium.disableCVAutoRestartAtCurrentOverflow()
    zahnerZennium.disableCVAutoRestartAtCurrentUnderflow()
    zahnerZennium.disableCVAnalogFunctionGenerator()

    zahnerZennium.checkCVSetup()
    print(zahnerZennium.readCVSetup())

    zahnerZennium.measureCV()

    zahnerZennium.selectPotentiostat(1)

    zahnerZennium.setCVNaming("individual")
    zahnerZennium.setCVOutputPath(r"C:\THALES\temp\cv")

    ScanRatesForMeasurement = [0.1, 0.2, 0.5, 1.0]

    for scanRate in ScanRatesForMeasurement:
        zahnerZennium.setCVOutputFileName(
            "cv_scanrate_{:d}mVs".format(int(scanRate * 1000))
        )
        zahnerZennium.setCVScanRate(scanRate)

        zahnerZennium.checkCVSetup()
        print(zahnerZennium.readCVSetup())

        zahnerZennium.measureCV()

    zahnerZennium.selectPotentiostat(0)

    zenniumConnection.disconnectFromTerm()
    print("finish")
