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
import math
import cmath

TARGET_HOST = "localhost"


def spectrum(scriptHandle, lower_frequency, upper_frequency, number_of_points):

    log_lower_frequency = math.log(lower_frequency)
    log_upper_frequency = math.log(upper_frequency)

    log_interval_spacing = (log_upper_frequency - log_lower_frequency) / (number_of_points - 1)
    
    for i in range(number_of_points):
        current_frequency = math.exp(log_lower_frequency + log_interval_spacing * i)
        print("Frequency: " + str(current_frequency))
        printImpedance(scriptHandle.getImpedance(current_frequency))


def printImpedance(impedance):
    print("Impedance: " + str(abs(impedance)) + " ohm, " + str(cmath.phase(impedance)) + " rad")


if __name__ == '__main__':
    thalesConnection = ThalesRemoteConnection()
    connectionSuccessful = thalesConnection.connectToTerm(TARGET_HOST, "ScriptRemote")
    if connectionSuccessful:
        print("connection successfull")
    else:
        print("connection not possible")
        
    remoteScript = ThalesRemoteScriptWrapper(thalesConnection)

    remoteScript.forceThalesIntoRemoteScript()

    print("Potential: " + str(remoteScript.getPotential()))
    print("Current: " + str(remoteScript.getCurrent()))
    
    '''
    Measure current and voltage several times.
    '''

    remoteScript.setPotentiostatMode(PotentiostatMode.POTMODE_POTENTIOSTATIC)
    remoteScript.setPotential(0)
    remoteScript.enablePotentiostat()

    for i in range(10):
        print("Potential: " + str(remoteScript.getPotential()))
        print("Current: " + str(remoteScript.getCurrent()))

    '''
    Measure impedance at individual frequency points.
    '''
    remoteScript.setFrequency(2000)
    remoteScript.setAmplitude(10e-3)
    remoteScript.setNumberOfPeriods(3)

    printImpedance(remoteScript.getImpedance())
    printImpedance(remoteScript.getImpedance(2000))
    printImpedance(remoteScript.getImpedance(2000, 10e-3, 3))

    '''
    Measurement of a spectrum with a previously defined function.
    '''
    spectrum(remoteScript, 1000, 2e5, 10)
    
    remoteScript.enablePotentiostat(False)
    
    thalesConnection.disconnectFromTerm()
    print("finish")
