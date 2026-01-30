# ********************************************************************
#
#  $Id: svn_id $
#
#  Doc-Inventory example
#
#  You can find more information on our web site:
#   Python V2 API Reference:
#      https://www.yoctopuce.com/EN/doc/reference/yoctolib-typedpython-EN.html
#
# *********************************************************************
import asyncio

from yoctolib.yocto_api_aio import YRefParam, YAPI, YModule


async def main():
    errmsg = YRefParam()
    if await YAPI.RegisterHub("localhost", errmsg) != YAPI.SUCCESS:
        print("YAPI.RegisterHub : " + str(errmsg))
        return

    print('Device list:')
    module = YModule.FirstModule()
    while module is not None:
        serial = await module.get_serialNumber()
        product_name = await module.get_productName()
        print(serial + ' (' + product_name + ')')
        module = module.nextModule()
    await YAPI.FreeAPI()


if __name__ == '__main__':
    asyncio.run(main(), debug=False)
