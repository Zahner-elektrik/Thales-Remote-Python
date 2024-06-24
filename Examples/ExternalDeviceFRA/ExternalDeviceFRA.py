from thales_remote.connection import ThalesRemoteConnection
from thales_remote.script_wrapper import PotentiostatMode, ThalesRemoteScriptWrapper
import time

zenniumConnection = ThalesRemoteConnection()
zenniumConnection.connectToTerm("192.168.2.47", "ScriptRemote")

zahnerZennium = ThalesRemoteScriptWrapper(zenniumConnection)
zahnerZennium.forceThalesIntoRemoteScript()

zahnerZennium.enableFraMode()

zahnerZennium.setFraVoltageMinimum(0)
zahnerZennium.setFraVoltageMaximum(18)
zahnerZennium.setFraCurrentMinimum(0)
zahnerZennium.setFraCurrentMaximum(220)

zahnerZennium.setFraVoltageInputGain(5 * (4 / 5))  # gain * (4 / 5)
zahnerZennium.setFraVoltageInputOffset(-25e-3)

zahnerZennium.setFraVoltageOutputGain(18.0 / 5.0)
zahnerZennium.setFraVoltageOutputOffset(-0.3)

zahnerZennium.setFraCurrentInputGain(-242)
zahnerZennium.setFraCurrentInputOffset(-15.03)

zahnerZennium.setFraCurrentOutputGain(-220.0 / 5.0)
zahnerZennium.setFraCurrentOutputOffset(-3)

zahnerZennium.setFraPotentiostatMode(PotentiostatMode.POTMODE_GALVANOSTATIC)
zahnerZennium.setCurrent(0)

for i in range(10):
    zahnerZennium.setCurrent(i)
    time.sleep(0.5)
    print(f"Potential:\t{zahnerZennium.getPotential()}\tV")
    print(f"Current:\t{zahnerZennium.getCurrent()}\tA")

zahnerZennium.setEISOutputPath(r"C:\THALES\temp\test1")
zahnerZennium.setEISNaming("counter")
zahnerZennium.setEISCounter(13)
zahnerZennium.setEISOutputFileName("spectra")

zahnerZennium.setCurrent(10)
zahnerZennium.setAmplitude(2)
zahnerZennium.setLowerFrequencyLimit(1)
zahnerZennium.setStartFrequency(1000)
zahnerZennium.setUpperFrequencyLimit(10e3)
zahnerZennium.setLowerNumberOfPeriods(3)
zahnerZennium.setLowerStepsPerDecade(2)
zahnerZennium.setUpperNumberOfPeriods(20)
zahnerZennium.setUpperStepsPerDecade(3)
zahnerZennium.setScanDirection("startToMax")
zahnerZennium.setScanStrategy("single")

zahnerZennium.measureEIS()

zenniumConnection.disconnectFromTerm()
print("finish")
