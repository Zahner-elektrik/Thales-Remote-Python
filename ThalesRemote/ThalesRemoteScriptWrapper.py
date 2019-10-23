"""
  ____       __                        __    __   __      _ __
 /_  / ___ _/ /  ___  ___ ___________ / /__ / /__/ /_____(_) /__
  / /_/ _ `/ _ \/ _ \/ -_) __/___/ -_) / -_)  '_/ __/ __/ /  '_/
 /___/\_,_/_//_/_//_/\__/_/      \__/_/\__/_/\_\\__/_/ /_/_/\_\

Copyright 2019 ZAHNER-elektrik I. Zahner-Schiller GmbH & Co. KG

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

from enum import Enum
import re

class PotentiostatMode(Enum):
    """
    Working modes for the potentiostat.
    """
    POTMODE_POTENTIOSTATIC = 1
    POTMODE_GALVANOSTATIC = 2
    POTMODE_PSEUDOGALVANOSTATIC = 3

class ThalesRemoteScriptWrapper(object):
    '''
    Wrapper that uses the ThalesRemoteConnection class.
    The commands are explained in http://zahner.de/pdf/Remote.pdf
    '''
    remoteConnection = None

    def __init__(self, remoteConnection):
        '''Constructor
        
        \param [in] remoteConnection the ThalesRemoteConnection object
        '''
        self.remoteConnection = remoteConnection
        
    
    def executeRemoteCommand(self, command):
        '''Directly execute a query to Remote Script.
        
        \param [in] command The query string, e.g. "IMPEDANCE" or "Pset=0"
        
        \returns the reply sent by Remote Script
        '''
        return self.remoteConnection.sendStringAndWaitForReplyString("1:"+command+":",2)
    
    def forceThalesIntoRemoteScript(self):
        '''Prompts Thales to start the Remote Script.
        
        Will switch a running Thales from anywhere like the main menu after
        startup to running measurements into Remote Script so it can process
        further requests.
        
        \warning This happens rather quickly if Thales is idle in main menu but
                 may take some time if it's perofming an EIS measurement or doing
                 something else. For high stability applications 20 seconds would
                 probably be a save bet.
        '''
        return self.remoteConnection.sendStringAndWaitForReplyString("2,ScriptRemote", 0x80)
        
    
    def getCurrent(self):
        ''' Read the measured current from the device.
        
        \returns the current value as floating point value.
        '''
        return self._requestValueAndParseUsingRegexp("CURRENT","current=\\s*(.*?)A?:")
        
    
    def getPotential(self):
        ''' Read the measured potential from the device.
        
        \returns the potential value as floating point value.
        '''
        return self._requestValueAndParseUsingRegexp("POTENTIAL","potential=\\s*(.*?)V?:")
        
    
    def setCurrent(self, current):
        ''' Set the output current.
        
        \param [in] current the output current to set.
        '''
        return self.setValue("Cset",current)
        
    
    def setPotential(self, potential):
        ''' Set the output potential.
        
        \param [in] potential the output potential to set.
        '''
        return self.setValue("Pset",potential)    
    
    
    def enablePotentiostat(self, enabled = True):
        '''Switch the potentiostat on or off.
        
        \param [in] enabled switches the potentiostat on if true and off if false.
        '''
        if enabled:
            self.executeRemoteCommand("Pot=-1")
        else:
            self.executeRemoteCommand("Pot=0")
        
    
    def setPotentiostatMode(self, potentiostatMode):
        '''Set the coupling of the potentiostat.
        
        \param  [in] potentiostatMode this can be PotentiostatMode.POTMODE_POTENTIOSTATIC
                      or PotentiostatMode.POTMODE_GALVANOSTATIC or
                      PotentiostatMode.POTMODE_PSEUDOGALVANOSTATIC
        '''
        if potentiostatMode == PotentiostatMode.POTMODE_POTENTIOSTATIC:
            command = "Gal=0:GAL=0"
        elif potentiostatMode == PotentiostatMode.POTMODE_GALVANOSTATIC:
            command = "Gal=-1:GAL=1"
        elif potentiostatMode == PotentiostatMode.POTMODE_PSEUDOGALVANOSTATIC:
            command = "Gal=0:GAL=-1"
        else:
            return
        self.executeRemoteCommand(command)
        
    
    def setFrequency(self, frequency):
        ''' Set the output frequency
        
        \param [in] frequency the output frequency for Impedance measurement to set.
        '''
        return self.setValue("Frq",frequency)  
        
    
    def setAmplitude(self, amplitude):
        ''' Set the output amplitude
        
        \param [in] amplitude the output amplitude for Impedance measurement to set.
        '''
        return self.setValue("Ampl",amplitude*1e3)  
        
    
    def setValue(self, name,value):
        ''' Set an parameter or value.
        
        \param [in] name the name of the parameter.
        \param [in] value the value of the parameter.
        '''
        self.executeRemoteCommand(name + "=" + str(value))
        
    
    def setNumberOfPeriods(self, number_of_periods):
        ''' Sets the number of periods to average for one impedance measurement.
        
        \param [in] number_of_periods the number of periods / waves to average.
        '''
        number_of_periods = round(number_of_periods)
        if number_of_periods > 100:
            number_of_periods = 100
        
        if number_of_periods < 1:
            number_of_periods = 1
        
        self.executeRemoteCommand("Nw=" + str(number_of_periods))
    
    def getImpedance(self, frequency = None, amplitude = None, number_of_periods = None):
        ''' Measure the impedance.
        
        Measure the impedance with the parameters. If the parameters are omitted the last will be used.
        
        \param [in] frequency the frequency to measure the impedance at.
        \param [in] amplitude the amplitude to measure the impedance with. In Volt if potentiostatic mode or Ampere for galvanostatic mode.
        \param [in] number_of_periods the number of periods / waves to average.
        
        \returns the complex impedance at the measured point.
        '''
        if frequency != None:
            self.setFrequency(frequency)
            
        if amplitude != None:
            self.setAmplitude(amplitude)
            
        if number_of_periods != None:
            self.setNumberOfPeriods(number_of_periods)
        
        reply = self.executeRemoteCommand("IMPEDANCE")
        
        match = re.search("impedance=\\s*(.*?),(.*?):", reply)
        return complex(float(match.group(1)),float(match.group(2)))
    
    """
    The following methods should not be called by the user.
    They are marked with the prefix '_' after the Python convention for proteced.
    """        
    
    def _requestValueAndParseUsingRegexp(self, command, pattern):
        '''
        Constructor
        '''
        reply = self.executeRemoteCommand(command)
        match = re.search(pattern, reply)
        return float(match.group(1))

    