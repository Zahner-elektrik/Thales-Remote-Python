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
    ZahnerZennium.setEISOutputFileName("spectra_cells")
        
    '''
    Setting the parameters for the spectra.
    Alternatively a rule file can be used as a template.
    '''
    ZahnerZennium.setPotentiostatMode(PotentiostatMode.POTMODE_POTENTIOSTATIC)
    ZahnerZennium.setAmplitude(10e-3)
    ZahnerZennium.setPotential(0)
    ZahnerZennium.setLowerFrequencyLimit(0.05)
    ZahnerZennium.setStartFrequency(1000)
    ZahnerZennium.setUpperFrequencyLimit(100000)
    ZahnerZennium.setLowerNumberOfPeriods(2)
    ZahnerZennium.setLowerStepsPerDecade(5)
    ZahnerZennium.setUpperNumberOfPeriods(20)
    ZahnerZennium.setUpperStepsPerDecade(10)
    ZahnerZennium.setScanDirection("startToMax")
    ZahnerZennium.setScanStrategy("single")
    
    '''
    Setup PAD4 Channels
    '''
    ZahnerZennium.setupPAD4(1,1,1)
    ZahnerZennium.setupPAD4(1,2,1)
    ZahnerZennium.enablePAD4()
    
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
    Import the spectra
    '''
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
    
    nyquistAxis.plot(np.real(impedanceComplexStack), -np.imag(impedanceComplexStack), marker="x", markersize=5, label="Stack")
    nyquistAxis.plot(np.real(impedanceComplexCell1), -np.imag(impedanceComplexCell1), marker="x", markersize=5, label="Cell 1")
    nyquistAxis.plot(np.real(impedanceComplexCell2), -np.imag(impedanceComplexCell2), marker="x", markersize=5, label="Cell 2")
    
    nyquistAxis.grid(which="both")
    nyquistAxis.set_aspect("equal")
    nyquistAxis.xaxis.set_major_formatter(EngFormatter(unit="$\Omega$"))
    nyquistAxis.yaxis.set_major_formatter(EngFormatter(unit="$\Omega$"))
    nyquistAxis.set_xlabel(r"$Z_{\rm re}$")
    nyquistAxis.set_ylabel(r"$-Z_{\rm im}$")
    nyquistAxis.legend(fontsize = "large")
    figNyquist.set_size_inches(30, 6)
    plt.show()
    