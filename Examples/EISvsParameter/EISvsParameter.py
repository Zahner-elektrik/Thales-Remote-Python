import sys
from thales_remote.connection import ThalesRemoteConnection
from thales_remote.script_wrapper import PotentiostatMode, ThalesRemoteScriptWrapper

from zahner_analysis.file_import.ism_import import IsmImport
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import EngFormatter, StrMethodFormatter
from matplotlib import ticker, colors, cm

if __name__ == "__main__":
    zenniumConnection = ThalesRemoteConnection()
    zenniumConnection.connectToTerm("localhost", "ScriptRemote")

    zahnerZennium = ThalesRemoteScriptWrapper(zenniumConnection)
    zahnerZennium.forceThalesIntoRemoteScript()

    zahnerZennium.calibrateOffsets()

    zahnerZennium.setEISNaming("individual")
    zahnerZennium.setEISOutputPath(r"C:\THALES\temp")

    zahnerZennium.setPotentiostatMode(PotentiostatMode.POTMODE_POTENTIOSTATIC)
    zahnerZennium.setAmplitude(10e-3)
    zahnerZennium.setLowerFrequencyLimit(100)
    zahnerZennium.setStartFrequency(100)
    zahnerZennium.setUpperFrequencyLimit(500000)
    zahnerZennium.setLowerNumberOfPeriods(10)
    zahnerZennium.setLowerStepsPerDecade(10)
    zahnerZennium.setUpperNumberOfPeriods(20)
    zahnerZennium.setUpperStepsPerDecade(10)
    zahnerZennium.setScanDirection("startToMin")
    zahnerZennium.setScanStrategy("single")

    potentialsToMeasure = np.linspace(0, 0.3, 13)
    print(potentialsToMeasure)

    for potential in potentialsToMeasure:
        filename = "{:d}_mvdc".format(int(round(potential * 1000)))
        print("step: " + filename)
        zahnerZennium.setEISOutputFileName(filename)
        zahnerZennium.setPotential(potential)

        zahnerZennium.enablePotentiostat()
        zahnerZennium.measureEIS()
        zahnerZennium.disablePotentiostat()

    zahnerZennium.setAmplitude(0)
    zenniumConnection.disconnectFromTerm()

    absoluteImpedances = []
    phases = []

    for potential in potentialsToMeasure:
        ismFile = IsmImport(
            r"C:\THALES\temp\{:d}_mvdc.ism".format(int(round(potential * 1000)))
        )
        absoluteImpedances.append(ismFile.getImpedanceArray())
        phases.append(ismFile.getPhaseArray())

    absoluteImpedances = np.array(absoluteImpedances)
    phases = np.array(phases)
    phases = np.abs(phases * (360 / (2 * np.pi)))

    impedanceFrequencies = ismFile.getFrequencyArray()

    X, Y = np.meshgrid(impedanceFrequencies, potentialsToMeasure)

    impedanceFigure, impedancePlot = plt.subplots(1, 1)
    impedanceFigure.suptitle("Impedance vs. DC Voltage vs. Frequency")

    ticks = np.power(
        10,
        np.arange(
            np.floor(np.log10(absoluteImpedances.min()) - 1),
            np.ceil(np.log10(absoluteImpedances.max()) + 1),
        ),
    )
    levels = np.logspace(
        np.floor(np.log10(absoluteImpedances.min()) - 1),
        np.ceil(np.log10(absoluteImpedances.max())),
        num=200,
    )
    impedanceContour = impedancePlot.contourf(
        X,
        Y,
        absoluteImpedances,
        levels=levels,
        norm=colors.LogNorm(absoluteImpedances.min(), absoluteImpedances.max(), True),
        cmap="jet",
    )

    impedancePlot.set_xlabel(r"Frequency")
    impedancePlot.set_xscale("log")
    impedancePlot.xaxis.set_major_formatter(EngFormatter(unit="Hz"))

    impedancePlot.set_ylabel(r"DC Voltage")
    impedancePlot.yaxis.set_major_formatter(EngFormatter(unit="V"))

    impedanceBar = impedanceFigure.colorbar(
        impedanceContour, ticks=ticks, format=EngFormatter(unit="$\Omega$")
    )
    impedanceBar.set_label("| Impedance |")
    impedanceFigure.set_size_inches(14, 12)
    plt.tight_layout()
    plt.show()
    impedanceFigure.savefig("impedance_contour.svg")

    phaseFigure, phasePlot = plt.subplots(1, 1)
    phaseFigure.suptitle("Phase vs. DC Voltage vs. Frequency")

    levels = np.linspace(phases.min(), phases.max(), 91)
    phaseContour = phasePlot.contourf(X, Y, phases, levels=levels, cmap="jet")

    phasePlot.set_xlabel(r"Frequency")
    phasePlot.set_xscale("log")
    phasePlot.xaxis.set_major_formatter(EngFormatter(unit="Hz"))

    phasePlot.set_ylabel(r"DC Voltage")
    phasePlot.yaxis.set_major_formatter(EngFormatter(unit="V"))

    phaseBar = phaseFigure.colorbar(
        phaseContour, format=StrMethodFormatter("{x:.0f}$°$")
    )
    phaseBar.set_label("| Phase |")

    phaseFigure.set_size_inches(14, 12)
    plt.tight_layout()
    plt.show()
    phaseFigure.savefig("phase_contour.svg")
