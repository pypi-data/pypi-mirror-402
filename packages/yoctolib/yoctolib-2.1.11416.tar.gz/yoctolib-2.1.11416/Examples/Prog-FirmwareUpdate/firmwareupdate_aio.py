import asyncio
import logging
import sys

from yoctolib.yocto_api_aio import YRefParam, YAPI, YModule, YFirmwareUpdate


async def die(msg):
    await YAPI.FreeAPI()
    sys.exit(msg + ' (check USB cable)')


async def upgradeSerialList(all_serials: list[str]):
    for serial in all_serials:
        module: YModule = YModule.FindModule(serial)
        product: str = await module.get_productName()
        serial: str = await module.get_serialNumber()
        current: str = await module.get_firmwareRelease()
        # check if new firmware is available on yoctopuce.com
        new_firmware: str = await module.checkFirmware("www.yoctopuce.com", True)
        if new_firmware == "":
            print(product + " " + serial + "(rev=" + current + ") is up to date")
        else:
            print(product + " " + serial + "(rev=" + current + ") need be updated with firmware : ")
            print("    " + new_firmware)
            # execute the firmware upgrade
            update: YFirmwareUpdate = await module.updateFirmware(new_firmware)
            status: int = await update.startUpdate()
            while 100 > status >= 0:
                new_status: int = await update.get_progress()
                if new_status != status:
                    print(str(new_status) + "% " + await update.get_progressMessage())
                await YAPI.Sleep(500)
                status = new_status
            if status < 0:
                await die("Firmware Update failed: " + await update.get_progressMessage())
            else:
                if await module.isOnline():
                    print(str(status) + "% Firmware Updated Successfully!")
                else:
                    await die(str(status) + " Firmware Update failed: module " + serial + "is not online")

async def main():

    # the API use local USB devices through VirtualHub
    errmsg: YRefParam = YRefParam()
    if await YAPI.RegisterHub("localhost", errmsg) != YAPI.SUCCESS:
        await die("RegisterHub failed: " + errmsg.value)

    i: int = 1
    for i in range(1, len(sys.argv)):
        print("Update module connected to hub " + sys.argv[i])
        # Setup the API to use local USB devices
        if await YAPI.RegisterHub(sys.argv[i], errmsg) != YAPI.SUCCESS:
            await die("init error" + errmsg.value)

    hubs: list[str] = []
    shield: list[str] = []
    devices: list[str] = []
    # fist step construct the list of all hub /shield and devices connected
    module: YModule = YModule.FirstModule()
    while module is not None:
        product: str = await module.get_productName()
        serial: str = await module.get_serialNumber()
        if product == "YoctoHub-Shield":
            shield.append(serial)
        elif product[0:8] == "YoctoHub":
            hubs.append(serial)
        elif product[0:9] != "VirtualHub":
            devices.append(serial)
        module = module.nextModule()
    # fist upgrades all Hubs...
    await upgradeSerialList(hubs)
    # ... then all shield..
    await upgradeSerialList(shield)
    # ... and finally all devices
    await upgradeSerialList(devices)
    print("All devices are now up to date")
    await YAPI.FreeAPI()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main(), debug=True)
