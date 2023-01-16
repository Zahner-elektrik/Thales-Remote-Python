from thales_remote.epc_scpi_handler import EpcScpiHandlerFactory, EpcScpiHandler
from thales_remote.script_wrapper import PotentiostatMode
from zahner_potentiostat.scpi_control.datahandler import DataManager
from zahner_potentiostat.display.onlinedisplay import OnlineDisplay
from zahner_potentiostat.scpi_control.datareceiver import TrackTypes

import threading
from datetime import datetime


def getFileName(channel, cycle):
    time = str(datetime.now().time())
    time = time.replace(":", "")
    time = time.replace(",", "")
    time = time.replace(".", "")
    return f"channel{channel}_cycle{cycle}"  # + time


def channel1Thread(deviceHandler, channel=0):
    deviceHandler.scpiInterface.setMaximumTimeParameter(15)
    deviceHandler.scpiInterface.setParameterLimitCheckToleranceTime(0.1)

    configuration = {
        "figureTitle": "Online Display Channel 1",
        "xAxisLabel": "Time",
        "xAxisUnit": "s",
        "xTrackName": TrackTypes.TIME.toString(),
        "yAxis": [
            {
                "label": "Voltage",
                "unit": "V",
                "trackName": TrackTypes.VOLTAGE.toString(),
            },
            {
                "label": "Current",
                "unit": "A",
                "trackName": TrackTypes.CURRENT.toString(),
            },
        ],
    }

    for i in range(3):
        filename = getFileName(channel=channel, cycle=i)

        onlineDisplay = OnlineDisplay(
            deviceHandler.scpiInterface.getDataReceiver(),
            displayConfiguration=configuration,
        )

        deviceHandler.scpiInterface.measureOCVScan()

        for n in range(2):
            deviceHandler.scpiInterface.measureCharge(
                current=1e-3, stopVoltage=2, maximumTime="5 min"
            )

            deviceHandler.scpiInterface.measureDischarge(
                current=-1e-3, stopVoltage=0.5, maximumTime="5 min"
            )

        deviceHandler.scpiInterface.setMaximumTimeParameter(15)
        while deviceHandler.acquireSharedZennium(blocking=False) == False:
            deviceHandler.scpiInterface.measureOCVScan()

        dataManager = DataManager(deviceHandler.scpiInterface.getDataReceiver())
        dataManager.saveDataAsText(filename + ".txt")

        onlineDisplay.close()
        del onlineDisplay

        deviceHandler.switchToEPC()

        deviceHandler.sharedZenniumInterface.setEISNaming("individual")
        deviceHandler.sharedZenniumInterface.setEISOutputPath(
            r"C:\THALES\temp\multichannel"
        )
        deviceHandler.sharedZenniumInterface.setEISOutputFileName(filename)

        deviceHandler.sharedZenniumInterface.setPotentiostatMode(
            PotentiostatMode.POTMODE_POTENTIOSTATIC
        )
        deviceHandler.sharedZenniumInterface.setAmplitude(10e-3)
        deviceHandler.sharedZenniumInterface.setPotential(0)
        deviceHandler.sharedZenniumInterface.setLowerFrequencyLimit(100)
        deviceHandler.sharedZenniumInterface.setStartFrequency(500)
        deviceHandler.sharedZenniumInterface.setUpperFrequencyLimit(1000)
        deviceHandler.sharedZenniumInterface.setLowerNumberOfPeriods(5)
        deviceHandler.sharedZenniumInterface.setLowerStepsPerDecade(2)
        deviceHandler.sharedZenniumInterface.setUpperNumberOfPeriods(20)
        deviceHandler.sharedZenniumInterface.setUpperStepsPerDecade(5)
        deviceHandler.sharedZenniumInterface.setScanDirection("startToMax")
        deviceHandler.sharedZenniumInterface.setScanStrategy("single")

        deviceHandler.sharedZenniumInterface.measureEIS()

        deviceHandler.switchToSCPIAndReleaseSharedZennium()

    return


def channel2Thread(deviceHandler):
    deviceHandler.scpiInterface.setMaximumTimeParameter(15)
    deviceHandler.scpiInterface.setParameterLimitCheckToleranceTime(0.1)

    configuration = {
        "figureTitle": "Online Display Channel 2",
        "xAxisLabel": "Time",
        "xAxisUnit": "s",
        "xTrackName": TrackTypes.TIME.toString(),
        "yAxis": [
            {
                "label": "Voltage",
                "unit": "V",
                "trackName": TrackTypes.VOLTAGE.toString(),
            },
            {
                "label": "Current",
                "unit": "A",
                "trackName": TrackTypes.CURRENT.toString(),
            },
        ],
    }

    for i in range(2):
        filename = getFileName(channel=2, cycle=i)

        onlineDisplay = OnlineDisplay(
            deviceHandler.scpiInterface.getDataReceiver(),
            displayConfiguration=configuration,
        )

        deviceHandler.scpiInterface.measureOCVScan()

        for n in range(2):
            deviceHandler.scpiInterface.measureCharge(
                current=4, stopVoltage=1, maximumTime="5 min"
            )

            deviceHandler.scpiInterface.measureDischarge(
                current=-4, stopVoltage=0.6, maximumTime="5 min"
            )

        dataManager = DataManager(deviceHandler.scpiInterface.getDataReceiver())
        dataManager.saveDataAsText(filename + ".txt")

        onlineDisplay.close()
        del onlineDisplay

        deviceHandler.acquireSharedZennium()
        deviceHandler.switchToEPC()

        deviceHandler.sharedZenniumInterface.setEISNaming("individual")
        deviceHandler.sharedZenniumInterface.setEISOutputPath(
            r"C:\THALES\temp\multichannel"
        )
        deviceHandler.sharedZenniumInterface.setEISOutputFileName(filename)

        deviceHandler.sharedZenniumInterface.setPotentiostatMode(
            PotentiostatMode.POTMODE_POTENTIOSTATIC
        )
        deviceHandler.sharedZenniumInterface.setAmplitude(10e-3)
        deviceHandler.sharedZenniumInterface.setPotential(0)
        deviceHandler.sharedZenniumInterface.setLowerFrequencyLimit(100)
        deviceHandler.sharedZenniumInterface.setStartFrequency(500)
        deviceHandler.sharedZenniumInterface.setUpperFrequencyLimit(1000)
        deviceHandler.sharedZenniumInterface.setLowerNumberOfPeriods(5)
        deviceHandler.sharedZenniumInterface.setLowerStepsPerDecade(2)
        deviceHandler.sharedZenniumInterface.setUpperNumberOfPeriods(20)
        deviceHandler.sharedZenniumInterface.setUpperStepsPerDecade(5)
        deviceHandler.sharedZenniumInterface.setScanDirection("startToMax")
        deviceHandler.sharedZenniumInterface.setScanStrategy("single")

        deviceHandler.sharedZenniumInterface.measureEIS()

        deviceHandler.switchToSCPIAndReleaseSharedZennium()

    return


if __name__ == "__main__":
    handlerFactory = EpcScpiHandlerFactory()

    XPOT2 = handlerFactory.createEpcScpiHandler(epcChannel=1, serialNumber=27000)
    PP242 = handlerFactory.createEpcScpiHandler(epcChannel=4, serialNumber=35000)

    channel1ThreadHandler = threading.Thread(target=channel1Thread, args=(XPOT2, 1))
    channel2ThreadHandler = threading.Thread(target=channel2Thread, args=(PP242,))

    channel1ThreadHandler.start()
    channel2ThreadHandler.start()

    channel1ThreadHandler.join()
    channel2ThreadHandler.join()

    handlerFactory.closeAll()
    print("finish")
