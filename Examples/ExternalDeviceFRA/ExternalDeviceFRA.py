import sys
from thales_remote.connection import ThalesRemoteConnection
from thales_remote.script_wrapper import PotentiostatMode, ThalesRemoteScriptWrapper
import time


if __name__ == "__main__":
    zenniumConnection = ThalesRemoteConnection()
    zenniumConnection.connectToTerm("localhost", "ScriptRemote")

    zahnerZennium = ThalesRemoteScriptWrapper(zenniumConnection)
    zahnerZennium.forceThalesIntoRemoteScript()

    zahnerZennium.disableFraMode()

    zahnerZennium.setFraVoltageMinimum(0)
    zahnerZennium.setFraVoltageMaximum(18)
    zahnerZennium.setFraCurrentMinimum(0)
    zahnerZennium.setFraCurrentMaximum(220)

    zahnerZennium.setFraVoltageInputGain(18.0 / 5.0)
    zahnerZennium.setFraVoltageOutputGain(18.0 / 5.0)
    zahnerZennium.setFraCurrentInputGain(-220.0 / 5.0)
    zahnerZennium.setFraCurrentOutputGain(-220.0 / 5.0)

    zahnerZennium.setFraPotentiostatMode(PotentiostatMode.POTMODE_GALVANOSTATIC)

    zahnerZennium.enableFraMode()
    zahnerZennium.setCurrent(0)

    for i in range(5):
        zahnerZennium.setCurrent(i)
        time.sleep(1)
        print(f"Potential:\t{zahnerZennium.getPotential()}\tV")

    zahnerZennium.setEISOutputPath(r"C:\THALES\temp\test1")
    zahnerZennium.setEISNaming("counter")
    zahnerZennium.setEISCounter(13)
    zahnerZennium.setEISOutputFileName("spectra")

    zahnerZennium.setAmplitude(0.5)
    zahnerZennium.setCurrent(5)
    zahnerZennium.setLowerFrequencyLimit(0.1)
    zahnerZennium.setStartFrequency(10)
    zahnerZennium.setUpperFrequencyLimit(100)
    zahnerZennium.setLowerNumberOfPeriods(3)
    zahnerZennium.setLowerStepsPerDecade(2)
    zahnerZennium.setUpperNumberOfPeriods(20)
    zahnerZennium.setUpperStepsPerDecade(3)
    zahnerZennium.setScanDirection("startToMax")
    zahnerZennium.setScanStrategy("single")

    zahnerZennium.measureEIS()

    zahnerZennium.disableFraMode()

    zenniumConnection.disconnectFromTerm()
    print("finish")
