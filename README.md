# Thales-Remote-Python
Thales-Remote-Python is a Python extension which uses the Zahner [Remote2](http://zahner.de/pdf/Remote2.pdf) to control [Zahner Zennium Potentiostats](http://zahner.de/products/electrochemical-workstation.html).  
It was developed to **easily integrate** Zahner Zennium Potentiostats into Python scripts for more **complex measurement** tasks and for **automation purposes**.

The measurement methods EIS IE CV and DC sequences are supported. Also constant current or constant voltage can be output and current and voltage can be measured. Single frequency impedance measurement is also possible.

The Python extension will be extended in the future with all functions of the Remote2.

# :wrench: Installation
### With integrated development environment
With an integrated development environment, for example [Eclipse](https://www.eclipse.org/) with [PyDev](https://www.pydev.org/) extension, the package must be added to the project.
ThalesRemote can either be simply downloaded or best pulled with Git from the GitHub repository. With GitHub integration into the project, updates can be easily done.
If you are using Eclipse you can use the extension [EGit](https://www.eclipse.org/egit/) for this.

### Only Package download
Download the folder ThalesRemote and add it to the PYTHONPATH to access the library from Python.

# :hammer: Basic Usage

```python

'''
Connect to the Zahner Zennium Potentiostat
'''
ZenniumConnection = ThalesRemoteConnection()
ZenniumConnection.connectToTerm("localhost", "ScriptRemote")
ZahnerZennium = ThalesRemoteScriptWrapper(ZenniumConnection)
ZahnerZennium.forceThalesIntoRemoteScript()

'''
Read the currently measured voltage and current.
'''
print("Potential: " + str(ZahnerZennium.getPotential()))
print("Current: " + str(ZahnerZennium.getCurrent()))


'''
Single frequency impedance measurement at 1 V DC and 2 kHz
with 10mV amplitude for 3 periods.
'''
ZahnerZennium.setPotentiostatMode(PotentiostatMode.POTMODE_POTENTIOSTATIC)
ZahnerZennium.setPotential(1)
ZahnerZennium.enablePotentiostat()
    
ZahnerZennium.setFrequency(2000)
ZahnerZennium.setAmplitude(10e-3)
ZahnerZennium.setNumberOfPeriods(3)

ZahnerZennium.getImpedance()

ZahnerZennium.enablePotentiostat(False)

```
Complete detailed examples can be found in the main directory.

# :email: Have a question?
Send an <a href="mailto:support@zahner.de?subject=Thales-Remote-Python Question&body=Your Message">e-mail</a> to our support team.

# :interrobang: Found a bug or missing a specific feature?
Feel free to **create a new issue** with a respective title and description on the the [Thales-Remote-Python](https://github.com/Zahner-elektrik/Thales-Remote-Python/issues) repository. If you already found a solution to your problem, **we would love to review your pull request**!

# :white_check_mark: Requirements
The library was developed with python 3.9 using only standard libraries.  
It was tested with Python 3.9 and 3.8.5.

# :closed_book: License
Copyright 2020 ZAHNER-elektrik I. Zahner-Schiller GmbH & Co. KG

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.