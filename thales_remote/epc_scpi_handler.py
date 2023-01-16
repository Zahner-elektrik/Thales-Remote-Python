from thales_remote.connection import ThalesRemoteConnection
from thales_remote.script_wrapper import PotentiostatMode, ThalesRemoteScriptWrapper
from thales_remote.error import TermConnectionError, ThalesRemoteError

from zahner_potentiostat.scpi_control.searcher import SCPIDeviceSearcher
from zahner_potentiostat.scpi_control.serial_interface import (
    SerialCommandInterface,
    SerialDataInterface,
)
from zahner_potentiostat.scpi_control.control import *
from zahner_potentiostat.scpi_control.datahandler import DataManager

import threading
import time
from dataclasses import dataclass


class EpcScpiHandler:
    """Class for the control objects.

    This class manages the object composed of a cennium and the external potentiostat.
    The object contains an instance of a :class:`~zahner_potentiostat.scpi_control.control.SCPIDevice`
    and the shared common :class:`~thales_remote.script_wrapper.ThalesRemoteScriptWrapper` object.

    The SCPI object is invalid when the device is in EPC mode.
    The device must be manually switched from EPC to SCPI before the SCPI object can be used again.

    :param sharedZennium: Zennium object.
    :type sharedZennium: :class:`~thales_remote.script_wrapper.ThalesRemoteScriptWrapper`
    :param epcChannel: Number of the EPC channel to which the device is connected via EPC cable.
        If a Rmux card is plugged in then the numbers have an offset.
    :param serialNumber: Serial number of the external potentiostat.
    """

    zenniumMutex = threading.Lock()  # class variable
    sharedZenniumInterface: ThalesRemoteScriptWrapper
    _epcId: int
    _serialNumber: int
    _isInEPC: bool
    _commandInterface: Union[SerialCommandInterface, None]
    scpiInterface: Union[SCPIDevice, None]

    def __init__(
        self,
        sharedZennium: ThalesRemoteScriptWrapper,
        epcPotentiostatId: int,
        serialNumber: int,
    ):
        self.sharedZenniumInterface = sharedZennium
        self._epcId = epcPotentiostatId
        self._serialNumber = serialNumber
        self._isInEPC = True

        self._commandInterface = None
        self.scpiInterface = None
        return

    def isSharedZenniumAvailable(self) -> bool:
        """Check if the zennium is available.

        The method checks if the threading.lock for synchronizing access to the Zennium is available.

        :returns: True if the zennium is not locked and available.
        """
        return EpcScpiHandler.zenniumMutex.locked() == False

    def acquireSharedZennium(self, blocking: bool = True, timeout: int = -1) -> bool:
        """Check if the Zennium is available.

        Wrapper for the aquire method of the `Python lock object <https://docs.python.org/3/library/threading.html#lock-objects>`_.
        The parameters and return values are simply passed through.

        :param blocking: When invoked with the blocking argument set to True (the default),
            block until the lock is unlocked, then set it to locked and return True.
        :param timeout: When invoked with the floating-point timeout argument set to a positive value,
            block for at most the number of seconds specified by timeout and as long as the lock cannot
            be acquired. A timeout argument of -1 specifies an unbounded wait. It is forbidden to
            specify a timeout when blocking is false.
        :returns: The return value is True if the lock is acquired successfully, False if not
            (for example if the timeout expired).
        """
        return EpcScpiHandler.zenniumMutex.acquire(blocking, timeout)

    def releaseSharedZennium(self) -> None:
        """Release the Zennium object.

        Wrapper for the aquire method of the `Python lock object <https://docs.python.org/3/library/threading.html#lock-objects>`_.

        Release a lock. This can be called from any thread, not only the thread which has acquired the lock.
        When the lock is locked, reset it to unlocked, and return. If any other threads are blocked
        waiting for the lock to become unlocked, allow exactly one of them to proceed.

        When invoked on an unlocked lock, a RuntimeError is raised.
        """
        EpcScpiHandler.zenniumMutex.release()
        return

    def connectSCPIDevice(self) -> None:
        """Establish connection to the potentiostat.

        This method establishes the connection to the potentiostat (PP2x2, XPOT2 and EL1002) and passes it to the internal data structure.
        When invoked on an unlocked lock, a RuntimeError is raised.
        """
        deviceSearcher = SCPIDeviceSearcher()
        deviceSearcher.searchZahnerDevices()
        commandSerial, dataSerial = deviceSearcher.selectDevice(self._serialNumber)
        self._commandInterface = SerialCommandInterface(commandSerial)

        self.scpiInterface = SCPIDevice(
            self._commandInterface, SerialDataInterface(dataSerial)
        )
        return

    def switchToSCPIAndReleaseSharedZennium(
        self, keepPotentiostatState: bool = False
    ) -> None:
        """Switch from EPC to SCPI mode of the potentiostat and release the Zennium.

        The switch from EPC to SCPI must be made from the EPC operation, both control options can
        only release control but cannot take control away from each other.

        After the control is released, the Zennium is released.

        :param keepPotentiostatState: If this parameter is True,
            the potentiostat is not switched off when switching from EPC to SCPI.
        """
        self.sharedZenniumInterface.selectPotentiostat(self._epcId)

        if keepPotentiostatState:
            self.sharedZenniumInterface.switchToSCPIControlWithoutPotentiostatStateChange()
        else:
            self.sharedZenniumInterface.switchToSCPIControl()

        self._isInEPC = False
        self.releaseSharedZennium()

        """
        It takes some time for the operating system to recognize the USB device.
        
        It tries to find the USB device 3 times every 3 seconds. If this fails, an exception is thrown.
        """
        maxTry = 3
        for i in range(maxTry):
            try:
                time.sleep(3)
                self.connectSCPIDevice()
            except Exception as e:
                if i == (maxTry - 1):
                    raise e
            else:
                break  # for loop
        return

    def switchToSCPI(self, keepPotentiostatState: bool = False) -> None:
        """Switch from EPC to SCPI mode.

        It is recommended to use :class:`~thales_remote.epc_scpi_handler.EpcScpiHandler.switchToSCPIAndReleaseSharedZennium` instead of this function.

        Before calling this method, the Zennium must have been released, since these methods call
        aquire and release themselves.
        If the Zennium was locked before this function will block.

        :param keepPotentiostatState: If this parameter is True,
            the potentiostat is not switched off when switching from EPC to SCPI.
        """
        self.acquireSharedZennium()

        if keepPotentiostatState:
            self.sharedZenniumInterface.selectPotentiostatWithoutPotentiostatStateChange(
                self._epcId
            )
            self.sharedZenniumInterface.switchToSCPIControlWithoutPotentiostatStateChange()
        else:
            self.sharedZenniumInterface.selectPotentiostat(self._epcId)
            self.sharedZenniumInterface.switchToSCPIControl()

        self._isInEPC = False
        self.releaseSharedZennium()
        """
        Wait a little so that windows recognizes the new usb device when the potentiostat logs on again.
        """
        time.sleep(3)
        self.connectSCPIDevice()
        return

    def switchToEPC(self, keepPotentiostatState: bool = False) -> None:
        """Switch from SCPI to EPC mode.

        Before calling this method the Zennium must be locked with aquire.

        This method is used to switch from SCPI to EPC operation. After this method is called, the
        scpiInterface object is destroyed because the USB connection is closed.

        This method automatically selects the correct EPC channel.

        :param keepPotentiostatState: If this parameter is True,
            the potentiostat is not switched off when switching from SCPI to EPC.
        """
        try:
            if keepPotentiostatState:
                self.scpiInterface.switchToEPCControlWithoutPotentiostatStateChange()
            else:
                self.scpiInterface.switchToEPCControl()
            self.scpiInterface.close()
        except:
            pass
        finally:
            self.scpiInterface = None
            self._isInEPC = True

        """
        Wait a little for the change to EPC.
        """
        time.sleep(2)
        if keepPotentiostatState:
            self.sharedZenniumInterface.selectPotentiostatWithoutPotentiostatStateChange(
                self._epcId
            )
        else:
            self.sharedZenniumInterface.selectPotentiostat(self._epcId)
        return

    def getSerialNumber(self):
        return self._serialNumber

    def close(self):
        """Close the SCPI connection.

        The function is not required in epc mode.
        """
        if self._isInEPC is False:
            self.scpiInterface.close()
        return


@dataclass
class HandlerDataItem:
    serialNumber: int
    epcIndex: int
    handlerObject: EpcScpiHandler


class EpcScpiHandlerFactory:
    """Class for creating the control objects.

    This class initializes the connection to the zennium.
    The :func:`~epc_scpi_handler.EpcScpiHandlerFactory.createEpcScpiHandler` method can then be used
    to create a control object for the corresponding device.

    :param shared_zennium_target: IP address at which the Zennium can be reached. Default is "localhost".
    """

    _zenniumConnection: ThalesRemoteConnection
    sharedZenniumInterface: ThalesRemoteScriptWrapper
    _handlerList: list[HandlerDataItem]

    def __init__(self, shared_zennium_target="127.0.0.1"):
        self._zenniumConnection = ThalesRemoteConnection()
        connectionSuccessful = self._zenniumConnection.connectToTerm(
            shared_zennium_target, "ScriptRemote"
        )
        if connectionSuccessful is False:
            raise TermConnectionError("connection to zennium not possible")

        self.sharedZenniumInterface = ThalesRemoteScriptWrapper(self._zenniumConnection)
        self.sharedZenniumInterface.forceThalesIntoRemoteScript()
        self._handlerList = []
        return

    def getSharedZennium(self) -> ThalesRemoteScriptWrapper:
        """Returns the zennium object.

        Returns the Zennium object, which contains the Remote2 commands as methods.

        :returns: Object with the Remote2 wrapper.
        """
        return self.sharedZenniumInterface

    def getZenniumConnection(self) -> ThalesRemoteConnection:
        """Returns the zennium connection object.

        Returns the object that manages the connection to the zennium.

        :returns: Object with the connection to the zennium.
        """
        return self._zenniumConnection

    def createEpcScpiHandler(
        self, epcChannel: int, serialNumber: int
    ) -> EpcScpiHandler:
        """Returns the zennium connection object.

        This method initializes the external potentiostats and creates the objects.

        The objects are in SCPI mode after calling this function.
        For compatibility, the devices always start in EPC mode when connected to EPC, then they must
        be switched to SCPI standalone mode via Remote2. It is only possible to switch to SCPI mode via Remote2.

        :param epcChannel: Number of the EPC channel to which the device is connected via EPC cable.
            If a Rmux card is plugged in then the numbers have an offset.
        :param serialNumber: Serial number of the external potentiostat.
        :returns: Object with the external potentiostat.
        """
        newDevice = EpcScpiHandler(self.getSharedZennium(), epcChannel, serialNumber)

        deviceSearcher = SCPIDeviceSearcher()
        deviceSearcher.searchZahnerDevices()
        commandSerial: SerialCommandInterface = None
        dataSerial: SerialDataInterface = None

        try:
            commandSerial, dataSerial = deviceSearcher.selectDevice(serialNumber)
        except:
            pass

        """
        If the device is not found, then it is checked whether it is found as an EPC device.
        If it is found as an EPC device, it is switched to SCPI mode.
        """
        if commandSerial is None and dataSerial is None:
            newDevice.acquireSharedZennium()
            newDevice.sharedZenniumInterface.selectPotentiostat(epcChannel)
            name, serial = newDevice.sharedZenniumInterface.getDeviceInformation()
            newDevice.releaseSharedZennium()

            if serial not in str(serialNumber):
                raise ThalesRemoteError("Potentiostat is not found on the EPC channel.")

            newDevice.switchToSCPI()
        else:
            newDevice.connectSCPIDevice()

        listItem = HandlerDataItem(serialNumber, epcChannel, newDevice)

        self._handlerList.append(listItem)

        return newDevice

    def closeAll(self) -> None:
        """Close connections to all devices.

        This command closes all connections to the external potentiostats and to the Zennium.
        """
        for element in self._handlerList:
            element.handlerObject.close()

        self._handlerList = []

        self._zenniumConnection.disconnectFromTerm()
        return
