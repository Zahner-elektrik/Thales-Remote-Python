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
import threading
import queue

from datetime import datetime


class DeltaConnectionError(Exception):
    """Delta Connection Exception Class

    This exception is thrown when an error occurs with the term communication,
    which has not yet been thrown by a socket exception.

    After this error the connection must be completely rebuilt.
    """

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class DeltaConnection(object):
    """
    Class to handle the connection to the Delta Elektronika power supply connection.
    """

    def __init__(self):
        self.bufferSize = 128
        self.socket_handle = None
        self.receivingWorker = None
        self._receiving_worker_is_running = False

        self.sendMutex = threading.Semaphore(1)
        self.receiveQueue = queue.Queue()

        return

    def connect(self, ip, port):
        """Connect to Delta Elektronika power supply.

        :param ip: The hostname or ip-address of the Delta Elektronika power supply.
        :param port: The port.
        :returns: True on success, False if failed.
        :rtype: bool
        """
        self.ip = ip
        self.port = port
        self.socket_handle = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket_handle.connect((self.ip, self.port))
        except:
            self.socket_handle = None
            return False

        self._startTelegramListener()

        return True

    def disconnect(self):
        """Close the connection."""
        self._stopTelegramListener()
        self._closeSocket()
        self.receiveQueue.put(None)
        return

    def isConnected(self):
        """Check if the connection to the Delta Elektronika is open.

        :returns: True if connected, False if not.
        :rtype: bool
        """
        return self.socket_handle != None

    def sendTelegram(self, payload, timeout=None):
        """Send a telegram/data.

        :param payload: The actual data which is being sent. This can be a string or an bytearray.
        :param timeout: The timeout for sending data in seconds, blocking at None.
        """
        packet = bytearray()

        if isinstance(payload, str):
            packet += bytearray(payload, "UTF-8")
        else:
            # datatype bytearray
            packet = payload

        if self.sendMutex.acquire(True, timeout=timeout):
            self.socket_handle.settimeout(timeout)
            try:
                self.socket_handle.sendall(packet)
            finally:
                self.socket_handle.settimeout(None)
                self.sendMutex.release()
        else:
            raise DeltaConnectionError("Socket error during data transmission.")
        return

    def waitForBinaryTelegram(self, timeout=None):
        """Block infinitely until the next Telegram is arriving.

        If some Telegram has already arrived it will just return the last one from the queue.

        :param timeout: The timeout for sending data in seconds, blocking at None
        :returns: The response from the device or an empty bytearray if someting went wrong.
        :rtype: bytearray
        """
        retval = self.receiveQueue.get(True, timeout=timeout)
        if retval is None:
            raise DeltaConnectionError("Socket error during data reception.")
        return retval

    def waitForStringTelegram(self, timeout=None):
        """Block infinitely until the next Telegram is arriving.

        If some Telegram has already arrived it will just return the last one from the queue.

        :param timeout: The timeout for sending data in seconds, blocking at None
        :returns: The last received telegram or an empty string if someting went wrong.
        :rtype: string
        """
        retval = self.waitForBinaryTelegram(timeout).decode("UTF-8")
        return retval

    def sendStringAndWaitForReplyString(self, payload, timeout=None):
        """Convenience function: Send a telegram and wait for it's reply.

        If a timeout or a socket error occurs an exception is thrown.

        :param payload: The actual data which is being sent. This can be a string or an bytearray.
        :param timeout: The timeout for sending data in seconds, blocking at None.
        :returns: The last received telegram or an empty string if someting went wrong.
        :rtype: string
        """
        self.sendTelegram(payload, timeout)
        return self.waitForStringTelegram(timeout)

    """
    The following methods should not be called by the user.
    They are marked with the prefix '_' after the Python convention for proteced.
    """

    def _telegramListenerJob(self):
        """The method running in a separate thread, pushing the incomming packets into the queues."""
        while self._receiving_worker_is_running:
            telegram = self._readTelegramFromSocket()
            self.receiveQueue.put(telegram)
            if len(telegram) == 0:
                self._receiving_worker_is_running = False
        return

    def _startTelegramListener(self):
        """Starts the thread handling the asyncronously incoming data."""
        self._receiving_worker_is_running = True
        self.receivingWorker = threading.Thread(target=self._telegramListenerJob)
        self.receivingWorker.start()
        return

    def _stopTelegramListener(self):
        """Stops the thread handling the incoming data gracefully."""
        self._receiving_worker_is_running = False
        self.socket_handle.shutdown(socket.SHUT_RDWR)
        self.receivingWorker.join()
        return

    def _readTelegramFromSocket(self):
        """Reads the raw telegram structure from the socket stream.

        When a socket exception occurs, None and an empty byte array are returned.
        The caller of the function then passes the None to the queue to raise an
        exception in the threads waiting at the queue.
        """
        try:
            data = self.socket_handle.recv(self.bufferSize)
        except:
            data = bytearray()
        return data

    def _closeSocket(self):
        """Close the socket."""
        self.socket_handle.close()
        self.socket_handle = None
        return
