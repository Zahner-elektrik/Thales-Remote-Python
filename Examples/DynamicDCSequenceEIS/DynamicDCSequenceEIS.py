import os
import jinja2
from thales_remote.connection import ThalesRemoteConnection
from thales_remote.script_wrapper import (
    PotentiostatMode,
    ScanDirection,
    ThalesRemoteScriptWrapper,
    FileNaming,
    ScanStrategy,
)


def fillTemplateFile(templateFile: str, outputFile: str, **kwargs):
    """
    Function to fill in template files.

    For example, the following placeholders must be in the passed template:
        `\PYVAR{dc_time}`

    Then the value for the template must be passed as an additional parameter as keyworded variable (kwargs):
        `dc_time=2.0`

    :param templateFile: path of the file containing the templates.
    :param outputFile: path to the file containing the completed templates.
    :param **kwargs: template parameters which should be filled in as keyworded variable.
    """
    latex_jinja_env = jinja2.Environment(
        variable_start_string="\PYVAR{",
        variable_end_string="}",
        trim_blocks=True,
        autoescape=False,
        keep_trailing_newline=True,
        newline_sequence="\r\n",
        loader=jinja2.FileSystemLoader(os.path.abspath(".")),
    )

    template = latex_jinja_env.get_template(templateFile)

    fileString = template.render(**kwargs)

    fileBytes = fileString.encode("utf-8")
    with open(outputFile, "wb") as f:
        f.write(fileBytes)

    return


currentSteps = [0, 0.5, 1, 1.5, 2]
amplitude = 0.05

zenniumConnection = ThalesRemoteConnection()
zenniumConnection.connectToTerm("localhost")
zahnerZennium = ThalesRemoteScriptWrapper(zenniumConnection)
zahnerZennium.forceThalesIntoRemoteScript()

for current in currentSteps:
    print(f"Step: {current}")
    """
    DC Sequence
    """
    fillTemplateFile(
        templateFile=r"ocp_constant_current_template.txt",
        outputFile=r"C:\THALES\script\sequencer\sequences\sequence09.seq",
        ocp_time=10,
        dc_time=20,
        dc_current=current,
    )

    filename = f"{int(current*1000)}ma_current"

    zahnerZennium.disableSequenceAcqGlobal()
    zahnerZennium.setSequenceNaming(FileNaming.INDIVIDUAL)
    zahnerZennium.setSequenceOutputPath(r"C:\THALES\temp")
    zahnerZennium.setSequenceOutputFileName(filename)
    zahnerZennium.selectSequence(9)
    zahnerZennium.runSequence()

    """
    EIS
    """
    zahnerZennium.setEISNaming(FileNaming.INDIVIDUAL)
    zahnerZennium.setEISOutputPath(r"C:\THALES\temp")
    zahnerZennium.setEISOutputFileName(filename)
    zahnerZennium.setPotentiostatMode(PotentiostatMode.POTMODE_GALVANOSTATIC)
    zahnerZennium.setAmplitude(amplitude)
    zahnerZennium.setCurrent(current)
    zahnerZennium.setLowerFrequencyLimit(10)
    zahnerZennium.setStartFrequency(1000)
    zahnerZennium.setUpperFrequencyLimit(10000)
    zahnerZennium.setLowerNumberOfPeriods(5)
    zahnerZennium.setLowerStepsPerDecade(2)
    zahnerZennium.setUpperNumberOfPeriods(20)
    zahnerZennium.setUpperStepsPerDecade(5)
    zahnerZennium.setScanDirection(ScanDirection.START_TO_MAX)
    zahnerZennium.setScanStrategy(ScanStrategy.SINGLE_SINE)

    zahnerZennium.measureEIS()

    zahnerZennium.setAmplitude(0)

zahnerZennium.disablePotentiostat()
zenniumConnection.disconnectFromTerm()
