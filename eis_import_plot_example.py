'''
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
'''

import sys
from thales_remote.connection import ThalesRemoteConnection
from thales_remote.script_wrapper import PotentiostatMode,ThalesRemoteScriptWrapper

'''
Import the ISM import package and the matplotlib plotting library.
'''
from thales_file_import.ism_import import IsmImport
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import EngFormatter

TARGET_HOST = "localhost"

if __name__ == "__main__":
    '''
    The Thales software must first be started so that it can be connected.
    '''
    ZenniumConnection = ThalesRemoteConnection()
    connectionSuccessful = ZenniumConnection.connectToTerm(TARGET_HOST, "ScriptRemote")
    if connectionSuccessful:
        print("connection successfull")
    else:
        print("connection not possible")
        sys.exit()
    
    ZahnerZennium = ThalesRemoteScriptWrapper(ZenniumConnection)
    
    ZahnerZennium.forceThalesIntoRemoteScript()
    
    '''
    Measure EIS spectra with a sequential number in the file name that has been specified.
    Starting with number 1.
    '''
    ZahnerZennium.setEISNaming("counter")
    ZahnerZennium.setEISCounter(1)
    ZahnerZennium.setEISOutputPath(r"C:\THALES\temp\test1")
    ZahnerZennium.setEISOutputFileName("spectra")
    
    '''
    Setting the parameters for the spectra.
    Alternatively a rule file can be used as a template.
    '''
    ZahnerZennium.setPotentiostatMode(PotentiostatMode.POTMODE_POTENTIOSTATIC)
    ZahnerZennium.setAmplitude(10e-3)
    ZahnerZennium.setPotential(0)
    ZahnerZennium.setLowerFrequencyLimit(0.05)
    ZahnerZennium.setStartFrequency(1000)
    ZahnerZennium.setUpperFrequencyLimit(1000000)
    ZahnerZennium.setLowerNumberOfPeriods(3)
    ZahnerZennium.setLowerStepsPerDecade(3)
    ZahnerZennium.setUpperNumberOfPeriods(20)
    ZahnerZennium.setUpperStepsPerDecade(10)
    ZahnerZennium.setScanDirection("startToMax")
    ZahnerZennium.setScanStrategy("single")
    
    '''
    Switching on the potentiostat before the measurement,
    so that EIS is measured at the set DC potential.
    If the potentiostat is off before the measurement,
    the measurement is performed at the OCP.
    '''
    ZahnerZennium.enablePotentiostat()
    
    ZahnerZennium.measureEIS()
    
    ZahnerZennium.disablePotentiostat()
    
    ZenniumConnection.disconnectFromTerm()
    
    '''
    Import the first spectrum from the previous measurement series.
    This was saved under the set path and name with the number expanded.
    The measurement starts at 1 therefore the following path results:
    "C:\THALES\temp\test1\spectra_0001.ism".
    '''
    
    ismFile = IsmImport(r"C:\THALES\temp\test1\spectra_0001.ism")
    
    impedanceFrequencies = ismFile.getFrequencyArray()
    
    impedanceAbsolute = ismFile.getImpedanceArray()
    impedancePhase = ismFile.getPhaseArray()
    
    impedanceComplex = ismFile.getComplexImpedanceArray()
    
    print("Measurement time: " + str(ismFile.getMeasurementDate()))
    
    '''
    Display the ism file in Nyquist and Bode representation.
    '''
    plt.ion()
    
    '''
    Nyquist representation.
    
    Display the data in the chart and then format the axes.
    '''
    figNyquist, (nyquistAxis) = plt.subplots(1, 1)
    figNyquist.suptitle("Nyquist")
    
    nyquistAxis.plot(np.real(impedanceComplex), -np.imag(impedanceComplex), marker="x", markersize=5)
    nyquistAxis.grid(which="both")
    nyquistAxis.set_aspect("equal")
    nyquistAxis.xaxis.set_major_formatter(EngFormatter(unit="$\Omega$"))
    nyquistAxis.yaxis.set_major_formatter(EngFormatter(unit="$\Omega$"))
    nyquistAxis.set_xlabel(r"$Z_{\rm re}$")
    nyquistAxis.set_ylabel(r"$-Z_{\rm im}$")
    
    '''
    Bode representation.
    
    Display the data in the chart and then format the axes.
    '''
    figBode, (impedanceAxis, phaseAxis) = plt.subplots(2, 1, sharex=True)
    figBode.suptitle("Bode")
    
    impedanceAxis.loglog(impedanceFrequencies, impedanceAbsolute, marker="+", markersize=5)
    impedanceAxis.xaxis.set_major_formatter(EngFormatter(unit="Hz"))
    impedanceAxis.yaxis.set_major_formatter(EngFormatter(unit="$\Omega$"))
    impedanceAxis.set_xlabel(r"$f$")
    impedanceAxis.set_ylabel(r"$|Z|$")
    impedanceAxis.grid(which="both")
    
    phaseAxis.semilogx(impedanceFrequencies, np.abs(impedancePhase * (360 / (2 * np.pi))), marker="+", markersize=5)
    phaseAxis.xaxis.set_major_formatter(EngFormatter(unit="Hz"))
    phaseAxis.yaxis.set_major_formatter(EngFormatter(unit="$°$", sep=""))
    phaseAxis.set_xlabel(r"$f$")
    phaseAxis.set_ylabel(r"$|Phase|$")
    phaseAxis.grid(which="both")
    phaseAxis.set_ylim([0, 90])
        
    plt.show()
    
    print("finish")
    
