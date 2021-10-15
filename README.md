![Thales-Remote-Python](https://doc.zahner.de/github_resources/Thales-Remote-Python.png)

Thales-Remote-Python is a Python extension which uses the Zahner [Remote2](http://zahner.de/pdf/Remote2.pdf) to control [Zahner Zennium Potentiostats](http://zahner.de/products/electrochemical-workstation.html).  
It was developed to **easily integrate** [Zahner Zennium Potentiostats](http://zahner.de/products/electrochemical-workstation.html) into Python scripts for more **complex measurement** tasks and for **automation purposes**.

The measurement methods **EIS**, **IE**, **CV** and **DC sequences** are supported. Also constant current or constant voltage can be output and current and voltage can be measured. Single frequency impedance measurement is also possible. Other supported functions are the remote control of the [BC-MUX](http://zahner.de/products/multiplexer/bc-mux.html) and the import of ism files in Python.  

# 📚 Documentation

The complete documentation of the individual functions can be found on the [API documentation website](https://doc.zahner.de/thales_remote/).  


# 🔧 Installation

The library to control the potentiostats is located in the subfolder [thales_remote](thales_remote). The [thales_file_import](thales_file_import) subfolder contains the library for importing Thales file formats. The class [BCMuxInterface](https://doc.zahner.de/thales_remote/bc_mux_interface.html) to control the [BC-MUX](http://zahner.de/products/multiplexer/bc-mux.html) is located in the Python file [BCMuxInterface.py](Examples/BCMuxInterface/BCMuxInterface.py), from this file the class can be imported.

### With integrated development environment
With an integrated development environment, for example [Eclipse](https://www.eclipse.org/) with [PyDev](https://www.pydev.org/) extension, the package must be added to the project.
ThalesRemote can either be simply downloaded or best pulled with Git from the GitHub repository. With GitHub integration into the project, updates can be easily done.
If you are using Eclipse you can use the extension [EGit](https://www.eclipse.org/egit/) for this.

### Only Package download
Download the folder and place it in the project directory or add it to the PYTHONPATH to access the library from Python.

# 🔨 Basic Usage

```python
"""
Connect to the Zahner Zennium Potentiostat
"""
zenniumConnection = ThalesRemoteConnection()
zenniumConnection.connectToTerm("localhost", "ScriptRemote")
zahnerZennium = ThalesRemoteScriptWrapper(zenniumConnection)
zahnerZennium.forceThalesIntoRemoteScript()

"""
Read the measured voltage and current.
"""
print("Potential: " + str(zahnerZennium.getPotential()))
print("Current: " + str(zahnerZennium.getCurrent()))


"""
Single frequency impedance measurement at 1 V DC and 2 kHz
with 10mV amplitude for 3 periods.
"""
zahnerZennium.setPotentiostatMode(PotentiostatMode.POTMODE_POTENTIOSTATIC)
zahnerZennium.setPotential(1)

zahnerZennium.enablePotentiostat()
    
zahnerZennium.setFrequency(2000)
zahnerZennium.setAmplitude(10e-3)
zahnerZennium.setNumberOfPeriods(3)

zahnerZennium.getImpedance()

zahnerZennium.disablePotentiostat()
```

# 📖 Examples
There are several examples which are structured according to electrochemical methods. [BasicIntroduction.ipynb](Examples/BasicIntroduction/BasicIntroduction.ipynb) is the most basic introduction, which describes the connection setup in detail.  
Unlike the examples, the methods can be flexibly combined in a Python script, for example a CV measurement followed by an EIS measurement.

### [BasicIntroduction.ipynb](Examples/BasicIntroduction/BasicIntroduction.ipynb)

* Basic introduction to remote control
* Switch potentiostat on or off
* Setting potentiostat potentiostatic or galvanostatic
* Setting output potential or current
* Read potential and current
* Measure impedance

### [EISImportPlot.ipynb](Examples/EISImportPlot/EISImportPlot.ipynb)

* Measure an impedance spectra
* **Importing the measurement results from the ism file into python**
* **Plotting the spectrum in bode and nyquist representation with the matplotlib library**

### [EIS.ipynb](Examples/EIS/EIS.ipynb)

* Setting output file naming for impedance spectras
* Parametrizing an impedance spectrum
* Measurement with an external potentiostat (EPC-Device)

### [CyclicVoltammetry.ipynb](Examples/CyclicVoltammetry/CyclicVoltammetry.ipynb)

* Setting output file naming for CV measurements
* Parametrizing an CV measurement
* Measurement with an external potentiostat (EPC-Device)

### [CurrentVoltageCurve.ipynb](Examples/CurrentVoltageCurve/CurrentVoltageCurve.ipynb)

* Setting output file naming for IE measurements
* Parametrizing an IE measurement

### [DCSequencer.ipynb](Examples/DCSequencer/DCSequencer.ipynb)

* The [Zahner sequencer](http://zahner.de/files/sequencer-an-introduction.pdf) outputs current and voltage curves defined in a text file.
* Setting output file naming for sequence measurements
* Parametrizing an sequence measurement
* Measurement with an external potentiostat (EPC-Device)

### [EISPad4.ipynb](Examples/EISPad4/EISPad4.ipynb)

* Measurement of an impedance spectrum on a stack with single cells connected to the [PAD4](http://zahner.de/products/addon-cards/pad4.html) card.
* **Importing the measurement results from the ism file into python**
* **Plotting the spectrum in bode and nyquist representation with the matplotlib library**

### [EISvsParameter.ipynb](Examples/EISvsParameter/EISvsParameter.ipynb)

* Setting output file naming for impedance spectras
* Measure impedance spectra with different DC parameters
* Importing the measurement results from the ism file into python
* Display impedance and phase in contourplots with the matplotlib library

### [ImpedanceMultiCellCycle.ipynb](https://github.com/Zahner-elektrik/Zahner-Remote-Python/blob/master/Examples/ImpedanceMultiCellCycle/ImpedanceMultiCellCycle.ipynb)

* Multichannel operation with several external potentiostats, of the latest generation, type **PP212, PP222, PP242 or XPOT2**.
* Control of standalone operation of external potentiostats with the [zahner_potentiostat](https://github.com/Zahner-elektrik/zahner_potentiostat) library.
* Shared [Zennium series](http://zahner.de/products/electrochemical-workstation.html) device for impedance measurements.

### [BCMuxInterface.ipynb](Examples/BCMuxInterface/BCMuxInterface.ipynb)

* Remote control of the BC-MUX.
* Class which realizes the remote control.

# 📧 Haveing a question?
Send an <a href="mailto:support@zahner.de?subject=Thales-Remote-Python Question&body=Your Message">mail</a> to our support team.

# ⁉️ Found a bug or missing a specific feature?
Feel free to **create a new issue** with an appropriate title and description in the [Thales-Remote-Python repository issue tracker](https://github.com/Zahner-elektrik/Thales-Remote-Python/issues). Or send a <a href="mailto:support@zahner.de?subject=Thales-Remote-Python Question&body=Your Message">mail</a> to our support team.  
If you have already found a solution to your issue, **we would be happy to review your pull request**!

# ✅ Requirements
Programming is done with the latest Python version at the time of commit.

The packages matplotlib, scipy and numpy are used to display the measurement results. Jupyter is not necessary, since each example is also available as a Python file.
