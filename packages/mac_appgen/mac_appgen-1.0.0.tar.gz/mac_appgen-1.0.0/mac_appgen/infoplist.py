from .structs import DstInfo, Info
import os

def gen_infoplist(dsti: DstInfo, info: Info):
    print("Generating Info.plist")
    infoplist = f"""
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
    <dict>
        <key>CFBundleDevelopmentRegion</key>
        <string>English</string>
        <key>CFBundleExecutable</key>
        <string>{os.path.basename(info.files.exe)}</string>
        <key>CFBundleGetInfoString</key>
        <string>{info.meta.description}</string>
        <key>CFBundleIconFile</key>
        <string>{'icon.icns' if info.files.icon.type is not None else ''}</string>
        <key>CFBundleIdentifier</key>
        <string>{info.meta.bundleid}</string>
        <key>CFBundleInfoDictionaryVersion</key>
        <string>6.0</string>
        <key>CFBundleLongVersionString</key>
        <string>{info.meta.version}</string>
        <key>CFBundleName</key>
        <string>{info.meta.bundle_name}</string>
        <key>CFBundlePackageType</key>
        <string>APPL</string>
        <key>CFBundleShortVersionString</key>
        <string>{info.meta.version}</string>
        <key>CFBundleSignature</key>
        <string>????</string>
        <key>CFBundleVersion</key>
        <string>1.0</string>
        <key>LSMinimumSystemVersion</key>
        <string>{info.meta.osxmin}</key>
        <key>CSResourcesFileMapped</key>
        <true/>
        <key>NSHumanReadableCopyright</key>
        <string>{info.meta.copyright}</string>
        <key>CFBundleSupportedPlatforms</key>
        <array>
            <string>MacOSX</string>
        </array>
    </dict>
</plist>
    """

    with open(dsti.InfoPlist, "w") as f:
        f.write(infoplist)
        f.close()

    with open(dsti.PkgInfo, "w") as f:
        f.write("APPL????")
        f.close()
