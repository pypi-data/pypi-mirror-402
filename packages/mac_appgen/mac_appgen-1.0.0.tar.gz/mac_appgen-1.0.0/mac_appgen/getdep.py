from .structs import DstInfo, Info
import subprocess
import os

def get_deps(dsti: DstInfo, info: Info):
    print("Retreiving Dependencies")
    subprocess.run([
        "dylibbundler",
        "-b",
        "-d", dsti.Libraries,
        "-p", "@executable_path/../Frameworks",
        "-x", dsti.MainExe
    ], stdout=open(os.devnull), stderr=open(os.devnull))
