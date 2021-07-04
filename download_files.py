# Download haarcascade and LBFmodel

import os
import urllib.request as urlreq
from urllib.error import URLError, HTTPError

if __name__ == "__main__":
    destination = "src/"
    haarcascade = "haarcascade_frontalface_alt2.xml"
    haarcascade_url = "https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_alt2.xml"
    LBFmodel = "lbfmodel.yaml"
    LBFmodel_url = "https://github.com/kurnianggoro/GSOC2017/raw/master/data/lbfmodel.yaml"

    print("[INFO] Downloading haarcascade...")
    try:
        urlreq.urlretrieve(haarcascade_url, os.path.join(destination, haarcascade))
    except (URLError, HTTPError):
        print("[ERROR] Could not download haarcascade! Check your internet connection!")
        exit(-1)

    print("[INFO] Downloading LBFmodel...")
    try:
        urlreq.urlretrieve(LBFmodel_url, os.path.join(destination, LBFmodel))
    except (URLError, HTTPError):
        print("[ERROR] Could not download LBFmodel! Check your internet connection!")
        exit(-1)
        
    print("[INFO] Done")