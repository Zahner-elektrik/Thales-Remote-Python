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

import os
import threading
from thales_remote.connection import ThalesRemoteConnection
from _queue import Empty
import time

class ThalesFileInterface(object):
    """ Class which realizes the file transfer between Term software and Python.
    
    The measurement files cannot be stored on network drives with the Term software, therefore
    this class was implemented. If Python runs on another computer and controls Thales via network,
    then with this class the measurement result files can be exchanged via network.
    
    This class establishes an additional socket connection to the Term, which can be used to transfer
    individual files manually. Or you can set that all ism, isc or isw files are transferred automatically
    at the end of the measurement.
    
    :param address: IP address of the computer running the Term software.
    :param connectionName: The name of the connection default FileExchange. But can also be freely assigned.
    """
 
    def __init__(self, address, connectionName = "FileExchange"):
        self._deviceName = connectionName
        self.remoteConnection = ThalesRemoteConnection()
        self.remoteConnection.connectToTerm(address, self._deviceName)
        self._receiver_is_running = False
        self._automaticFileExchange = False
        self._filesToSkip = ["lastshot.ism"]
        self.receivedFiles = []
        self.pathToSave = os.getcwd()
        self._saveReceivedFilesToDisk = False
        self._keepFilesInObject = True
        return       
        
    def close(self):
        """ Close the file interface.
        
        The automatic file sending is disabled and the socket connection is closed.
        """
        self.disableAutomaticFileExchange()
        self.remoteConnection.disconnectFromTerm()
        return            
        
    def enableAutomaticFileExchange(self,enable = True, fileExtensions = "*.ism*.isc*.isw"):
        """ Turn on automatic file exchange.
        
        If automatic file exchange is enabled, the files configured with the fileExtensions variable are transferred automatically.
        
        In order for the files to be automatically saved to disk, this must be configured with the :func:`~thales_remote.file_interface.ThalesFileInterface.enableSaveReceivedFilesToDisk` method.
        With the method :func:`~thales_remote.file_interface.ThalesFileInterface.enableKeepReceivedFilesInObject`
        can be set whether the files should still remain in the Python object, so that you can read
        the received files as an array with :func:`~thales_remote.file_interface.ThalesFileInterface.getReceivedFiles`.
        The standard setting is that the files remain in the object.        
        
        :param enable: Enable automatic file exchange. Default = True.
        :param fileExtensions: File extensions that will be exchanged. You can see the default paramter.
            But you can also specify only one type of file or more.
        :type fileExtensions: string
        :returns: The response string from the device.
        :rtype: string  
        """
        if enable == True:
            retval = self.remoteConnection.sendStringAndWaitForReplyString(f"3,{self._deviceName},4,ON,{fileExtensions}", message_type=128, answer_message_type=132)
            self._startWorker()
        else:
            """
            Sending the command that no more data should be sent.
            Then wait 1 second until the Thales has possibly sent everything.
            Then stopp the worker thread.
            """
            retval = self.remoteConnection.sendStringAndWaitForReplyString(f"3,{self._deviceName},4,OFF", message_type=128, answer_message_type=132)
            time.sleep(1)
            self._stoppWorker()
        return retval
    
    def appendFilesToSkip(self, file):
        """ Set filenames to be filtered and not processed by Python.
        
        Files with these names are not saved to disk by Python and do not remain in the object.
        
        :param file: Filename or list with filenames to be filtered.
        """
        self._filesToSkip += file            
        return
        
    def disableAutomaticFileExchange(self):
        """ Turn off automatic file exchange.
        
        :returns: The response string from the device.
        :rtype: string  
        """
        return self.enableAutomaticFileExchange(False)
    
    def aquireFile(self,filename):
        r""" Transfer a single file.
        
        This command transfers a single from Term to Python.
        **This command can only be executed if automatic transfer is disabled.** If automatic transfer is enabled, None is returned.
        The parameter filename is used to specify the full path of the file, on the computer running
        the Thales software, to be transferred e.g. r"C:\\THALES\\temp\\test1\\myeis.ism".
        
        The function returns the file as dictionary. The dictionary has the following keys:
        
        * "name": Filename without path.
        * "path": Filename with path on the Thales computer.
        * "binary_data": Data as bytearray.
        
        If the file does not exist, the key "binary_data" contains an empty byte array.
        
        :param filename: Filename with path on the Thales computer.
        :type filename: string
        :returns: A dictionary with the file or None if this command is called when automatic file
            exchange is activated.
        :rtype: dictionary, None
        """
        file = None
        if self._receiver_is_running == False:
            self.remoteConnection.sendTelegram(f"3,{self._deviceName},1,{filename}", message_type=128)
            file = self._receiveFile()
        return file
    
    def setSavePath(self, path):
        r""" Set the path where the files should be saved on the local computer.
        
        This command sets only the path. If the path does not exist, it will be created.
        The path must be accessible by Python, otherwise there are no restrictions on the path.
        
        :param path: Path where the files should be saved. For example r"D:\\myLocalDirectory".
        :type path: string
        """
        self.pathToSave = path
        os.makedirs(self.pathToSave, exist_ok = True)
        return
    
    def enableSaveReceivedFilesToDisk(self,enable = True, path = None):
        r""" Enable the automatic saving of files to the hard disk.
        
        This command configures that the files are automatically saved by Python.
        With this command the path can be passed with the optional parameter path.
        The path must be accessible by Python, otherwise there are no restrictions on the path.
        Default path is the current working directory of Python.
        
        :param enable: Enable automatic file saving to the hard disk. Default = True.
        :param path: Optional path where the files should be saved. For example r"D:\\myLocalDirectory".
        :type path: string
        """
        if path is not None:
            self.setSavePath(path)
        self._saveReceivedFilesToDisk = enable
        return
        
    def disableSaveReceivedFilesToDisk(self):
        """ Disable the automatic saving of files to the hard disk.
        """
        return self.enableAutomaticFileExchange(False)
    
    def enableKeepReceivedFilesInObject(self,enable = True):
        """ Enable that the files remain in the Python object.
        
        If you perform many measurements, the Python object would grow larger and larger due to the
        number of files, so you can disable that the files are stored in the object as an array.
        By default, the files remain in the object.
        
        :param enable: True = Allow the files to remain in the object.
        """
        self._keepFilesInObject = enable
        return
    
    def disableKeepReceivedFilesInObject(self):
        """ Disable that the files remain in the Python object.
        """
        return self.enableKeepReceivedFilesInObject(False)
    
    def getReceivedFiles(self):
        """ Read all files from the Python object.
        
        This function returns an array. Each element in the array is a dictionary as described in
        function :func:`~thales_remote.file_interface.ThalesFileInterface.aquireFile`.
        
        
        :returns: Array with the files from the Python object.
        :rtype: array 
        """
        return self.receivedFiles
    
    def deleteReceivedFiles(self):
        """ Delete all files from the Python object.
        """
        self.receivedFiles = []
        return
        
    """
    The following methods should not be called by the user.
    They are marked with the prefix '_' after the Python convention for proteced.
    """
    
    def _saveReceivedFile(self, fileToWrite):
        """ Saves the passed file to disk.
        """
        if self._saveReceivedFilesToDisk == True:
            fileNameWithPath = os.path.join(self.pathToSave,fileToWrite["name"])
            
            file = open(fileNameWithPath,"wb")
            file.write(fileToWrite["binary_data"])
            file.close()
        return
    
    def _receiveFile(self, timeout = None):
        """ Receive one file with optional timeout.
        """
        retval = None
        try:
            filePath = self.remoteConnection.waitForStringTelegram(130,timeout = timeout)
        except Empty:
            return retval
        
        fileLength = int(self.remoteConnection.waitForStringTelegram(129))
        bytesToReceive = fileLength
        
        fileData = bytearray()
        while bytesToReceive > 0:
            receivedBytes = self.remoteConnection.waitForBinaryTelegram(131)
            fileData += receivedBytes
            bytesToReceive -= len(receivedBytes)
        
        retval = dict()
        
        fileSplit = filePath.split("\\")
        fileName = fileSplit[-1]
        
        retval["name"] = fileName
        retval["path"] = filePath
        retval["binary_data"] = fileData
        return retval
    
    def _startWorker(self):
        """ Starts the thread handling the asyncronously incoming data.
        """
        if self._receiver_is_running == False:
            self._receiver_is_running = True
            self.receivingWorker = threading.Thread(target=self._fileReceiverJob)
            self.receivingWorker.start()
        return
    
    def _stoppWorker(self):
        """ Stops the thread handling the incoming data gracefully.
        """
        if self._receiver_is_running == True:
            self._receiver_is_running = False
            self.receivingWorker.join()
        return
            
    def _fileReceiverJob(self):
        """ The method running in a separate thread, this method runs in a separate thread and manages the received files.
        """
        while self._receiver_is_running == True:
            try:
                file = self._receiveFile(1)
                if file is not None:
                    if file["name"] not in self._filesToSkip:
                        if self._keepFilesInObject == True:
                            self.receivedFiles.append(file)
                        
                        if self._saveReceivedFilesToDisk == True:
                            self._saveReceivedFile(file)
            except:
                self._receiver_is_running = False
        return
    