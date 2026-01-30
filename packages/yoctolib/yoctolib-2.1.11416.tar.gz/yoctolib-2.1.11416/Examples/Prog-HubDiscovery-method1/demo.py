from yoctolib.yocto_api import YRefParam, YAPI, YModule

KnownHubs: list[str] = []


def HubDiscovered(serial: str, url: str) -> None:
    global KnownHubs

    # The call-back can be called several times for the same hub
    # (the discovery technique is based on a periodic broadcast)
    # So we use a dictionnary to avoid duplicates
    if serial in KnownHubs:
        return

    print("hub found: " + serial + " (" + url + ")")

    # connect to the hub
    msg: YRefParam = YRefParam()
    YAPI.RegisterHub(url, msg)

    #  find the hub module
    hub: YModule = YModule.FindModule(serial)

    # iterate on all functions on the module and find the ports
    fctCount: int = hub.functionCount()
    for i in range(fctCount):
        # retreive the hardware name of the ith function
        fctHwdName: str = hub.functionId(i)
        if fctHwdName[:7] == "hubPort":
            # The port logical name is always the serial#
            # of the connected device
            deviceid: str = hub.functionName(i)
            print("  " + fctHwdName + " : " + deviceid)

    # add the hub to the dictionnary so we won't have to
    # process is again.
    KnownHubs.append(serial)

    # disconnect from the hub
    YAPI.UnregisterHub(url)


errmsg: YRefParam = YRefParam()
print("Waiting for hubs to signal themselves...")

# register the callback: HubDiscovered will be
# invoked each time a hub signals its presence
YAPI.RegisterHubDiscoveryCallback(HubDiscovered)

# wait for 30 seconds, doing nothing.
for j in range(30):
    YAPI.UpdateDeviceList(errmsg)
    YAPI.Sleep(1000, errmsg)
