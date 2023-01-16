import sys
import os

from thales_remote.connection import ThalesRemoteConnection
from thales_remote.script_wrapper import ThalesRemoteScriptWrapper, PotentiostatMode
from thales_remote.file_interface import ThalesFileInterface

from zahner_analysis.file_import.isc_import import IscImport
from zahner_analysis.file_import.ism_import import IsmImport

import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
from matplotlib.ticker import EngFormatter
import jinja2

if __name__ == "__main__":
    remoteIP = "localhost"

    zenniumConnection = ThalesRemoteConnection()
    zenniumConnection.connectToTerm(remoteIP, "ScriptRemote")

    zahnerZennium = ThalesRemoteScriptWrapper(zenniumConnection)
    zahnerZennium.forceThalesIntoRemoteScript()

    measDataInterface = ThalesFileInterface(remoteIP)
    measDataInterface.disableSaveReceivedFilesToDisk()
    measDataInterface.enableKeepReceivedFilesInObject()
    measDataInterface.enableAutomaticFileExchange(fileExtensions="*.ism*.isc")

    zahnerZennium.calibrateOffsets()

    zahnerZennium.setCVStartPotential(0)
    zahnerZennium.setCVUpperReversingPotential(1)
    zahnerZennium.setCVLowerReversingPotential(0)
    zahnerZennium.setCVEndPotential(0)

    zahnerZennium.setCVStartHoldTime(2)
    zahnerZennium.setCVEndHoldTime(2)

    zahnerZennium.setCVCycles(1.5)
    zahnerZennium.setCVSamplesPerCycle(400)

    zahnerZennium.setCVMaximumCurrent(1e-3)
    zahnerZennium.setCVMinimumCurrent(-1e-3)

    zahnerZennium.setCVOhmicDrop(0)

    zahnerZennium.disableCVAutoRestartAtCurrentOverflow()
    zahnerZennium.disableCVAutoRestartAtCurrentUnderflow()
    zahnerZennium.disableCVAnalogFunctionGenerator()

    zahnerZennium.setCVNaming("individual")
    zahnerZennium.setCVOutputPath(r"C:\THALES\temp\cv")
    zahnerZennium.setCVOutputFileName("cv_measurement")

    scanRate = 0.25

    zahnerZennium.setCVScanRate(scanRate)

    zahnerZennium.checkCVSetup()
    zahnerZennium.measureCV()

    CVmeasurementData = IscImport(measDataInterface.getLatestReceivedFile().binaryData)
    maximumCurrent = max(CVmeasurementData.getCurrentArray())
    minimumCurrent = min(CVmeasurementData.getCurrentArray())

    capacitance = ((maximumCurrent - minimumCurrent) / 2) / scanRate

    capacitanceFormatter = EngFormatter(places=3, unit="F")
    print(f"{capacitanceFormatter.format_data(capacitance)} Capacitor")

    figCV, (axis) = plt.subplots(1, 1)
    figCV.suptitle(
        f"Cyclic Voltammetry {capacitanceFormatter.format_data(capacitance)} Capacitor"
    )

    axis.plot(
        CVmeasurementData.getVoltageArray(),
        CVmeasurementData.getCurrentArray(),
        color="red",
    )

    axis.grid(which="both")
    axis.xaxis.set_major_formatter(EngFormatter(unit="V"))
    axis.yaxis.set_major_formatter(EngFormatter(unit="A"))
    axis.set_xlabel(r"Voltage")
    axis.set_ylabel(r"Current")

    figCV.set_size_inches(10, 10)
    plt.show()
    figCV.savefig("CV.pdf")

    zahnerZennium.setEISNaming("individual")
    zahnerZennium.setEISOutputPath(r"C:\THALES\temp")
    zahnerZennium.setEISOutputFileName("eis_measurement")

    zahnerZennium.setPotentiostatMode(PotentiostatMode.POTMODE_POTENTIOSTATIC)
    zahnerZennium.setAmplitude(10e-3)
    zahnerZennium.setPotential(0)
    zahnerZennium.setLowerFrequencyLimit(10)
    zahnerZennium.setStartFrequency(10)
    zahnerZennium.setUpperFrequencyLimit(500000)
    zahnerZennium.setLowerNumberOfPeriods(3)
    zahnerZennium.setLowerStepsPerDecade(5)
    zahnerZennium.setUpperNumberOfPeriods(20)
    zahnerZennium.setUpperStepsPerDecade(5)
    zahnerZennium.setScanDirection("startToMin")
    zahnerZennium.setScanStrategy("single")

    zahnerZennium.enablePotentiostat()
    zahnerZennium.measureEIS()
    zahnerZennium.disablePotentiostat()

    zahnerZennium.setAmplitude(0)

    EISmeasurementData = IsmImport(measDataInterface.getLatestReceivedFile().binaryData)

    zenniumConnection.disconnectFromTerm()
    measDataInterface.close()

    impedanceFrequencies = EISmeasurementData.getFrequencyArray()
    impedanceAbsolute = EISmeasurementData.getImpedanceArray()
    impedancePhase = EISmeasurementData.getPhaseArray()
    figBode, (impedanceAxis) = plt.subplots(1, 1)
    figBode.suptitle(f"EIS {capacitanceFormatter.format_data(capacitance)} Capacitor")

    phaseAxis = impedanceAxis.twinx()

    impedanceAxis.loglog(
        impedanceFrequencies, impedanceAbsolute, marker="o", markersize=3, color="blue"
    )
    impedanceAxis.xaxis.set_major_formatter(EngFormatter(unit="Hz"))
    impedanceAxis.yaxis.set_major_formatter(EngFormatter(unit="$\Omega$"))
    impedanceAxis.set_xlabel(r"f")
    impedanceAxis.set_ylabel(r"|Z|")
    impedanceAxis.yaxis.label.set_color("blue")
    impedanceAxis.grid(which="both")
    impedanceAxis.set_xlim([min(impedanceFrequencies), max(impedanceFrequencies)])

    phaseAxis.semilogx(
        impedanceFrequencies,
        np.abs(impedancePhase * (360 / (2 * np.pi))),
        marker="o",
        markersize=3,
        color="red",
    )
    phaseAxis.yaxis.set_major_formatter(EngFormatter(unit="$°$", sep=""))
    phaseAxis.xaxis.set_major_formatter(EngFormatter(unit="Hz"))
    phaseAxis.set_xlabel(r"f")
    phaseAxis.set_ylabel(r"|Phase|")
    phaseAxis.yaxis.label.set_color("red")
    phaseAxis.set_ylim([0, 90])
    figBode.set_size_inches(10, 4)
    plt.show()
    figBode.savefig("EIS.pdf")

    mpl.rcParams["axes.unicode_minus"] = False
    prefixFormatter = EngFormatter(places=3, sep="")
    defaultMu = prefixFormatter.ENG_PREFIXES[-6]
    prefixFormatter.ENG_PREFIXES[-6] = "\\textmu"  # LaTeX notation for micro

    with open("EIS.csv", "wb") as file:
        file.write(bytearray("Frequency;Impedance;Phase" + os.linesep, "utf-8"))

        for freq, imp, phase in zip(
            impedanceFrequencies, impedanceAbsolute, impedancePhase
        ):
            file.write(
                bytearray(
                    f"{prefixFormatter.format_data(freq)};{prefixFormatter.format_data(imp)};{prefixFormatter.format_data(phase * (360 / (2 * np.pi)))}"
                    + os.linesep,
                    "utf-8",
                )
            )

    objectName = input("Input Test Object Identifier:")

    latex_jinja_env = jinja2.Environment(
        variable_start_string="\PYVAR{",
        variable_end_string="}",
        trim_blocks=True,
        autoescape=False,
        loader=jinja2.FileSystemLoader(os.path.abspath(".")),
    )

    template = latex_jinja_env.get_template(r"report.tex")

    currentFormatter = EngFormatter(unit="A")
    currentFormatter.ENG_PREFIXES[-6] = "\\mu "  # LaTeX notation for micro

    fileString = template.render(
        objectname=objectName,
        capacitance=capacitanceFormatter.format_data(capacitance),
        cv_filename="CV.pdf",
        eis_filename="EIS.pdf",
        eis_csv_filename="EIS.csv",
        cv_maximum_current=currentFormatter.format_data(maximumCurrent),
        cv_minimum_current=currentFormatter.format_data(minimumCurrent),
        cv_scanrate=scanRate,
    )

    fileString = bytearray(fileString, "utf-8")
    f = open("report_filled.tex", "wb")
    f.write(fileString)
    f.close()

    # Only needed for Jupyter, that the kernel does not have to be restarted all the time.
    currentFormatter.ENG_PREFIXES[-6] = defaultMu

    command = f'pdflatex.exe report_filled.tex -jobname="{objectName}"'
    os.system(command)
    os.popen(f"{objectName}.pdf")
    print("finish")
