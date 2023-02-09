import sys
from thales_remote.connection import ThalesRemoteConnection
from thales_remote.script_wrapper import (
    PotentiostatMode,
    ScanStrategy,
    ScanDirection,
    FileNaming,
    Pad4Mode,
    ThalesRemoteScriptWrapper,
)
from thales_remote.file_interface import ThalesFileInterface
from zahner_analysis.file_import.ism_import import IsmImport

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import EngFormatter
import os
import shutil

if __name__ == "__main__":
    remoteIP = "192.168.2.66"

    zenniumConnection = ThalesRemoteConnection()
    zenniumConnection.connectToTerm(remoteIP, "ScriptRemote")

    zahnerZennium = ThalesRemoteScriptWrapper(zenniumConnection)
    zahnerZennium.forceThalesIntoRemoteScript()

    zahnerZennium.calibrateOffsets()

    fileInterface = ThalesFileInterface(remoteIP)

    zahnerZennium.setEISOutputPath(r"C:\THALES\temp")
    zahnerZennium.setEISNaming(FileNaming.INDIVIDUAL)
    zahnerZennium.setEISOutputFileName("myeis")

    zahnerZennium.setPotentiostatMode(PotentiostatMode.POTMODE_POTENTIOSTATIC)
    zahnerZennium.setAmplitude(100e-3)
    zahnerZennium.setPotential(0)
    zahnerZennium.setLowerFrequencyLimit(10)
    zahnerZennium.setStartFrequency(1000)
    zahnerZennium.setUpperFrequencyLimit(10000)
    zahnerZennium.setLowerNumberOfPeriods(5)
    zahnerZennium.setLowerStepsPerDecade(5)
    zahnerZennium.setUpperNumberOfPeriods(20)
    zahnerZennium.setUpperStepsPerDecade(5)
    zahnerZennium.setScanDirection(ScanDirection.START_TO_MAX)
    zahnerZennium.setScanStrategy(ScanStrategy.SINGLE_SINE)

    zahnerZennium.enablePotentiostat()

    zahnerZennium.measureEIS()

    zahnerZennium.disablePotentiostat()
    zahnerZennium.setAmplitude(0)

    file = fileInterface.acquireFile(r"C:\THALES\temp\myeis.ism")

    fileHandle = open(r"D:\myLocalDirectory\asdf.ism", "wb")
    fileHandle.write(file.binaryData)
    fileHandle.close()

    ismFile = IsmImport(file.binaryData)

    impedanceFrequencies = ismFile.getFrequencyArray()

    impedanceAbsolute = ismFile.getImpedanceArray()
    impedancePhase = ismFile.getPhaseArray()

    figBode, (impedanceAxis, phaseAxis) = plt.subplots(2, 1, sharex=True)
    figBode.suptitle("Bode")

    impedanceAxis.loglog(
        impedanceFrequencies, impedanceAbsolute, marker="+", markersize=5
    )
    impedanceAxis.xaxis.set_major_formatter(EngFormatter(unit="Hz"))
    impedanceAxis.yaxis.set_major_formatter(EngFormatter(unit="$\Omega$"))
    impedanceAxis.set_xlabel(r"$f$")
    impedanceAxis.set_ylabel(r"$|Z|$")
    impedanceAxis.grid(which="both")

    phaseAxis.semilogx(
        impedanceFrequencies,
        np.abs(impedancePhase * (360 / (2 * np.pi))),
        marker="+",
        markersize=5,
    )
    phaseAxis.xaxis.set_major_formatter(EngFormatter(unit="Hz"))
    phaseAxis.yaxis.set_major_formatter(EngFormatter(unit="$°$", sep=""))
    phaseAxis.set_xlabel(r"$f$")
    phaseAxis.set_ylabel(r"$|Phase|$")
    phaseAxis.grid(which="both")
    phaseAxis.set_ylim([0, 90])
    figBode.set_size_inches(18, 12)
    plt.show()

    localDirectory = r"D:\myLocalDirectory"

    # Delete the entire contents of the directory.
    for file in os.listdir(localDirectory):
        fileWithPath = os.path.join(localDirectory, file)
        try:
            if os.path.isfile(fileWithPath) or os.path.islink(fileWithPath):
                os.unlink(fileWithPath)
            elif os.path.isdir(fileWithPath):
                shutil.rmtree(fileWithPath)
        except:
            pass

    fileInterface.enableSaveReceivedFilesToDisk(path=localDirectory)
    fileInterface.enableKeepReceivedFilesInObject()
    fileInterface.enableAutomaticFileExchange()

    zahnerZennium.setEISNaming("counter")
    zahnerZennium.setEISCounter(13)
    zahnerZennium.setEISOutputFileName("spectra")

    zahnerZennium.setupPad4Channel(1, 1, 1, voltageRange=4.0, shuntResistor=10e-3)
    zahnerZennium.setupPad4Channel(1, 2, 1, voltageRange=4.0, shuntResistor=10e-3)
    zahnerZennium.setupPad4ModeGlobal(Pad4Mode.VOLTAGE)  # or Pad4Mode.CURRENT
    zahnerZennium.enablePad4Global()

    zahnerZennium.measureEIS()
    fileInterface.disableAutomaticFileExchange()

    zahnerZennium.measureEIS()

    fileInterface.enableAutomaticFileExchange()
    zahnerZennium.measureEIS()
    zahnerZennium.setAmplitude(0)

    for file in fileInterface.getReceivedFiles():
        ismFile = IsmImport(file.binaryData)
        print(
            f"{file.name} measurement finished at {ismFile.getMeasurementEndDateTime()}"
        )

    for file in os.listdir(localDirectory):
        print(file)

    zenniumConnection.disconnectFromTerm()
    fileInterface.close()
