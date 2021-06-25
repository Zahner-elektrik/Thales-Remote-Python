"""
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
"""

import socket
import time
import struct
import threading
import queue
from _socket import SHUT_RD
from thales_remote.error import TermConnectionError


class ThalesRemoteConnection(object):
    """
    Class to handle the Thales remote connection.
    """
    
    def __init__(self):
        self.term_port = 260  # The port used by Thales
        self.socket_handle = None
        
        self.receivingWorker = None
        
        self.sendMutex = threading.Semaphore(1)
        
        self._receiving_worker_is_running = False
        
        self.queuesForChannels = dict()
        self.queuesForChannels[2] = queue.Queue()
        self.queuesForChannels[128] = queue.Queue()
        return
        
    def connectToTerm(self, address, connectionName):
        """ Connect to Term Software.
        
        
        :param address: The hostname or ip-address of the host running Term.
        :param connectionName: The name of the connection ScriptRemote for Remote and Logging as Online Display.
        :returns: True on success, False if failed.
        :rtype: bool
        """
        self.socket_handle = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket_handle.connect((address, self.term_port))
        except:
            self.socket_handle = None
            return False
            
        self._startTelegramListener()
        
        time.sleep(0.4)
        
        payload_length = len(connectionName)
        
        registration_packet = bytearray()
        registration_packet += bytearray(struct.pack('H', payload_length))
        registration_packet += bytearray([0x02, 0xd0, 0xff, 0xff, 0xff, 0xff])
        registration_packet += bytearray(connectionName, 'ASCII')
        
        self.sendMutex.acquire()
        self.socket_handle.sendall(registration_packet)
        self.sendMutex.release()
        
        time.sleep(0.8)
        
        return True
            
    def disconnectFromTerm(self):
        """ Close the connection to Term and cleanup.
        
        Stops the thread used for receiving telegrams assynchronously and shuts down
        the network connection. Put None into the Queues to free the waiting threads.
        They wait in waitForBinaryTelegram and if they receive None from the Queue, the will throw an exception.
        """
        self.sendTelegram("\0xFF\0xFF", 4)
        time.sleep(0.2)
        self._stopTelegramListener()
        time.sleep(0.2)
        self._closeSocket()
        for key in self.queuesForChannels.keys():
            self.queuesForChannels[key].put(None)
        return
        
    def isConnectedToTerm(self):
        """Check if the connection to Term is open.
        
        :returns: True if connected, False if not.
        :rtype: bool
        """
        return self.socket_handle != None
            
    def sendTelegram(self, payload, message_type, timeout=None):
        """Send a telegram (data) to Term.
        
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
        
        if(isinstance(payload, str)):
            # datatype string
            payload_length = len(payload)
            data += bytearray(payload, 'ASCII')
        else:
            # datatype bytearray
            payload_length = len(payload)
            data = payload
        
        packet += bytearray(struct.pack('H', payload_length))
        packet += bytearray(struct.pack('B', message_type))
        packet += data
        
        if self.sendMutex.acquire(True,timeout=timeout):
            self.socket_handle.settimeout(timeout)
            try:
                self.socket_handle.sendall(packet)
            finally:
                self.socket_handle.settimeout(None)
                self.sendMutex.release()
        else:
            """
            The semaphore to send could not be aquired within the timeout.
            There must be an error in the connection to the term.
            """
            raise TermConnectionError("Timeout aquiring send semaphore.")
        return
    
    
    def waitForBinaryTelegram(self, message_type=2, timeout=None):
        """ Block infinitely until the next Telegram is arriving.
        
        If some Telegram has already arrived it will just return the last one from the queue.
        
        :param message_type: Used internally by the DevCli dll. Depends on context. Most of the time 2.
        :param timeout: The timeout for sending data in seconds, blocking at None
        :returns: The response from the device or an empty bytearray if someting went wrong.
        :rtype: bytearray
        """
        retval = self.queuesForChannels[message_type].get(True, timeout=timeout)
        if retval == None:
            raise TermConnectionError("Error during data reception.")
        return retval
            
    def waitForStringTelegram(self, message_type=2, timeout=None):
        """ Block infinitely until the next Telegram is arriving.
        
        If some Telegram has already arrived it will just return the last one from the queue.
        
        :param message_type: Used internally by the DevCli dll. Depends on context. Most of the time 2.
        :param timeout: The timeout for sending data in seconds, blocking at None
        :returns: The last received telegram or an empty string if someting went wrong.
        :rtype: string
        """
        retval = self.waitForBinaryTelegram(message_type,timeout).decode("ASCII")
        return retval
        
    def sendStringAndWaitForReplyString(self, payload, message_type, timeout=None):
        """ Convenience function: Send a telegram and wait for it's reply.
        
        If a timeout or a socket error occurs an exception is thrown.
        
        
        :param payload: The actual data which is being sent to Term. This can be a string or an bytearray.
        :param message_type: Used internally by the DevCli dll. Depends on context. Most of the time 2.
        :param timeout: The timeout for sending data in seconds, blocking at None.
        :returns: The last received telegram or an empty string if someting went wrong.
        :rtype: string
        """
        self.sendTelegram(payload, message_type, timeout)
        return self.waitForStringTelegram(message_type, timeout)
        
    """
    The following methods should not be called by the user.
    They are marked with the prefix '_' after the Python convention for proteced.
    """
        
    def _telegramListenerJob(self):
        """
        The method running in a separate thread, pushing the incomming packets into the queues.
        """
        while self._receiving_worker_is_running:
            message_type, telegram = self._readTelegramFromSocket()
            if len(telegram) > 0 and (message_type == 2 or message_type == 128):
                self.queuesForChannels[message_type].put(telegram)
            elif message_type == None:
                """
                An error has occurred in the connection. None is passed into all queues to free
                the waiting threads from the queue. If they have received None, they throw an exception.
                The thread is then exited.
                """
                for key in self.queuesForChannels.keys():
                    self.queuesForChannels[key].put(None)
                self._receiving_worker_is_running = False
        return
            
    def _startTelegramListener(self):
        """
        Starts the thread handling the asyncronously incoming data.
        """
        self._receiving_worker_is_running = True
        self.receivingWorker = threading.Thread(target=self._telegramListenerJob)
        self.receivingWorker.start()
        
    def _stopTelegramListener(self):
        """
        Stops the thread handling the incoming data gracefully.
        """
        self.socket_handle.shutdown(SHUT_RD)
        self._receiving_worker_is_running = False
        self.receivingWorker.join()
            
    def _readTelegramFromSocket(self):
        """
        Reads the raw telegram structure from the socket stream.
        
        When a socket exception occurs, None and an empty byte array are returned.
        The caller of the function then passes the None to the queue to raise an
        exception in the threads waiting at the queue.
        """
        try:
            header_len = self.socket_handle.recv(2)
            header_type = self.socket_handle.recv(1)
            header_type = struct.unpack('B', header_type)[0]
            incoming_packet = self.socket_handle.recv(struct.unpack('H', header_len)[0])
        except:
            header_type = None
            incoming_packet = bytearray()
        return header_type, incoming_packet
            
    def _closeSocket(self):
        """
        Close the socket.
        """
        self.socket_handle.close()
        self.socket_handle = None
        
