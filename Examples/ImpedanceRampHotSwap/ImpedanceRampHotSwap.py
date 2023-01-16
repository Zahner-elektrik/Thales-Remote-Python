from thales_remote.epc_scpi_handler import EpcScpiHandlerFactory, EpcScpiHandler
from thales_remote.script_wrapper import PotentiostatMode
from zahner_potentiostat.scpi_control.datahandler import DataManager
from zahner_potentiostat.display.onlinedisplay import OnlineDisplay
from zahner_potentiostat.scpi_control.datareceiver import TrackTypes


class TargetCurrents:
    def __init__(self, dc, amplitude, scanrate):
        self.dc = dc
        self.amplitude = amplitude
        self.scanrate = scanrate
        return


def measure_UI_EPC(deviceHandler):
    for _ in range(3):
        print(
            f"EPC-Potential:\t{deviceHandler.sharedZenniumInterface.getPotential():>10.6f} V"
        )
        print(
            f"EPC-Current:\t{deviceHandler.sharedZenniumInterface.getCurrent():>10.3e} A"
        )
    return


def measure_UI_SCPI(deviceHandler):
    for _ in range(3):
        print(f"SCPI-Potential:\t{deviceHandler.scpiInterface.getPotential():>10.6f} V")
        print(f"SCPI-Current:\t{deviceHandler.scpiInterface.getCurrent():>10.3e} A")
    return


if __name__ == "__main__":
    startCurrent = 0.0
    handlerFactory = EpcScpiHandlerFactory("192.168.2.94")
    deviceHandler = handlerFactory.createEpcScpiHandler(
        epcChannel=1, serialNumber=33021
    )

    deviceHandler.scpiInterface.calibrateOffsets()

    deviceHandler.acquireSharedZennium(blocking=True)
    deviceHandler.switchToEPC()

    deviceHandler.sharedZenniumInterface.calibrateOffsets()

    deviceHandler.sharedZenniumInterface.setPotentiostatMode(
        PotentiostatMode.POTMODE_GALVANOSTATIC
    )
    deviceHandler.sharedZenniumInterface.setCurrent(startCurrent)
    deviceHandler.sharedZenniumInterface.enablePotentiostat()

    measure_UI_EPC(deviceHandler)
    deviceHandler.switchToSCPIAndReleaseSharedZennium(keepPotentiostatState=True)
    measure_UI_SCPI(deviceHandler)

    measurementSettings = [
        TargetCurrents(dc=1, amplitude=0.1, scanrate=0.1),
        TargetCurrents(dc=2, amplitude=0.1, scanrate=0.1),
        TargetCurrents(dc=4, amplitude=0.2, scanrate=0.5),
    ]

    for setting in measurementSettings:

        deviceHandler.scpiInterface.setCurrentValue(
            deviceHandler.scpiInterface.getCurrent()
        )

        configuration = {
            "figureTitle": f"Online Display Targetcurrent: {setting.dc} Scanrate: {setting.scanrate}",
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
        onlineDisplay = OnlineDisplay(
            deviceHandler.scpiInterface.getDataReceiver(),
            displayConfiguration=configuration,
        )

        deviceHandler.scpiInterface.setCurrentParameter(setting.dc)
        deviceHandler.scpiInterface.setScanRateParameter(setting.scanrate)
        deviceHandler.scpiInterface.measureRampValueInScanRate()

        deviceHandler.scpiInterface.setMaximumTimeParameter(5)
        deviceHandler.scpiInterface.measurePolarization()
        while deviceHandler.acquireSharedZennium(blocking=False) == False:
            deviceHandler.scpiInterface.measurePolarization()

        dataManager = DataManager(deviceHandler.scpiInterface.getDataReceiver())
        dataManager.saveDataAsText(f"ramp_to{setting.dc}a_{setting.scanrate}apers.txt")

        onlineDisplay.close()
        del onlineDisplay
        del dataManager

        measure_UI_SCPI(deviceHandler)
        deviceHandler.switchToEPC(keepPotentiostatState=True)
        measure_UI_EPC(deviceHandler)

        deviceHandler.sharedZenniumInterface.setEISNaming("individual")
        deviceHandler.sharedZenniumInterface.setEISOutputPath(r"C:\THALES\temp")
        deviceHandler.sharedZenniumInterface.setEISOutputFileName(
            f"{setting.dc}adc_{setting.amplitude}aac".replace(".", "")
        )

        deviceHandler.sharedZenniumInterface.setPotentiostatMode(
            PotentiostatMode.POTMODE_GALVANOSTATIC
        )
        deviceHandler.sharedZenniumInterface.setPotential(setting.dc)
        deviceHandler.sharedZenniumInterface.setAmplitude(setting.amplitude)

        deviceHandler.sharedZenniumInterface.setLowerFrequencyLimit(100)
        deviceHandler.sharedZenniumInterface.setStartFrequency(250)
        deviceHandler.sharedZenniumInterface.setUpperFrequencyLimit(500)
        deviceHandler.sharedZenniumInterface.setLowerNumberOfPeriods(5)
        deviceHandler.sharedZenniumInterface.setLowerStepsPerDecade(10)
        deviceHandler.sharedZenniumInterface.setUpperNumberOfPeriods(20)
        deviceHandler.sharedZenniumInterface.setUpperStepsPerDecade(10)
        deviceHandler.sharedZenniumInterface.setScanDirection("startToMax")
        deviceHandler.sharedZenniumInterface.setScanStrategy("single")

        deviceHandler.sharedZenniumInterface.enablePotentiostat()
        deviceHandler.sharedZenniumInterface.measureEIS()
        deviceHandler.sharedZenniumInterface.setAmplitude(0)

        measure_UI_EPC(deviceHandler)
        deviceHandler.switchToSCPIAndReleaseSharedZennium(keepPotentiostatState=True)
        measure_UI_SCPI(deviceHandler)

    deviceHandler.scpiInterface.setPotentiostatEnabled(False)
    handlerFactory.closeAll()
    print("finish")
