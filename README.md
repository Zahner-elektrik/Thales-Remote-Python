![Thales-Remote-Python](https://doc.zahner.de/github_resources/Thales-Remote-Python.png)

Thales-Remote-Python is a Python extension which uses the Zahner [Remote2](https://doc.zahner.de/manuals/remote2.pdf) to control [Zahner ZENNIUM Potentiostats](https://zahner.de/products#potentiostats).  
It was developed to **easily integrate** [Zahner ZENNIUM Potentiostats](https://zahner.de/products#potentiostats) into Python scripts for more **complex measurement** tasks and for **automation purposes**.

The measurement methods **Impedance Spectroscopy (EIS)**, **Cyclic Voltammetry (CV)**, **Current–Voltage characteristic (IE)**,and **DC sequences** are supported. Also constant current or constant voltage can be output and current and voltage can be measured. Single frequency impedance measurement is also possible. Other supported functions are the remote control of the [BC-MUX](https://zahner.de/products-details/multiplexer/bc-mux) and the import of ism files in Python.  

# 📚 Documentation

The complete documentation of the individual functions can be found on the [API documentation website](https://doc.zahner.de/thales_remote/).  

# 🔧 Installation

The package can be installed via pip.

```
pip install thales_remote
```

The class [BCMuxInterface](https://doc.zahner.de/thales_remote/bc_mux_interface.html) to control the [BC-MUX](https://zahner.de/products-details/multiplexer/bc-mux) is located in the Python file [BCMuxInterface.py](Examples/BCMuxInterface/BCMuxInterface.py), from this file the class can be imported.

# 🔬 Measurement Data Analysis

There is a separate Python package on [GitHub](https://github.com/Zahner-elektrik/Zahner-Analysis-Python) and [PyPI/pip](https://pypi.org/project/zahner-analysis/) for analyzing measurement data.

In this repository there are examples of how to fit equivalent electrical circuit models to electrochemical impedance spectra, also known as EIS equivalent circuit fitting. The model parameters can be further processed after the fit with Python, for example for the comparison of serial measurements.

# 🔨 Basic Usage

The [Jupyter](https://jupyter.org/) notebook [BasicIntroduction.ipynb](Examples/BasicIntroduction/BasicIntroduction.ipynb) explains the fundamentals of using the library.

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
zenniumConnection.disconnectFromTerm()
```

# 📖 Examples

There is at least one example for each possible electrochemical method that can be controlled remotely.

[BasicIntroduction.ipynb](Examples/BasicIntroduction/BasicIntroduction.ipynb) is the most basic introduction, which describes the connection setup in detail. For each example there is a [Jupyter](https://jupyter.org/) notebook which explains the example code in detail. For the user there is a Python script for each example which contains the pure Python code so that Jupyter does not need to be installed.

In the examples only one method is explained and parameterized at a time for better comprehension. But the methods can also be combined flexibly in a Python script, for example a CV measurement followed by an EIS measurement.

## [BasicIntroduction.ipynb](Examples/BasicIntroduction/BasicIntroduction.ipynb)

* Basic introduction to remote control
* Switch potentiostat on or off
* Setting potentiostat potentiostatic or galvanostatic
* Setting output potential or current
* Read potential and current
* Single frequency impedance measurement

## [EISImportPlot.ipynb](Examples/EISImportPlot/EISImportPlot.ipynb)

* Measurement of an impedance spectrum - EIS
* **Importing the measurement results from the ism file into Python**
* **Plotting the spectrum in bode and nyquist representation with the matplotlib library**

## [FileExchangeEIS.ipynb](Examples/FileExchangeEIS/FileExchangeEIS.ipynb)

* Measurement of an impedance spectrum - EIS
* Importing the measurement results from the ism file into Python
* **Acquiring the measurement files with Python via network**

## [EIS.ipynb](Examples/EIS/EIS.ipynb)

* Setting output file naming for impedance spectras
* Parametrizing an impedance spectrum
* Measurement with an external potentiostat (EPC-Device)

## [CyclicVoltammetry.ipynb](Examples/CyclicVoltammetry/CyclicVoltammetry.ipynb)

* Measure cylic voltammetry measurement
* Setting output file naming for CV measurements
* Parametrizing an CV measurement
* Importing the measurement results from the isc file into Python
* **Acquiring the measurement files with Python via network**

## [CVImportPlot.ipynb](Examples/CVImportPlot/CVImportPlot.ipynb)

* Measure cylic voltammetry measurement
* Setting output file naming for CV measurements
* Parametrizing an CV measurement
* Importing the measurement results from the isc file into Python
* **Acquiring the measurement files with Python via network**

## [CurrentVoltageCurve.ipynb](Examples/CurrentVoltageCurve/CurrentVoltageCurve.ipynb)

* Setting output file naming for IE measurements
* Parametrizing an IE measurement
* Importing the measurement results from the iss file into Python

## [DCSequencer.ipynb](Examples/DCSequencer/DCSequencer.ipynb)

* The [Zahner sequencer](https://doc.zahner.de/manuals/sequencer.pdf) outputs current and voltage curves defined in a text file.
* Setting output file naming for sequence measurements
* Parametrizing an sequence measurement
* Measurement with an [external potentiostat](https://zahner.de/products#external-potentiostats) or [external load](https://zahner.de/products#electronic-loads) ([EPC-Device](https://zahner.de/products-details/addon-cards/epc42))

## [EISCVLaTeX.ipynb](Examples/EISCVLaTeX/EISCVLaTeX.ipynb)

* Measure impedance specta and cyclic voltammetry
* Plotting the measurement data.
* Create a PDF with the measurement data using [LaTeX](https://www.latex-project.org/zah)

## [EISPad4.ipynb](Examples/EISPad4/EISPad4.ipynb)

* Measurement of an impedance spectrum on a stack with single cells connected to the [PAD4](https://zahner.de/products-details/addon-cards/pad4) card.
* **Importing the measurement results from the ism file into Python**
* **Plotting the spectrum in bode and nyquist representation with the matplotlib library**

## [EISvsParameter.ipynb](Examples/EISvsParameter/EISvsParameter.ipynb)

* Setting output file naming for impedance spectra
* Measure impedance spectra with different DC parameters
* Importing the measurement results from the ism file into Python
* Display impedance and phase in contourplots with the matplotlib library

## [ExternalDeviceFRA.ipynb](Examples/ExternalDeviceFRA/ExternalDeviceFRA.ipynb)

* Configure FRA Probe measurement
* Measure EIS with FRA Probe

## [LoadWithExternalSource.ipynb](Examples/LoadWithExternalSource/LoadWithExternalSource.ipynb)

* Measure EIS at OCP with the [electronic load EL1002](https://zahner.de/products-details/electronic-loads/el1002) and the [Delta Elektronika SM3300 SM 18-220](https://www.delta-elektronika.nl/en/products/dc-power-supplies-3300w-sm3300-series.html)
* Remote control [Delta Elektronika SM3300 SM 18-220](https://www.delta-elektronika.nl/en/products/dc-power-supplies-3300w-sm3300-series.html)
* **Acquiring the measurement files with Python via network**
* **Plotting the spectrum in bode representation with the matplotlib library**

## [ImpedanceMultiCellCycle.ipynb](Examples/ImpedanceMultiCellCycle/ImpedanceMultiCellCycle.ipynb)

* Multichannel operation with several external potentiostats, of the latest generation, type **PP2x2, XPOT2 or EL1002**
* Shared [Zennium series](https://zahner.de/products#potentiostats) device for impedance measurements
* Operation of the power potentiostats standalone without thales with the Python package [zahner_potentiostat](https://github.com/Zahner-elektrik/zahner_potentiostat)

## [ImpedanceRampHotSwap.ipynb](Examples/ImpedanceRampHotSwap/ImpedanceRampHotSwap.ipynb)

* Switch between Thales/EPC and SCPI/standalone operation of the external potentiostats (PP2x2, XPOT2 or EL1002) **without switching off the potentiostat**
* Shared [Zennium series](https://zahner.de/products#potentiostats) device for impedance measurements
* Operation of the power potentiostats standalone without thales with the Python package [zahner_potentiostat](https://github.com/Zahner-elektrik/zahner_potentiostat)

## [BCMuxInterface.ipynb](Examples/BCMuxInterface/BCMuxInterface.ipynb)

* Remote control of the BC-MUX
* Class which realizes the remote control

# 📧 Haveing a question?

Send a [mail](mailto:support@zahner.de?subject=Thales-Remote-Python%20Question&body=Your%20Message) to our support team.

# ⁉️ Found a bug or missing a specific feature?

Feel free to **create a new issue** with an appropriate title and description in the [Thales-Remote-Python repository issue tracker](https://github.com/Zahner-elektrik/Thales-Remote-Python/issues). Or send a [mail](mailto:support@zahner.de?subject=Thales-Remote-Python%20Question&body=Your%20Message) to our support team.  
If you have already found a solution to your issue or feature, **we would be happy to review your pull request**!

# ✅ Requirements

Programming is done with the latest Python version at the time of commit.

For the [thales_remote](thales_remote) package only the Python standard library was used.
If measurement data are imported and plotted, the package [zahner_analysis](https://github.com/Zahner-elektrik/Zahner-Analysis-Python) is used.

For standalone communication without Thales with the PP2x2, XPOT2 or EL1002 devices the [zahner_potentiostat](https://github.com/Zahner-elektrik/zahner_potentiostat) package is used.

The packages [matplotlib](https://matplotlib.org/), [SciPy](https://scipy.org/) and [NumPy](https://numpy.org/) are used in some examples to display the measurement data graphically.
Jupyter is not necessary, since each example is also available as a Python file.
