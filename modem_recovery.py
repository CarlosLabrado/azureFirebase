"""
Check internet connection and reboot modem if necessary
"""
import RPi.GPIO as RPIO
import time
import commands
import config


def recover_thread():
    seconds = 0
    RPIO.setmode(RPIO.BOARD)
    # set up GPIO output channel
    RPIO.setup(3, RPIO.OUT)
    while True:
        if seconds < config.delayPing:
            time.sleep(1)
            seconds += 1
        else:
            seconds = 0
            ping_count = 0
            ping_ok = False
            while ping_count < 10:
                config.logging.warning('pingBroker: Trying to ping Google ({0})'.format(config.resin))
                status, ping_result = commands.getstatusoutput('ping -c 10 {0}'.format(config.resin))
                if status == 0:
                    config.logging.warning('pingBroker: Ping to Resin ({0}) Success! .. Keep Alive!'
                                           .format(config.resin))
                    time.sleep(1)
                    ping_ok = True
                    break
                else:
                    # Pinging, don't kill me yet
                    ping_count += 1
            if ping_ok:
                pass
            else:
                # Kill Mifi via io port
                config.logging.warning('pingBroker: Error in ping: ({0}).'
                                       ' Rebooting mifi ...'.format(config.resin))
                while True:
                    # set turn modem off
                    RPIO.output(3, False)
                    time.sleep(10)
                    RPIO.output(3, True)
                    break
