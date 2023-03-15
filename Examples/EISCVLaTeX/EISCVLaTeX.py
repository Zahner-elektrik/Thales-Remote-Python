import os

from thales_remote.connection import ThalesRemoteConnection
from thales_remote.script_wrapper import ThalesRemoteScriptWrapper, PotentiostatMode
from thales_remote.file_interface import ThalesFileInterface

from zahner_analysis.analysis_tools.eis_fitting import EisFitting, EisFittingPlotter
from zahner_analysis.plotting.impedance_plot import bodePlotter
from zahner_analysis.file_import.impedance_model_import import IsfxModelImport
from zahner_analysis.file_import.isc_import import IscImport
from zahner_analysis.file_import.ism_import import IsmImport

import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
from matplotlib.ticker import EngFormatter
import jinja2

remoteIP = "localhost"

zenniumConnection = ThalesRemoteConnection()
zenniumConnection.connectToTerm(remoteIP)

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
zahnerZennium.setCVOutputPath(r"C:\THALES\temp")
zahnerZennium.setCVOutputFileName("cv_measurement")

scanRate = 0.25

zahnerZennium.setCVScanRate(scanRate)

zahnerZennium.checkCVSetup()
zahnerZennium.measureCV()

CVmeasurementData = IscImport(measDataInterface.getLatestReceivedFile().binaryData)
maximumCurrent = max(CVmeasurementData.getCurrentArray())
minimumCurrent = min(CVmeasurementData.getCurrentArray())

capacitanceCV = ((maximumCurrent - minimumCurrent) / 2) / scanRate

capacitanceFormatter = EngFormatter(places=3, unit="F", sep="")
print(f"Capacitance CV: {capacitanceFormatter.format_data(capacitanceCV)}")

figCV, (axis) = plt.subplots(1, 1)

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
zahnerZennium.setPotential(1)
zahnerZennium.setLowerFrequencyLimit(5)
zahnerZennium.setStartFrequency(1000)
zahnerZennium.setUpperFrequencyLimit(500000)
zahnerZennium.setLowerNumberOfPeriods(3)
zahnerZennium.setLowerStepsPerDecade(3)
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

impedanceCircuitModel = IsfxModelImport("rlc-model.isfx")
print("fit start values:")
print(impedanceCircuitModel)

fitting = EisFitting()

fitParams = {
    "UpperFrequencyLimit": 200e3,
    "DataSource": "zhit",  # "original", "smoothed" or "zhit"
    "Smoothness": 0.0002,
}

simulationParams = {
    "UpperFrequencyLimit": 10e6,
    "LowerFrequencyLimit": 500e-3,
    "NumberOfSamples": 150,
}

simulatedData = fitting.simulate(impedanceCircuitModel, simulationParams)

(fig1, (impedanceAxis1, phaseAxis1)) = bodePlotter(impedanceObject=EISmeasurementData)
fig1.set_size_inches(10, 5)
fig1.savefig("EIS.pdf")

(fig1, (impedanceAxis1, phaseAxis1)) = bodePlotter(
    (impedanceAxis1, phaseAxis1),
    impedanceObject=simulatedData,
    argsImpedanceAxis={"linestyle": "solid", "marker": None},
    argsPhaseAxis={"linestyle": "solid", "marker": None},
)

impedanceAxis1.legend(
    impedanceAxis1.get_lines() + phaseAxis1.get_lines(),
    2 * ["Measured Data", "Model start values"],
)
fig1.set_size_inches(10, 5)
plt.show()

fittingResult = fitting.fit(
    impedanceCircuitModel,
    EISmeasurementData,
    fitParams=fitParams,
    simulationParams=simulationParams,
)

capacitanceEIS = fittingResult.getFittedModel()["C0"]["C"].getValue()
print(f"Capacitance EIS: {capacitanceFormatter.format_data(capacitanceEIS)}")

print(fittingResult)

(fig2, (impedanceAxis2, phaseAxis2)) = EisFittingPlotter.plotBode(
    fittingResult, EISmeasurementData
)
impedanceAxis2.legend(
    impedanceAxis2.get_lines() + phaseAxis2.get_lines(),
    2 * ["Measured Data", "Fitted Model"],
    loc="lower left",  # with capacitors, there are never measurement data at this position
)
fig2.set_size_inches(10, 5)
plt.show()

fig2.savefig("EIS_fitted.pdf")

mpl.rcParams["axes.unicode_minus"] = False
prefixFormatter = EngFormatter(places=3, sep="")
defaultMu = prefixFormatter.ENG_PREFIXES[-6]
prefixFormatter.ENG_PREFIXES[-6] = "\\textmu"  # LaTeX notation for micro

with open("EIS.csv", "wb") as file:
    file.write(bytearray("Frequency;Impedance;Phase" + os.linesep, "utf-8"))

    for freq, imp, phase in zip(
        EISmeasurementData.getFrequencyArray(),
        EISmeasurementData.getImpedanceArray(),
        EISmeasurementData.getPhaseArray(),
    ):
        file.write(
            bytearray(
                f"{prefixFormatter.format_data(freq)};{prefixFormatter.format_data(imp)};{prefixFormatter.format_data(phase * (360 / (2 * np.pi)))}"
                + os.linesep,
                "utf-8",
            )
        )

objectName = input("Input Test Object Identifier:")

EISmeasurementData.save(f"{objectName}.ism")

fittingResult.save(
    path=f"{objectName}_result",
    exist_ok=True,
    saveFitResultJson=True,
    saveFittedModel=True,
    saveFittedSimulatedSamples=True,
    saveFitInputSamples=True,
    fitResultJsonFilename="fit_result.json",
    fittedModelFilename="fitted.isfx",
    fittedSimulatedDataFilename="fitted_simulated.ism",
    fitInputDataFilename="fit_samples.ism",
)

latex_jinja_env = jinja2.Environment(
    variable_start_string="\PYVAR{",
    variable_end_string="}",
    trim_blocks=True,
    autoescape=False,
    loader=jinja2.FileSystemLoader(os.path.abspath(".")),
)

template = latex_jinja_env.get_template(r"report.tex")

currentFormatter = EngFormatter(places=3, unit="A", sep="")
currentFormatter.ENG_PREFIXES[-6] = "\\mu "  # LaTeX notation for micro
resistanceFormatter = EngFormatter(places=3, unit="$\Omega$", sep="")
resistanceFormatter.ENG_PREFIXES[-6] = "\\mu "
inductanceFormatter = EngFormatter(places=3, unit="H", sep="")
inductanceFormatter.ENG_PREFIXES[-6] = "\\mu "

fittedModel = fittingResult.getFittedModel()
fitResult = fittingResult.getFitResultJson()

fileString = template.render(
    objectname=objectName,
    capacitance_cv=capacitanceFormatter.format_data(capacitanceCV),
    cv_filename="CV.pdf",
    eis_filename="EIS.pdf",
    eis_fitted_filename="EIS_fitted.pdf",
    eis_csv_filename="EIS.csv",
    cv_maximum_current=currentFormatter.format_data(maximumCurrent),
    cv_minimum_current=currentFormatter.format_data(minimumCurrent),
    cv_scanrate=scanRate,
    capacitance_eis=capacitanceFormatter.format_data(capacitanceEIS),
    capacitance_eis_error=f"{fitResult['model']['C0']['C']['error']:.1f}",
    resistance_eis=resistanceFormatter.format_data(fittedModel["R0"]["R"].getValue()),
    resistance_eis_error=f"{fitResult['model']['R0']['R']['error']:.1f}",
    inductance_eis=inductanceFormatter.format_data(fittedModel["L0"]["L"].getValue()),
    inductance_eis_error=f"{fitResult['model']['L0']['L']['error']:.1f}",
)

fileString = bytearray(fileString, "utf-8")
f = open("report_filled.tex", "wb")
f.write(fileString)
f.close()

# only needed for Jupyter, that the kernel does not have to be restarted all the time.
prefixFormatter.ENG_PREFIXES[-6] = defaultMu
currentFormatter.ENG_PREFIXES[-6] = defaultMu
resistanceFormatter.ENG_PREFIXES[-6] = defaultMu
inductanceFormatter.ENG_PREFIXES[-6] = defaultMu

# close pdf viewer so that the pdf can be overwritten for debugging
os.system("taskkill /IM Acrobat.exe /T /F")

command = f'pdflatex.exe report_filled.tex -jobname="{objectName}"'
os.system(command)
os.popen(f"{objectName}.pdf")
print("finish")
