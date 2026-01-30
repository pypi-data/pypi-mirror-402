import sys

from yoctolib.yocto_api import YRefParam, YAPI
from yoctolib.yocto_colorled import YColorLed


def die(msg: str) -> None:
    YAPI.FreeAPI()
    sys.exit(msg)


def main() -> None:
    # the API use local USB devices through VirtualHub
    errmsg: YRefParam = YRefParam()
    if YAPI.RegisterHub("localhost", errmsg) != YAPI.SUCCESS:
        sys.exit("RegisterHub failed: " + errmsg.value)

    led: YColorLed = YColorLed.FirstColorLed()
    if led is None:
        die("No led connected (check USB cable)")

    led.resetBlinkSeq()  # cleans the sequence
    led.addRgbMoveToBlinkSeq(0x00FF00, 500)  # move to green in 500 ms
    led.addRgbMoveToBlinkSeq(0x000000, 0)  # switch to black instantaneously
    led.addRgbMoveToBlinkSeq(0x000000, 250)  # stays black for 250ms
    led.addRgbMoveToBlinkSeq(0x0000FF, 0)  # switch to blue instantaneously
    led.addRgbMoveToBlinkSeq(0x0000FF, 100)  # stays blue for 100ms
    led.addRgbMoveToBlinkSeq(0x000000, 0)  # switch to black instantaneously
    led.addRgbMoveToBlinkSeq(0x000000, 250)  # stays black for 250ms
    led.addRgbMoveToBlinkSeq(0xFF0000, 0)  # switch to red instantaneously
    led.addRgbMoveToBlinkSeq(0xFF0000, 100)  # stays red for 100ms
    led.addRgbMoveToBlinkSeq(0x000000, 0)  # switch to black instantaneously
    led.addRgbMoveToBlinkSeq(0x000000, 1000)  # stays black for 1s
    led.startBlinkSeq()  # starts sequence
    print("The led is now blinking autonomously")
    YAPI.FreeAPI()


if __name__ == '__main__':
    main()
