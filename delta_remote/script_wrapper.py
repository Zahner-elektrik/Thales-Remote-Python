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


class DeltaSCPIError(Exception):
    """Delta Connection Exception Class

    This exception is thrown when an error occurs with the communication,
    which has not yet been thrown by a socket exception.

    After this error the connection must be completely rebuilt.
    """

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class DeltaSources(Enum):
    """Delta Elektronika power supply source options.

    The class manages the possible sources to be used for setting the target voltage and current.
    """

    front = "front"
    web = "web"
    seq = "seq"
    eth = "eth"
    slot1 = "slot1"
    slot2 = "slot2"
    slot3 = "slot3"
    slot4 = "slot4"
    loc = "loc"
    rem = "rem"


class DeltaSCPIWrapper(object):
    """Class containing the SCPI commands for the Delta Elektronika power supply.

    This class wraps the SCPI commands in getter and setter methods.

    :param connection: The connection object to the Delta power supply.
    :type connection: :class:`~delta_remote.connection.DeltaConnection`
    """

    def __init__(self, connection):
        self.defaultTimeout = None
        self.connection = connection

        self.maximumVoltage = self._requestFloatValue("SOUR:VOLT:MAX?")
        self.maximumCurrent = self._requestFloatValue("SOUR:CUR:MAX?")
        return

    def setDefaultTimout(self, time):
        """Set the default timeout.

        The command sets the default timeout that is used.

        :param time: Timout in seconds.
        """
        self.defaultTimeout = time
        return

    def IDN(self):
        """Querying the device identification.

        This is the standard SCPI command for requesting the identification.

        :returns: The response string from the device.
        """
        return self.executeCommandAndWaitForReply("*IDN?")

    def setTargetVoltage(self, value):
        """Set the target output voltage.

        :param value: The output voltage.
        """
        if value >= 0 and value <= self.maximumVoltage:
            self.executeCommand(f"SOUR:VOLT {value}")
        else:
            raise DeltaSCPIError("Voltage out of range.")
        return

    def setTargetCurrent(self, value):
        """Set the target output current.

        :param value: The output current.
        """
        if value >= 0 and value <= self.maximumCurrent:
            self.executeCommand(f"SOUR:CUR {value}")
        else:
            raise DeltaSCPIError("Voltage out of range.")
        return

    def getTargetVoltage(self):
        """Read the target output voltage.

        :returns: The value.
        """
        return self._requestFloatValue("SOUR:VOLT?")

    def getTargetCurrent(self):
        """Read the target output current.

        :returns: The value.
        """
        return self._requestFloatValue("SOUR:CUR?")

    def getMeasuredVoltage(self):
        """Measure the actual output voltage.

        :returns: The value.
        """
        return self._requestFloatValue("MEAS:VOLT?")

    def getMeasuredCurrent(self):
        """Measure the actual output current.

        :returns: The value.
        """
        return self._requestFloatValue("MEAS:CUR?")

    def getMeasuredPower(self):
        """Measure the actual output power.

        :returns: The value.
        """
        return self._requestFloatValue("MEAS:POW?")

    def setProgSourceVoltage(self, source: DeltaSources):
        """Set the voltage source option.

        Defines which interface defines the voltage to be applied.

        :param source: The source option.
        :type source: :class:`~delta_remote.script_wrapper.DeltaSources`
        """
        self.executeCommand(f"SYST:REM:CV {source.value}")
        return

    def setProgSourceCurrent(self, source: DeltaSources):
        """Set the current source option.

        Defines which interface defines the current to be applied.

        :param source: The source option.
        :type source: :class:`~delta_remote.script_wrapper.DeltaSources`
        """
        self.executeCommand(f"SYST:REM:CC {source.value}")
        return

    def enableOutput(self, enable=True):
        """Enable the output of the supply.

        :param enable: True to turn the output on.
        """
        if enable:
            self.executeCommand("OUTPUT 1")
        else:
            self.executeCommand("OUTPUT 0")
        return

    def disableOutput(self):
        """Disable the output of the supply."""
        self.enableOutput(False)
        return

    def executeCommand(self, command, timeout=None):
        """Executes a command.

        :param command: The command.
        :param timeout: The timeout for sending data in seconds, blocking at None.
        """
        if timeout is None:
            timeout = self.defaultTimeout
        return self.connection.sendTelegram(command + "\n", timeout)

    def executeCommandAndWaitForReply(self, command, timeout=None):
        """Executes a command and waits for the reply from the device.

        :param command: The command.
        :param timeout: The timeout for sending data in seconds, blocking at None.
        """
        if timeout is None:
            timeout = self.defaultTimeout
        return self.connection.sendStringAndWaitForReplyString(
            command + "\n", timeout
        ).rstrip()

    def _requestValueAndParseUsingRegexp(self, command, pattern):
        reply = self.executeCommandAndWaitForReply(command)
        match = re.search(pattern, reply)
        return float(match.group(1))

    def _requestFloatValue(self, command):
        return float(self.executeCommandAndWaitForReply(command))
