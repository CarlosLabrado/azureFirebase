FROM resin/rpi-raspbian:jessie

RUN apt-cache policy
RUN apt-get update && apt-get install -y nano net-tools git python python-dev python-pip python-serial gcc sudo
RUN apt-get update && apt-get install -y cmake iputils-ping usbutils usb-modeswitch wvdial
RUN apt-get update && apt-get install ifupdown resolvconf
RUN pip install requests minimalmodbus
RUN pip install -U RPi.GPIO
RUN git clone --recursive https://github.com/Azure/azure-iot-sdks.git
ADD make_azure_iot.sh /azure-iot-sdks/make_azure_iot.sh

ADD wvdial.conf /etc/wvdial.conf

ADD wvdial_auto_reconnect.sh /wvdial_auto_reconnect.sh

RUN chmod +x /azure-iot-sdks/make_azure_iot.sh
RUN ["/azure-iot-sdks/./make_azure_iot.sh"]
COPY . /app

ENV INITSYSTEM=on

CMD ["bash", "/app/start.sh"]