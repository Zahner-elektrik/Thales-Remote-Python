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

import socket
import time
import struct
import threading
from _socket import SHUT_RD

class ThalesRemoteConnection(object):
    '''
    Class to handle the Thales remote connection.
    '''
    
    def __init__(self):
        """
        Constructor
        """
        self.term_port = 260     #The port used by Thales
        self.socket_handle = None
        
        self.receivingWorker = None
        self.receivedTelegrams = []
        self.receivedTelegramsGuard = threading.Semaphore()
        self.telegramsAvailableMutex = threading.Semaphore()
        
        self._receiving_worker_is_running = False
                
        
    def connectToTerm(self, address, connectionName):
        ''' Connect to Term (The Thales Terminal)
        
        \param [in] address the hostname or ip-address of the host running Term
        \returns true on success, false if failed
        
        \todo actually just hangs if the host is up but Term has not been started.
        '''
        self.socket_handle = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try:
            self.socket_handle.connect((address,self.term_port))
        except:
            self.socket_handle = None
            print("could not connect to term")
            return False
            
        self._startTelegramListener()
        
        time.sleep(0.4)
        
        payload_length = len(connectionName)
        
        registration_packet = bytearray()
        registration_packet += bytearray(struct.pack('H', payload_length))
        registration_packet += bytearray([0x02,0xd0,0xff,0xff,0xff,0xff])
        registration_packet += bytearray(connectionName,'ASCII')
        
        self.socket_handle.sendall(registration_packet)
        
        time.sleep(0.8)
        
        return True
            
    def disconnectFromTerm(self):
        ''' Close the connection to Term and cleanup.
        
        Stops the thread used for receiving telegrams assynchronously and shuts down
        the network connection.
        '''
        self.sendTelegram("\0xFF\0xFF", 4)
        self._stopTelegramListener()
        self._closeSocket()
        
    def isConnectedToTerm(self):
        '''Check if the connection to Term is open.
        
        \returns true if connected, false if not.
        '''
        return self.socket_handle != None
        
    
        
            
    def sendTelegram(self, payload, message_type):
        '''Send a telegram (data) to Term.
        
        \param [in] payload the actual data which is being sent to Term. This can be a string or an bytearray.
        \param [in] message_type used internally by the DevCli dll. Depends on context. Most of the time 2.
        '''
        packet = bytearray()
        data = bytearray()
        
        if(isinstance(payload, str)):
            #datatype string
            payload_length = len(payload) # da bei c \0 folgt
            data += bytearray(payload,'ASCII')
        else:
            #datatype bytearray
            payload_length = len(payload)
            data = payload
        
        packet += bytearray(struct.pack('H', payload_length))
        packet += bytearray(struct.pack('B', message_type))
        packet += data
        self.socket_handle.sendall(packet)
        
            
    def waitForStringTelegram(self, timeout = None):
        ''' Block infinitely until the next Telegram is arriving.
        
        If some Telegram has already arrived it will just return the last one from the queue.
        
        \param [in] timout if used the timeout to receive data in seconds.
        
        \returns the last received telegram or an empty string if someting went wrong.
        '''
        while(self.telegramReceived() == False):
            if self.telegramsAvailableMutex.acquire(timeout = timeout) == False:
                return ""
        
        return self.receiveStringTelegram()
    
    
    def waitForTelegram(self, timeout = None):
        ''' Block infinitely until the next Telegram is arriving.
        
        If some Telegram has already arrived it will just return the last one from the queue.
        
        \param [in] timout if used the timeout to receive data in seconds.
        
        \returns the last received telegram or an empty byte array if something went wrong.
        '''
        while(self.telegramReceived() == False):
            if self.telegramsAvailableMutex.acquire(timeout = timeout) == False:
                return bytearray()
        
        return self.receiveTelegram()
    
           
    def receiveStringTelegram(self):
        ''' Immediately return the last received telegram.
        
        \returns the last received telegram or an empty string if no telegram was received or something went wrong.
        '''
        return self.receiveTelegram().decode("ASCII")
            
    def receiveTelegram(self):
        ''' Immediately return the last received telegram.
        
        \returns the last received telegram or an empty bytearray if no telegram was received or something went wrong.
        '''
        receivedTelegram = bytearray()
        
        self.receivedTelegramsGuard.acquire()
        
        if (len(self.receivedTelegrams) != 0):
            receivedTelegram = self.receivedTelegrams.pop(0)
        
        self.receivedTelegramsGuard.release()
        
        return receivedTelegram
        
    def sendStringAndWaitForReplyString(self, payload, message_type):
        ''' Convenience function: Send a telegram and wait for it's reply.
        
        \param [in] payload the actual data which is being sent to Term.
        \param [in] message_type used internally by the DevCli dll. Depends on context. Most of the time 2.
        \returns the last received telegram or an empty string if someting went wrong.
        
        \warning If the queue is not empty the last received telegram will be returned. Recommended to flush the queue first.
        '''
        self.sendTelegram(payload, message_type)
        return self.waitForStringTelegram()
            
    def telegramReceived(self):
        ''' Checks if there is some telegram in the queue.
        
        \returns true if there is some telegram in the queue and false if not.
        '''
        telegramsAvailable = False
        
        self.receivedTelegramsGuard.acquire()
        
        telegramsAvailable =  (len(self.receivedTelegrams) != 0)
        
        self.receivedTelegramsGuard.release()
        
        return telegramsAvailable
        
    def clearIncomingTelegramQueue(self):
        ''' Clears the queue of incoming telegrams.
        
        All telegrams received to this point will be discarded.
        
        \warning This does not stop new telegrams from being received after calling this method!
        '''
        self.receivedTelegramsGuard.acquire()
        
        while (len(self.receivedTelegrams) != 0):
            self.receivedTelegrams.pop()
            
        self.receivedTelegramsGuard.release()
        
    """
    The following methods should not be called by the user.
    They are marked with the prefix '_' after the Python convention for proteced.
    """
        
    def _telegramListenerJob(self):
        '''
        The method running in a separate thread, pushing the incomming packets into the queue.
        '''
        while self._receiving_worker_is_running:
            telegram = self._readTelegramFromSocket()
            if (len(telegram) > 0):
                self.receivedTelegramsGuard.acquire()
                self.receivedTelegrams.append(telegram)
                self.telegramsAvailableMutex.release()
                self.receivedTelegramsGuard.release()
                
                
            
    def _startTelegramListener(self):
        '''
        Starts the thread handling the asyncronously incoming data.
        '''
        self._receiving_worker_is_running = True
        self.telegramsAvailableMutex.acquire()
        self.receivingWorker = threading.Thread(target = self._telegramListenerJob)
        self.receivingWorker.start()
        
        
    def _stopTelegramListener(self):
        '''
        Stops the thread handling the incoming data gracefully.
        '''
        self.socket_handle.shutdown(SHUT_RD)
        self._receiving_worker_is_running = False
        self.receivingWorker.join()
        self.telegramsAvailableMutex.release()
            
    def _readTelegramFromSocket(self):
        '''
        Reads the raw telegram structure from the socket stream.
        '''
        try:
            header_bytes = self.socket_handle.recv(3)
            incoming_packet = self.socket_handle.recv(struct.unpack('Hx', header_bytes)[0])
        except:
            incoming_packet = bytearray()
        return incoming_packet
        
            
    def _closeSocket(self):
        '''
        Close the socket.
        '''
        self.socket_handle.close()
        self.socket_handle = None
        
        
        
