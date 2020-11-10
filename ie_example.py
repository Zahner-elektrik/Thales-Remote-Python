'''
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
'''
 
from ThalesRemoteConnection import ThalesRemoteConnection
from ThalesRemoteScriptWrapper import ThalesRemoteScriptWrapper

TARGET_HOST = "localhost"

if __name__ == '__main__':
    '''
    The Thales software must first be started so that it can be connected.
    '''
    ZenniumConnection = ThalesRemoteConnection()
    connectionSuccessful = ZenniumConnection.connectToTerm(TARGET_HOST, "ScriptRemote")
    if connectionSuccessful:
        print("connection successfull")
    else:
        print("connection not possible")
        
    ZahnerZennium = ThalesRemoteScriptWrapper(ZenniumConnection)

    ZahnerZennium.forceThalesIntoRemoteScript()
    
    '''
    Measure cv with a sequential number in the file name that has been specified.
    Starting with number 1.
    '''
    ZahnerZennium.setIENaming("counter")
    ZahnerZennium.setIECounter(1)
    ZahnerZennium.setIEOutputPath("C:\\THALES\\temp\\ie")
    ZahnerZennium.setIEOutputFileName("ie_steady")
    
    '''
    Setting the parameters for the cv measurment.
    Alternatively a rule file can be used as a template.
    '''
    ZahnerZennium.setIEFirstEdgePotential(1)
    ZahnerZennium.setIEFirstEdgePotentialRelation("absolute")
    ZahnerZennium.setIESecondEdgePotential(1.1)
    ZahnerZennium.setIESecondEdgePotentialRelation("absolute")
    ZahnerZennium.setIEThirdEdgePotential(0.9)
    ZahnerZennium.setIEThirdEdgePotentialRelation("absolute")
    ZahnerZennium.setIEFourthEdgePotential(1)
    ZahnerZennium.setIEFourthEdgePotentialRelation("absolute")
    
    ZahnerZennium.setIEPotentialResolution(0.01)
    ZahnerZennium.setIEMinimumWaitingTime(1)
    ZahnerZennium.setIEMaximumWaitingTime(15)
    ZahnerZennium.setIERelativeTolerance(0.01)  #1 %
    ZahnerZennium.setIEAbsoluteTolerance(0.001) #1 mA
    ZahnerZennium.setIEOhmicDrop(0)
    ZahnerZennium.setIESweepMode("steady state")
    ZahnerZennium.setIEScanRate(0.05)
    ZahnerZennium.setIEMaximumCurrent(0.01)
    ZahnerZennium.setIEMinimumCurrent(-0.01)
    
    ZahnerZennium.checkIESetup()
    ZahnerZennium.applyIESetup()
    
    for i in range(2):
        ZahnerZennium.measureIE()
        
    '''
    Another IE with dynamic scan.
    The names of the measurement results are extended with date and time.
    '''
    ZahnerZennium.setIESweepMode("dynamic scan")
    ZahnerZennium.setIENaming("dateTime")
    ZahnerZennium.setIEOutputFileName("ie_dynamic")
    
    ZahnerZennium.checkIESetup()
    ZahnerZennium.applyIESetup()
    
    for i in range(2):
        ZahnerZennium.measureIE()
        
    '''
    Another IE with fixed sampling.
    The names of the measurement results are extended with date and time.
    '''
    ZahnerZennium.setIESweepMode("fixed sampling")
    ZahnerZennium.setIEOutputFileName("ie_fixed")
    
    ZahnerZennium.checkIESetup()
    ZahnerZennium.applyIESetup()
    
    for i in range(2):
        ZahnerZennium.measureIE()
    
    
    
    ZenniumConnection.disconnectFromTerm()
    print("finish")
