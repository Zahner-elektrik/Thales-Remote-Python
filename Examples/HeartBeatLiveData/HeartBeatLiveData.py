import sys
from thales_remote.connection import ThalesRemoteConnection
from thales_remote.script_wrapper import PotentiostatMode, ThalesRemoteScriptWrapper
import time
import threading

zenniumConnection = None
zahnerZennium = None
zenniumConnectionLiveData = None

keepThreadRunning = True


def watchThreadFunction():
    global keepThreadRunning
    global zenniumConnection
    global zahnerZennium

    print("watch thread started")
    while keepThreadRunning:
        time.sleep(1)
        try:
            beat = zahnerZennium.getWorkstationHeartBeat(2)
        except:
            print("term error watch thread")
            keepThreadRunning = False
        else:
            print("Heartbeat: " + str(beat) + " ms")

    print("watch thread left")
    return


def liveDataThreadFunction():
    global keepThreadRunning
    global zenniumConnectionLiveData

    print("live thread started")
    while keepThreadRunning:
        try:
            data = zenniumConnectionLiveData.waitForBinaryTelegram()
            packetId = data[0]
            data = data[1:]
            """
            Type:
            1 = Init measurement begin
            2 = Measurement end
            4 = Measurement data names
            5 = Measurement data units
            6 = ASCII data
            """
            if packetId in [1, 2, 4, 5, 6]:
                print(data.decode("ASCII"))
        except:
            """
            The connection to the term has an error or the socket has been closed.
            """
            print("term error live thread")
            keepThreadRunning = False

    print("live thread left")
    return


if __name__ == "__main__":
    zenniumConnectionLiveData = ThalesRemoteConnection()
    zenniumConnectionLiveData.connectToTerm("localhost", "Logging")

    liveThread = threading.Thread(target=liveDataThreadFunction)
    liveThread.start()

    zenniumConnection = ThalesRemoteConnection()
    zenniumConnection.connectToTerm("localhost", "ScriptRemote")

    zahnerZennium = ThalesRemoteScriptWrapper(zenniumConnection)
    zahnerZennium.forceThalesIntoRemoteScript()

    zahnerZennium.calibrateOffsets()

    watchThread = threading.Thread(target=watchThreadFunction)
    watchThread.start()

    zahnerZennium.setPotentiostatMode(PotentiostatMode.POTMODE_POTENTIOSTATIC)
    zahnerZennium.setAmplitude(10e-3)
    zahnerZennium.setPotential(0)
    zahnerZennium.setLowerFrequencyLimit(750)
    zahnerZennium.setStartFrequency(1000)
    zahnerZennium.setUpperFrequencyLimit(1500)
    zahnerZennium.setLowerNumberOfPeriods(2)
    zahnerZennium.setLowerStepsPerDecade(2)
    zahnerZennium.setUpperNumberOfPeriods(2)
    zahnerZennium.setUpperStepsPerDecade(20)
    zahnerZennium.setScanDirection("startToMax")
    zahnerZennium.setScanStrategy("single")

    zahnerZennium.enablePotentiostat()

    zahnerZennium.setFrequency(1)
    zahnerZennium.setAmplitude(10e-3)
    zahnerZennium.setNumberOfPeriods(3)

    print("measurement start")

    zahnerZennium.measureEIS()
    for i in range(20):
        zahnerZennium.getPotential()
        zahnerZennium.setPotential(0)

    print("measurement end")

    zahnerZennium.disablePotentiostat()

    print("set thread kill flag")
    keepThreadRunning = False

    print("disconnect connections")
    zenniumConnection.disconnectFromTerm()
    zenniumConnectionLiveData.disconnectFromTerm()

    print("join the threads")
    liveThread.join()
    watchThread.join()

    print("finish")
