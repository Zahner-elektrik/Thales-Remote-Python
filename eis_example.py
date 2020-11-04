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
    thalesConnection = ThalesRemoteConnection()
    connectionSuccessful = thalesConnection.connectToTerm(TARGET_HOST, "ScriptRemote")
    if connectionSuccessful:
        print("connection successfull")
    else:
        print("connection not possible")
        
    remoteScript = ThalesRemoteScriptWrapper(thalesConnection)

    remoteScript.forceThalesIntoRemoteScript()
    
    '''
    Measure EIS spectra with a sequential number in the file name that has been specified.
    Starting with number 13.
    '''
    remoteScript.setEISNaming("counter")
    remoteScript.setEISCounter(13)
    remoteScript.setEISOutputPath("C:\\THALES\\temp\\test1")
    remoteScript.setEISOutputFileName("spectra")
    
    '''
    Setting the parameters for the spectra.
    '''
    remoteScript.setPotentiostatMode(PotentiostatMode.POTMODE_POTENTIOSTATIC)
    remoteScript.setAmplitude(10e-3)
    remoteScript.setPotential(1)
    remoteScript.setLowerFrequencyLimit(10)
    remoteScript.setStartFrequency(1000)
    remoteScript.setUpperFrequencyLimit(10000)
    remoteScript.setLowerNumberOfPeriods(5)
    remoteScript.setLowerStepsPerDecade(5)
    remoteScript.setUpperNumberOfPeriods(20)
    remoteScript.setUpperStepsPerDecade(10)
    remoteScript.setScanDirection("startToMax")
    remoteScript.setScanStrategy("single")
    
    '''
    Switching on the potentiostat before the measurement,
    so that EIS is measured at the set DC potential.
    If the potentiostat is off before the measurement,
    the measurement is performed at the OCP.
    '''
    remoteScript.enablePotentiostat()
    
    remoteScript.measureEIS()
    remoteScript.measureEIS()
    remoteScript.enablePotentiostat(False)
    
    '''
    Measure another spectrum and store it at another location.
    Measure with a different amplitude and from start to minimum frequency,
    otherwise same parameters.
    '''
    remoteScript.setEISNaming("dateTime")
    remoteScript.setEISOutputPath("C:\\THALES\\temp\\test2")
    remoteScript.setEISOutputFileName("spectra")
    
    remoteScript.setAmplitude(50e-3)
    remoteScript.setScanDirection("startToMin")
    
    remoteScript.measureEIS()
    remoteScript.measureEIS()
    
    thalesConnection.disconnectFromTerm()
    print("finish")
