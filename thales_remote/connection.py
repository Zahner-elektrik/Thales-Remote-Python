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

import socket
import time
import struct
import threading
import queue
from _socket import SHUT_RD


class ThalesRemoteConnection(object):
    '''
    Class to handle the Thales remote connection.
    '''
    
    def __init__(self):
        '''
        Constructor
        '''
        self.term_port = 260  # The port used by Thales
        self.socket_handle = None
        
        self.receivingWorker = None
        
        self.socketMutex = threading.Semaphore()
        self.socketMutex.release()
        
        self._receiving_worker_is_running = False
        
        self.queuesForChannels = dict()
        self.queuesForChannels[2] = queue.Queue()
        self.queuesForChannels[128] = queue.Queue()
        return
        
    def connectToTerm(self, address, connectionName):
        ''' Connect to Term (The Thales Terminal)
        
        \param [in] address the hostname or ip-address of the host running Term
        \returns true on success, false if failed
        
        \todo actually just hangs if the host is up but Term has not been started.
        '''
        self.socket_handle = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket_handle.connect((address, self.term_port))
        except:
            self.socket_handle = None
            print("could not connect to term")
            return False
            
        self._startTelegramListener()
        
        time.sleep(0.4)
        
        payload_length = len(connectionName)
        
        registration_packet = bytearray()
        registration_packet += bytearray(struct.pack('H', payload_length))
        registration_packet += bytearray([0x02, 0xd0, 0xff, 0xff, 0xff, 0xff])
        registration_packet += bytearray(connectionName, 'ASCII')
        
        self.socketMutex.acquire()
        self.socket_handle.sendall(registration_packet)
        self.socketMutex.release()
        
        time.sleep(0.8)
        
        return True
            
    def disconnectFromTerm(self):
        ''' Close the connection to Term and cleanup.
        
        Stops the thread used for receiving telegrams assynchronously and shuts down
        the network connection.
        '''
        self.sendTelegram("\0xFF\0xFF", 4)
        time.sleep(0.2)
        self._stopTelegramListener()
        time.sleep(0.2)
        self._closeSocket()
        
    def isConnectedToTerm(self):
        '''Check if the connection to Term is open.
        
        \returns true if connected, false if not.
        '''
        return self.socket_handle != None
            
    def sendTelegram(self, payload, message_type, timeout=None):
        '''Send a telegram (data) to Term.
        
        \param [in] payload the actual data which is being sent to Term. This can be a string or an bytearray.
        \param [in] message_type used internally by the DevCli dll. Depends on context. Most of the time 2.
        '''
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
        
        self.socketMutex.acquire()
        self.socket_handle.settimeout(timeout)
        try:
            self.socket_handle.sendall(packet)
        finally:
            self.socket_handle.settimeout(None)
            self.socketMutex.release()
            
    def waitForStringTelegram(self, message_type=2, timeout=None):
        ''' Block infinitely until the next Telegram is arriving.
        
        If some Telegram has already arrived it will just return the last one from the queue.
        
        \param [in] timout if used the timeout to receive data in seconds. In case of a timeout, an Empty exception is thrown.
        \param [in] message_type used internally by the DevCli dll. Depends on context. Most of the time 2.        
        \returns the last received telegram or an empty string if someting went wrong.
        '''
        retval = self.queuesForChannels[message_type].get(True, timeout=timeout).decode("ASCII")
        return retval
        
    def sendStringAndWaitForReplyString(self, payload, message_type, timeout=None):
        ''' Convenience function: Send a telegram and wait for it's reply.
        
        \param [in] payload the actual data which is being sent to Term.
        \param [in] message_type used internally by the DevCli dll. Depends on context. Most of the time 2.
        \param [in] timeout timeout in seconds, to wait vor an answer from the Term software.     
        \returns the last received telegram or an empty string if someting went wrong.
        
        \warning If the queue is not empty the last received telegram will be returned. Recommended to flush the queue first.
        '''
        self.sendTelegram(payload, message_type, timeout)
        return self.waitForStringTelegram(message_type, timeout)
        
    """
    The following methods should not be called by the user.
    They are marked with the prefix '_' after the Python convention for proteced.
    """
        
    def _telegramListenerJob(self):
        '''
        The method running in a separate thread, pushing the incomming packets into the queue.
        '''
        while self._receiving_worker_is_running:
            message_type, telegram = self._readTelegramFromSocket()
            if len(telegram) > 0 and (message_type == 2 or message_type == 128):
                self.queuesForChannels[message_type].put(telegram)
            
    def _startTelegramListener(self):
        '''
        Starts the thread handling the asyncronously incoming data.
        '''
        self._receiving_worker_is_running = True
        self.receivingWorker = threading.Thread(target=self._telegramListenerJob)
        self.receivingWorker.start()
        
    def _stopTelegramListener(self):
        '''
        Stops the thread handling the incoming data gracefully.
        '''
        self.socket_handle.shutdown(SHUT_RD)
        self._receiving_worker_is_running = False
        self.receivingWorker.join()
            
    def _readTelegramFromSocket(self):
        '''
        Reads the raw telegram structure from the socket stream.
        '''
        self.socketMutex.acquire()
        try:
            header_len = self.socket_handle.recv(2)
            header_type = self.socket_handle.recv(1)
            header_type = struct.unpack('B', header_type)[0]
            incoming_packet = self.socket_handle.recv(struct.unpack('H', header_len)[0])
        except:
            incoming_packet = bytearray()
            header_type = 2
        self.socketMutex.release()
        return header_type, incoming_packet
            
    def _closeSocket(self):
        '''
        Close the socket.
        '''
        self.socket_handle.close()
        self.socket_handle = None
        
