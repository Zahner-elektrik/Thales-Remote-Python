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
 
import sys
from thales_remote.connection import ThalesRemoteConnection
from thales_remote.script_wrapper import ThalesRemoteScriptWrapper

TARGET_HOST = "localhost"

if __name__ == "__main__":
    '''
    The Thales software must first be started so that it can be connected.
    '''
    ZenniumConnection = ThalesRemoteConnection()
    connectionSuccessful = ZenniumConnection.connectToTerm(TARGET_HOST, "ScriptRemote")
    if connectionSuccessful:
        print("connection successfull")
    else:
        print("connection not possible")
        sys.exit()
        
    ZahnerZennium = ThalesRemoteScriptWrapper(ZenniumConnection)

    ZahnerZennium.forceThalesIntoRemoteScript()
    
    '''
    Measurement of sequences and storage of sequences with date and time.
    '''
    ZahnerZennium.setSequenceNaming("dateTime")
    ZahnerZennium.setSequenceOutputPath(r"C:\THALES\temp\test1")
    ZahnerZennium.setSequenceOutputFileName("batterysequence")
    
    '''
    Select the sequence to run.
     
    The sequences must be stored under "C:\THALES\script\sequencer\sequences\".
    Sequences from 0 to 9 can be created.
    These must have the names from "sequence00.seq" to "sequence09.seq".
    '''
    ZahnerZennium.selectSequence(0)
     
    '''
    Run the sequences.
    '''
    for i in range(3):
        ZahnerZennium.runSequence()

    '''
    By default the main potentiostat with the number 0 is selected.
    1 corresponds to the external potentiostat connected to EPC channel 1.
    '''
    ZahnerZennium.selectPotentiostat(1)

    '''
    Measureing the next sequences with a sequential number in the file name that has been specified.
    Starting with number 13.
    '''
    ZahnerZennium.setSequenceNaming("counter")
    ZahnerZennium.setSequenceCounter(13)
    ZahnerZennium.setSequenceOutputPath(r"C:\THALES\temp\test1")
    ZahnerZennium.setSequenceOutputFileName("batterysequence")

    '''
    Execute a sequence that can be stored anywhere.
    
    This sequence file is copied by this function as sequence 9 to the Thales directory.
    Then sequence 9 is selected and executed.
    '''
    for i in range(3):
        ZahnerZennium.runSequenceFile(r"C:\Users\XXX\Desktop\myZahnerSequence.seq")
    
    '''
    Switch back to the main potentiostat and disconnect.
    '''
    ZahnerZennium.selectPotentiostat(0)
    
    ZenniumConnection.disconnectFromTerm()
    print("finish")
