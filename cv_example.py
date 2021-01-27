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
from ThalesRemoteConnection import ThalesRemoteConnection
from ThalesRemoteScriptWrapper import ThalesRemoteScriptWrapper

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
    Measure cv with a sequential number in the file name that has been specified.
    Starting with number 1.
    '''
    ZahnerZennium.setCVNaming("counter")
    ZahnerZennium.setCVCounter(1)
    ZahnerZennium.setCVOutputPath(r"C:\THALES\temp\cv")
    ZahnerZennium.setCVOutputFileName("cv_series")
    
    '''
    Setting the parameters for the cv measurment.
    Alternatively a rule file can be used as a template.
    '''
    ZahnerZennium.setCVStartPotential(1)
    ZahnerZennium.setCVUpperReversingPotential(2)
    ZahnerZennium.setCVLowerReversingPotential(0)
    ZahnerZennium.setCVEndPotential(1)
    
    ZahnerZennium.setCVStartHoldTime(2)
    ZahnerZennium.setCVEndHoldTime(2)
    
    ZahnerZennium.setCVCycles(1.5)
    ZahnerZennium.setCVSamplesPerCycle(400)
    ZahnerZennium.setCVScanRate(0.5)
    
    ZahnerZennium.setCVMaximumCurrent(0.03)
    ZahnerZennium.setCVMinimumCurrent(-0.03)
    
    ZahnerZennium.setCVOhmicDrop(0)
    
    ZahnerZennium.disableCVAutoRestartAtCurrentOverflow()
    ZahnerZennium.disableCVAutoRestartAtCurrentUnderflow()
    ZahnerZennium.disableCVAnalogFunctionGenerator()
    
    ZahnerZennium.checkCVSetup()
    print(ZahnerZennium.readCVSetup())
    
    for i in range(3):
        ZahnerZennium.measureCV()
    
    '''
    By default the main potentiostat with the number 0 is selected.
    1 corresponds to the external potentiostat connected to EPC channel 1.
    '''
    ZahnerZennium.selectPotentiostat(1)
    
    '''
    Measurement with spectra of different amplitudes.
    The amplitude is written into the file name.
    '''
    ZahnerZennium.setCVNaming("individual")
    ZahnerZennium.setCVOutputPath(r"C:\THALES\temp\cv")
    
    ScanRatesForMeasurement = [0.1, 0.2, 0.5, 1.0]
    
    for scanRate in ScanRatesForMeasurement:
        ZahnerZennium.setCVOutputFileName("cv_scanrate_{:d}mVs".format(int(scanRate * 1000)))
        ZahnerZennium.setCVScanRate(scanRate)
    
        ZahnerZennium.checkCVSetup()
        print(ZahnerZennium.readCVSetup())
        
        ZahnerZennium.measureCV()
    
    '''
    Switch back to the main potentiostat and disconnect.
    '''
    ZahnerZennium.selectPotentiostat(0)
    
    ZenniumConnection.disconnectFromTerm()
    print("finish")
