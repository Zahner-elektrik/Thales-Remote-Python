# Thales-Remote-Python
Thales-Remote-Python is a Python extension which uses the Zahner [Remote2](http://zahner.de/pdf/Remote2.pdf) to control [Zahner Zennium Potentiostats](http://zahner.de/products/electrochemical-workstation.html).  
It was developed to **easily integrate** Zahner Zennium Potentiostats into Python scripts for more **complex measurement** tasks and for **automation purposes**.

The measurement methods **EIS**, **IE**, **CV** and **DC sequences** are supported. Also constant current or constant voltage can be output and current and voltage can be measured. Single frequency impedance measurement is also possible.

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
Read the measured voltage and current.
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

ZahnerZennium.disablePotentiostat()

```

# :book: Examples
There are several examples available on different topics.

### [general_example.py](general_example.py)

* Switch potentiostat on or off
* Setting potentiostat potentiostatic or galvanostatic
* Setting output potential or current
* Read potential and current
* Measure impedance

### [eis_import_plot_example.ipynb](eis_import_plot_example.ipynb)
This example also requires numpy, matplotlib and the package ThalesFileImport from the repository.  
This file also exists only as python without the Jupyter documentation.  
For the development numpy version 1.19.3 and matplotlib version 3.3.3 were used.

It is an example of the following possibilities:
* Measure an impedance spectra
* **Importing the measurement results from the ism file into python**
* Plotting the spectrum in bode and nyquist representation with the matplotlib library

### [eis_example.py](eis_example.py)

* Setting output file naming for impedance spectras
* Parametrizing an impedance spectrum
* Measurement with an external potentiostat (EPC-Device)

### [cv_example.py](cv_example.py)

* Setting output file naming for CV measurements
* Parametrizing an CV measurement
* Measurement with an external potentiostat (EPC-Device)

### [ie_example.py](ie_example.py)

* Setting output file naming for IE measurements
* Parametrizing an IE measurement

### [sequencer_example.py](sequencer_example.py)
With the [Zahner sequencer](http://zahner.de/files/sequencer-an-introduction.pdf), DC voltage and current curves defined in a text file can be output to the potentiostat.

* Setting output file naming for sequence measurements
* Parametrizing an sequence measurement
* Measurement with an external potentiostat (EPC-Device)

### [eis_pad4_example.ipynb](eis_pad4_example.ipynb)
This example also requires numpy, matplotlib and the package ThalesFileImport from the repository.  
This file also exists only as python without the Jupyter documentation.  
For the development numpy version 1.20.3 and matplotlib version 3.4.2 were used.

It is an example of the following possibilities:
* Measurement of an impedance spectrum on a stack with single cells connected to the PAD4 card.
* **Importing the measurement results from the ism file into python**
* Plotting the spectrum in bode and nyquist representation with the matplotlib library

### [ImpedanceMultiCellCycle.ipynb](https://github.com/Zahner-elektrik/Zahner-Remote-Python/blob/master/Examples/ImpedanceMultiCellCycle/ImpedanceMultiCellCycle.ipynb)

* Multichannel operation with several external potentiostats, of the latest generation, type **PP212, PP222, PP242 or XPOT2**.
* Control of standalone operation of external potentiostats with the [zahner_potentiostat](https://github.com/Zahner-elektrik/zahner_potentiostat) library.
* Shared [Zennium series](http://zahner.de/products/electrochemical-workstation.html) device for impedance measurements.

# :email: Haveing a question?
Send an <a href="mailto:support@zahner.de?subject=Thales-Remote-Python Question&body=Your Message">e-mail</a> to our support team.

# :interrobang: Found a bug or missing a specific feature?
Feel free to **create a new issue** with a respective title and description on the the [Thales-Remote-Python](https://github.com/Zahner-elektrik/Thales-Remote-Python/issues) repository. If you already found a solution to your problem, **we would love to review your pull request**!

# :white_check_mark: Requirements
The library was developed and tested with Python 3.9.5.\
Only standard python libraries were used.