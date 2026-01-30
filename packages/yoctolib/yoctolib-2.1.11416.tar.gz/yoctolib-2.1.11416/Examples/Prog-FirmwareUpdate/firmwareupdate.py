import sys

from yoctolib.yocto_api import YRefParam, YAPI, YModule, YFirmwareUpdate


def die(msg):
    YAPI.FreeAPI()
    sys.exit(msg + ' (check USB cable)')


def upgradeSerialList(all_serials: list[str]):
    for serial in all_serials:
        module: YModule = YModule.FindModule(serial)
        product: str = module.get_productName()
        serial: str = module.get_serialNumber()
        current: str = module.get_firmwareRelease()
        # check if new firmware is available on yoctopuce.com
        new_firmware: str = module.checkFirmware("www.yoctopuce.com", True)
        if new_firmware == "":
            print(product + " " + serial + "(rev=" + current + ") is up to date")
        else:
            print(product + " " + serial + "(rev=" + current + ") need be updated with firmware : ")
            print("    " + new_firmware)
            # execute the firmware upgrade
            update: YFirmwareUpdate = module.updateFirmware(new_firmware)
            status: int = update.startUpdate()
            while 100 > status >= 0:
                new_status: int = update.get_progress()
                if new_status != status:
                    print(str(new_status) + "% " + update.get_progressMessage())
                YAPI.Sleep(500, errmsg)
                status = new_status
            if status < 0:
                die("Firmware Update failed: " + update.get_progressMessage())
            else:
                if module.isOnline():
                    print(str(status) + "% Firmware Updated Successfully!")
                else:
                    die(str(status) + " Firmware Update failed: module " + serial + "is not online")


# the API use local USB devices through VirtualHub
errmsg: YRefParam = YRefParam()
if YAPI.RegisterHub("localhost", errmsg) != YAPI.SUCCESS:
    die("RegisterHub failed: " + errmsg.value)

i: int = 1
for i in range(1, len(sys.argv)):
    print("Update module connected to hub " + sys.argv[i])
    # Setup the API to use local USB devices
    if YAPI.RegisterHub(sys.argv[i], errmsg) != YAPI.SUCCESS:
        die("init error" + errmsg.value)

hubs: list[str] = []
shield: list[str] = []
devices: list[str] = []
# fist step construct the list of all hub /shield and devices connected
module: YModule = YModule.FirstModule()
while module is not None:
    product: str = module.get_productName()
    serial: str = module.get_serialNumber()
    if product == "YoctoHub-Shield":
        shield.append(serial)
    elif product[0:8] == "YoctoHub":
        hubs.append(serial)
    elif product[0:9] != "VirtualHub":
        devices.append(serial)
    module = module.nextModule()
# fist upgrades all Hubs...
upgradeSerialList(hubs)
# ... then all shield..
upgradeSerialList(shield)
# ... and finally all devices
upgradeSerialList(devices)
print("All devices are now up to date")
YAPI.FreeAPI()
