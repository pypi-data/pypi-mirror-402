import os
import urllib.request
import zipfile
import shutil

TOR_URL = "https://archive.torproject.org/tor-package-archive/torbrowser/13.0.15/tor-win64-0.4.8.21.zip"

BASE_DIR = os.path.join(os.path.expanduser("~"), ".fast_tor")
TOR_DIR = os.path.join(BASE_DIR, "tor")

def ensure_tor_binary():
    tor_exe = os.path.join(TOR_DIR, "tor.exe")
    if os.path.exists(tor_exe):
        return tor_exe

    os.makedirs(TOR_DIR, exist_ok=True)
    zip_path = os.path.join(BASE_DIR, "tor.zip")

    urllib.request.urlretrieve(TOR_URL, zip_path)

    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(TOR_DIR)

    os.remove(zip_path)

    return tor_exe
