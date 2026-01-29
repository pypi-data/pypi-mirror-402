from dataclasses import dataclass
from enum import Enum

@dataclass
class Info():
    @dataclass
    class Files():
        @dataclass
        class Icon():
            path: str
            class Type(Enum):
                PNG = "png"
                ICNS = "icns"
                NONE = "none"
            type: Type
        icon: Icon
        exe: str
        resources: list[str]
    @dataclass
    class Meta():
        bundle_name: str
        copyright: str
        description: str
        bundleid: str
        version: str
        osxmin: str

    files: Files
    meta: Meta

@dataclass
class DstInfo():
    BundleDir: str
    ContentsDir: str
    InfoPlist: str
    PkgInfo: str
    Resources: str
    Executables: str
    Libraries: str
    MainExe: str
    IconPath: str
