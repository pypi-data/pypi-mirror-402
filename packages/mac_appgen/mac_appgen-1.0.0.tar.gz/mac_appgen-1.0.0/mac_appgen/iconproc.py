import shutil
import os
import subprocess

from .structs import Info, DstInfo

def process_icon(info: Info, dsti: DstInfo):
    print("Processing app icon")
    iconnames = [
        [16, "icon_16x16.png"],
        [32, "icon_16x16@2x.png"],
        [32, "icon_32x32.png"],
        [64, "icon_32x32@2x.png"],
        [128, "icon_128x128.png"],
        [256, "icon_128x128@2x.png"],
        [256, "icon_256x256.png"],
        [512, "icon_256x256@2x.png"],
        [512, "icon_512x512.png"],
        [1024, "icon_512x512@2x.png"]
    ]

    iconpath = info.files.icon.path
    type = info.files.icon.type
    dest = dsti.IconPath
    if type == Info.Files.Icon.Type.PNG:
        out = "icon.iconset"
        def mki(size: int, name: str):
            subprocess.run(["sips", "-z", str(size), str(size), iconpath, "--out", out + "/" + name])
        os.mkdir("icon.iconset")
        for icn in iconnames:
            mki(icn[0], icn[1])
        subprocess.run(["iconutil", "-c", out, "--output", dest])
    elif type == Info.Files.Icon.Type.ICNS:
        shutil.copyfile(iconpath, dest)
    elif type == Info.Files.Icon.Type.NONE:
        return
