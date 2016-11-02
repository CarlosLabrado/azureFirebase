"""
Entry point script
"""

import time
import config
import threading

__author__ = 'Cesar'

if config.console_only:
    while True:
        time.sleep(1800)
        config.logging.warning("No app running, console only")
else:
    config.logging.warning("----------------App-Start-------------------")

    error = True
    try:
        from modbus_lufkin import ModbusLufkin
        lufkin = ModbusLufkin(address=config.modbus_address)
        polling = threading.Thread(target=lufkin.polling_loop,
                                   args=[config.polling_rate])
        polling.daemon = True
        polling.start()
    except Exception as e:
        config.logging.error('Error no Serial Port found: {0}'.format(e.message))
        while True:
            time.sleep(20)
            config.logging.warning('Error initializing USB serial. Console Only')
            # TODO: Reboot using resin.io API
    else:
        error = False

while True:
    pass
