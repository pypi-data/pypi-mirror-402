import sys

from yoctolib.yocto_api import YRefParam, YAPI, xarray
from yoctolib.yocto_files import YFiles, YFileRecord


def die(msg: str) -> None:
    YAPI.FreeAPI()
    sys.exit(msg + ' (check USB cable)')


# the API use local USB devices through VirtualHub
errmsg: YRefParam = YRefParam()
if YAPI.RegisterHub("localhost", errmsg) != YAPI.SUCCESS:
    sys.exit("RegisterHub failed: " + errmsg.value)

target: str = 'any'
if len(sys.argv) > 1:
    target = sys.argv[1]

if target == 'any':
    # retrieve any filesystem
    files = YFiles.FirstFiles()
    if files is None:
        die('No module connected')
else:
    files = YFiles.FindFiles(target + ".files")

if not files.isOnline():
    die("Module not connected ")

# create text files and upload them to the device
for i in range(1, 5):
    contents: str = "This is file " + str(i)
    # convert the string to binary data
    binaryData = contents.encode("latin-1")
    # upload the file to the device
    files.upload("file" + str(i) + ".txt", binaryData)

# list files found on the device
print("Files on device:")
filelist: list[YFileRecord] = files.get_list("*")

for i in range(len(filelist)):
    file: YFileRecord = filelist[i]
    print('%-40s%08x    %d bytes' % (file.get_name(), file.get_crc() % 0xffffffff, file.get_size()))

# download a file
binaryData = files.download("file1.txt")

# and display
print("")
print("contents of file1.txt:")
print(binaryData.decode("latin-1"))
YAPI.FreeAPI()
