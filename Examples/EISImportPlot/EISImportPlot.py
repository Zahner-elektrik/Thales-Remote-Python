import sys
from thales_remote.connection import ThalesRemoteConnection
from thales_remote.script_wrapper import PotentiostatMode,ThalesRemoteScriptWrapper

from thales_file_import.ism_import import IsmImport
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import EngFormatter

if __name__ == "__main__":
    zenniumConnection = ThalesRemoteConnection()
    connectionSuccessful = zenniumConnection.connectToTerm("localhost", "ScriptRemote")
    if connectionSuccessful:
        print("connection successfull")
    else:
        print("connection not possible")
        sys.exit()
          
    zahnerZennium = ThalesRemoteScriptWrapper(zenniumConnection)
    zahnerZennium.forceThalesIntoRemoteScript()
    
    zahnerZennium.calibrateOffsets()

    zahnerZennium.setEISNaming("counter")
    zahnerZennium.setEISCounter(1)
    zahnerZennium.setEISOutputPath(r"C:\THALES\temp\test1")
    zahnerZennium.setEISOutputFileName("spectra")

    zahnerZennium.setPotentiostatMode(PotentiostatMode.POTMODE_POTENTIOSTATIC)
    zahnerZennium.setAmplitude(10e-3)
    zahnerZennium.setPotential(0)
    zahnerZennium.setLowerFrequencyLimit(0.01)
    zahnerZennium.setStartFrequency(1000)
    zahnerZennium.setUpperFrequencyLimit(200000)
    zahnerZennium.setLowerNumberOfPeriods(3)
    zahnerZennium.setLowerStepsPerDecade(5)
    zahnerZennium.setUpperNumberOfPeriods(20)
    zahnerZennium.setUpperStepsPerDecade(10)
    zahnerZennium.setScanDirection("startToMax")
    zahnerZennium.setScanStrategy("single")

    zahnerZennium.enablePotentiostat()
    zahnerZennium.measureEIS()
    zahnerZennium.disablePotentiostat()
    
    zahnerZennium.setAmplitude(0)
    
    zenniumConnection.disconnectFromTerm()

    ismFile = IsmImport(r"C:\THALES\temp\test1\spectra_0001.ism")
    
    impedanceFrequencies = ismFile.getFrequencyArray()
    
    impedanceAbsolute = ismFile.getImpedanceArray()
    impedancePhase = ismFile.getPhaseArray()
    
    impedanceComplex = ismFile.getComplexImpedanceArray()

    print("Measurement end time: " + str(ismFile.getMeasurementEndDateTime()))

    figNyquist, (nyquistAxis) = plt.subplots(1, 1)
    figNyquist.suptitle("Nyquist")
    
    nyquistAxis.plot(np.real(impedanceComplex), -np.imag(impedanceComplex), linestyle='dashed', linewidth=1, marker="o", markersize=5, fillstyle = "none", color = "#2e8b57")
    nyquistAxis.grid(which="both", linestyle="dashed", linewidth=0.5)
    nyquistAxis.set_aspect("equal")
    nyquistAxis.xaxis.set_major_formatter(EngFormatter(unit="$\Omega$"))
    nyquistAxis.yaxis.set_major_formatter(EngFormatter(unit="$\Omega$"))
    nyquistAxis.set_xlabel(r"$Z_{\rm re}$")
    nyquistAxis.set_ylabel(r"$-Z_{\rm im}$")
    figNyquist.set_size_inches(18, 18)
    plt.show()
    figNyquist.savefig("nyquist.svg")

    figBode, (impedanceAxis) = plt.subplots(1, 1)
    figBode.suptitle("Bode")
    
    phaseAxis = impedanceAxis.twinx()
    
    impedanceAxis.loglog(impedanceFrequencies, impedanceAbsolute, linestyle='dashed', linewidth=1, marker="o", markersize=5, fillstyle = "none", color = "blue")
    impedanceAxis.xaxis.set_major_formatter(EngFormatter(unit="Hz"))
    impedanceAxis.yaxis.set_major_formatter(EngFormatter(unit="$\Omega$"))
    impedanceAxis.set_xlabel(r"f")
    impedanceAxis.set_ylabel(r"|Z|")
    impedanceAxis.yaxis.label.set_color("blue")
    impedanceAxis.grid(which="both", linestyle="dashed", linewidth=0.5)
    impedanceAxis.set_xlim([min(impedanceFrequencies)*0.8, max(impedanceFrequencies)*1.2])
    
    phaseAxis.semilogx(impedanceFrequencies, np.abs(impedancePhase * (360 / (2 * np.pi))), linestyle='dashed', linewidth=1, marker="o", markersize=5, fillstyle = "none", color = "red")
    phaseAxis.yaxis.set_major_formatter(EngFormatter(unit="$°$", sep=""))
    phaseAxis.xaxis.set_major_formatter(EngFormatter(unit="Hz"))
    phaseAxis.set_xlabel(r"f")
    phaseAxis.set_ylabel(r"|Phase|")
    phaseAxis.yaxis.label.set_color("red")
    phaseAxis.set_ylim([0, 90])
    figBode.set_size_inches(18, 12)
    plt.show()
    figBode.savefig("bode.svg")

