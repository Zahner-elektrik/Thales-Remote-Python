"""
  ____       __                        __    __   __      _ __
 /_  / ___ _/ /  ___  ___ ___________ / /__ / /__/ /_____(_) /__
  / /_/ _ `/ _ \/ _ \/ -_) __/___/ -_) / -_)  '_/ __/ __/ /  '_/
 /___/\_,_/_//_/_//_/\__/_/      \__/_/\__/_/\_\\__/_/ /_/_/\_\
 
Copyright 2022 Zahner-Elektrik GmbH & Co. KG
 
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
from thales_remote.error import ThalesRemoteError
import re
import shutil
import os
 
 
class PotentiostatMode(Enum):
    """
    Working modes for the potentiostat.
    """
    POTMODE_POTENTIOSTATIC = 1
    POTMODE_GALVANOSTATIC = 2
    POTMODE_PSEUDOGALVANOSTATIC = 3
 
 
class ThalesRemoteScriptWrapper(object):
    """
    Wrapper that uses the ThalesRemoteConnection class.
    The commands are explained in the `Remote2-Manual <https://doc.zahner.de/Remote.pdf>`_.
    In the document you can also find a table with error numbers which are returned.
    
    :param remoteConnection: The connection object to the Thales software.
    :type remoteConnection: :class:`~thales_remote.connection.ThalesRemoteConnection`
    """
    undefindedStandardErrorString = ""
 
    def __init__(self, remoteConnection):
        self.remoteConnection = remoteConnection
     
    def getCurrent(self):
        """ Read the measured current from the device.
        
        :returns: The current value.
        :rtype: float
        """
        return self._requestValueAndParseUsingRegexp("CURRENT", "current=\s*(.*?)A?[\r\n]{0,2}$")
     
    def getPotential(self):
        """ Read the measured potential from the device.
        
        :returns: The potential value.
        :rtype: float
        """
        return self._requestValueAndParseUsingRegexp("POTENTIAL", "potential=\s*(.*?)V?[\r\n]{0,2}$")
     
    def setCurrent(self, current):
        """ Set the output current.
        
        :param current: The output current to set.
        :returns: The response string from the device.
        :rtype: string
        """
        return self.setValue("Cset", current)
     
    def setPotential(self, potential):
        """ Set the output potential.
         
        :param potential: The output potential to set.
        :returns: The response string from the device.
        :rtype: string
        """
        return self.setValue("Pset", potential)    
     
    def setMaximumShunt(self, shunt):
        """ Set the maximum shunt for measurement.
         
        Set the maximum shunt index for impedance measurements.
         
        :param shunt: The number of the shunt.
        :returns: The response string from the device.
        :rtype: string
        """
        return self.setValue("Rmax", shunt)
     
    def setMinimumShunt(self, shunt):
        """ Set the minimum shunt for measurement.
         
        Set the minimum shunt index for impedance measurements.
         
        :param shunt: The number of the shunt.
        :returns: The response string from the device.
        :rtype: string
        """
        return self.setValue("Rmin", shunt)
     
    def setShuntIndex(self, shunt):
        """ Set the shunt for measurement.
         
        Fixes the shunt to the passed index.
         
        :param shunt: The number of the shunt.
        :returns: The response string from the device.
        :rtype: string
        """
        self.setMinimumShunt(shunt)
        self.setMaximumShunt(shunt)
        return
         
    def setVoltageRangeIndex(self, vrange):
        """ Set the voltage range for measurement.
        
        If a Zennium, Zennium E, Zennium E4 or a device from the IM6 series is used, the set index must match the U-buffer. If the U-buffer does not match the set value, the measurement is wrong.
        The Zennium pro, Zennium X and Zennium XC series automatically change the range.
         
        :param vrange: The number of the voltage range.
        :returns: The response string from the device.
        :rtype: string
        """
        return self.setValue("Potrange", vrange)
         
    def selectPotentiostat(self, device):
        """ Set the device for output.
        
        Device which is to be selected, on which the settings are output.
        First, the device must be selected.
        Only then can devices other than the internal main potentiostat be configured.
        
        :param device: Number of the device. 0 = Main. 1 = EPC channel 1 and so on.
        :returns: The response string from the device.
        :rtype: string
        """
        return self.setValue("DEV%", device)
    
    def switchToSCPIControl(self):
        """ Change away from operation as EPC device to SCPI operation.
        
        This command works only with external potentiostats of the latest generation PP212, PP222, PP242 and XPOT2.
        After this command they are no longer accessible with the EPC interface.
        Then you can connect to the potentiostat with USB via the Comports.
        The change back to EPC operation is also done explicitly from the USB side.
        
        :returns: The response string from the device.
        :rtype: string
        """
        return self.executeRemoteCommand("SETUSB")
     
    def getSerialNumber(self):
        """ Get the serial number of the active device.
        
        Active device ist the device selected with :func:`~thales_remote.script_wrapper.ThalesRemoteScriptWrapper.selectPotentiostat`.
        
        :returns: The device serial number.
        :rtype: string
        """
        reply = self.executeRemoteCommand("ALLNUM")
        match = re.search("(.*);(.*);([a-zA-Z]*)", reply)
        return match.group(2)
     
    def getDeviceInformation(self):
        """ Get the name and serial number of the active device.
         
        :returns: Returns a tuple with the information about the selected potentiostat. (Name, Serialnumber).
        """
        reply = self.executeRemoteCommand("DEVINF")
        match = re.search("(.*);(.*);(.*);([0-9]*)", reply)
        return match.group(3), match.group(4)
    
    def getSetup(self):
        return self.executeRemoteCommand("SENDSETUP")
     
    def getDeviceName(self):
        """ Get the name of the active device.
         
        :returns: The device name.
        :rtype: string
        """
        reply = self.executeRemoteCommand("ALLNUM")
        match = re.search("(.*);(.*);([a-zA-Z]*)", reply)
        return match.group(3)
    
    def calibrateOffsets(self):
        """ Perform offset calibration on the device.
        
        When the instrument has warmed up for about 30 minutes,
        this command can be used to perform the offset calibration again.
        
        :returns: The response string from the device.
        :rtype: string
        """
        return self.executeRemoteCommand("CALOFFSETS")
     
    def enablePotentiostat(self, enabled=True):
        """ Switch the potentiostat on or off.
         
        :param enabled: Switches the potentiostat on if true and off if false.
        :returns: The response string from the device.
        :rtype: string
        """
        if enabled:
            reply = self.executeRemoteCommand("Pot=-1")
        else:
            reply = self.executeRemoteCommand("Pot=0")
        return reply
             
    def disablePotentiostat(self):
        """ Switch the potentiostat off.
         
        :returns: The response string from the device.
        :rtype: string
        """
        return self.enablePotentiostat(False)
     
    def setPotentiostatMode(self, potentiostatMode):
        """ Set the coupling of the potentiostat.
         
        This can be PotentiostatMode.POTMODE_POTENTIOSTATIC or PotentiostatMode.POTMODE_GALVANOSTATIC or
        PotentiostatMode.POTMODE_PSEUDOGALVANOSTATIC.
        
        :param potentiostatMode: The coupling of the potentiostat
        :type potentiostatMode: :class:`~thales_remote.script_wrapper.PotentiostatMode`
        :returns: The response string from the device.
        :rtype: string
        """
        if potentiostatMode == PotentiostatMode.POTMODE_POTENTIOSTATIC:
            command = "Gal=0:GAL=0"
        elif potentiostatMode == PotentiostatMode.POTMODE_GALVANOSTATIC:
            command = "Gal=-1:GAL=1"
        elif potentiostatMode == PotentiostatMode.POTMODE_PSEUDOGALVANOSTATIC:
            command = "Gal=0:GAL=-1"
        else:
            return ""
        return self.executeRemoteCommand(command)
         
    def enableRuleFileUsage(self, enable=True):
        """ Enable the usage of a rule file.
        
        If the usage of the rule file is activated all the parameters required
        for the EIS, CV, and/or IE are taken from the rule file.
        The exact usage can be found in the remote manual.
        
        :param potentiostatMode: Enable the state of rule file usage.
        :returns: The response string from the device.
        :rtype: string
        """
        if enable == True:
            enable = 1
        else:
            enable = 0
        return self.setValue("UseRuleFile", enable)
     
    def disableRuleFileUsage(self):
        """ Disable the usage of a rule file.
         
        :returns: The response string from the device.
        :rtype: string
        """
        return self.enableRuleFileUsage(False)
     
    def setupPAD4(self, card, channel, state):
        """ Setting a channel of a PAD4 card for an EIS measurement.
                
        :param card: The number of the card starting at 1 and up to 4.
        :type card: int
        :param channel: The channel of the card starting at 1 and up to 4.
        :type channel: int
        :param state: If state = 1 the channel is switched on else switched off.
        :type state: int
        :returns: The response string from the device.
        :rtype: string
        """
        command = "PAD4=" + str(card) + ";"
        command = command + str(channel) + ";"
        if state == 1:
            command = command + "1"
        else:
            command = command + "0"
        reply = self.executeRemoteCommand(command)
        
        if reply.find("ERROR") >= 0:
            raise ThalesRemoteError(reply.rstrip("\r") + ThalesRemoteScriptWrapper.undefindedStandardErrorString)
        return reply
     
    def enablePAD4(self, state=True):
        """ Switching on the set PAD4 channels.
        
        The files of the measurement results with PAD4 are numbered consecutively.
        The lowest number is the main channel of the potentiostat.
        
        :param state: If state = True PAD4 channels are enabled.
        :returns: The response string from the device.
        :rtype: string
        """
        if state == True:
            state = 1
        else:
            state = 0
        return self.setValue("PAD4ENA", state)
     
    def disablePAD4(self):
        """ Switching off the set PAD4 channels.
        
        :returns: The response string from the device.
        :rtype: string
        """
        return self.enablePAD4(False)
     
    def readPAD4Setup(self):
        """ Read the set parameters.
        
        Reading the set PAD4 configuration.
        
        :returns: The response string from the device.
        :rtype: string
        """
        reply = self.executeRemoteCommand("SENDPAD4SETUP")
        if reply.find("ERROR") >= 0:
            raise ThalesRemoteError(reply.rstrip("\r") + ThalesRemoteScriptWrapper.undefindedStandardErrorString)
        return reply
         
    """
    Section with settings for single impedance and EIS measurements.
    """

    def setFrequency(self, frequency):
        """ Set the output frequency for single frequency impedance.
        
        :param frequency: The output frequency for Impedance measurement to set.
        :returns: The response string from the device.
        :rtype: string
        """
        return self.setValue("Frq", frequency)  
     
    def setAmplitude(self, amplitude):
        """ Set the output amplitude
        
        :param amplitude: The output amplitude for Impedance measurement to set in Volt or Ampere.
        :returns: The response string from the device.
        :rtype: string
        """
        return self.setValue("Ampl", amplitude * 1e3)  
     
    def setNumberOfPeriods(self, number_of_periods):
        """ Set the number of periods to average for one impedance measurement.
        
        :param number_of_periods: The number of periods / waves to average.
        :returns: The response string from the device.
        :rtype: string
        """
        number_of_periods = round(number_of_periods)
        if number_of_periods > 100:
            number_of_periods = 100
         
        if number_of_periods < 1:
            number_of_periods = 1
         
        return self.setValue("Nw", number_of_periods)
     
    def setUpperFrequencyLimit(self, frequency):
        """ Set the upper frequency limit for EIS measurements.
        
        :param frequency: The upper frequency limit.
        :returns: The response string from the device.
        :rtype: string
        """
        return self.setValue("Fmax", frequency)
     
    def setLowerFrequencyLimit(self, frequency):
        """ Set the lower frequency limit for EIS measurements.
        
        :param frequency: The lower frequency limit.
        :returns: The response string from the device.
        :rtype: string
        """
        return self.setValue("Fmin", frequency)
     
    def setStartFrequency(self, frequency):
        """ Set the start frequency for EIS measurements.
        
        :param frequency: The start frequency.
        :returns: The response string from the device.
        :rtype: string
        """
        return self.setValue("Fstart", frequency)
     
    def setUpperStepsPerDecade(self, steps):
        """ Set the number of steps per decade in frequency range above 66 Hz for EIS measurements.
                
        :param steps: The number of steps per decade.
        :returns: The response string from the device.
        :rtype: string
        """
        return self.setValue("dfm", steps)
     
    def setLowerStepsPerDecade(self, steps):
        """ Set the number of steps per decade in frequency range below 66 Hz for EIS measurements.
        
        :param steps: The number of steps per decade.
        :returns: The response string from the device.
        :rtype: string
        """
        return self.setValue("dfl", steps)
     
    def setUpperNumberOfPeriods(self, periods):
        """ Set the number of periods to measure in frequency range above 66 Hz for EIS measurements.
        Must be greater than :func:`~thales_remote.script_wrapper.ThalesRemoteScriptWrapper.setLowerNumberOfPeriods`.
        
        :param periods: The number of periods.
        :returns: The response string from the device.
        :rtype: string
        """
        return self.setValue("Nws", periods)
     
    def setLowerNumberOfPeriods(self, periods):
        """ Set the number of periods to measure  in frequency range below 66 Hz for EIS measurements.
        Must be smaller than :func:`~thales_remote.script_wrapper.ThalesRemoteScriptWrapper.setUpperNumberOfPeriods`.
        
        :param periods: The number of periods.
        :returns: The response string from the device.
        :rtype: string
        """
        return self.setValue("Nwl", periods)
     
    def setScanStrategy(self, strategy):
        """ Set the scan strategy for EIS measurements.
        
        strategy = "single": single sine.
        strategy = "multi": multi sine.
        strategy = "table": frequency table.
        
        :param strategy: The scan for EIS measurements.
        :type strategy: string
        :returns: The response string from the device.
        :rtype: string
        """
        if strategy == "multi":
            strategy = 1
        elif strategy == "table":
            strategy = 2
        else:
            strategy = 0
        return self.setValue("ScanStrategy", strategy)
     
    def setScanDirection(self, direction):
        """ Set the scan direction for EIS measurements.
        
        direction = "startToMax": Scan at first from start to maximum frequency.
        direction = "startToMin": Scan at first from start to lower frequency.
        
        :param direction: The scan direction for EIS measurements.
        :type direction: string
        :returns: The response string from the device.
        :rtype: string  
        """
        if direction == "startToMin":
            direction = 1
        else:
            direction = 0
        return self.setValue("ScanDirection", direction)
     
    def getImpedance(self, frequency=None, amplitude=None, number_of_periods=None):
        """ Measure the impedance.
        
        Measure the impedance with the parameters. If the parameters are omitted the last will be used.
        
        \param [in] frequency the frequency to measure the impedance at.
        \param [in] amplitude the amplitude to measure the impedance with. In Volt if potentiostatic mode or Ampere for galvanostatic mode.
        \param [in] number_of_periods the number of periods / waves to average.
        
        :param frequency: The frequency to measure the impedance at.
        :param amplitude: The amplitude to measure the impedance with. In Volt if potentiostatic mode or Ampere for galvanostatic mode.
        :param number_of_periods: The number of periods / waves to average.
        :returns: The complex impedance at the measured point.
        :rtype: complex
        """
        if frequency != None:
            self.setFrequency(frequency)
             
        if amplitude != None:
            self.setAmplitude(amplitude)
             
        if number_of_periods != None:
            self.setNumberOfPeriods(number_of_periods)
         
        reply = self.executeRemoteCommand("IMPEDANCE")
         
        if reply.find("ERROR") >= 0:
            raise ThalesRemoteError(reply.rstrip("\r") + ThalesRemoteScriptWrapper.undefindedStandardErrorString)
        match = re.search("impedance=\\s*(.*?),\\s*(.*?)$", reply)
        return complex(float(match.group(1)), float(match.group(2)))
     
    def setEISNaming(self, naming):
        """ Set the EIS measurement naming rule.
        
        naming = "dateTime": extend the :func:`~thales_remote.script_wrapper.ThalesRemoteScriptWrapper.setEISOutputFileName` with date and time.
        naming = "counter": extend the :func:`~thales_remote.script_wrapper.ThalesRemoteScriptWrapper.setEISOutputFileName` with an sequential number.
        naming = "individual": the file is named like :func:`~thales_remote.script_wrapper.ThalesRemoteScriptWrapper.setEISOutputFileName`.
        
        :param naming: The EIS measurement naming rule.
        :type naming: string
        :returns: The response string from the device.
        :rtype: string  
        """
        if naming == "dateTime":
            naming = 0
        elif naming == "individual":
            naming = 2
        else:
            naming = 1
        return self.setValue("EIS_MOD", naming)
     
    def setEISCounter(self, number):
        """ Set the current number of EIS measurement for filename.
        
        Current number for the file name for EIS measurements which is used next and then incremented.
        
        :param number: The next measurement number.
        :returns: The response string from the device.
        :rtype: string
        """
        return self.setValue("EIS_NUM", number)
     
    def setEISOutputPath(self, path):
        """ Set the path where the EIS measurements should be stored.
        
        The results must be stored on the C hard disk.
        If an error occurs test an alternative path or c:\THALES\temp.
        The directory must exist.
        
        :param path: The path to the directory.
        :type path: string
        :returns: The response string from the device.
        :rtype: string
        """
        path = path.lower()  # c: has to be lower case
        return self.setValue("EIS_PATH", path)
     
    def setEISOutputFileName(self, name):
        """ Set the basic EIS output filename.
        
        The basic name of the file, which is extended by a sequential number or the date and time.
        Only numbers, underscores and letters from a-Z may be used.
        
        If the name is set to "individual", the file with the same name must not yet exist.
        Existing files are not overwritten.
        
        :param name: The basic name of the file.
        :type name: string
        :returns: The response string from the device.
        :rtype: string
        """
        return self.setValue("EIS_ROOT", name)
         
    def measureEIS(self):
        """ Measure EIS.
        
        For the measurement all parameters must be specified before.
        
        :returns: The response string from the device.
        :rtype: string
        """
        reply = self.executeRemoteCommand("EIS")
        if reply.find("ERROR") >= 0:
            raise ThalesRemoteError(reply.rstrip("\r") + ThalesRemoteScriptWrapper.undefindedStandardErrorString)
        return reply
         
    """
    Section with settings for CV measurements.
    """
 
    def setCVStartPotential(self, potential):
        """ Set the start potential of a CV measurment.
        
        :param potential: The start potential.
        :returns: The response string from the device.
        :rtype: string  
        """
        return self.setValue("CV_Pstart", potential)
     
    def setCVUpperReversingPotential(self, potential):
        """ Set the upper reversal potential of a CV measurement.
        
        :param potential: The upper reversal potential.
        :returns: The response string from the device.
        :rtype: string
        """
        return self.setValue("CV_Pupper", potential)
     
    def setCVLowerReversingPotential(self, potential):
        """ Set the lower reversal potential of a CV measurement.
        
        :param potential: The lower reversal potential.
        :returns: The response string from the device.
        :rtype: string
        """
        return self.setValue("CV_Plower", potential)
     
    def setCVEndPotential(self, potential):
        """ Set the end potential of a CV measurment.
        
        :param potential: The end potential.
        :returns: The response string from the device.
        :rtype: string
        """
        return self.setValue("CV_Pend", potential)
     
    def setCVStartHoldTime(self, time):
        """ Setting the holding time at the start potential.
         
        The time must be given in seconds.
        
        :param time: The waiting time at start potential in s.
        :returns: The response string from the device.
        :rtype: string
        """
        return self.setValue("CV_Tstart", time)
     
    def setCVEndHoldTime(self, time):
        """ Setting the holding time at the end potential.
         
        The time must be given in seconds.
        
        :param time: The waiting time at end potential in s.
        :returns: The response string from the device.
        :rtype: string
        """
        return self.setValue("CV_Tend", time)
     
    def setCVScanRate(self, scanRate):
        """ Set the scan rate.
         
        The scan rate must be specified in V/s.
        
        :param scanRate: The scan rate in V/s.
        :returns: The response string from the device.
        :rtype: string
        """
        return self.setValue("CV_Srate", scanRate)
     
    def setCVCycles(self, cycles):
        """ Set the number of cycles.
        
        At least 0.5 cycles are necessary.
        The number of cycles must be a multiple of 0.5. 3.5 are also possible, for example.
        
        :param cycles: The number of CV cycles, at least 0.5.
        :returns: The response string from the device.
        :rtype: string
        """
        return self.setValue("CV_Periods", cycles)
     
    def setCVSamplesPerCycle(self, samples):
        """ Set the number of measurements per CV cycle.
        
        :param samples: The number of measurments per cycle.
        :returns: The response string from the device.
        :rtype: string
        """
        return self.setValue("CV_PpPer", samples)
     
    def setCVMaximumCurrent(self, current):
        """ Set the maximum current.
        
        The maximum positive current at which the measurement is interrupted.
        
        :param current: The maximum current for measurement in A.
        :returns: The response string from the device.
        :rtype: string
        """
        return self.setValue("CV_Ima", current)
     
    def setCVMinimumCurrent(self, current):
        """ Set the minimum current.
        
        The maximum negative current at which the measurement is interrupted.
        
        :param current: The minimum current for measurement in A.
        :returns: The response string from the device.
        :rtype: string
        """
        return self.setValue("CV_Imi", current)
     
    def setCVOhmicDrop(self, ohmicdrop):
        """ Set the ohmic drop for CV measurement.
        
        :param ohmicdrop: The ohmic drop for measurement.
        :returns: The response string from the device.
        :rtype: string
        """
        return self.setValue("CV_Odrop", ohmicdrop)
     
    def enableCVAutoRestartAtCurrentOverflow(self, state=True):
        """ Automatically restart if current is exceeded.
        
        A new measurement is automatically started with a different
        reverse potential at which the current limit is not exceeded.
        
        :param state: If state = True the auto restart is enabled.
        :returns: The response string from the device.
        :rtype: string
        """
        if state == True:
            state = 1
        else:
            state = 0
        return self.setValue("CV_AutoReStart", state)
     
    def disableCVAutoRestartAtCurrentOverflow(self):
        """ Disable automatically restart if current is exceeded.
        
        :returns: The response string from the device.
        :rtype: string
        """
        return self.enableCVAutoRestartAtCurrentOverflow(False)
     
    def enableCVAutoRestartAtCurrentUnderflow(self, state=True):
        """ Restart automatically if the current drops below the limit.
        
        A new measurement is automatically started with a smaller
        current range than that determined by the minimum and maximum current.
        
        :param state: If state = True the auto restart is enabled.
        :returns: The response string from the device.
        :rtype: string
        """
        if state == True:
            state = 1
        else:
            state = 0
        return self.setValue("CV_AutoScale", state)
     
    def disableCVAutoRestartAtCurrentUnderflow(self):
        """ Disable automatically restart if the current drops below the limit.
        
        :returns: The response string from the device.
        :rtype: string
        """
        return self.enableCVAutoRestartAtCurrentUnderflow(False)
     
    def enableCVAnalogFunctionGenerator(self, state=True):
        """ Switch on the analog function generator (AFG).
        
        The analog function generator can only be used if it was purchased with the device.
        If the device has the AFG function, you will see a button in the CV software to activate this function.
        
        :param state: If state = True the AFG is used.
        :returns: The response string from the device.
        :rtype: string
        """
        if state == True:
            state = 1
        else:
            state = 0
        return self.setValue("CV_AFGena", state)
     
    def disableCVAnalogFunctionGenerator(self):
        """ Disable the analog function generator (AFG).
         
        :returns: The response string from the device.
        :rtype: string
        """
        return self.enableCVAnalogFunctionGenerator(False)
     
    def setCVNaming(self, naming):
        """ Set the CV measurement naming rule.
        
        naming = "dateTime": extend the :func:`~thales_remote.script_wrapper.ThalesRemoteScriptWrapper.setCVOutputFileName` with date and time.
        naming = "counter": extend the :func:`~thales_remote.script_wrapper.ThalesRemoteScriptWrapper.setCVOutputFileName` with an sequential number.
        naming = "individual": the file is named like :func:`~thales_remote.script_wrapper.ThalesRemoteScriptWrapper.setCVOutputFileName`.
        
        :param naming: The CV measurement naming rule.
        :type naming: string
        :returns: The response string from the device.
        :rtype: string  
        """
        if naming == "dateTime":
            naming = 0
        elif naming == "individual":
            naming = 2
        else:
            naming = 1
        return self.setValue("CV_MOD", naming)
     
    def setCVCounter(self, number):
        """ Set the current number of CV measurement for filename.
        
        Current number for the file name for CV measurements which is used next and then incremented.
        
        :param number: The next measurement number
        :returns: The response string from the device.
        :rtype: string
        """
        return self.setValue("CV_NUM", number)
     
    def setCVOutputPath(self, path):
        """ Set the path where the CV measurements should be stored.
        
        The results must be stored on the C hard disk.
        If an error occurs test an alternative path or c:\THALES\temp.
        The directory must exist.
        
        :param path: The path to the directory.
        :returns: The response string from the device.
        :rtype: string
        """
        path = path.lower()  # c: has to be lower case
        return self.setValue("CV_PATH", path)
     
    def setCVOutputFileName(self, name):
        """ Set the basic CV output filename.
        
        The basic name of the file, which is extended by a sequential number or the date and time.
        Only numbers, underscores and letters from a-Z may be used.
        
        If the name is set to "individual", the file with the same name must not yet exist.
        Existing files are not overwritten.
        
        :param name: The basic name of the file.
        :returns: The response string from the device.
        :rtype: string
        """
        return self.setValue("CV_ROOT", name)
     
    def checkCVSetup(self):
        """ Check the set parameters.
        
        With the error number the wrong parameter can be found.
        The error numbers are listed in the Remote2 manual.
        
        :returns: The response string from the device.
        :rtype: string
        """
        reply = self.executeRemoteCommand("CHECKCV")
        if reply.find("ERROR") >= 0:
            raise ThalesRemoteError(reply.rstrip("\r") + ThalesRemoteScriptWrapper.undefindedStandardErrorString)
        return reply
     
    def readCVSetup(self):
        """ Read the set parameters.
        
        After checking with checkCVSetup() the parameters can be read back from the workstation.
        
        :returns: The response string from the device.
        :rtype: string
        """
        reply = self.executeRemoteCommand("SENDCVSETUP")
        if reply.find("ERROR") >= 0:
            raise ThalesRemoteError(reply.rstrip("\r") + ThalesRemoteScriptWrapper.undefindedStandardErrorString)
        return reply
     
    def measureCV(self):
        """ Measure CV.
         
        Before measurement, all parameters must be checked with :func:`~thales_remote.script_wrapper.ThalesRemoteScriptWrapper.checkCVSetup`.
        
        :returns: The response string from the device.
        :rtype: string
        """
        reply = self.executeRemoteCommand("CV")
        if reply.find("ERROR") >= 0:
            raise ThalesRemoteError(reply.rstrip("\r") + ThalesRemoteScriptWrapper.undefindedStandardErrorString)
        return reply
         
    """
    Section with settings for IE measurements.
    Additional informations can be found in the IE manual.
    """
    
    def setIEFirstEdgePotential(self, potential):
        """ Set the first edge potential.
        
        :param potential: The potential of the first edge in V.
        :returns: The response string from the device.
        :rtype: string
        """    
        return self.setValue("IE_EckPot1", potential)
    
    def setIESecondEdgePotential(self, potential):
        """ Set the second edge potential.
        
        :param potential: The potential of the second edge in V.
        :returns: The response string from the device.
        :rtype: string
        """    
        return self.setValue("IE_EckPot2", potential)
    
    def setIEThirdEdgePotential(self, potential):
        """ Set the third edge potential.
        
        :param potential: The potential of the third edge in V.
        :returns: The response string from the device.
        :rtype: string
        """    
        return self.setValue("IE_EckPot3", potential)
    
    def setIEFourthEdgePotential(self, potential):
        """ Set the fourth edge potential.
        
        :param potential: The potential of the fourth edge in V.
        :returns: The response string from the device.
        :rtype: string
        """    
        return self.setValue("IE_EckPot4", potential)
    
    def setIEFirstEdgePotentialRelation(self, relation):
        """ Set the relation of the first edge potential.
        
        relation = "absolute": Absolute relation of the potential.
        relation = "relative": Relative relation of the potential.
        
        :param relation: The relation of the edge potential absolute or relative.
        :returns: The response string from the device.
        :rtype: string
        """
        if relation == "relative":
            relation = -1
        else:
            relation = 0
        return self.setValue("IE_EckPot1rel", relation)
    
    def setIESecondEdgePotentialRelation(self, relation):
        """ Set the relation of the second edge potential.
        
        relation = "absolute": Absolute relation of the potential.
        relation = "relative": Relative relation of the potential.
        
        :param relation: The relation of the edge potential absolute or relative.
        :returns: The response string from the device.
        :rtype: string
        """
        if relation == "relative":
            relation = -1
        else:
            relation = 0
        return self.setValue("IE_EckPot2rel", relation)
    
    def setIEThirdEdgePotentialRelation(self, relation):
        """ Set the relation of the third edge potential.
        
        relation = "absolute": Absolute relation of the potential.
        relation = "relative": Relative relation of the potential.
        
        :param relation: The relation of the edge potential absolute or relative.
        :returns: The response string from the device.
        :rtype: string
        """
        if relation == "relative":
            relation = -1
        else:
            relation = 0
        return self.setValue("IE_EckPot3rel", relation)
    
    def setIEFourthEdgePotentialRelation(self, relation):
        """ Set the relation of the fourth edge potential.
        
        relation = "absolute": Absolute relation of the potential.
        relation = "relative": Relative relation of the potential.
        
        :param relation: The relation of the edge potential absolute or relative.
        :returns: The response string from the device.
        :rtype: string
        """
        if relation == "relative":
            relation = -1
        else:
            relation = 0
        return self.setValue("IE_EckPot4rel", relation)
     
    def setIEPotentialResolution(self, resolution):
        """ Set the potential resolution.
        
        The potential step size for IE measurements in V.
        
        :param relation: The resolution for the measurement in V.
        :returns: The response string from the device.
        :rtype: string
        """
        return self.setValue("IE_Resolution", resolution)
     
    def setIEMinimumWaitingTime(self, time):
        """ Set the minimum waiting time.
        
        The minimum waiting time on each step of the IE measurement.
        This time is at least waited, even if the tolerance abort criteria are met.
        
        :param time: The waiting time in seconds.
        :returns: The response string from the device.
        :rtype: string
        """
        return self.setValue("IE_WZmin", time)
     
    def setIEMaximumWaitingTime(self, time):
        """ Set the maximum waiting time.
        
        The maximum waiting time on each step of the IE measurement.
        After this time the measurement is stopped at this potential
        and continued with the next potential even if the tolerances are not reached.
        
        :param time: The waiting time in seconds.
        :returns: The response string from the device.
        :rtype: string
        """
        return self.setValue("IE_WZmax", time)
     
    def setIERelativeTolerance(self, tolerance):
        """ Set the relative tolerance criteria.
        
        This parameter is only used in sweep mode steady state.
        The relative tolerance to wait in percent.
        The explanation can be found in the IE manual.
        
        :param tolerance: The tolerance to wait until break, 0.01 = 1%.
        :returns: The response string from the device.
        :rtype: string
        """
        return self.setValue("IE_Torel", tolerance)
     
    def setIEAbsoluteTolerance(self, tolerance):
        """ Set the absolute tolerance criteria.
         
        This parameter is only used in sweep mode steady state.
        The absolute tolerance to wait in A.
        The explanation can be found in the IE manual.
        
        :param tolerance: The tolerance to wait until break, 0.01 = 1%.
        :returns: The response string from the device.
        :rtype: string
        """
        return self.setValue("IE_Toabs", tolerance)
     
    def setIEOhmicDrop(self, ohmicdrop):
        """ Set the ohmic drop for IE measurement.
        
        :param ohmicdrop: The ohmic drop for measurement.
        :returns: The response string from the device.
        :rtype: string
        """
        return self.setValue("IE_Odrop", ohmicdrop)
     
    def setIESweepMode(self, mode):
        """ Set the sweep mode.
         
        The explanation of the modes can be found in the IE manual.
        mode="steady state"
        mode="fixed sampling"
        mode="dynamic scan"
        
        :param mode: The sweep mode for measurement.
        :returns: The response string from the device.
        :rtype: string
        """
        if mode == "steady state":
            mode = 0
        elif mode == "dynamic scan":
            mode = 2        
        else:
            mode = 1
        return self.setValue("IE_SweepMode", mode)
     
    def setIEScanRate(self, scanRate):
        """ Set the scan rate.
        
        This parameter is only used in sweep mode dynamic scan.
        The scan rate must be specified in V/s.
        
        :param scanRate: The scan rate in V/s.
        :returns: The response string from the device.
        :rtype: string
        """
        return self.setValue("IE_Srate", scanRate)
     
    def setIEMaximumCurrent(self, current):
        """ Set the maximum current.
        
        The maximum positive current at which the measurement is interrupted.
        
        :param current: The maximum current for measurement in A.
        :returns: The response string from the device.
        :rtype: string
        """
        return self.setValue("IE_Ima", current)
     
    def setIEMinimumCurrent(self, current):
        """ Set the minimum current.
         
        The maximum negative current at which the measurement is interrupted.
        
        :param current: The minimum current for measurement in A.
        :returns: The response string from the device.
        :rtype: string
        """
        return self.setValue("IE_Imi", current)
     
    def setIENaming(self, naming):
        """ Set the IE measurement naming rule.
         
        naming = "dateTime": extend the :func:`~thales_remote.script_wrapper.ThalesRemoteScriptWrapper.setIEOutputFileName` with date and time.
        naming = "counter": extend the :func:`~thales_remote.script_wrapper.ThalesRemoteScriptWrapper.setIEOutputFileName` with an sequential number.
        naming = "individual": the file is named like :func:`~thales_remote.script_wrapper.ThalesRemoteScriptWrapper.setIEOutputFileName`.
        
        :param naming: The IE measurement naming rule.
        :type naming: string
        :returns: The response string from the device.
        :rtype: string
        """
        if naming == "dateTime":
            naming = 0
        elif naming == "individual":
            naming = 2
        else:
            naming = 1
        return self.setValue("IE_MOD", naming)
     
    def setIECounter(self, number):
        """ Set the current number of IE measurement for filename.
        
        Current number for the file name for EIS measurements which is used next and then incremented.
        
        :param number: The next measurement number.
        :returns: The response string from the device.
        :rtype: string
        """
        return self.setValue("IE_NUM", number)
     
    def setIEOutputPath(self, path):
        """ Set the path where the IE measurements should be stored.
        
        The results must be stored on the C hard disk. If an error occurs test an alternative path or c:\THALES\temp.
        The directory must exist.
        
        :param path: The path to the directory.
        :returns: The response string from the device.
        :rtype: string
        """
        path = path.lower()  # c: has to be lower case
        return self.setValue("IE_PATH", path)
     
    def setIEOutputFileName(self, name):
        """ Set the basic IE output filename.
        
        The basic name of the file, which is extended by a sequential number or the date and time.
        Only numbers, underscores and letters from a-Z may be used.
        
        If the name is set to "individual", the file with the same name must not yet exist.
        Existing files are not overwritten.
        
        :param name: The basic name of the file.
        :returns: The response string from the device.
        :rtype: string
        """
        return self.setValue("IE_ROOT", name)
     
    def checkIESetup(self):
        """ Check the set parameters.
         
        With the error number the wrong parameter can be found.
        The error numbers are listed in the Remote2 manual.
        
        :returns: The response string from the device.
        :rtype: string
        """
        reply = self.executeRemoteCommand("CHECKIE")
        if reply.find("ERROR") >= 0:
            raise ThalesRemoteError(reply.rstrip("\r") + ThalesRemoteScriptWrapper.undefindedStandardErrorString)
        return reply
     
    def readIESetup(self):
        """ Read the set parameters.
         
        After checking with :func:`~thales_remote.script_wrapper.ThalesRemoteScriptWrapper.checkIESetup` the parameters can be read back from the workstation.
        
        :returns: The response string from the device.
        :rtype: string
        """
        reply = self.executeRemoteCommand("SENDIESETUP")
        if reply.find("ERROR") >= 0:
            raise ThalesRemoteError(reply.rstrip("\r") + ThalesRemoteScriptWrapper.undefindedStandardErrorString)
        return reply
     
    def measureIE(self):
        """ Measure IE.
         
        Before measurement, all parameters must be checked with :func:`~thales_remote.script_wrapper.ThalesRemoteScriptWrapper.checkIESetup`.
        
        :returns: The response string from the device.
        :rtype: string
        """
        reply = self.executeRemoteCommand("IE")
        if reply.find("ERROR") >= 0:
            raise ThalesRemoteError(reply.rstrip("\r") + ThalesRemoteScriptWrapper.undefindedStandardErrorString)
        return reply
     
    """
    Section of remote functions for the sequencer.
 
    With the sequencer DC profiles can be described textually.
    For instructions on how the sequencer file is structured, please refer to the manual of the sequencer.
    """
 
    def selectSequence(self, number):
        """ Select the sequence to run with runSequence().
        
        The sequences must be stored under "C:\THALES\script\sequencer\sequences".
        Sequences from 0 to 9 can be created.
        These must have the names from "sequence00.seq" to "sequence09.seq".
        
        :param number: The number of the sequence.
        :returns: The response string from the device.
        :rtype: string
        """
        reply = self.executeRemoteCommand("SELSEQ=" + str(number))
        if(reply != "SELOK\r"):
            raise ThalesRemoteError(reply.rstrip("\r") + " The selected sequence does not exist.")
        return reply
     
    def setSequenceNaming(self, naming):
        """ Set the sequence measurement naming rule.
        
        naming = "dateTime": extend the setSequenceOutputFileName(name) with date and time.
        naming = "counter": extend the setSequenceOutputFileName(name) with an sequential number.
        naming = "individual": the file is named like setEISOutputFileName(name).
        
        :param naming: The naming rule.
        :type naming: string
        :returns: The response string from the device.
        :rtype: string
        """
        if naming == "dateTime":
            naming = 0
        elif naming == "individual":
            naming = 2
        else:
            naming = 1
        return self.setValue("SEQ_MOD", naming)
     
    def setSequenceCounter(self, number):
        """ Set the current number of sequence measurement for filename.
        
        Current number for the file name for EIS measurements which is used next and then incremented.
        
        :param number: The next measurement number
        :returns: The response string from the device.
        :rtype: string
        """
        return self.setValue("SEQ_NUM", number)
     
    def setSequenceOutputPath(self, path):
        """ Set the path where the sequence measurements should be stored.
        
        The results must be stored on the C hard disk. If an error occurs test an alternative path or c:\THALES\temp.
        The directory must exist.
        
        :param path: The path to the directory.
        :returns: The response string from the device.
        :rtype: string
        """
        path = path.lower()  # c: has to be lower case
        return self.setValue("SEQ_PATH", path)
     
    def setSequenceOutputFileName(self, name):
        """ Set the basic sequence output filename.
        
        The basic name of the file, which is extended by a sequential number or the date and time.
        Only numbers, underscores and letters from a-Z may be used.
        
        If the name is set to "individual", the file with the same name must not yet exist.
        Existing files are not overwritten.
        
        :param name: The basic name of the file.
        :returns: The response string from the device.
        :rtype: string
        """
        return self.setValue("SEQ_ROOT", name)
     
    def runSequence(self):
        """ Run the selected sequence.
         
        This command executes the selected sequence between 0 and 9.
        
        :returns: The response string from the device.
        :rtype: string
        """
        reply = self.executeRemoteCommand("DOSEQ")
        if(reply != "SEQ DONE\r"):
            raise ThalesRemoteError(reply.rstrip("\r") + ThalesRemoteScriptWrapper.undefindedStandardErrorString)
        return reply
     
    def runSequenceFile(self, filepath, sequence_folder="C:/THALES/script/sequencer/sequences", sequence_number=9):
        """ Run the sequence at filepath.
        
        The file from the specified path is copied as sequence sequence_number=9 to the correct location in the Thales directory and then selected and executed.
        The default sequence number is 9 and does not need to be changed.
        The old sequence sequence_number is overwritten.
        
        The variable sequence_folder is ONLY NECESSARY if python is running on ANOTHER COMPUTER like the one connected to the Zennium.
        For this the controlling computer must have access to the hard disk of the computer with the Zennium to access the THALES folder.
        In this case the path to the sequences folder in sequence_folder must be set to "C:/THALES/script/sequencer/sequences" on the computer with the zennium.
        
        :param filepath: Filepath of the sequence.
        :type filepath: string
        :param sequence_folder: The filepath to the THALES sequence folder.
            Does not normally need to be transferred and changed. Explanation see in the text before.
        :type sequence_folder: string
        :param sequence_number: The number in the THALES sequence directory.
            Does not normally need to be transferred and changed.
        :type sequence_number: int
        :returns: The response string from the device.
        :rtype: string
        """
        if sequence_number > 9 or sequence_number < 0:
            raise ThalesRemoteError("Wrong sequence number.")
         
        sequence_folder = sequence_folder + "/sequence{:02d}.seq".format(sequence_number)
         
        if filepath.find(".seq") < 0:
            raise ThalesRemoteError("Wrong sequence file extension.")
        if os.path.exists(sequence_folder):
            os.remove(sequence_folder)
        shutil.copy2(filepath, sequence_folder)
         
        self.selectSequence(sequence_number)
        return self.runSequence() 
     
    def setValue(self, name, value):
        """ Set an Remote2 parameter or value.
        
        :param name: Name of the Remote2 parameter.
        :type name: string
        :param value: The value of the parameter.
        :returns: The response string from the device.
        :rtype: string
        """
        if isinstance(value, float):
            value = "{:.16e}".format(value)        
        
        reply = self.executeRemoteCommand(name + "=" + str(value))
        if reply.find("ERROR") >= 0:
            raise ThalesRemoteError(reply.rstrip("\r") + ThalesRemoteScriptWrapper.undefindedStandardErrorString)
        return reply
     
    def executeRemoteCommand(self, command):
        """ Directly execute a query to Remote Script.
        
        :param command: The command query string, e.g. "IMPEDANCE" or "Pset=0".
        :returns: The response string from the device.
        :rtype: string
        """
        return self.remoteConnection.sendStringAndWaitForReplyString("1:" + command + ":", 2)
     
    def forceThalesIntoRemoteScript(self):
        """ Prompts Thales to start the Remote Script.
         
        Will switch a running Thales from anywhere like the main menu after
        startup to running measurements into Remote Script so it can process
        further requests.
         
        .. note::
            This happens rather quickly if Thales is idle in main menu but
            may take some time if it's performing an EIS measurement or doing
            something else. For high stability applications 20 seconds would
            probably be a save bet.
        
        :returns: The response string from the device.
        :rtype: string
        """
        self.remoteConnection.sendStringAndWaitForReplyString(f"3,{self.remoteConnection.getConnectionName()},0,OFF", 128)
        return self.remoteConnection.sendStringAndWaitForReplyString(f"2,{self.remoteConnection.getConnectionName()}", 128)
     
    def getWorkstationHeartBeat(self, timeout=None):
        """ Query the heartbeat time from the Term software for the workstation and the Thales software accordingly.
        
        The complete documentation can be found in the `DevCli-Manual <https://doc.zahner.de/DevCli.pdf>`_ Page 8.
         
        
        The timeout is not set by default and the command blocks indefinitely.
        However, a time in seconds can optionally be specified for the timeout.
        When the timeout expires, an exception is thrown by the socket.
        
        :param timeout: The time in seconds in which the term must provide the answer.
        :returns: The HeartBeat time in milli seconds.
        """
        retval = self.remoteConnection.sendStringAndWaitForReplyString(f"1,{self.remoteConnection.getConnectionName()}", 128, timeout)
        return retval.split(",")[2]
    
    def getSerialNumberFromTerm(self):
        """ Get the serial number of the workstation via the Term software.
        
        The serial number of the active potentiostat with EPC devices can be read with the
        :func:`~thales_remote.script_wrapper.ThalesRemoteScriptWrapper.getSerialNumber` function.
        This function returns only the serial number of the workstation, which is determined by the Term software.
        
        :returns: The workstation serial number.
        :rtype: string
        """
        retval = self.remoteConnection.sendStringAndWaitForReplyString(f"3,{self.remoteConnection.getConnectionName()},6", 128)
        return retval.split(",")[2]       
    
    def getTermIsActive(self, timeout=2):
        """ Check if the Term still responds to requests.
        
        Whether the term is still active is checked by sending a heartbeat command.
        If the term does not respond after the timeout, an exception is thrown and this is caught with the except block.
        The time returned by getWorkstationHeartBeat is not relevant,
        it is only important that a response was returned within the time.
        
        Afterwards False is returned if the exception was resolved.
        Once False is returned, the connection to the term MUST be completely re-established with
        connectToTerm and forceThalesIntoRemoteScript.
        The workstation must also be reset. To re-establish a controlled state.
        
        :param timeout: Time in seconds in which the term must provide the answer, default 2 seconds.
        :returns: True or False if the Term is Active.
        :rtype: bool
        """
        active = True
        try:
            self.remoteConnection.sendStringAndWaitForReplyString(f"1,{self.remoteConnection.getConnectionName()}", 128, timeout)
        except:
            active = False
        return active
    
    """
    The following methods should not be called by the user.
    They are marked with the prefix '_' after the Python convention for proteced.
    """
    def _requestValueAndParseUsingRegexp(self, command, pattern):
        reply = self.executeRemoteCommand(command)
        if reply.find("ERROR") >= 0:
            raise ThalesRemoteError(reply.rstrip("\r") + ThalesRemoteScriptWrapper.undefindedStandardErrorString)
        match = re.search(pattern, reply)
        return float(match.group(1))




