"""
  ____       __                        __    __   __      _ __
 /_  / ___ _/ /  ___  ___ ___________ / /__ / /__/ /_____(_) /__
  / /_/ _ `/ _ \/ _ \/ -_) __/___/ -_) / -_)  '_/ __/ __/ /  '_/
 /___/\_,_/_//_/_//_/\__/_/      \__/_/\__/_/\_\\__/_/ /_/_/\_\

Copyright 2021 ZAHNER-elektrik I. Zahner-Schiller GmbH & Co. KG

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the Software
is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH
THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import sys
from thales_remote.connection import ThalesRemoteConnection
from thales_remote.script_wrapper import PotentiostatMode,ThalesRemoteScriptWrapper

"""
Import the ISM import package and the matplotlib plotting library.
"""
from thales_file_import.ism_import import IsmImport
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import EngFormatter, StrMethodFormatter
from matplotlib import ticker,colors,cm

if __name__ == "__main__":
    """
    The Thales software must first be started so that it can be connected.
    """
    ZenniumConnection = ThalesRemoteConnection()
    connectionSuccessful = ZenniumConnection.connectToTerm("localhost", "ScriptRemote")
    if connectionSuccessful:
        print("connection successfull")
    else:
        print("connection not possible")
        sys.exit()
    
    ZahnerZennium = ThalesRemoteScriptWrapper(ZenniumConnection)
    
    ZahnerZennium.forceThalesIntoRemoteScript()
    
    ZahnerZennium.setEISNaming("individual")
    ZahnerZennium.setEISOutputPath(r"C:\THALES\temp")
    
    ZahnerZennium.setPotentiostatMode(PotentiostatMode.POTMODE_POTENTIOSTATIC)
    ZahnerZennium.setAmplitude(10e-3)
    ZahnerZennium.setLowerFrequencyLimit(100)
    ZahnerZennium.setStartFrequency(100)
    ZahnerZennium.setUpperFrequencyLimit(500000)
    ZahnerZennium.setLowerNumberOfPeriods(10)
    ZahnerZennium.setLowerStepsPerDecade(10)
    ZahnerZennium.setUpperNumberOfPeriods(20)
    ZahnerZennium.setUpperStepsPerDecade(10)
    ZahnerZennium.setScanDirection("startToMin")
    ZahnerZennium.setScanStrategy("single")
    
    """
    Switching on the potentiostat before the measurement,
    so that EIS is measured at the set DC potential.
    If the potentiostat is off before the measurement,
    the measurement is performed at the OCP.
    """
    potentialsToMeasure = np.linspace(0,0.3,13)
    print(potentialsToMeasure)
    
    for potential in potentialsToMeasure:
        ZahnerZennium.setEISOutputFileName("{:d}_mvdc".format(int(potential*1000)))
        ZahnerZennium.setPotential(potential)
    
        ZahnerZennium.enablePotentiostat()
        ZahnerZennium.measureEIS()
        ZahnerZennium.disablePotentiostat()
    
    ZenniumConnection.disconnectFromTerm()
    
    absoluteImpedances = []
    phases = []
    
    ismFile = None
    for potential in potentialsToMeasure:
        ismFile = IsmImport(r"C:\THALES\temp\{:d}_mvdc.ism".format(int(potential*1000)))
        absoluteImpedances.append(ismFile.getImpedanceArray())
        phases.append(ismFile.getPhaseArray())
        
    absoluteImpedances = np.array(absoluteImpedances)
    phases = np.array(phases)
    phases = np.abs(phases * (360 / (2 * np.pi)))
    
    impedanceFrequencies = ismFile.getFrequencyArray()
    
    X,Y = np.meshgrid(impedanceFrequencies,potentialsToMeasure)
    
    """
    Impedance Figure
    """
    impedanceFigure, impedancePlot = plt.subplots(1,1)
    impedanceFigure.suptitle("Impedance vs. DC Voltage vs. Frequency")
    
    ticks = np.power(10, np.arange(np.floor(np.log10(absoluteImpedances.min())-1), np.ceil(np.log10(absoluteImpedances.max())+1)))
    levels = np.logspace(np.floor(np.log10(absoluteImpedances.min())-1), np.ceil(np.log10(absoluteImpedances.max())), num=200)
    impedanceContour = impedancePlot.contourf(X, Y, absoluteImpedances, levels = levels, norm = colors.LogNorm(absoluteImpedances.min(), absoluteImpedances.max(), True), cmap="jet")
    
    impedancePlot.set_xlabel(r"Frequency")
    impedancePlot.set_xscale("log")
    impedancePlot.xaxis.set_major_formatter(EngFormatter(unit="Hz"))
    
    impedancePlot.set_ylabel(r"DC Voltage")
    impedancePlot.yaxis.set_major_formatter(EngFormatter(unit="V"))
    
    impedanceBar = impedanceFigure.colorbar(impedanceContour, ticks=ticks, format=EngFormatter(unit="$\Omega$"))
    impedanceBar.set_label('| Impedance |')
    impedanceFigure.set_size_inches(10, 8)
    plt.tight_layout()
    plt.show()
    
        
    
    """
    Phase Figure
    """
    phaseFigure, phasePlot = plt.subplots(1, 1)
    phaseFigure.suptitle("Phase vs. DC Voltage vs. Frequency")

    levels = np.linspace(phases.min(), phases.max(), 91)
    phaseContour = phasePlot.contourf(X, Y, phases, levels = levels, cmap="jet")

    phasePlot.set_xlabel(r"Frequency")
    phasePlot.set_xscale("log")
    phasePlot.xaxis.set_major_formatter(EngFormatter(unit="Hz"))

    phasePlot.set_ylabel(r"DC Voltage")
    phasePlot.yaxis.set_major_formatter(EngFormatter(unit="V"))

    phaseBar = phaseFigure.colorbar(phaseContour, format=StrMethodFormatter("{x:.0f}$°$"))
    phaseBar.set_label('| Phase |')

    phaseFigure.set_size_inches(10, 8)
    plt.tight_layout()
    plt.show()    
    
    
    print("finish")
    
