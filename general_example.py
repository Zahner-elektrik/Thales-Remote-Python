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
from ThalesRemoteScriptWrapper import PotentiostatMode, ThalesRemoteScriptWrapper
import math
import cmath

TARGET_HOST = "localhost"

'''
Help functions
'''
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
    Measure current and voltage several times.
    '''

    ZahnerZennium.setPotentiostatMode(PotentiostatMode.POTMODE_POTENTIOSTATIC)
    ZahnerZennium.setPotential(0)
    ZahnerZennium.enablePotentiostat()

    for i in range(10):
        print("Potential: " + str(ZahnerZennium.getPotential()))
        print("Current: " + str(ZahnerZennium.getCurrent()))

    '''
    Measure impedance at individual frequency points.
    '''
    ZahnerZennium.setFrequency(2000)
    ZahnerZennium.setAmplitude(10e-3)
    ZahnerZennium.setNumberOfPeriods(3)

    printImpedance(ZahnerZennium.getImpedance())
    printImpedance(ZahnerZennium.getImpedance(2000))
    printImpedance(ZahnerZennium.getImpedance(2000, 10e-3, 3))

    '''
    Measurement of a spectrum with a previously defined function.
    '''
    spectrum(ZahnerZennium, 1000, 2e5, 10)
    
    ZahnerZennium.disablePotentiostat()
    
    ZenniumConnection.disconnectFromTerm()
    print("finish")
