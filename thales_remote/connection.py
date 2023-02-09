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

import socket
import time
import struct
import threading
import queue
from typing import Optional, Union
from _socket import SHUT_RD
from thales_remote.error import TermConnectionError

from datetime import datetime


class ThalesRemoteConnection(object):
    """
    Class to handle the Thales remote connection.
    """

    _term_port: int
    _socket_handle: Optional[socket.socket]
    _receiving_worker: Optional[threading.Thread]
    _send_mutex: threading.Semaphore
    _receiving_worker_is_running: bool
    _available_channels: list[int]
    _queuesForChannels: dict[int, queue.Queue[Optional[bytes]]]
    _connectionName: str

    def __init__(self):
        self._term_port = 260  # The port used by Thales
        self._socket_handle = None
        self._receiving_worker = None
        self._send_mutex = threading.Semaphore(1)
        self._receiving_worker_is_running = False
        self._available_channels = [2, 128, 129, 130, 131, 132]
        self._queuesForChannels = dict()

        for channel in self._available_channels:
            self._queuesForChannels[channel] = queue.Queue()

        self._connectionName = ""

    # methods for context handler
    # documentation: https://docs.python.org/3/reference/datamodel.html#context-managers
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._socket_handle is not None:
            self.disconnectFromTerm()

    def connectToTerm(
        self, address: str, connection_name: str = "ScriptRemote"
    ) -> bool:
        """
        Connect to Term Software.

        :param address: hostname or ip-address of the host running "Term" application
        :param connection_name: name of the connection ScriptRemote for Remote and Logging as Online Display
        :returns: True on success, False on failure
        """
        time.sleep(0.4)
        self._socket_handle = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self._socket_handle.connect((address, self._term_port))
        except:
            raise TermConnectionError("Connection to the Term not possible.")

        self._startTelegramListener()

        time.sleep(0.4)

        self._connectionName = connection_name
        payload_length = len(connection_name)

        registration_packet = bytearray()
        registration_packet += bytearray(struct.pack("<H", payload_length))
        registration_packet += bytearray([0x12, 0xD0, 0xFF, 0xFF, 0xFF, 0xFF])
        registration_packet += bytearray(connection_name, "ASCII")

        # print("\n" + str(datetime.now().time()) + " send:")
        # print(f"payload_length: {payload_length}")
        # print(f"registration_packet: {registration_packet}")
        # print("complete packet:" + str(registration_packet))

        self._send_mutex.acquire()
        self._socket_handle.sendall(registration_packet)
        self._send_mutex.release()

        time.sleep(0.8)

        return True

    def getConnectionName(self) -> str:
        """
        get the connection name

        :returns: name of the connection
        """
        return self._connectionName

    def disconnectFromTerm(self) -> None:
        """
        close the connection to Term and cleanup

        Stops the thread used for receiving telegrams assynchronously and shuts down
        the network connection. Put None into the Queues to free the waiting threads.
        They wait in waitForBinaryTelegram and if they receive None from the Queue, the will throw an exception.
        """
        self.sendStringAndWaitForReplyString(
            "3," + str(self._connectionName) + ",0,RS", 128
        )
        time.sleep(0.2)
        self.sendTelegram(bytearray([255, 255]), 4)
        time.sleep(0.2)
        self._stopTelegramListener()
        time.sleep(0.2)
        self._closeSocket()
        for key in self._queuesForChannels.keys():
            self._queuesForChannels[key].put(None)
        return

    def isConnectedToTerm(self) -> bool:
        """
        check if the connection to Term is open

        :returns: True if connected, False otherwise
        """
        return self._socket_handle != None

    def sendTelegram(
        self,
        payload: Union[str, bytearray],
        message_type: int,
        timeout: Optional[float] = None,
    ) -> None:
        """
        send a telegram (data) to Term

        Sending a telegram to the term.
        If the other thread hangs while sending and the semaphore cannot be aquired within the timout,
        then a TermConnectionError is thrown. If a timeout occurs in the socket,
        then an exception is thrown by the socket.

        :param payload: The actual data which is being sent to Term. This can be a string or an bytearray.
        :param message_type: Used internally by the DevCli dll. Depends on context. Most of the time 2.
        :param timeout: The timeout for sending data in seconds, blocking at None.
        """
        packet = bytearray()
        data = bytearray()

        if isinstance(payload, str):
            # datatype string
            payload_length = len(payload)
            data += bytearray(payload, "ASCII")
        else:
            # datatype bytearray
            payload_length = len(payload)
            data = payload

        packet += bytearray(struct.pack("<H", payload_length))
        packet += bytearray(struct.pack("<B", message_type))
        packet += data

        if self._send_mutex.acquire(True, timeout=timeout):
            self._socket_handle.settimeout(timeout)
            try:
                # print("\n" + str(datetime.now().time()) + " send:")
                # print(f"payload_length: {payload_length} message_type: {message_type}")
                # print(f"payload: {data}")
                # print("complete packet:" + str(packet))

                self._socket_handle.sendall(packet)
            finally:
                self._socket_handle.settimeout(None)
                self._send_mutex.release()
        else:
            """
            The semaphore to send could not be aquired within the timeout.
            There must be an error in the connection to the term.
            """
            raise TermConnectionError("Socket error during data transmission.")
        return

    def waitForBinaryTelegram(
        self, message_type: int = 2, timeout: Optional[float] = None
    ) -> bytes:
        """
        block infinitely until the next Telegram is arriving

        If some Telegram has already arrived it will just return the last one from the queue.

        :param message_type: Used internally by the DevCli dll. Depends on context. Most of the time 2.
        :param timeout: The timeout for sending data in seconds, blocking at None
        :returns: The response from the device or an empty bytearray if someting went wrong.
        :rtype: bytearray
        """
        retval = self._queuesForChannels[message_type].get(True, timeout=timeout)
        if retval is None:
            raise TermConnectionError("Socket error during data reception.")
        return retval

    def waitForStringTelegram(
        self, message_type: int = 2, timeout: Optional[float] = None
    ) -> str:
        """
        block infinitely until the next Telegram is arriving

        If some Telegram has already arrived it will just return the last one from the queue.

        :param message_type: Used internally by the DevCli dll. Depends on context. Most of the time 2.
        :param timeout: The timeout for sending data in seconds, blocking at None
        :returns: The last received telegram or an empty string if someting went wrong.
        :rtype: string
        """
        retval = self.waitForBinaryTelegram(message_type, timeout).decode("ASCII")
        return retval

    def sendStringAndWaitForReplyString(
        self,
        payload: Union[str, bytearray],
        message_type: int,
        timeout: Optional[float] = None,
        answer_message_type: int = None,
    ) -> str:
        """
        convenience function: send a telegram and wait for it's reply

        If a timeout or a socket error occurs an exception is thrown.


        :param payload: The actual data which is being sent to Term. This can be a string or an bytearray.
        :param message_type: Used internally by the DevCli dll. Depends on context. Most of the time 2.
        :param timeout: The timeout for sending data in seconds, blocking at None.
        :returns: The last received telegram or an empty string if someting went wrong.
        :rtype: string
        """
        if answer_message_type is None:
            answer_message_type = message_type
        self.sendTelegram(payload, message_type, timeout)
        return self.waitForStringTelegram(answer_message_type, timeout)

    # The following methods should not be called by the user.
    # They are marked with the prefix '_' after the Python convention for proteced.

    def _telegramListenerJob(self) -> None:
        """
        runs in a separate thread, pushing the incomming packets into the queues.
        """
        while self._receiving_worker_is_running:
            message_type, telegram = self._readTelegramFromSocket()
            if len(telegram) > 0 and message_type in self._available_channels:
                self._queuesForChannels[message_type].put(telegram)
            elif message_type is None:
                # An error has occurred in the connection. None is passed into all queues to free
                # the waiting threads from the queue. If they have received None, they throw an exception.
                # The thread is then exited.
                for key, value in self._queuesForChannels.items():
                    value.put(None)
                self._receiving_worker_is_running = False
        return

    def _startTelegramListener(self) -> None:
        """
        starts the thread handling the asyncronously incoming data
        """
        self._receiving_worker_is_running = True
        self._receiving_worker = threading.Thread(target=self._telegramListenerJob)
        self._receiving_worker.start()
        return

    def _stopTelegramListener(self) -> None:
        """
        stops the thread handling the incoming data gracefully
        """
        self._socket_handle.shutdown(SHUT_RD)
        self._receiving_worker_is_running = False
        self._receiving_worker.join()
        return

    def _readTelegramFromSocket(self) -> tuple[Optional[str], bytearray]:
        """
        reads the raw telegram structure from the socket stream

        When a socket exception occurs, None and an empty byte array are returned.
        The caller of the function then passes the None to the queue to raise an
        exception in the threads waiting at the queue.
        """
        try:
            header_len: bytes = self._socket_handle.recv(2)
            header_type_bytes: bytes = self._socket_handle.recv(1)
            header_type: str = struct.unpack("<B", header_type_bytes)[
                0
            ]  # actually a character, not a str
            incoming_packet: int = self._socket_handle.recv(
                struct.unpack("<H", header_len)[0]
            )

            # print("\n" + str(datetime.now().time()) + " read:")
            # print(f"payload_length: {struct.unpack('<H', header_len)[0]} message_type: {header_type}")
            # print(f"payload: {incoming_packet}")
            # print("complete packet:" + str(header_len + header_type_bytes + incoming_packet))

        except:
            header_type = None
            incoming_packet = bytearray()
        return header_type, incoming_packet

    def _closeSocket(self) -> None:
        """
        close the socket
        """
        self._socket_handle.close()
        self._socket_handle = None
        return
