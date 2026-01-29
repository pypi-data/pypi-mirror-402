import subprocess
import os
import time
from .tor_binary import ensure_tor_binary

BASE_DIR = os.path.join(os.path.expanduser("~"), ".fast_tor")
TORRC_PATH = os.path.join(BASE_DIR, "torrc")

def write_torrc():
    os.makedirs(BASE_DIR, exist_ok=True)
    with open(TORRC_PATH, "w") as f:
        f.write(
            "SocksPort 9050 IsolateSOCKSAuth\n"
            "ControlPort 9051\n"
            "CookieAuthentication 1\n"
        )

def start_tor():
    write_torrc()
    tor_exe = ensure_tor_binary()

    subprocess.Popen(
        [tor_exe, "-f", TORRC_PATH],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW
    )

    time.sleep(5)  # وقت bootstrap
