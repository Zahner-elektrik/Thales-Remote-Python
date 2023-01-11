# simple example script on how to interface with a DE Supply
# communicates via a TCP socket with SCPI commands as found in the programming manual
import socket

SUPPLY_IP = "192.168.2.90"
SUPPLY_PORT = 8462
BUFFER_SIZE = 128  # max msg size
TIMEOUT_SECONDS = 10  # return error if we dont hear from supply within 10 sec
MAX_VOLT = 10  # default
MAX_CUR = 10  # default
validSrcList = [
    "front",
    "web",
    "seq",
    "eth",
    "slot1",
    "slot2",
    "slot3",
    "slot4",
    "loc",
    "rem",
]


supplySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # set up socket
supplySocket.connect((SUPPLY_IP, SUPPLY_PORT))  # connect socket
supplySocket.settimeout(TIMEOUT_SECONDS)


def sendAndReceiveCommand(msg):
    msg = msg + "\n"
    supplySocket.sendall(msg.encode("UTF-8"))
    return supplySocket.recv(BUFFER_SIZE).decode("UTF-8").rstrip()


# set value without receiving a response
def sendCommand(msg):
    msg = msg + "\n"
    supplySocket.sendall(msg.encode("UTF-8"))


def setRemoteShutdownState(state):

    if state:
        sendCommand("SYST:RSD 1")
    else:
        sendCommand("SYST:RSD 0")


def setVoltage(volt):
    retval = 0
    if volt > 0 and volt <= MAX_VOLT:
        sendCommand("SOUR:VOLT {0}".format(volt))
    else:

        retval = -1

    return retval


def setCurrent(cur):
    retval = 0
    if cur > 0 and cur <= MAX_VOLT:
        sendCommand("SOUR:CUR {0}".format(cur))
    else:
        retval = -1

    return retval


def readVoltage():
    return sendAndReceiveCommand("SOUR:VOLT?")


def readCurrent():
    return sendAndReceiveCommand("SOUR:CUR?")


def setProgSourceV(src):

    retval = 0
    if src in validSrcList:
        sendCommand("SYST:REM:CV {0}".format(src))

    else:
        retval = -1
    return retval


def setProgSourceI(src):
    retval = 0
    if src.lower() in validSrcList:
        sendCommand("SYST:REM:CC {0}".format(src))
    else:
        retval = -1
    return retval


def setOutputState(state):
    if state:
        sendCommand("OUTPUT 1")

    else:
        sendCommand("OUTPUT 0")


def closeSocket():
    supplySocket.close()


if __name__ == "__main__":
    print(sendAndReceiveCommand("*IDN?"))
    MAX_VOLT = float(sendAndReceiveCommand("SOUR:VOLT:MAX?"))
    MAX_CUR = float(sendAndReceiveCommand("SOUR:CUR:MAX?"))

    print(MAX_VOLT, MAX_CUR)

    setProgSourceV("eth")
    setProgSourceI("eth")

    setVoltage(12.23)
    setCurrent(43.01)

    setRemoteShutdownState(0)  # RSD Enabled = supply off/disabled
    print(readVoltage())
    print(readCurrent())
    closeSocket()
