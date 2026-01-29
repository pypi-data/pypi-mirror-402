from .structs import Info
import json

def get_info(filepath: str) -> Info:
    print("Loading app info")
    with open(filepath) as f:
        data = json.load(f)

    mdata = data["meta"]
    fdata = data["files"]

    return Info(
        files=Info.Files(
            icon=Info.Files.Icon(
                path = fdata["icon"]["path"],
                type = fdata["icon"]["type"]
            ),
            exe=fdata["executable"],
            resources=fdata["resources"]
        ),
        meta=Info.Meta(
            bundle_name=mdata["bundlename"],
            copyright=mdata["copyright"],
            description=mdata["description"],
            bundleid=mdata["bundleid"],
            version=mdata["version"],
            osxmin =  mdata["osxminimum"]
        )
    )
