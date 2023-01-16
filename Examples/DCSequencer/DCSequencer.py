import sys
from thales_remote.connection import ThalesRemoteConnection
from thales_remote.script_wrapper import ThalesRemoteScriptWrapper

if __name__ == "__main__":
    zenniumConnection = ThalesRemoteConnection()
    zenniumConnection.connectToTerm("localhost", "ScriptRemote")

    zahnerZennium = ThalesRemoteScriptWrapper(zenniumConnection)
    zahnerZennium.forceThalesIntoRemoteScript()

    zahnerZennium.calibrateOffsets()
    zahnerZennium.setSequenceNaming("dateTime")
    zahnerZennium.setSequenceOutputPath(r"C:\THALES\temp\test1")
    zahnerZennium.setSequenceOutputFileName("batterysequence")

    zahnerZennium.selectSequence(0)

    zahnerZennium.runSequence()

    zahnerZennium.selectPotentiostat(1)

    zahnerZennium.setSequenceNaming("counter")
    zahnerZennium.setSequenceCounter(13)
    zahnerZennium.setSequenceOutputPath(r"C:\THALES\temp\test1")
    zahnerZennium.setSequenceOutputFileName("batterysequence")

    zahnerZennium.runSequenceFile(r"C:\Users\XXX\Desktop\myZahnerSequence.seq")

    zahnerZennium.selectPotentiostat(0)

    zenniumConnection.disconnectFromTerm()
    print("finish")
