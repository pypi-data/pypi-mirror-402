import os
import shutil

from .structs import Info, DstInfo

def genskel(info: Info) -> DstInfo:
    print("Generating app skeleton")

    dir = info.meta.bundle_name + ".app"
    cdir = dir + "/Contents"

    dsti = DstInfo(
        BundleDir = dir,
        ContentsDir = cdir,
        InfoPlist = cdir + "/Info.plist",
        PkgInfo = cdir + "/PkgInfo",
        Resources = cdir + "/Resources",
        Executables = cdir + "/MacOS",
        Libraries = cdir + "/Frameworks",
        MainExe = f"{cdir}/MacOS/{os.path.basename(info.files.exe)}",
        IconPath = cdir + "/Resources/icon.icns"
    )

    if os.path.exists(dir):
        shutil.rmtree(dir)
    os.mkdir(dir)
    os.mkdir(cdir)
    os.mkdir(dsti.Resources)
    os.mkdir(dsti.Libraries)
    os.mkdir(dsti.Executables)
    return dsti
