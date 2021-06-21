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

import numpy as np
import datetime


class IsmImport(object):
    '''
    Class to be able to read out ism files.
    '''

    def __init__(self, filePath):
        '''Constructor
        
        This object contains the values from the ism file after intitialization.
        
        \param [in] filePath the path to the ism files.
        '''
        ismFile = open(filePath, 'rb')
        ismFile.read(6)
        numberOfElements = int.from_bytes(ismFile.read(6), "big", signed=True) + 1             
        tmpFrequency = np.ndarray(shape=(numberOfElements,), dtype='>f8', buffer=ismFile.read(8 * numberOfElements))
        tmpImpedance = np.ndarray(shape=(numberOfElements,), dtype='>f8', buffer=ismFile.read(8 * numberOfElements))
        tmpPhase = np.ndarray(shape=(numberOfElements,), dtype='>f8', buffer=ismFile.read(8 * numberOfElements))
        tmpTime = np.ndarray(shape=(numberOfElements,), dtype='>f8', buffer=ismFile.read(8 * numberOfElements))
        tmpSignificance = np.ndarray(shape=(numberOfElements,), dtype='>i2', buffer=ismFile.read(2 * numberOfElements))
        
        dateStringLength = int.from_bytes(ismFile.read(2), "big", signed=True)
        dateString = ismFile.read(dateStringLength)
        date = dateString[0:6].decode("ASCII")
        
        day = int(date[0:2])
        month = int(date[2:4])
        year = int(date[4:6])
        
        """
        Only the last two digits of the date are saved.
        It is assumed that the measurement was carried out between 1970 and 2070.
        A software update is necessary in the year 2070 at the latest.
        """
        if year < 70:
            year += 2000
        else:
            year += 1900
            
        self.measurementDate = datetime.datetime(year,month,day)
        
        self.frequency = np.zeros(len(tmpFrequency))
        for i in range(len(tmpFrequency)):
            self.frequency[i] = tmpFrequency[i]
        
        self.impedance = np.zeros(len(tmpImpedance))
        for i in range(len(tmpImpedance)):
            self.impedance[i] = tmpImpedance[i]
        
        self.phase = np.zeros(len(tmpPhase))
        for i in range(len(tmpPhase)):
            self.phase[i] = tmpPhase[i]
        
        self.significance = np.zeros(len(tmpSignificance))
        for i in range(len(tmpSignificance)):
            self.significance[i] = tmpSignificance[i]
        
        ismFile.close()
        
        '''
        Determination of the upper or lower reversing frequency in order to be
        able to output the range between the reversing frequency and the final frequency.
        '''
        self.firstUp = False
        if self.frequency[0] < self.frequency[1]:
            self.firstUp = True
        
        self.reverseIndex = 0
        oldFrequency = self.frequency[0]            
        for i in range(len(self.frequency)):
            if self.firstUp:
                if oldFrequency > self.frequency[i]:
                    self.reverseIndex = i
                    break
            else:
                if oldFrequency < self.frequency[i]:
                    self.reverseIndex = i
                    break
            oldFrequency = self.frequency[i]
        
        self.reverseIndex = self.reverseIndex - 1
        return
    
    def getFrequencyArray(self):
        '''Get the frequency points from the measurement.
        
        The frequency points between the reversal frequency and the final frequency are returned.
        
        \returns an numpy array with the frequency points.
        '''
        return np.flip(self.frequency[self.reverseIndex:])
    
    def getImpedanceArray(self):
        '''Get the impedance points from the measurement.
        
        The impedance points between the reversal frequency and the final frequency are returned.
        
        \returns an numpy array with the impedance points.
        '''
        return np.flip(self.impedance[self.reverseIndex:])
        
    def getPhaseArray(self):
        '''Get the phase points from the measurement.
        
        The phase points between the reversal frequency and the final frequency are returned.
        
        \returns an numpy array with the phase points.
        '''
        return np.flip(self.phase[self.reverseIndex:])
    
    def getComplexImpedanceArray(self):
        '''Get the complex impedance points from the measurement.
        
        The complex impedance points between the reversal frequency and the final frequency are returned.
        
        \returns an numpy array with the complex impedance points.
        '''
        freq = self.getFrequencyArray()
        imp = self.getImpedanceArray()
        phase = self.getPhaseArray()
        
        cplx = []
        for i in range(len(freq)):
            cplx.append(np.cos(phase[i]) * imp[i] + 1j * np.sin(phase[i]) * imp[i])
    
        return np.array(cplx)
    
    def getSignificanceArray(self):
        '''Get the significance points from the measurement.
        
        The significance points between the reversal frequency and the final frequency are returned.
        
        \returns an numpy array with the significance points.
        '''
        return np.flip(self.significance[self.reverseIndex:])
    
    def getMeasurementDate(self):
        '''Get the measurement date.
        
        Only the date of the measurement is saved. The measurement time is not saved in the ISM file.
        The time is initialized by Python with 00:00:00.
        
        \returns a python datetime object.
        '''
        return self.measurementDate
    
