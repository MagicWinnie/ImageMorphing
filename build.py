import os
import sys
import shutil
import subprocess

PY_FILE = "ImageMorphGUITK.py"
haarcascade = "haarcascade_frontalface_alt2.xml"
LBFmodel = "lbfmodel.yaml"

if not os.path.isfile(os.path.join("src", PY_FILE)):
    print("[ERROR] %s not found." % os.path.join("src", PY_FILE))
    sys.exit(-1)

try:
    print("[INFO] Trying to delete %s ..." % PY_FILE.replace(".py", ""))
    shutil.rmtree(PY_FILE.replace(".py", ""))
except FileNotFoundError:
    print("[INFO] %s does not exist." % PY_FILE.replace(".py", ""))

try:
    print(
        "[INFO] Trying to delete %s-%s.zip ..."
        % (PY_FILE.replace(".py", ""), "Windows")
    )
    os.remove("%s-%s.zip" % (PY_FILE.replace(".py", ""), "Windows"))
except FileNotFoundError:
    print("[INFO] %s-%s.zip does not exist." % (PY_FILE.replace(".py", ""), "Windows"))


print("[INFO] Running pyinstaller...")
try:
    subprocess.run(
        [
            "pyinstaller.exe",
            "--windowed",
            "--distpath",
            ".",
            os.path.join("src", PY_FILE),
        ],
        check=True,
    )
except subprocess.CalledProcessError:
    print("[ERROR] Unknown error.")

PY_FILE = PY_FILE.replace(".py", "")

try:
    print("[INFO] Trying to delete build/ ...")
    shutil.rmtree("build/")
except FileNotFoundError:
    print("[INFO] build/ does not exist.")
try:
    print("[INFO] Trying to delete %s.spec..." % PY_FILE)
    os.remove("%s.spec" % PY_FILE)
except FileNotFoundError:
    print("[INFO] %s.spec does not exist." % PY_FILE)
    pass

print("[INFO] Copying %s ..." % haarcascade)
shutil.copyfile(
    os.path.join("src", haarcascade),
    os.path.join(PY_FILE, haarcascade),
)
print("[INFO] Copying %s ..." % LBFmodel)
shutil.copyfile(
    os.path.join("src", LBFmodel),
    os.path.join(PY_FILE, LBFmodel),
)
print("[INFO] Making an archive from %s ..." % PY_FILE)
shutil.make_archive("%s-%s" % (PY_FILE, "Windows"), "zip", PY_FILE)
print("[INFO] Done.")
