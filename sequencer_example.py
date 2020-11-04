"""
  ____       __                        __    __   __      _ __
 /_  / ___ _/ /  ___  ___ ___________ / /__ / /__/ /_____(_) /__
  / /_/ _ `/ _ \/ _ \/ -_) __/___/ -_) / -_)  '_/ __/ __/ /  '_/
 /___/\_,_/_//_/_//_/\__/_/      \__/_/\__/_/\_\\__/_/ /_/_/\_\

Copyright 2020 ZAHNER-elektrik I. Zahner-Schiller GmbH & Co. KG

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
 
from ThalesRemoteConnection import ThalesRemoteConnection
from ThalesRemoteScriptWrapper import ThalesRemoteScriptWrapper

TARGET_HOST = "localhost"

if __name__ == '__main__':
    thalesConnection = ThalesRemoteConnection()
    connectionSuccessful = thalesConnection.connectToTerm(TARGET_HOST, "ScriptRemote")
    if connectionSuccessful:
        print("connection successfull")
    else:
        print("connection not possible")
        
    remoteScript = ThalesRemoteScriptWrapper(thalesConnection)

    remoteScript.forceThalesIntoRemoteScript()
    
    '''
    Select the sequence to run.
     
    The sequences must be stored under "C:\THALES\script\sequencer\sequences\".
    Sequences from 0 to 9 can be created.
    These must have the names from "sequence00.seq" to "sequence09.seq".
    '''
    remoteScript.selectSequence(0)
     
    '''
    Run the sequence.
    '''
    remoteScript.runSequence()

    '''
    By default the main potentiostat with the number 0 is selected.
    1 corresponds to the external potentiostat connected to EPC channel 1.
    '''
    remoteScript.selectPotentiostat(1)

    '''
    Execute a sequence that can be stored anywhere.
    
    This sequence file is copied by this function as sequence 9 to the Thales directory.
    Then sequence 9 is selected and executed.
    '''
    remoteScript.runSequenceFile("C:/Users/XXX/Desktop/myZahnerSequence.seq")
    
    thalesConnection.disconnectFromTerm()
    print("finish")
