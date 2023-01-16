import sys
import time

from delta_remote.connection import DeltaConnection
from delta_remote.script_wrapper import DeltaSCPIWrapper, DeltaSources

from thales_remote.connection import ThalesRemoteConnection
from thales_remote.script_wrapper import PotentiostatMode, ThalesRemoteScriptWrapper
from thales_remote.file_interface import ThalesFileInterface
from zahner_analysis.file_import.ism_import import IsmImport

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import EngFormatter

if __name__ == "__main__":
    zenniumConnection = ThalesRemoteConnection()
    zenniumConnection.connectToTerm("localhost")

    zahnerZennium = ThalesRemoteScriptWrapper(zenniumConnection)
    zahnerZennium.forceThalesIntoRemoteScript()
    zahnerZennium.calibrateOffsets()

    fileInterface = ThalesFileInterface("localhost")
    fileInterface.enableKeepReceivedFilesInObject()
    fileInterface.enableAutomaticFileExchange()

    deltaConnection = DeltaConnection()
    deltaConnection.connect(ip="192.168.2.73", port=8462)

    deltaSM18_220 = DeltaSCPIWrapper(deltaConnection)

    print(f"IDN:\t{deltaSM18_220.IDN()}")

    deltaSM18_220.setProgSourceVoltage(DeltaSources.eth)
    deltaSM18_220.setProgSourceCurrent(DeltaSources.eth)

    zahnerZennium.setEISOutputPath(r"C:\THALES\temp")
    zahnerZennium.setEISNaming("individual")
    zahnerZennium.setEISOutputFileName("spectra_5aac")

    zahnerZennium.selectPotentiostat(1)
    zahnerZennium.setPotentiostatMode(PotentiostatMode.POTMODE_GALVANOSTATIC)
    zahnerZennium.setAmplitude(0)
    zahnerZennium.setLowerFrequencyLimit(0.01)
    zahnerZennium.setStartFrequency(1000)
    zahnerZennium.setUpperFrequencyLimit(100000)
    zahnerZennium.setLowerNumberOfPeriods(5)
    zahnerZennium.setLowerStepsPerDecade(5)
    zahnerZennium.setUpperNumberOfPeriods(10)
    zahnerZennium.setUpperStepsPerDecade(10)
    zahnerZennium.setScanDirection("startToMax")
    zahnerZennium.setScanStrategy("single")

    zahnerZennium.setCurrent(0)
    zahnerZennium.enablePotentiostat()

    time.sleep(1.0)

    deltaSM18_220.setTargetVoltage(6)
    deltaSM18_220.setTargetCurrent(20)
    deltaSM18_220.enableOutput()

    time.sleep(1)

    print(f"Measured current\tEL1002:\t\t{zahnerZennium.getCurrent():>10.3f} A")

    print(
        f"Measured current\tDelta SM18-220:\t{deltaSM18_220.getMeasuredCurrent():>10.3f} A"
    )
    print(
        f"Measured voltage\tDelta SM18-220:\t{deltaSM18_220.getMeasuredVoltage():>10.3f} V"
    )
    print(
        f"Measured power\t\tDelta SM18-220:\t{deltaSM18_220.getMeasuredPower():>10.3f} W"
    )

    zahnerZennium.setAmplitude(5)
    zahnerZennium.measureEIS()
    zahnerZennium.setAmplitude(0)

    deltaSM18_220.disableOutput()

    time.sleep(1)

    zahnerZennium.disablePotentiostat()

    ismFile = IsmImport(fileInterface.getLatestReceivedFile().binaryData)

    impedanceFrequencies = ismFile.getFrequencyArray()
    impedanceAbsolute = ismFile.getImpedanceArray()
    impedancePhase = ismFile.getPhaseArray()
    impedanceComplex = ismFile.getComplexImpedanceArray()

    figBode, (impedanceAxis) = plt.subplots(1, 1)

    phaseAxis = impedanceAxis.twinx()

    impedanceAxis.loglog(
        impedanceFrequencies,
        impedanceAbsolute,
        linestyle="dashed",
        linewidth=1,
        marker="o",
        markersize=5,
        fillstyle="none",
        color="blue",
    )
    impedanceAxis.xaxis.set_major_formatter(EngFormatter(unit="Hz"))
    impedanceAxis.yaxis.set_major_formatter(EngFormatter(unit="$\Omega$"))
    impedanceAxis.set_xlabel(r"f")
    impedanceAxis.set_ylabel(r"|Z|")
    impedanceAxis.yaxis.label.set_color("blue")
    impedanceAxis.grid(which="both", linestyle="dashed", linewidth=0.5)
    impedanceAxis.set_xlim(
        [min(impedanceFrequencies) * 0.8, max(impedanceFrequencies) * 1.2]
    )

    phaseAxis.semilogx(
        impedanceFrequencies,
        np.abs(impedancePhase * (360 / (2 * np.pi))),
        linestyle="dashed",
        linewidth=1,
        marker="o",
        markersize=5,
        fillstyle="none",
        color="red",
    )
    phaseAxis.yaxis.set_major_formatter(EngFormatter(unit="$°$", sep=""))
    phaseAxis.xaxis.set_major_formatter(EngFormatter(unit="Hz"))
    phaseAxis.set_xlabel(r"f")
    phaseAxis.set_ylabel(r"|Phase|")
    phaseAxis.yaxis.label.set_color("red")
    phaseAxis.set_ylim([0, 90])
    figBode.set_size_inches(15, 6)
    plt.show()

    zahnerZennium.selectPotentiostat(0)
    zenniumConnection.disconnectFromTerm()
    fileInterface.close()

    deltaSM18_220.setProgSourceVoltage(DeltaSources.front)
    deltaSM18_220.setProgSourceCurrent(DeltaSources.front)
    deltaConnection.disconnect()

    print("finish")
