import sys

from yoctolib.yocto_api import YRefParam, YAPI
from yoctolib.yocto_colorledcluster import YColorLedCluster


def die(msg: str) -> None:
    YAPI.FreeAPI()
    sys.exit(msg)


def main():
    # the API use local USB devices through VirtualHub
    errmsg: YRefParam = YRefParam()
    if YAPI.RegisterHub("localhost", errmsg) != YAPI.SUCCESS:
        sys.exit("RegisterHub failed: " + errmsg.value)

    leds: YColorLedCluster = YColorLedCluster.FirstColorLedCluster()
    if leds is None:
        sys.exit("No Color Led cluster found (check USB cable)")

    leds.resetBlinkSeq(0)  # cleans the sequence 0
    leds.addRgbMoveToBlinkSeq(0, 0x400000, 0)  # move instantaneously to red 25%
    leds.addRgbMoveToBlinkSeq(0, 0x400000, 500)  # stay on the same color for 0.5sec
    leds.addRgbMoveToBlinkSeq(0, 0x000040, 0)  # move instantaneously to red 25%
    leds.addRgbMoveToBlinkSeq(0, 0x000040, 500)  # stay on the same color for 0.5sec
    leds.linkLedToBlinkSeq(0, 1, 0, 0)  # link led 0 to sequence 0
    leds.linkLedToBlinkSeqAtPowerOn(0, 1, 0, 0)  # led 0 will automatically be linked to sequence 0  at startup
    leds.set_blinkSeqStateAtPowerOn(0, 1)  # sequence 0 will automatically run at startup
    leds.saveBlinkSeq(0)  # save the sequence on flash memory

    leds.resetBlinkSeq(1)  # cleans the sequence  1
    leds.addHslMoveToBlinkSeq(1, 0x00FF20, 2000)  # Circle over all hue values
    leds.addHslMoveToBlinkSeq(1, 0x55FF20, 2000)  # Saturation =100%
    leds.addHslMoveToBlinkSeq(1, 0xAAFF20, 2000)  # luminosity = 12%
    leds.linkLedToBlinkSeq(1, 1, 1, 0)  # link led 1 to sequence 1
    leds.linkLedToBlinkSeqAtPowerOn(1, 1, 1, 0)  # led 1 will automatically be linked to sequence 1  at startup
    leds.set_blinkSeqStateAtPowerOn(1, 1)  # sequence 1  will automatically run at startup
    leds.saveBlinkSeq(1)  # save the sequence on flash memory

    leds.saveLedsConfigAtPowerOn()  # All leds configuration

    leds.startBlinkSeq(0)  # start sequence 0
    leds.startBlinkSeq(1)  # start sequence 1

    print("The leds are now blinking autonomously")
    YAPI.FreeAPI()


if __name__ == '__main__':
    main()
