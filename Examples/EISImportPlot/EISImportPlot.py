import sys
from thales_remote.connection import ThalesRemoteConnection
from thales_remote.script_wrapper import PotentiostatMode, ThalesRemoteScriptWrapper

from zahner_analysis.file_import.ism_import import IsmImport
from zahner_analysis.plotting.impedance_plot import nyquistPlotter, bodePlotter

import matplotlib.pyplot as plt
import numpy as np

if __name__ == "__main__":
    zenniumConnection = ThalesRemoteConnection()
    zenniumConnection.connectToTerm("localhost", "ScriptRemote")

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

    (figNyquist, nyquistAxis) = nyquistPlotter(impedanceObject=ismFile)

    figNyquist.suptitle("Nyquist")
    figNyquist.set_size_inches(18, 18)

    plt.show()

    figNyquist.savefig("nyquist.svg")

    (figBode, (impedanceAxis, phaseAxis)) = bodePlotter(impedanceObject=ismFile)

    figBode.suptitle("Bode")
    figBode.set_size_inches(18, 12)

    plt.show()

    figBode.savefig("bode.svg")
