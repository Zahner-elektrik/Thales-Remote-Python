"""
  ____       __                        __    __   __      _ __
 /_  / ___ _/ /  ___  ___ ___________ / /__ / /__/ /_____(_) /__
  / /_/ _ `/ _ \/ _ \/ -_) __/___/ -_) / -_)  '_/ __/ __/ /  '_/
 /___/\_,_/_//_/_//_/\__/_/      \__/_/\__/_/\_\\__/_/ /_/_/\_\
 
Copyright 2023 Zahner-Elektrik GmbH & Co. KG
 
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
import shutil
import os
from typing import Optional, Union, Any

from thales_remote.error import ThalesRemoteError
from thales_remote.connection import ThalesRemoteConnection


class PotentiostatMode(Enum):
    """
    working modes for the potentiostat
    """

    POTMODE_POTENTIOSTATIC = 1
    POTMODE_GALVANOSTATIC = 2
    POTMODE_PSEUDOGALVANOSTATIC = 3


class ScanStrategy(Enum):
    """
    options for the EIS scan strategy.

    * SINGLE_SINE: single frequency sweep
    * MULTI_SINE: multi sine
    * TABLE: frequency table
    """

    SINGLE_SINE = 0
    MULTI_SINE = 1
    TABLE = 2

    @classmethod
    def stringToEnum(cls, string: str):
        stringEnumMap = {
            "single": ScanStrategy.SINGLE_SINE,
            "multi": ScanStrategy.MULTI_SINE,
            "table": ScanStrategy.TABLE,
        }
        if not string in stringEnumMap:
            raise ValueError("invalid string: " + string)
        return stringEnumMap.get(string)


class ScanDirection(Enum):
    """
    set the scan direction for EIS measurements.

    * START_TO_MAX: from the start frequency to the maximum frequency
    * START_TO_MIN: from the start to the minimum frequency
    """

    START_TO_MAX = 0
    START_TO_MIN = 1

    @classmethod
    def stringToEnum(cls, string: str):
        stringEnumMap = {
            "startToMax": ScanDirection.START_TO_MAX,
            "startToMin": ScanDirection.START_TO_MIN,
        }
        if not string in stringEnumMap:
            raise ValueError("invalid string: " + string)
        return stringEnumMap.get(string)


class FileNaming(Enum):
    """
    options for the file names in Thales.

    * DATE_TIME: naming with time stamp
    * INDIVIDUAL: only the specified filename without extension
    * COUNTER: consecutive number
    """

    DATE_TIME = 0
    COUNTER = 1
    INDIVIDUAL = 2

    @classmethod
    def stringToEnum(cls, string: str):
        stringEnumMap = {
            "dateTime": FileNaming.DATE_TIME,
            "individual": FileNaming.INDIVIDUAL,
            "counter": FileNaming.COUNTER,
        }
        if not string in stringEnumMap:
            raise ValueError("invalid string: " + string)
        return stringEnumMap.get(string)


class Pad4Mode(Enum):
    """
    options for the PAD4 operating mode.

    All channels can be either voltage or current. Individual setting is not possible.
    """

    VOLTAGE = 0
    CURRENT = 1


class ThalesRemoteScriptWrapper(object):
    """
    Wrapper that uses the ThalesRemoteConnection class.
    The commands are explained in the `Remote2-Manual <https://doc.zahner.de/manuals/remote2.pdf>`_.
    In the document you can also find a table with error numbers which are returned.

    :param remoteConnection: The connection object to the Thales software.
    """

    undefindedStandardErrorString: str = ""
    _remote_connection: ThalesRemoteConnection

    def __init__(self, remoteConnection: ThalesRemoteConnection):
        self._remote_connection = remoteConnection

    def getCurrent(self) -> float:
        """
        read the measured current from the device

        :returns: the measured current value
        """
        return self._requestValueAndParseUsingRegexp(
            "CURRENT", "current=\s*(.*?)A?[\r\n]{0,2}$"
        )

    def getPotential(self) -> float:
        """
        fead the measured potential from the device

        :returns: the measured potential value
        """
        return self._requestValueAndParseUsingRegexp(
            "POTENTIAL", "potential=\s*(.*?)V?[\r\n]{0,2}$"
        )

    def setCurrent(self, current: float) -> str:
        """
        set the output current

        :param current: the output current to set
        :returns: response string from the device
        """
        return self.setValue("Cset", current)

    def setPotential(self, potential: float) -> str:
        """
        set the output potential

        :param potential: the output potential to set
        :returns: response string from the device
        """
        return self.setValue("Pset", potential)

    def setVoltage(self, potential) -> str:
        """
        set the output potential

        :param potential: the output potential to set
        :returns: response string from the device
        """
        return self.setPotential(potential)

    def setMaximumShunt(self, shunt: int) -> str:
        """
        set the maximum shunt index for measurement

        Set the maximum shunt index for impedance measurements.

        :param shunt: the number of the shunt
        :returns: response string from the device
        """
        return self.setValue("Rmax", shunt)

    def setMinimumShunt(self, shunt) -> str:
        """
        set the minimum shunt for measurement

        Set the minimum shunt index for impedance measurements.

        :param shunt: index of the shunt to set
        :returns: response string from the device
        """
        return self.setValue("Rmin", shunt)

    def setShuntIndex(self, shunt: int) -> None:
        """
        set the shunt index for measurement

        Fixes the shunt to the passed index.

        :param shunt: The number of the shunt.
        :returns: reponse string from the device
        """
        self.setMinimumShunt(shunt)
        self.setMaximumShunt(shunt)
        return

    def setVoltageRangeIndex(self, vrange: int) -> str:
        """
        set the voltage range for measurement

        If a Zennium, Zennium E, Zennium E4 or a device from the IM6 series is
        used, the set index must match the U-buffer. If the U-buffer does not
        match the set value, the measurement is wrong.
        The Zennium pro, Zennium X and Zennium XC series automatically change
        the range.

        :param vrange: index of the voltage range
        :returns: response string from the device
        """
        return self.setValue("Potrange", vrange)

    def selectPotentiostat(self, device: int) -> str:
        """
        select device onto which all subsequent calls to set* methods are forwarded

        First, the device must be selected. Only then can devices other than
        the internal main potentiostat be configured.

        :param device: Number of the device. 0 = Main. 1 = EPC channel 1 and so on.
        :returns: reponse string from the device
        """
        return self.setValue("DEV%", device)

    def selectPotentiostatWithoutPotentiostatStateChange(self, device: int) -> str:
        """
        select device onto which all subsequent calls to set* methods are forwarded

        Device which is to be selected, on which the settings are output.
        First, the device must be selected.
        Only then can devices other than the internal main potentiostat be configured.
        The potentiostat is not turned off.

        :param device: Number of the device. 0 = Main. 1 = EPC channel 1 and so on.
        :returns: The response string from the device.
        """
        return self.setValue("DEVHOT%", device)

    def switchToSCPIControl(self) -> str:
        """
        change away from operation as EPC device to SCPI operation

        This command works only with external potentiostats of the latest generation PP212, PP222, PP242 and XPOT2.
        After this command they are no longer accessible with the EPC interface.
        Then you can connect to the potentiostat with USB via the Comports.
        The change back to EPC operation is also done explicitly from the USB side.

        :returns: response string from the device
        """
        return self.executeRemoteCommand("SETUSB")

    def switchToSCPIControlWithoutPotentiostatStateChange(self) -> str:
        """Change away from operation as EPC device to SCPI operation.

        This command works only with external potentiostats of the latest generation XPOT2, PP2x2, EL1002.
        This requires a device firmware with at least version 1.0.4.
        After this command they are no longer accessible with the EPC interface.
        Then you can connect to the potentiostat with USB via the Comports.
        The change back to EPC operation is also done explicitly from the USB side.

        This function leaves the potentiostat in its current operating state and then switches to USB mode.
        This should only be used when it is really necessary to leave the potentiostat on,
        because between the change of control no quantities like current and voltage are monitored.

        To ensure that the switch between Thales and Python/SCPI is interference-free, the following procedure should be followed.
        This is necessary to ensure that both Thales and Python/SCPI have calibrated offsets, otherwise jumps may occur when switching modes:

         1. Connect Zennium with USB and EPC-device/power potentiostat (XPOT2, PP2x2, EL1002) with USB to the computer. As well as Zennium to power potentiostat by EPC cable.
         2. Switch on all devices.
         3. Allow the equipment to warm up for at least 30 minutes.
         4. Select and calibrate the EPC-device in Thales (with Remote2).
         5. Switching the EPC-device to SCPI mode via Remote2 command.
         6. Performing the offset calibration with Python/SCPI.
         7. Then it is possible to switch between Thales and Python/SCPI with the potentiostat switched on.

        With Thales, the DC operating point must first be set.
        When changing the EPC device then measures current and voltage and sets the size internally.
        When switching back to Thales, the same DC operating point must be set as when switching from Thales to USB.

        :returns: The response string from the device.
        """
        return self.executeRemoteCommand("HOT2USB")

    def getSerialNumber(self) -> str:
        """
        get the serial number of the active device

        Active device ist the device selected with
        :func:`~thales_remote.script_wrapper.ThalesRemoteScriptWrapper.selectPotentiostat`.

        :returns: the device serial number
        """
        reply = self.executeRemoteCommand("ALLNUM")
        match = re.search("(.*);(.*);([a-zA-Z]*)", reply)
        return match.group(2)

    def getDeviceInformation(self) -> tuple[str, str]:
        """
        get the name and serial number of the active device

        :returns: tuple with the information about the selected potentiostat. (Name, Serialnumber).
        """
        reply = self.executeRemoteCommand("DEVINF")
        match = re.search("(.*);(.*);(.*);([0-9]*)", reply)
        return match.group(3), match.group(4)

    def getDeviceName(self) -> str:
        """
        get the name of the active device

        :returns: the device name
        """
        reply = self.executeRemoteCommand("ALLNUM")
        match = re.search("(.*);(.*);([a-zA-Z]*)", reply)
        return match.group(3)

    def calibrateOffsets(self) -> str:
        """
        perform offset calibration on the device

        When the instrument has warmed up for about 30 minutes,
        this command can be used to perform the offset calibration again.

        :returns: response string from the device
        """
        return self.executeRemoteCommand("CALOFFSETS")

    def enablePotentiostat(self, enabled: bool = True) -> str:
        """
        switch the potentiostat on or off

        :param enabled: Switches the potentiostat on if True and off otherwise
        :returns: response string from the device
        """
        return self.executeRemoteCommand("Pot=" + ("-1" if enabled else "0"))

    def disablePotentiostat(self) -> str:
        """
        switch the potentiostat off

        :returns: response string from the device
        """
        return self.enablePotentiostat(False)

    def setPotentiostatMode(self, potentiostatMode: PotentiostatMode) -> str:
        """
        set the coupling of the potentiostat

        This can be PotentiostatMode.POTMODE_POTENTIOSTATIC or PotentiostatMode.POTMODE_GALVANOSTATIC or
        PotentiostatMode.POTMODE_PSEUDOGALVANOSTATIC.

        :param potentiostatMode: The coupling of the potentiostat
        :type potentiostatMode: :class:`~thales_remote.script_wrapper.PotentiostatMode`
        :returns: response string from the device
        """
        command_strings = {
            PotentiostatMode.POTMODE_POTENTIOSTATIC: "Gal=0:GAL=0",
            PotentiostatMode.POTMODE_GALVANOSTATIC: "Gal=-1:GAL=1",
            PotentiostatMode.POTMODE_PSEUDOGALVANOSTATIC: "Gal=0:GAL=-1",
        }
        if not potentiostatMode in command_strings:
            raise ValueError("invalid potentiostat mode: " + str(potentiostatMode))
        return self.executeRemoteCommand(command_strings.get(potentiostatMode))

    def enableRuleFileUsage(self, enable: bool = True) -> str:
        """
        enable the usage of a rule file

        If the usage of the rule file is activated all the parameters required
        for the EIS, CV, and/or IE are taken from the rule file.
        The exact usage can be found in the remote manual.

        :param potentiostatMode: Enable the state of rule file usage.
        :returns: response string from the device
        """
        return self.setValue("UseRuleFile", 1 if enable else 0)

    def disableRuleFileUsage(self) -> str:
        """
        disable the usage of a rule file

        :returns: reponse string from the device
        """
        return self.enableRuleFileUsage(False)

    def setupPad4Channel(
        self,
        card: int,
        channel: int,
        state: Union[int, bool],
        voltageRange: Optional[float] = None,
        shuntResistor: Optional[float] = None,
    ) -> None:
        """
        Setting a channel of a PAD4 card for an EIS measurement

        Each PAD4 channel must be configured individually. Each channel can be switched on or off individually.
        But the PAD4 measurements must still be switched on globally with :func:`~thales_remote.script_wrapper.ThalesRemoteScriptWrapper.enablePad4Global`.
        Each channel can be given a different voltage range or shunt.

        :param card: index of the card starting at 1 and up to 4
        :param channel: index of the card starting at 1 and up to 4
        :param state: If `1` or `True` the channel is switched on else switched off
        :param voltageRange: input voltage range, if this differs from 4 V
        :param shuntResistor: shunt resistor, which is used. Only used if :func:`~thales_remote.script_wrapper.ThalesRemoteScriptWrapper.setupPad4ModeGlobal` is set to :class:`.Pad4Mode`.CURRENT
        :returns: reponse string from the device
        """
        commands = [f"PAD4={card};{channel};{1 if state else 0}"]
        if voltageRange:
            commands.append(f"PAD4_PRANGE={card};{channel};{voltageRange}")
        if shuntResistor:
            commands.append(f"PAD4_RSHUNT={card};{channel};{shuntResistor}")

        for command in commands:
            if isinstance(state, int):
                state = state == 1
            reply = self.executeRemoteCommand(command)

            if "ERROR" in reply:
                raise ThalesRemoteError(
                    reply.rstrip("\r")
                    + ThalesRemoteScriptWrapper.undefindedStandardErrorString
                )
        return

    def setupPad4ModeGlobal(self, mode: Pad4Mode) -> str:
        """
        Switch between current and voltage measurement

        The user can switch the type of PAD4 channels between voltage sense (standard configuration) and current sense (with additional shunt resistor).

        :param mode: :class:`.Pad4Mode`.VOLTAGE or :class:`.Pad4Mode`.CURRENT
        :returns: reponse string from the device
        """
        return self.executeRemoteCommand(f"PAD4MOD={mode.value}")

    def enablePad4Global(self, state: bool = True) -> str:
        """
        switch on the set PAD4 channels

        The files of the measurement results with PAD4 are numbered consecutively.
        The lowest number is the main channel of the potentiostat.

        :param state: If state = True PAD4 channels are enabled.
        :returns: reponse string from the device
        """
        return self.setValue("PAD4ENA", 1 if state else 0)

    def disablePad4Global(self) -> str:
        """
        switch off the set PAD4 channels

        :returns: reponse string from the device
        """
        return self.enablePAD4(False)

    def readPad4SetupGlobal(self) -> str:
        """
        read the currently set parameters

        Reading the set PAD4 configuration.
        A string containing the configuration is returned.

        :returns: reponse string from the device
        """
        reply = self.executeRemoteCommand("SENDPAD4SETUP")
        if reply.find("ERROR") >= 0:
            raise ThalesRemoteError(
                reply.rstrip("\r")
                + ThalesRemoteScriptWrapper.undefindedStandardErrorString
            )
        return reply

    # Section with settings for single impedance and EIS measurements.

    def setFrequency(self, frequency: float) -> str:
        """Set the output frequency for single frequency impedance.

        :param frequency: the output frequency for Impedance measurement to set
        :returns: reponse string from the device
        """
        return self.setValue("Frq", frequency)

    def setAmplitude(self, amplitude: float) -> str:
        """
        set the output amplitude

        :param amplitude: the output amplitude for Impedance measurement to set in Volt or Ampere
        :returns: reponse string from the device
        """
        return self.setValue("Ampl", amplitude * 1e3)

    def setNumberOfPeriods(self, number_of_periods: Union[int, float]):
        """
        set the number of periods to average for one impedance measurement

        :param number_of_periods: the number of periods / waves to average
        :returns: reponse string from the device
        """
        if isinstance(number_of_periods, float):
            number_of_periods = round(number_of_periods)
        if number_of_periods > 100:
            number_of_periods = 100

        if number_of_periods < 1:
            number_of_periods = 1

        return self.setValue("Nw", number_of_periods)

    def setUpperFrequencyLimit(self, frequency: float) -> str:
        """
        set the upper frequency limit for EIS measurements

        :param frequency: the upper frequency limit to set
        :returns: reponse string from the device
        """
        return self.setValue("Fmax", frequency)

    def setLowerFrequencyLimit(self, frequency: float) -> str:
        """
        set the lower frequency limit for EIS measurements

        :param frequency: the lower frequency limit to set
        :returns: reponse string from the device
        """
        return self.setValue("Fmin", frequency)

    def setStartFrequency(self, frequency: float) -> str:
        """
        set the start frequency for EIS measurements

        :param frequency: the start frequency to set
        :returns: reponse string from the device
        """
        return self.setValue("Fstart", frequency)

    def setUpperStepsPerDecade(self, steps: int) -> str:
        """
        set the number of steps per decade in frequency range above 66 Hz for EIS measurements

        :param steps: the number of steps per decade to set
        :returns: reponse string from the device
        """
        return self.setValue("dfm", steps)

    def setLowerStepsPerDecade(self, steps: int) -> str:
        """
        set the number of steps per decade in frequency range below 66 Hz for EIS measurements

        :param steps: the number of steps per decade to set
        :returns: reponse string from the device
        """
        return self.setValue("dfl", steps)

    def setUpperNumberOfPeriods(self, periods: int) -> str:
        """
        set the number of periods to measure in frequency range above 66 Hz for EIS measurements

        Note:
            value must be greater than the one set with
            :func:`~thales_remote.script_wrapper.ThalesRemoteScriptWrapper.setLowerNumberOfPeriods`

        :param periods: the number of periods to set
        :returns: reponse string from the device
        """
        return self.setValue("Nws", periods)

    def setLowerNumberOfPeriods(self, periods: int) -> str:
        """
        set the number of periods to measure  in frequency range below 66 Hz for EIS measurements

        Note:
            Value mustbe smaller than the one set with
            :func:`~thales_remote.script_wrapper.ThalesRemoteScriptWrapper.setUpperNumberOfPeriods`.

        :param periods: the number of periods to set
        :returns: reponse string from the device
        """
        return self.setValue("Nwl", periods)

    def setScanStrategy(self, strategy: Union[ScanStrategy, str]) -> str:
        """Set the scan strategy for EIS measurements.

        strategy = "single": single sine.
        strategy = "multi": multi sine.
        strategy = "table": frequency table.

        :param strategy: the scan strategy to set for EIS measurements
        :returns: reponse string from the device
        """
        strat = strategy
        if isinstance(strategy, str):
            strat = ScanStrategy.stringToEnum(strategy)
        return self.setValue("ScanStrategy", strat.value)

    def setScanDirection(self, direction: Union[ScanDirection, str]) -> str:
        """Set the scan direction for EIS measurements.

        direction = "startToMax": Scan at first from start to maximum frequency.
        direction = "startToMin": Scan at first from start to lower frequency.

        :param direction: The scan direction for EIS measurements.
        :type direction: string
        :returns: reponse string from the device
        """
        dir = direction
        if isinstance(direction, str):
            dir = ScanDirection.stringToEnum(direction)
        return self.setValue("ScanDirection", dir.value)

    def getImpedance(
        self,
        frequency: Optional[float] = None,
        amplitude: Optional[float] = None,
        number_of_periods: Optional[int] = None,
    ) -> complex:
        """
        measure the impedance

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
            raise ThalesRemoteError(
                reply.rstrip("\r")
                + ThalesRemoteScriptWrapper.undefindedStandardErrorString
            )
        match = re.search("impedance=\\s*(.*?),\\s*(.*?)$", reply)
        return complex(float(match.group(1)), float(match.group(2)))

    def setEISNaming(self, naming: Union[str, FileNaming]) -> str:
        """
        set the EIS measurement naming rule

        naming = "dateTime": extend the :func:`~thales_remote.script_wrapper.ThalesRemoteScriptWrapper.setEISOutputFileName` with date and time.
        naming = "counter": extend the :func:`~thales_remote.script_wrapper.ThalesRemoteScriptWrapper.setEISOutputFileName` with an sequential number.
        naming = "individual": the file is named like :func:`~thales_remote.script_wrapper.ThalesRemoteScriptWrapper.setEISOutputFileName`.

        :param naming: the EIS measurement naming rule to set.
        :returns: reponse string from the device
        """
        nameingType = naming
        if isinstance(naming, str):
            nameingType = FileNaming.stringToEnum(naming)
        return self.setValue("EIS_MOD", nameingType.value)

    def setEISCounter(self, number: int) -> str:
        """
        set the current number of EIS measurement for filename

        Current number for the file name for EIS measurements which is used next and then incremented.

        :param number: the next measurement number to set
        :returns: reponse string from the device
        """
        return self.setValue("EIS_NUM", number)

    def setEISOutputPath(self, path: str) -> str:
        """
        set the path where the EIS measurements should be stored

        The results must be stored on the C hard disk.
        If an error occurs test an alternative path or c:\THALES\temp.
        The directory must exist.

        :param path: path to the directory
        :returns: reponse string from the device
        """
        path = path.lower()  # c: has to be lower case
        return self.setValue("EIS_PATH", path)

    def setEISOutputFileName(self, name: str) -> str:
        """
        set the basic EIS output filename

        The basic name of the file, which is extended by a sequential number or the date and time.
        Only numbers, underscores and letters from a-Z may be used.

        If the name is set to "individual", the file with the same name must not yet exist.
        Existing files are not overwritten.

        :param name: basic name of the file
        :returns: reponse string from the device
        """
        return self.setValue("EIS_ROOT", name)

    def measureEIS(self) -> str:
        """
        take an EIS measurement

        For the measurement all parameters must be specified before.

        :returns: reponse string from the device
        """
        reply = self.executeRemoteCommand("EIS")
        if reply.find("ERROR") >= 0:
            raise ThalesRemoteError(
                reply.rstrip("\r")
                + ThalesRemoteScriptWrapper.undefindedStandardErrorString
            )
        return reply

    # Section with settings for CV measurements.

    def setCVStartPotential(self, potential: float) -> str:
        """
        set the start potential of a CV measurment

        :param potential: the start potential to set
        :returns: reponse string from the device
        """
        return self.setValue("CV_Pstart", potential)

    def setCVUpperReversingPotential(self, potential: float) -> str:
        """
        set the upper reversal potential of a CV measurement

        :param potential: the upper reversal potential to set
        :returns: reponse string from the device
        """
        return self.setValue("CV_Pupper", potential)

    def setCVLowerReversingPotential(self, potential: float) -> str:
        """
        set the lower reversal potential of a CV measurement

        :param potential: the lower reversal potential to set
        :returns: reponse string from the device
        """
        return self.setValue("CV_Plower", potential)

    def setCVEndPotential(self, potential: float) -> str:
        """
        set the end potential of a CV measurment

        :param potential: the end potential to set
        :returns: reponse string from the device
        """
        return self.setValue("CV_Pend", potential)

    def setCVStartHoldTime(self, time: float) -> str:
        """
        setting the holding time at the start potential

        The time must be given in seconds.

        :param time: the waiting time at start potential in s
        :returns: reponse string from the device
        """
        return self.setValue("CV_Tstart", time)

    def setCVEndHoldTime(self, time: float) -> str:
        """
        setting the holding time at the end potential

        The time must be given in seconds.

        :param time: the waiting time at end potential in s
        :returns: reponse string from the device
        """
        return self.setValue("CV_Tend", time)

    def setCVScanRate(self, scanRate: float) -> str:
        """
        set the scan rate

        The scan rate must be specified in V/s.

        :param scanRate: the scan rate to set in V/s
        :returns: reponse string from the device
        """
        return self.setValue("CV_Srate", scanRate)

    def setCVCycles(self, cycles: int) -> str:
        """
        set the number of cycles

        At least 0.5 cycles are necessary.
        The number of cycles must be a multiple of 0.5. 3.5 are also possible, for example.

        :param cycles: the number of CV cycles to set, at least 0.5.
        :returns: reponse string from the device
        """
        return self.setValue("CV_Periods", cycles)

    def setCVSamplesPerCycle(self, samples: int) -> str:
        """
        set the number of measurements per CV cycle

        :param samples: the number of measurments per cycle to set
        :returns: reponse string from the device
        """
        return self.setValue("CV_PpPer", samples)

    def setCVMaximumCurrent(self, current: float) -> str:
        """
        set the maximum current

        The maximum positive current at which the measurement is interrupted.
        This is also the current which is used to determine the shunt. This cannot be deactivated.

        :param current: The maximum current for measurement in A at which the measurement is interrupted
        :returns: reponse string from the device
        """
        return self.setValue("CV_Ima", current)

    def setCVMinimumCurrent(self, current: float) -> str:
        """
        set the minimum current

        The maximum negative current at which the measurement is interrupted.
        This is also the current which is used to determine the shunt. This cannot be deactivated.

        :param current: The minimum current for measurement in A.
        :returns: reponse string from the device
        """
        return self.setValue("CV_Imi", current)

    def setCVOhmicDrop(self, ohmicdrop: float) -> str:
        """
        Set the ohmic drop for CV measurement

        :param ohmicdrop: The ohmic drop for measurement.
        :returns: reponse string from the device
        """
        return self.setValue("CV_Odrop", ohmicdrop)

    def enableCVAutoRestartAtCurrentOverflow(self, state: bool = True) -> str:
        """Automatically restart if current is exceeded.

        A new measurement is automatically started with a different
        reverse potential at which the current limit is not exceeded.

        :param state: If state == True the auto restart is enabled.
        :returns: reponse string from the device
        """
        return self.setValue("CV_AutoReStart", 1 if state else 0)

    def disableCVAutoRestartAtCurrentOverflow(self) -> str:
        """
        disable automatic restart if current is exceeded

        :returns: reponse string from the device
        """
        return self.enableCVAutoRestartAtCurrentOverflow(False)

    def enableCVAutoRestartAtCurrentUnderflow(self, state: bool = True) -> str:
        """Restart automatically if the current drops below the limit.

        A new measurement is automatically started with a smaller
        current range than that determined by the minimum and maximum current.

        :param state: If state = True the auto restart is enabled.
        :returns: reponse string from the device
        """
        return self.setValue("CV_AutoScale", 1 if state else 0)

    def disableCVAutoRestartAtCurrentUnderflow(self) -> str:
        """
        disable automatically restart if the current drops below the limit

        :returns: reponse string from the device
        """
        return self.enableCVAutoRestartAtCurrentUnderflow(False)

    def enableCVAnalogFunctionGenerator(self, state: bool = True) -> str:
        """
        switch on the analog function generator (AFG)

        The analog function generator can only be used if it was purchased with the device.
        If the device has the AFG function, you will see a button in the CV software to activate this function.

        :param state: If state == True the AFG is used.
        :returns: reponse string from the device
        """
        return self.setValue("CV_AFGena", 1 if state else 0)

    def disableCVAnalogFunctionGenerator(self) -> str:
        """
        disable the analog function generator (AFG)

        :returns: reponse string from the device
        """
        return self.enableCVAnalogFunctionGenerator(False)

    def setCVNaming(self, naming: Union[str, FileNaming]) -> str:
        """Set the CV measurement naming rule.

        naming = "dateTime": extend the :func:`~thales_remote.script_wrapper.ThalesRemoteScriptWrapper.setCVOutputFileName` with date and time.
        naming = "counter": extend the :func:`~thales_remote.script_wrapper.ThalesRemoteScriptWrapper.setCVOutputFileName` with an sequential number.
        naming = "individual": the file is named like :func:`~thales_remote.script_wrapper.ThalesRemoteScriptWrapper.setCVOutputFileName`.

        :param naming: CV measurement naming rule to set
        :returns: reponse string from the device
        """
        nameingType = naming
        if isinstance(naming, str):
            nameingType = FileNaming.stringToEnum(naming)
        return self.setValue("CV_MOD", nameingType.value)

    def setCVCounter(self, number: int) -> str:
        """
        set the current number of CV measurement for filename

        Current number for the file name for CV measurements which is used next and then incremented.

        :param number: the next measurement number
        :returns: reponse string from the device
        """
        return self.setValue("CV_NUM", number)

    def setCVOutputPath(self, path: str) -> str:
        """
        set the path where the CV measurements should be stored.

        The results must be stored on the C hard disk.
        If an error occurs test an alternative path or c:\THALES\temp.
        The directory must exist.

        :param path: path to the output directory
        :returns: reponse string from the device
        """
        path = path.lower()  # c: has to be lower case
        return self.setValue("CV_PATH", path)

    def setCVOutputFileName(self, name: str) -> str:
        """
        set the basic CV output filename

        The basic name of the file, which is extended by a sequential number or the date and time.
        Only numbers, underscores and letters from a-Z may be used.

        If the name is set to "individual", the file with the same name must not yet exist.
        Existing files are not overwritten.

        :param name: basic name of the file to set
        :returns: reponse string from the device
        """
        return self.setValue("CV_ROOT", name)

    def checkCVSetup(self) -> str:
        """
        check the set parameters

        With the error number the wrong parameter can be found.
        The error numbers are listed in the Remote2 manual.

        :returns: reponse string from the device
        """
        reply = self.executeRemoteCommand("CHECKCV")
        if reply.find("ERROR") >= 0:
            raise ThalesRemoteError(
                reply.rstrip("\r")
                + ThalesRemoteScriptWrapper.undefindedStandardErrorString
            )
        return reply

    def readCVSetup(self) -> str:
        """
        read the set parameters

        After checking with checkCVSetup() the parameters can be read back from the workstation.
        This command returns a list of all set parameters.

        :returns: reponse string from the device
        """
        reply = self.executeRemoteCommand("SENDCVSETUP")
        if reply.find("ERROR") >= 0:
            raise ThalesRemoteError(
                reply.rstrip("\r")
                + ThalesRemoteScriptWrapper.undefindedStandardErrorString
            )
        return reply

    def measureCV(self) -> str:
        """
        take a CV (cyclic voltammetry) measurement

        Note:
            Before starting the measurement, all parameters must be checked with
            :func:`~thales_remote.script_wrapper.ThalesRemoteScriptWrapper.checkCVSetup`.

        :returns: reponse string from the device
        """
        reply = self.executeRemoteCommand("CV")
        if reply.find("ERROR") >= 0:
            raise ThalesRemoteError(
                reply.rstrip("\r")
                + ThalesRemoteScriptWrapper.undefindedStandardErrorString
            )
        return reply

    # Section with settings for IE measurements.
    # Additional informations can be found in the IE manual.

    def setIEFirstEdgePotential(self, potential: float) -> str:
        """Set the first edge potential.

        :param potential: The potential of the first edge in V.
        :returns: reponse string from the device
        """
        return self.setValue("IE_EckPot1", potential)

    def setIESecondEdgePotential(self, potential: float) -> str:
        """Set the second edge potential.

        :param potential: The potential of the second edge in V.
        :returns: reponse string from the device
        """
        return self.setValue("IE_EckPot2", potential)

    def setIEThirdEdgePotential(self, potential: float) -> str:
        """Set the third edge potential.

        :param potential: The potential of the third edge in V.
        :returns: reponse string from the device
        """
        return self.setValue("IE_EckPot3", potential)

    def setIEFourthEdgePotential(self, potential: float) -> str:
        """Set the fourth edge potential.

        :param potential: The potential of the fourth edge in V.
        :returns: reponse string from the device
        """
        return self.setValue("IE_EckPot4", potential)

    def setIEFirstEdgePotentialRelation(self, relation: float) -> str:
        """Set the relation of the first edge potential.

        relation = "absolute": Absolute relation of the potential.
        relation = "relative": Relative relation of the potential.

        :param relation: The relation of the edge potential absolute or relative.
        :returns: reponse string from the device
        """
        if relation == "relative":
            relation = -1
        else:
            relation = 0
        return self.setValue("IE_EckPot1rel", relation)

    def setIESecondEdgePotentialRelation(self, relation) -> str:
        """Set the relation of the second edge potential.

        relation = "absolute": Absolute relation of the potential.
        relation = "relative": Relative relation of the potential.

        :param relation: The relation of the edge potential absolute or relative.
        :returns: reponse string from the device
        """
        if relation == "relative":
            relation = -1
        else:
            relation = 0
        return self.setValue("IE_EckPot2rel", relation)

    def setIEThirdEdgePotentialRelation(self, relation) -> str:
        """Set the relation of the third edge potential.

        relation = "absolute": Absolute relation of the potential.
        relation = "relative": Relative relation of the potential.

        :param relation: The relation of the edge potential absolute or relative.
        :returns: reponse string from the device
        """
        if relation == "relative":
            relation = -1
        else:
            relation = 0
        return self.setValue("IE_EckPot3rel", relation)

    def setIEFourthEdgePotentialRelation(self, relation) -> str:
        """Set the relation of the fourth edge potential.

        relation = "absolute": Absolute relation of the potential.
        relation = "relative": Relative relation of the potential.

        :param relation: The relation of the edge potential absolute or relative.
        :returns: reponse string from the device
        """
        if relation == "relative":
            relation = -1
        else:
            relation = 0
        return self.setValue("IE_EckPot4rel", relation)

    def setIEPotentialResolution(self, resolution: float) -> str:
        """Set the potential resolution.

        The potential step size for IE measurements in V.

        :param relation: The resolution for the measurement in V.
        :returns: reponse string from the device
        """
        return self.setValue("IE_Resolution", resolution)

    def setIEMinimumWaitingTime(self, time: float) -> str:
        """Set the minimum waiting time.

        The minimum waiting time on each step of the IE measurement.
        This time is at least waited, even if the tolerance abort criteria are met.

        :param time: The waiting time in seconds.
        :returns: reponse string from the device
        """
        return self.setValue("IE_WZmin", time)

    def setIEMaximumWaitingTime(self, time: float) -> str:
        """Set the maximum waiting time.

        The maximum waiting time on each step of the IE measurement.
        After this time the measurement is stopped at this potential
        and continued with the next potential even if the tolerances are not reached.

        :param time: The waiting time in seconds.
        :returns: reponse string from the device
        """
        return self.setValue("IE_WZmax", time)

    def setIERelativeTolerance(self, tolerance: float) -> str:
        """Set the relative tolerance criteria.

        This parameter is only used in sweep mode steady state.
        The relative tolerance to wait in percent.
        The explanation can be found in the IE manual.

        :param tolerance: The tolerance to wait until break, 0.01 = 1%.
        :returns: reponse string from the device
        """
        return self.setValue("IE_Torel", tolerance)

    def setIEAbsoluteTolerance(self, tolerance: float) -> str:
        """Set the absolute tolerance criteria.

        This parameter is only used in sweep mode steady state.
        The absolute tolerance to wait in A.
        The explanation can be found in the IE manual.

        :param tolerance: The tolerance to wait until break, 0.01 = 1%.
        :returns: reponse string from the device
        """
        return self.setValue("IE_Toabs", tolerance)

    def setIEOhmicDrop(self, ohmicdrop: float) -> str:
        """Set the ohmic drop for IE measurement.

        :param ohmicdrop: The ohmic drop for measurement.
        :returns: reponse string from the device
        """
        return self.setValue("IE_Odrop", ohmicdrop)

    def setIESweepMode(self, mode) -> str:
        """Set the sweep mode.

        The explanation of the modes can be found in the IE manual.
        mode="steady state"
        mode="fixed sampling"
        mode="dynamic scan"

        :param mode: The sweep mode for measurement.
        :returns: reponse string from the device
        """
        if mode == "steady state":
            mode = 0
        elif mode == "dynamic scan":
            mode = 2
        else:
            mode = 1
        return self.setValue("IE_SweepMode", mode)

    def setIEScanRate(self, scanRate: float) -> str:
        """Set the scan rate.

        This parameter is only used in sweep mode dynamic scan.
        The scan rate must be specified in V/s.

        :param scanRate: The scan rate in V/s.
        :returns: reponse string from the device
        """
        return self.setValue("IE_Srate", scanRate)

    def setIEMaximumCurrent(self, current: float) -> str:
        """Set the maximum current.

        The maximum positive current at which the measurement is interrupted.

        :param current: The maximum current for measurement in A.
        :returns: reponse string from the device
        """
        return self.setValue("IE_Ima", current)

    def setIEMinimumCurrent(self, current: float) -> str:
        """Set the minimum current.

        The maximum negative current at which the measurement is interrupted.

        :param current: The minimum current for measurement in A.
        :returns: reponse string from the device
        """
        return self.setValue("IE_Imi", current)

    def setIENaming(self, naming: Union[str, FileNaming]) -> str:
        """Set the IE measurement naming rule.

        naming = "dateTime": extend the :func:`~thales_remote.script_wrapper.ThalesRemoteScriptWrapper.setIEOutputFileName` with date and time.
        naming = "counter": extend the :func:`~thales_remote.script_wrapper.ThalesRemoteScriptWrapper.setIEOutputFileName` with an sequential number.
        naming = "individual": the file is named like :func:`~thales_remote.script_wrapper.ThalesRemoteScriptWrapper.setIEOutputFileName`.

        :param naming: The IE measurement naming rule.
        :type naming: string
        :returns: reponse string from the device
        """
        nameingType = naming
        if isinstance(naming, str):
            nameingType = FileNaming.stringToEnum(naming)
        return self.setValue("IE_MOD", nameingType.value)

    def setIECounter(self, number: int) -> str:
        """Set the current number of IE measurement for filename.

        Current number for the file name for EIS measurements which is used next and then incremented.

        :param number: The next measurement number.
        :returns: reponse string from the device
        """
        return self.setValue("IE_NUM", number)

    def setIEOutputPath(self, path: str) -> str:
        """Set the path where the IE measurements should be stored.

        The results must be stored on the C hard disk. If an error occurs test an alternative path or c:\THALES\temp.
        The directory must exist.

        :param path: The path to the directory.
        :returns: reponse string from the device
        """
        path = path.lower()  # c: has to be lower case
        return self.setValue("IE_PATH", path)

    def setIEOutputFileName(self, name: str) -> str:
        """Set the basic IE output filename.

        The basic name of the file, which is extended by a sequential number or the date and time.
        Only numbers, underscores and letters from a-Z may be used.

        If the name is set to "individual", the file with the same name must not yet exist.
        Existing files are not overwritten.

        :param name: The basic name of the file.
        :returns: reponse string from the device
        """
        return self.setValue("IE_ROOT", name)

    def checkIESetup(self) -> str:
        """Check the set parameters.

        With the error number the wrong parameter can be found.
        The error numbers are listed in the Remote2 manual.

        :returns: reponse string from the device
        """
        reply = self.executeRemoteCommand("CHECKIE")
        if reply.find("ERROR") >= 0:
            raise ThalesRemoteError(
                reply.rstrip("\r")
                + ThalesRemoteScriptWrapper.undefindedStandardErrorString
            )
        return reply

    def readIESetup(self) -> str:
        """Read the set parameters.

        After checking with :func:`~thales_remote.script_wrapper.ThalesRemoteScriptWrapper.checkIESetup` the parameters can be read back from the workstation.

        :returns: reponse string from the device
        """
        reply = self.executeRemoteCommand("SENDIESETUP")
        if reply.find("ERROR") >= 0:
            raise ThalesRemoteError(
                reply.rstrip("\r")
                + ThalesRemoteScriptWrapper.undefindedStandardErrorString
            )
        return reply

    def measureIE(self) -> str:
        """Measure IE.

        Before measurement, all parameters must be checked with :func:`~thales_remote.script_wrapper.ThalesRemoteScriptWrapper.checkIESetup`.

        :returns: reponse string from the device
        """
        reply = self.executeRemoteCommand("IE")
        if reply.find("ERROR") >= 0:
            raise ThalesRemoteError(
                reply.rstrip("\r")
                + ThalesRemoteScriptWrapper.undefindedStandardErrorString
            )
        return reply

    """
    Section of remote functions for the sequencer.
 
    With the sequencer DC profiles can be described textually.
    For instructions on how the sequencer file is structured, please refer to the manual of the sequencer.
    """

    def selectSequence(self, number: int) -> str:
        """Select the sequence to run with runSequence().

        The sequences must be stored under "C:\THALES\script\sequencer\sequences".
        Sequences from 0 to 9 can be created.
        These must have the names from "sequence00.seq" to "sequence09.seq".

        :param number: The number of the sequence.
        :returns: reponse string from the device
        """
        reply = self.executeRemoteCommand("SELSEQ=" + str(number))
        if reply != "SELOK\r":
            raise ThalesRemoteError(
                reply.rstrip("\r") + " The selected sequence does not exist."
            )
        return reply

    def setSequenceNaming(self, naming: Union[str, FileNaming]) -> str:
        """Set the sequence measurement naming rule.

        naming = "dateTime": extend the setSequenceOutputFileName(name) with date and time.
        naming = "counter": extend the setSequenceOutputFileName(name) with an sequential number.
        naming = "individual": the file is named like setEISOutputFileName(name).

        :param naming: The naming rule.
        :type naming: string
        :returns: reponse string from the device
        """
        nameingType = naming
        if isinstance(naming, str):
            nameingType = FileNaming.stringToEnum(naming)
        return self.setValue("SEQ_MOD", nameingType.value)

    def setSequenceCounter(self, number: int) -> str:
        """Set the current number of sequence measurement for filename.

        Current number for the file name for EIS measurements which is used next and then incremented.

        :param number: The next measurement number
        :returns: reponse string from the device
        """
        return self.setValue("SEQ_NUM", number)

    def setSequenceOutputPath(self, path: str) -> str:
        """Set the path where the sequence measurements should be stored.

        The results must be stored on the C hard disk. If an error occurs test an alternative path or c:\THALES\temp.
        The directory must exist.

        :param path: The path to the directory.
        :returns: reponse string from the device
        """
        path = path.lower()  # c: has to be lower case
        return self.setValue("SEQ_PATH", path)

    def setSequenceOutputFileName(self, name: str) -> str:
        """Set the basic sequence output filename.

        The basic name of the file, which is extended by a sequential number or the date and time.
        Only numbers, underscores and letters from a-Z may be used.

        If the name is set to "individual", the file with the same name must not yet exist.
        Existing files are not overwritten.

        :param name: The basic name of the file.
        :returns: reponse string from the device
        """
        return self.setValue("SEQ_ROOT", name)

    def runSequence(self) -> str:
        """Run the selected sequence.

        This command executes the selected sequence between 0 and 9.

        :returns: reponse string from the device
        """
        reply = self.executeRemoteCommand("DOSEQ")
        if reply != "SEQ DONE\r":
            raise ThalesRemoteError(
                reply.rstrip("\r")
                + ThalesRemoteScriptWrapper.undefindedStandardErrorString
            )
        return reply

    def enableFraMode(self, state: bool = True) -> str:
        """Enables the use of the FRA probe.

        With the FRA Probe, external power potentiostats, signal generators, sources, sinks can be
        controlled analog for impedance measurements.

        `FRA Product Page <https://zahner.de/products-details/probes/fra-probe>`_
        `FRA Manual <https://doc.zahner.de/hardware/fra_probe.pdf>`_

        Before this function is called, the analog interface to the external interface must be initialized
        with the correct factors. It may be necessary to use + or - as sign, this must be tested to ensure
        that potentiostatic and galvanostatic function correctly.

        For example, if the device has 100 A output current and the analog signal input range of the
        device is 5 V, then the current gain is 100/5.

        :param state: If state = True FRA mode is enabled.
        :returns: reponse string from the device
        """
        if state == True:
            state = 1
        else:
            state = 0
        return self.setValue("FRA", state)

    def disableFraMode(self) -> str:
        return self.enableFraMode(False)

    def setFraVoltageInputGain(self, value: float) -> str:
        """Sets the input voltage gain.

        :param value: The value to set.
        :returns: reponse string from the device
        """
        return self.setValue("FRA_POT_IN", value)

    def setFraVoltageOutputGain(self, value: float) -> str:
        """Sets the output voltage gain.

        :param value: The value to set.
        :returns: reponse string from the device
        """
        return self.setValue("FRA_POT_OUT", value)

    def setFraVoltageMinimum(self, value: float) -> str:
        """Sets the minimum voltage.

        Sets the minimum voltage of the FRA device.

        :param value: The value to set.
        :returns: reponse string from the device
        """
        return self.setValue("FRA_POT_MIN", value)

    def setFraVoltageMaximum(self, value: float) -> str:
        """Sets the maximum voltage.

        Sets the maximum voltage of the FRA device.

        :param value: The value to set.
        :returns: reponse string from the device
        """
        return self.setValue("FRA_POT_MAX", value)

    def setFraCurrentInputGain(self, value: float) -> str:
        """Sets the input current gain.

        :param value: The value to set.
        :returns: reponse string from the device
        """
        return self.setValue("FRA_CUR_IN", value)

    def setFraCurrentOutputGain(self, value: float) -> str:
        """Sets the output current gain.

        :param value: The value to set.
        :returns: reponse string from the device
        """
        return self.setValue("FRA_CUR_OUT", value)

    def setFraCurrentMinimum(self, value: float) -> str:
        """Sets the minimum current.

        Sets the minimum current of the FRA device.

        :param value: The value to set.
        :returns: reponse string from the device
        """
        return self.setValue("FRA_CUR_MIN", value)

    def setFraCurrentMaximum(self, value: float) -> str:
        """Sets the maximum current.

        Sets the maximum current of the FRA device.

        :param value: The value to set.
        :returns: reponse string from the device
        """
        return self.setValue("FRA_CUR_MAX", value)

    def setFraPotentiostatMode(self, potentiostatMode: PotentiostatMode) -> str:
        """Set the coupling of the FRA mode.

        This can be PotentiostatMode.POTMODE_POTENTIOSTATIC or PotentiostatMode.POTMODE_GALVANOSTATIC

        :param potentiostatMode: The coupling of the FRA mode
        :returns: reponse string from the device
        """
        if potentiostatMode == PotentiostatMode.POTMODE_POTENTIOSTATIC:
            command = "FRAGAL=0"
        elif potentiostatMode == PotentiostatMode.POTMODE_GALVANOSTATIC:
            command = "FRAGAL=1"
        else:
            return ValueError(
                "PotentiostatMode.POTMODE_POTENTIOSTATIC or PotentiostatMode.POTMODE_GALVANOSTATIC"
            )
        return self.executeRemoteCommand(command)

    def runSequenceFile(
        self,
        filepath: str,
        sequence_folder: str = "C:/THALES/script/sequencer/sequences",
        sequence_number: int = 9,
    ) -> str:
        """Run the sequence at filepath.

        The file from the specified path is copied as sequence sequence_number=9 to the correct location in the Thales directory and then selected and executed.
        The default sequence number is 9 and does not need to be changed.
        The old sequence sequence_number is overwritten.

        The variable sequence_folder is ONLY NECESSARY if python is running on ANOTHER COMPUTER like the one connected to the Zennium.
        For this the controlling computer must have access to the hard disk of the computer with the Zennium to access the THALES folder.
        In this case the path to the sequences folder in sequence_folder must be set to "C:/THALES/script/sequencer/sequences" on the computer with the zennium.

        :param filepath: Filepath of the sequence.
        :param sequence_folder: The filepath to the THALES sequence folder.
            Does not normally need to be transferred and changed. Explanation see in the text before.
        :param sequence_number: The number in the THALES sequence directory.
            Does not normally need to be transferred and changed.
        :returns: reponse string from the device
        """
        if sequence_number > 9 or sequence_number < 0:
            raise ThalesRemoteError("Wrong sequence number.")

        sequence_folder = sequence_folder + "/sequence{:02d}.seq".format(
            sequence_number
        )

        if filepath.find(".seq") < 0:
            raise ThalesRemoteError("Wrong sequence file extension.")
        if os.path.exists(sequence_folder):
            os.remove(sequence_folder)
        shutil.copy2(filepath, sequence_folder)

        self.selectSequence(sequence_number)
        return self.runSequence()

    def setValue(self, name: str, value: Union[int, float, str, Any]) -> str:
        """
        set an Remote2 parameter or value.

        :param name: name of the Remote2 parameter
        :param value: value of the parameter to set
        :returns: response string from the device
        """
        if isinstance(value, float):
            value = "{:.14e}".format(value)

        reply = self.executeRemoteCommand(name + "=" + str(value))
        if "ERROR" in reply:
            raise ThalesRemoteError(
                reply.rstrip("\r")
                + ThalesRemoteScriptWrapper.undefindedStandardErrorString
            )
        return reply

    def executeRemoteCommand(self, command: str) -> str:
        """Directly execute a query to Remote Script.

        :param command: The command query string, e.g. "IMPEDANCE" or "Pset=0".
        :returns: reponse string from the device
        """
        return self._remote_connection.sendStringAndWaitForReplyString(
            "1:" + command + ":", 2
        )

    def forceThalesIntoRemoteScript(self) -> str:
        """Prompts Thales to start the Remote Script.

        Will switch a running Thales from anywhere like the main menu after
        startup to running measurements into Remote Script so it can process
        further requests.

        .. note::
            This happens rather quickly if Thales is idle in main menu but
            may take some time if it's performing an EIS measurement or doing
            something else. For high stability applications 20 seconds would
            probably be a save bet.

        :returns: reponse string from the device
        """
        self._remote_connection.sendStringAndWaitForReplyString(
            f"3,{self._remote_connection.getConnectionName()},0,OFF", 128
        )
        return self._remote_connection.sendStringAndWaitForReplyString(
            f"2,{self._remote_connection.getConnectionName()}", 128
        )

    def getWorkstationHeartBeat(self, timeout: Optional[float] = None) -> float:
        """Query the heartbeat time from the Term software for the workstation and the Thales software accordingly.

        The complete documentation can be found in the `DevCli-Manual <https://doc.zahner.de/manuals/devcli.pdf>`_ Page 8.


        The timeout is not set by default and the command blocks indefinitely.
        However, a time in seconds can optionally be specified for the timeout.
        When the timeout expires, an exception is thrown by the socket.

        :param timeout: The time in seconds in which the term must provide the answer.
        :returns: The HeartBeat time in milli seconds.
        """
        retval = self._remote_connection.sendStringAndWaitForReplyString(
            f"1,{self._remote_connection.getConnectionName()}", 128, timeout
        )
        return float(retval.split(",")[2])

    def getSerialNumberFromTerm(self) -> str:
        """Get the serial number of the workstation via the Term software.

        The serial number of the active potentiostat with EPC devices can be read with the
        :func:`~thales_remote.script_wrapper.ThalesRemoteScriptWrapper.getSerialNumber` function.
        This function returns only the serial number of the workstation, which is determined by the Term software.

        :returns: The workstation serial number.
        """
        retval = self._remote_connection.sendStringAndWaitForReplyString(
            f"3,{self._remote_connection.getConnectionName()},6", 128
        )
        return retval.split(",")[2]

    def getTermIsActive(self, timeout: float = 2) -> bool:
        """Check if the Term still responds to requests.

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
        """
        active = True
        try:
            self._remote_connection.sendStringAndWaitForReplyString(
                f"1,{self._remote_connection.getConnectionName()}", 128, timeout
            )
        except:
            active = False
        return active

    """
    The following methods should not be called by the user.
    They are marked with the prefix '_' after the Python convention for proteced.
    """

    def _requestValueAndParseUsingRegexp(self, command: str, pattern: str) -> float:
        reply = self.executeRemoteCommand(command)
        if reply.find("ERROR") >= 0:
            raise ThalesRemoteError(
                reply.rstrip("\r")
                + ThalesRemoteScriptWrapper.undefindedStandardErrorString
            )
        match = re.search(pattern, reply)
        return float(match.group(1))
