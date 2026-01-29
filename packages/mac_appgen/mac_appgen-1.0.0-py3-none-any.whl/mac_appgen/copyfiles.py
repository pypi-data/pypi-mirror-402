import shutil
import os

from .structs import DstInfo, Info

def copy_files(dsti: DstInfo, files: Info.Files):
    print(f"Copying executable: {files.exe} -> {dsti.MainExe}")
    shutil.copyfile(files.exe, dsti.MainExe)
    os.chmod(dsti.MainExe, 0o0755)
    for file in files.resources:
        path = dsti.Resources + os.path.basename(file)
        print(f"Copying resource: {file} -> {path}")
        shutil.copyfile(file, path)
