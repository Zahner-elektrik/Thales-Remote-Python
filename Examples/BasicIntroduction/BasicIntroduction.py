import sys
from thales_remote.connection import ThalesRemoteConnection
from thales_remote.script_wrapper import PotentiostatMode,ThalesRemoteScriptWrapper
import math
import cmath

def printImpedance(impedance):
    print("Impedance: " + str(abs(impedance)) + " ohm, " + str(cmath.phase(impedance)) + " rad")
    return

def spectrum(scriptHandle, lower_frequency, upper_frequency, number_of_points):
    log_lower_frequency = math.log(lower_frequency)
    log_upper_frequency = math.log(upper_frequency)
    log_interval_spacing = (log_upper_frequency - log_lower_frequency) / (number_of_points - 1)
    
    for i in range(number_of_points):
        current_frequency = math.exp(log_lower_frequency + log_interval_spacing * i)
        print("Frequency: " + str(current_frequency))
        printImpedance(scriptHandle.getImpedance(current_frequency))
        
    return

TARGET_HOST = "localhost"

if __name__ == "__main__":
    zenniumConnection = ThalesRemoteConnection()
    connectionSuccessful = zenniumConnection.connectToTerm(TARGET_HOST, "ScriptRemote")
    if connectionSuccessful:
        print("connection successfull")
    else:
        print("connection not possible")
        sys.exit()

    zahnerZennium = ThalesRemoteScriptWrapper(zenniumConnection)
    zahnerZennium.forceThalesIntoRemoteScript()

    zahnerZennium.calibrateOffsets()

    zahnerZennium.setPotentiostatMode(PotentiostatMode.POTMODE_POTENTIOSTATIC)
    zahnerZennium.setPotential(1.0)
    zahnerZennium.enablePotentiostat()

    for i in range(5):
        print(f"Potential:\t{zahnerZennium.getPotential()}\tV")
        print(f"Current:\t{zahnerZennium.getCurrent()}\tA")

    zahnerZennium.disablePotentiostat()
    zahnerZennium.setPotentiostatMode(PotentiostatMode.POTMODE_GALVANOSTATIC)
    zahnerZennium.setCurrent(20e-9)
    zahnerZennium.enablePotentiostat()

    for i in range(5):
        print(f"Potential:\t{zahnerZennium.getPotential()}\tV")
        print(f"Current:\t{zahnerZennium.getCurrent()}\tA")

    zahnerZennium.disablePotentiostat()
    zahnerZennium.setPotentiostatMode(PotentiostatMode.POTMODE_POTENTIOSTATIC)
    zahnerZennium.setPotential(1.0)
    zahnerZennium.enablePotentiostat()
    zahnerZennium.setFrequency(2000)
    zahnerZennium.setAmplitude(10e-3)
    zahnerZennium.setNumberOfPeriods(3)

    printImpedance(zahnerZennium.getImpedance())
    printImpedance(zahnerZennium.getImpedance(2000))
    printImpedance(zahnerZennium.getImpedance(2000, 10e-3, 3))

    spectrum(zahnerZennium, 1000, 2e5, 10)

    zahnerZennium.disablePotentiostat()
    zahnerZennium.setAmplitude(0)

    zenniumConnection.disconnectFromTerm()
    print("finish")

