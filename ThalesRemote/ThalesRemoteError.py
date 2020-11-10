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



'''
The following is an example for troubleshooting when an exception is thrown.

----Example exception----
Traceback (most recent call last):
  File "C:\XXX\Thales-Remote-Python\ie_example.py", line 62, in <module>
    ZahnerZennium.setIESecondEdgePotential(10000)
  File "C:\XXX\Thales-Remote-Python\ThalesRemote\ThalesRemoteScriptWrapper.py", line 648, in setIESecondEdgePotential
    return self.setValue("IE_EckPot2", potential)
  File "C:\XXX\Thales-Remote-Python\ThalesRemote\ThalesRemoteScriptWrapper.py", line 1026, in setValue
    raise ThalesRemoteError(reply.rstrip("\r") + ThalesRemoteScriptWrapper.undefindedStandardErrorString)
ThalesRemoteError.ThalesRemoteError: ERROR;100;1

----Explanation----

In the last line you can see what kind of error has occurred:

ThalesRemoteError.ThalesRemoteError: ERROR;100;1
    ^                                       ^
    |                                       |
    |        Error number from the Remote2 manual http://zahner.de/pdf/Remote2.pdf
    |        You can see in the table in chapter 7 of the manual:
    |        100 | ERROR_PARAMETER_OUT_OF_RANGE | Sent value too low/high
    |
    ThalesRemoteError shows that it is an error generated by the library due to a response from the Zenniums containing an error.

The first two lines of the traceback show the file and line number and the content of the line where the error occurred.  
                          
  File "C:\XXX\Thales-Remote-Python\ie_example.py", line 62, in <module>
    ZahnerZennium.setIESecondEdgePotential(10000)
    
            The error occurred in line 62 of the file ie_example.py with the statement ZahnerZennium.setIESecondEdgePotential(10000).
            This means that the value 10000, which should be set, is out of the allowed range.
'''


class ThalesRemoteError(Exception):
    '''
    Thales Exception Class
    '''

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
