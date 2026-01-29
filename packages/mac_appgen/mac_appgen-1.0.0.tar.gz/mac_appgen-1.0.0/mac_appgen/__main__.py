import os
import sys

from .getinfo import get_info
from .genskel import genskel
from .copyfiles import copy_files
from .iconproc import process_icon
from .infoplist import gen_infoplist
from .getdep import get_deps

if not os.path.exists("appinfo.json"):
    print("Could not find appinfo.json", file=sys.stderr)
    sys.exit(1)

info = get_info("appinfo.json")
dsti = genskel(info)
copy_files(dsti, info.files)
process_icon(info, dsti)
gen_infoplist(dsti, info)
get_deps(dsti, info)

os.chmod(dsti.MainExe, 0o0755)
print("Done!")
