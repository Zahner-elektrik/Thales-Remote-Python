import sys
from thales_remote.connection import ThalesRemoteConnection
from thales_remote.script_wrapper import (
    PotentiostatMode,
    ThalesRemoteScriptWrapper,
    ScanStrategy,
    ScanDirection,
)

if __name__ == "__main__":
    zenniumConnection = ThalesRemoteConnection()
    zenniumConnection.connectToTerm("localhost", "ScriptRemote")

    zahnerZennium = ThalesRemoteScriptWrapper(zenniumConnection)
    zahnerZennium.forceThalesIntoRemoteScript()

    zahnerZennium.calibrateOffsets()

    zahnerZennium.setEISOutputPath(r"C:\THALES\temp\test1")
    zahnerZennium.setEISNaming("counter")
    zahnerZennium.setEISCounter(13)
    zahnerZennium.setEISOutputFileName("spectra")

    zahnerZennium.setPotentiostatMode(PotentiostatMode.POTMODE_POTENTIOSTATIC)
    zahnerZennium.setAmplitude(10e-3)
    zahnerZennium.setPotential(1)
    zahnerZennium.setLowerFrequencyLimit(10)
    zahnerZennium.setStartFrequency(1000)
    zahnerZennium.setUpperFrequencyLimit(10000)
    zahnerZennium.setLowerNumberOfPeriods(5)
    zahnerZennium.setLowerStepsPerDecade(2)
    zahnerZennium.setUpperNumberOfPeriods(20)
    zahnerZennium.setUpperStepsPerDecade(5)
    zahnerZennium.setScanDirection(ScanDirection.START_TO_MAX)
    zahnerZennium.setScanStrategy(ScanStrategy.SINGLE_SINE)

    zahnerZennium.enablePotentiostat()

    zahnerZennium.measureEIS()

    zahnerZennium.disablePotentiostat()

    zahnerZennium.selectPotentiostat(1)

    zahnerZennium.setEISNaming("dateTime")
    zahnerZennium.setEISOutputPath(r"C:\THALES\temp\test2")
    zahnerZennium.setEISOutputFileName("spectra")

    zahnerZennium.setAmplitude(50e-3)
    zahnerZennium.setScanDirection("startToMin")

    zahnerZennium.measureEIS()

    zahnerZennium.setEISNaming("individual")
    zahnerZennium.setEISOutputPath(r"C:\THALES\temp\test3")

    AmplitudesIn_mV_forMeasurement = [5, 10, 20, 50]

    for amplitude in AmplitudesIn_mV_forMeasurement:
        zahnerZennium.setEISOutputFileName("spectraAmplitude{}mV".format(amplitude))
        zahnerZennium.setAmplitude(amplitude / 1000)
        zahnerZennium.measureEIS()

    zahnerZennium.setAmplitude(0)

    zahnerZennium.selectPotentiostat(0)

    zenniumConnection.disconnectFromTerm()
    print("finish")
