import sys
from thales_remote.connection import ThalesRemoteConnection
from thales_remote.script_wrapper import PotentiostatMode, ThalesRemoteScriptWrapper
import time
import threading

zenniumConnection = None
zahnerZennium = None
keepThreadRunning = True


def watchThreadFunction():
    global zenniumConnection
    global zahnerZennium
    global keepThreadRunning

    while keepThreadRunning:
        time.sleep(1)
        active = zahnerZennium.getTermIsActive()
        print("active state: " + str(active))
        if active:
            print("beat count: " + str(zahnerZennium.getWorkstationHeartBeat()))


if __name__ == "__main__":
    zenniumConnection = ThalesRemoteConnection()
    zenniumConnection.connectToTerm("localhost", "ScriptRemote")

    zahnerZennium = ThalesRemoteScriptWrapper(zenniumConnection)
    zahnerZennium.forceThalesIntoRemoteScript()

    zahnerZennium.calibrateOffsets()

    testThread = threading.Thread(target=watchThreadFunction)
    testThread.start()
    print("heartbeat thread started")

    zahnerZennium.setPotentiostatMode(PotentiostatMode.POTMODE_POTENTIOSTATIC)
    zahnerZennium.setAmplitude(10e-3)
    zahnerZennium.setPotential(0)
    zahnerZennium.setLowerFrequencyLimit(500)
    zahnerZennium.setStartFrequency(1000)
    zahnerZennium.setUpperFrequencyLimit(10000)
    zahnerZennium.setLowerNumberOfPeriods(5)
    zahnerZennium.setLowerStepsPerDecade(2)
    zahnerZennium.setUpperNumberOfPeriods(20)
    zahnerZennium.setUpperStepsPerDecade(20)
    zahnerZennium.setScanDirection("startToMax")
    zahnerZennium.setScanStrategy("single")

    zahnerZennium.enablePotentiostat()

    zahnerZennium.setFrequency(1)
    zahnerZennium.setAmplitude(10e-3)
    zahnerZennium.setNumberOfPeriods(3)

    print("measurement start")
    zahnerZennium.measureEIS()
    print("measurement end")

    zahnerZennium.disablePotentiostat()

    print("thread kill")
    keepThreadRunning = False
    testThread.join()
    print("thread killed")

    zenniumConnection.disconnectFromTerm()
    print("finish")
