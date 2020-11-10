'''
  ____       __                        __    __   __      _ __
 /_  / ___ _/ /  ___  ___ ___________ / /__ / /__/ /_____(_) /__
  / /_/ _ `/ _ \/ _ \/ -_) __/___/ -_) / -_)  '_/ __/ __/ /  '_/
 /___/\_,_/_//_/_//_/\__/_/      \__/_/\__/_/\_\\__/_/ /_/_/\_\

Copyright 2020 ZAHNER-elektrik I. Zahner-Schiller GmbH & Co. KG

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
 
from ThalesRemoteConnection import ThalesRemoteConnection
from ThalesRemoteScriptWrapper import PotentiostatMode, ThalesRemoteScriptWrapper

TARGET_HOST = "localhost"

if __name__ == '__main__':
    '''
    The Thales software must first be started so that it can be connected.
    '''
    ZenniumConnection = ThalesRemoteConnection()
    connectionSuccessful = ZenniumConnection.connectToTerm(TARGET_HOST, "ScriptRemote")
    if connectionSuccessful:
        print("connection successfull")
    else:
        print("connection not possible")
        
    ZahnerZennium = ThalesRemoteScriptWrapper(ZenniumConnection)

    ZahnerZennium.forceThalesIntoRemoteScript()
    
    '''
    Measure EIS spectra with a sequential number in the file name that has been specified.
    Starting with number 13.
    '''
    ZahnerZennium.setEISNaming("counter")
    ZahnerZennium.setEISCounter(13)
    ZahnerZennium.setEISOutputPath("C:\\THALES\\temp\\test1")
    ZahnerZennium.setEISOutputFileName("spectra")
    
    '''
    Setting the parameters for the spectra.
    Alternatively a rule file can be used as a template.
    '''
    ZahnerZennium.setPotentiostatMode(PotentiostatMode.POTMODE_POTENTIOSTATIC)
    ZahnerZennium.setAmplitude(10e-3)
    ZahnerZennium.setPotential(1)
    ZahnerZennium.setLowerFrequencyLimit(10)
    ZahnerZennium.setStartFrequency(1000)
    ZahnerZennium.setUpperFrequencyLimit(10000)
    ZahnerZennium.setLowerNumberOfPeriods(5)
    ZahnerZennium.setLowerStepsPerDecade(2)
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
    
    for i in range(3):
        ZahnerZennium.measureEIS()
        
    ZahnerZennium.disablePotentiostat()
    
    '''
    By default the main potentiostat with the number 0 is selected.
    1 corresponds to the external potentiostat connected to EPC channel 1.
    '''
    ZahnerZennium.selectPotentiostat(1)
    
    '''
    Measure another spectrum and store it at another location.
    Measure with a different amplitude and from start to minimum frequency,
    otherwise same parameters.
    '''
    ZahnerZennium.setEISNaming("dateTime")
    ZahnerZennium.setEISOutputPath("C:\\THALES\\temp\\test2")
    ZahnerZennium.setEISOutputFileName("spectra")
    
    ZahnerZennium.setAmplitude(50e-3)
    ZahnerZennium.setScanDirection("startToMin")
    
    for i in range(3):
        ZahnerZennium.measureEIS()
    
    '''
    Measurement with spectra of different amplitudes.
    The amplitude is written into the file name.
    '''
    ZahnerZennium.setEISNaming("individual")
    ZahnerZennium.setEISOutputPath("C:\\THALES\\temp\\test3")
    
    AmplitudesIn_mV_forMeasurement = [5, 10, 20, 50]
    
    for amplitude in AmplitudesIn_mV_forMeasurement:
        ZahnerZennium.setEISOutputFileName("spectraAmplitude{}mV".format(amplitude))
        ZahnerZennium.setAmplitude(amplitude / 1000)
        ZahnerZennium.measureEIS()
    
    '''
    Switch back to the main potentiostat and disconnect.
    '''
    ZahnerZennium.selectPotentiostat(0)
    
    ZenniumConnection.disconnectFromTerm()
    print("finish")
