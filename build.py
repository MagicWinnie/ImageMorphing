import os
import sys
import shutil
import subprocess

args = sys.argv

if len(args) != 3:
    print("Usage: python build.py <version> <.py file>")
    sys.exit(-1)

if not os.path.isfile(os.path.join('src', args[2])):
    print("[ERROR] %s not found." % os.path.join('src', args[2]))
    sys.exit(-1)

try:
    print("[INFO] Trying to delete %s ..." % args[2].replace('.py', ''))
    shutil.rmtree(args[2].replace('.py', ''))
except FileNotFoundError:
    print("[INFO] %s does not exist." % args[2].replace('.py', ''))

try:
    print("[INFO] Trying to delete %s-%s.zip ..." % (args[1], args[2].replace('.py', '')))
    os.remove("%s-%s.zip" % (args[1], args[2].replace('.py', '')))
except FileNotFoundError:
    print("[INFO] %s-%s.zip does not exist." % (args[1], args[2].replace('.py', '')))


print("[INFO] Running pyinstaller...")
try:
    subprocess.run(['pyinstaller.exe', '--windowed', '--distpath', '.', os.path.join('src', args[2])], check=True)
except subprocess.CalledProcessError:
    print("[ERROR] Unknown error.")
args[2] = args[2].replace('.py', '')

try:
    print("[INFO] Trying to delete build/ ...")
    shutil.rmtree('build/')
except FileNotFoundError:
    print("[INFO] build/ does not exist.")
try:
    print("[INFO] Trying to delete %s.spec..." % args[2])
    os.remove('%s.spec' % args[2])
except FileNotFoundError:
    print("[INFO] %s.spec does not exist." % args[2])
    pass

print("[INFO] Copying shape_predictor_68_face_landmarks.dat ...")
shutil.copyfile(
    os.path.join('src', 'shape_predictor_68_face_landmarks.dat'),
    os.path.join(args[2], 'shape_predictor_68_face_landmarks.dat')
)
print("[INFO] Making an archive from %s ..." % args[2])
shutil.make_archive('%s-%s' % (args[1], args[2]), 'zip', args[2])
print("[INFO] Done.")
