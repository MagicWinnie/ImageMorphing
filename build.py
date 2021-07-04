import os
import sys
import shutil
import subprocess


PY_FILE = "ImageMorphGUITK"
haarcascade = "haarcascade_frontalface_alt2.xml"
LBFmodel = "lbfmodel.yaml"


if not os.path.isfile(os.path.join("src", PY_FILE + ".py")):
    print("[ERROR] %s not found." % os.path.join("src", PY_FILE + ".py"))
    sys.exit(-1)


print("[INFO] Trying to delete files from the last build...")
if os.path.isdir(PY_FILE):
    shutil.rmtree(PY_FILE)
if os.path.isdir("dist"):
    shutil.rmtree("dist")
if os.path.isdir("build"):
    shutil.rmtree("build")
if os.path.isfile("%s-%s.zip" % (PY_FILE, "Windows")):
    os.remove("%s-%s.zip" % (PY_FILE, "Windows"))


print("[INFO] Running pyinstaller...")
try:
    subprocess.run(
        [
            "pyinstaller.exe",
            "--windowed",
            "--icon=icon.ico",
            "--distpath",
            ".",
            os.path.join("src", PY_FILE + ".py"),
        ],
        check=True,
    )
except subprocess.CalledProcessError:
    print("[ERROR] Unknown error.")
    exit(-1)


if os.path.isdir("dist"):
    shutil.rmtree("dist")
if os.path.isdir("build"):
    shutil.rmtree("build")
if os.path.isfile("%s.spec" % PY_FILE):
    os.remove("%s.spec" % PY_FILE)


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
print("[INFO] Copying %s ..." % "icon.ico")
shutil.copyfile(
    "icon.ico",
    os.path.join(PY_FILE, "icon.ico"),
)


print("[INFO] Making an archive from %s ..." % PY_FILE)
shutil.make_archive("%s-%s" % (PY_FILE, "Windows"), "zip", PY_FILE)


print("[INFO] Done")
