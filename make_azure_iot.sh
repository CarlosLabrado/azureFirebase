#!/usr/bin/env bash

# Making Azure IoT python SDK
echo ----- Setup Environment Azure IoT! -----
azure-iot-sdks/c/build_all/linux/./setup.sh
echo ===== Bulding Environment Azure IoT! =====
azure-iot-sdks/c/build_all/linux/./build.sh
echo Done -> Bulding Environment Azure IoT!

echo ***** Python Azure IoT Client - Setup *****
azure-iot-sdks/python/build_all/linux/./setup.sh
echo +++++ Python Azure IoT Client - Build +++++
azure-iot-sdks/python/build_all/linux/./build.sh
echo Done -> Python Azure IoT Client