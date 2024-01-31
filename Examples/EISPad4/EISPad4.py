from thales_remote.connection import ThalesRemoteConnection
from thales_remote.script_wrapper import (
    PotentiostatMode,
    ScanStrategy,
    ScanDirection,
    FileNaming,
    Pad4Mode,
    ThalesRemoteScriptWrapper,
)

from zahner_analysis.file_import.ism_import import IsmImport
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import EngFormatter

zenniumConnection = ThalesRemoteConnection()
zenniumConnection.connectToTerm("192.168.2.47", "ScriptRemote")

zahnerZennium = ThalesRemoteScriptWrapper(zenniumConnection)
zahnerZennium.forceThalesIntoRemoteScript()

zahnerZennium.calibrateOffsets()

zahnerZennium.setEISNaming(FileNaming.COUNTER)
zahnerZennium.setEISCounter(1)
zahnerZennium.setEISOutputPath(r"C:\THALES\temp\test1")
zahnerZennium.setEISOutputFileName("spectra_cells")

zahnerZennium.setPotentiostatMode(PotentiostatMode.POTMODE_POTENTIOSTATIC)
zahnerZennium.setAmplitude(100e-3)
zahnerZennium.setPotential(0)
zahnerZennium.setLowerFrequencyLimit(0.1)
zahnerZennium.setStartFrequency(1000)
zahnerZennium.setUpperFrequencyLimit(10000)
zahnerZennium.setLowerNumberOfPeriods(2)
zahnerZennium.setLowerStepsPerDecade(5)
zahnerZennium.setUpperNumberOfPeriods(20)
zahnerZennium.setUpperStepsPerDecade(10)
zahnerZennium.setScanDirection(ScanDirection.START_TO_MAX)
zahnerZennium.setScanStrategy(ScanStrategy.SINGLE_SINE)

zahnerZennium.setPotential(1)
zahnerZennium.enablePotentiostat()

print(f"ACQ-Setup: {zahnerZennium.readAcqSetup()}")

for i in range(2):
    print(f"Current:\t{zahnerZennium.getCurrent():>10.3e} A")
    print(f"Potential:\t{zahnerZennium.getPotential():>10.6f} V")
    print(zahnerZennium.readAllAcqChannels())
    print(f"PAD4 Channel: {0} = {zahnerZennium.readAcqChannel(0)}")
    print(f"PAD4 Channel: {1} = {zahnerZennium.readAcqChannel(1)}")


zahnerZennium.setPotential(0)

zahnerZennium.setupPad4Channel(1, 1, 1, voltageRange=4.0, shuntResistor=10e-3)
zahnerZennium.setupPad4Channel(1, 2, 1, voltageRange=4.0, shuntResistor=10e-3)
zahnerZennium.setupPad4Channel(1, 3, 0)
zahnerZennium.setupPad4Channel(1, 4, 0)
zahnerZennium.setupPad4ModeGlobal(Pad4Mode.VOLTAGE)  # or Pad4Mode.CURRENT
zahnerZennium.enablePad4Global()

for frequency in [100, 300, 1000]:
    print(f"frequency: {frequency}")
    impedanceResult = zahnerZennium.getImpedancePad4(frequency=frequency)

    for key, val in impedanceResult.items():
        print(f"{key}: {val}")

zahnerZennium.enablePotentiostat()
zahnerZennium.measureEIS()
zahnerZennium.disablePotentiostat()
zahnerZennium.setAmplitude(0)
zenniumConnection.disconnectFromTerm()

ismFileStack = IsmImport(r"C:\THALES\temp\test1\spectra_cells_0001_ser00.ism")
impedanceFrequenciesStack = ismFileStack.getFrequencyArray()
impedanceAbsoluteStack = ismFileStack.getImpedanceArray()
impedancePhaseStack = ismFileStack.getPhaseArray()
impedanceComplexStack = ismFileStack.getComplexImpedanceArray()

ismFileCell1 = IsmImport(r"C:\THALES\temp\test1\spectra_cells_0001_ser01.ism")
impedanceFrequenciesCell1 = ismFileCell1.getFrequencyArray()
impedanceAbsoluteCell1 = ismFileCell1.getImpedanceArray()
impedancePhaseCell1 = ismFileCell1.getPhaseArray()
impedanceComplexCell1 = ismFileCell1.getComplexImpedanceArray()

ismFileCell2 = IsmImport(r"C:\THALES\temp\test1\spectra_cells_0001_ser02.ism")
impedanceFrequenciesCell2 = ismFileCell2.getFrequencyArray()
impedanceAbsoluteCell2 = ismFileCell2.getImpedanceArray()
impedancePhaseCell2 = ismFileCell2.getPhaseArray()
impedanceComplexCell2 = ismFileCell2.getComplexImpedanceArray()

figNyquist, (nyquistAxis) = plt.subplots(1, 1)
figNyquist.suptitle("Nyquist")

nyquistAxis.plot(
    np.real(impedanceComplexStack),
    -np.imag(impedanceComplexStack),
    marker="x",
    markersize=5,
    label="Stack",
)
nyquistAxis.plot(
    np.real(impedanceComplexCell1),
    -np.imag(impedanceComplexCell1),
    marker="x",
    markersize=5,
    label="Cell 1",
)
nyquistAxis.plot(
    np.real(impedanceComplexCell2),
    -np.imag(impedanceComplexCell2),
    marker="x",
    markersize=5,
    label="Cell 2",
)

nyquistAxis.grid(which="both")
nyquistAxis.set_aspect("equal")
nyquistAxis.xaxis.set_major_formatter(EngFormatter(unit=r"$\Omega$"))
nyquistAxis.yaxis.set_major_formatter(EngFormatter(unit=r"$\Omega$"))
nyquistAxis.set_xlabel(r"$Z_{\rm re}$")
nyquistAxis.set_ylabel(r"$-Z_{\rm im}$")
nyquistAxis.legend(fontsize="large")
figNyquist.set_size_inches(20, 8)
plt.show()
figNyquist.savefig("nyquist.svg")
