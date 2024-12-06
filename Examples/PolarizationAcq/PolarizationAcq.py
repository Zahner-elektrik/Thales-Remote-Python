import sys
import math
import cmath
from thales_remote.connection import ThalesRemoteConnection
from thales_remote.script_wrapper import PotentiostatMode, ThalesRemoteScriptWrapper
import datetime
import time
import csv
import re

TARGET_HOST = "10.10.255.211"

zenniumConnection = ThalesRemoteConnection()
zenniumConnection.connectToTerm(TARGET_HOST)

zahnerZennium = ThalesRemoteScriptWrapper(zenniumConnection)
zahnerZennium.forceThalesIntoRemoteScript()

print("acq configuration")

acq_setup = zahnerZennium.readAcqSetup()
print(f"setup string from the device:{acq_setup}")

index_channel_name_regex = r"DISP(?P<index>[\d+]);[\d+];(?P<channel_name>.*?);"
headers_match = re.finditer(index_channel_name_regex, acq_setup)

acq_channels = dict()
for match in headers_match:
    acq_channels[int(match.group("index"))] = match.group("channel_name")

print("found channels:")
for index, name in acq_channels.items():
    print(f"index:{index} channel name:{name}")

zahnerZennium.calibrateOffsets()
zahnerZennium.setPotentiostatMode(PotentiostatMode.POTMODE_GALVANOSTATIC)
zahnerZennium.setCurrent(0.1)
zahnerZennium.enablePotentiostat()

duration = 10.0
sampling_frequency = 1.0

interval = 1.0 / sampling_frequency
samples = int(duration * sampling_frequency)
measurements = []
start_time = datetime.datetime.now()

for sample_index in range(samples):
    print(f"sample:{sample_index}/{samples}")
    loop_start = time.time()

    # measure all channels
    current_time = datetime.datetime.now()
    voltage = zahnerZennium.getPotential()
    current = zahnerZennium.getCurrent()
    acq_data = zahnerZennium.readAllAcqChannels()

    # store the results
    measurement = {
        "time": current_time,
        "voltage": voltage,
        "current": current,
        "index": sample_index,
    }

    for key, value in acq_data.items():
        measurement[key] = value

    measurements.append(measurement)

    # calculate the waiting time
    elapsed = time.time() - loop_start
    sleep_time = interval - elapsed

    # wait until the next measurement point
    if sleep_time > 0:
        time.sleep(sleep_time)
    else:
        print("sampling_frequency too high")

with open("polarization.txt", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f, delimiter="\t")

    headers = ["time", "voltage", "current"]
    headers.extend([f"{value}" for key, value in acq_channels.items()])
    headers.append("index")

    writer.writerow(headers)

    for m in measurements:
        row = [m["time"].strftime("%Y-%m-%d %H:%M:%S.%f"), m["voltage"], m["current"]]
        for key, value in acq_channels.items():
            row.append(m[key])
        row.append(m["index"])

        writer.writerow(row)


zahnerZennium.disablePotentiostat()
zenniumConnection.disconnectFromTerm()
print("finish")
