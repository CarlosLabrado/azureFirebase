#!/usr/bin/env bash

echo ////// Create log directory /////
mkdir /home/logs

echo ...... Copy iothub_client .....
cp /azure-iot-sdks/python/device/samples/iothub_client.so /app/utils
cp /azure-iot-sdks/python/device/samples/iothub_client.so /app

echo ...... Copy iothub_client_cert.py .....
cp /azure-iot-sdks/python/device/samples/iothub_client_cert.py /app/utils
cp /azure-iot-sdks/python/device/samples/iothub_client_cert.py /app

python /app/main.py