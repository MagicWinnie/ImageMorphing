import imageio
import numpy as np
import cv2
from ImageResizer import resize, image_resize
from imutils import face_utils


def rectContains(rect, point):
    if point[0] < rect[0]:
        return False
    elif point[1] < rect[1]:
        return False
    elif point[0] > rect[2]:
        return False
    elif point[1] > rect[3]:
        return False
    return True


def calculateDelaunayTriangles(rect, points):
    subdiv = cv2.Subdiv2D(rect)

    for p in points:
        subdiv.insert((p[0], p[1]))

    triangleList = subdiv.getTriangleList()

    delaunayTri = []

    for t in triangleList:
        pt = []
        pt.append((t[0], t[1]))
        pt.append((t[2], t[3]))
        pt.append((t[4], t[5]))

        pt1 = (t[0], t[1])
        pt2 = (t[2], t[3])
        pt3 = (t[4], t[5])

        if (
            rectContains(rect, pt1)
            and rectContains(rect, pt2)
            and rectContains(rect, pt3)
        ):
            ind = []
            for j in range(0, 3):
                for k in range(0, len(points)):
                    if (
                        abs(pt[j][0] - points[k][0]) < 1.0
                        and abs(pt[j][1] - points[k][1]) < 1.0
                    ):
                        ind.append(k)
            if len(ind) == 3:
                delaunayTri.append((ind[0], ind[1], ind[2]))

    return delaunayTri


# Apply affine transform calculated using srcTri and dstTri to src and
# output an image of size.
def applyAffineTransform(src, srcTri, dstTri, size):
    warpMat = cv2.getAffineTransform(np.float32(srcTri), np.float32(dstTri))
    dst = cv2.warpAffine(
        src,
        warpMat,
        (size[0], size[1]),
        None,
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REFLECT_101,
    )

    return dst


# Warps and alpha blends triangular regions from img1 and img2 to img
def morphTriangle(img1, img2, img, t1, t2, t, alpha):
    # Find bounding rectangle for each triangle
    r1 = cv2.boundingRect(np.float32([t1]))
    r2 = cv2.boundingRect(np.float32([t2]))
    r = cv2.boundingRect(np.float32([t]))

    # Offset points by left top corner of the respective rectangles
    t1Rect = []
    t2Rect = []
    tRect = []

    for i in range(0, 3):
        tRect.append(((t[i][0] - r[0]), (t[i][1] - r[1])))
        t1Rect.append(((t1[i][0] - r1[0]), (t1[i][1] - r1[1])))
        t2Rect.append(((t2[i][0] - r2[0]), (t2[i][1] - r2[1])))

    # Get mask by filling triangle
    mask = np.zeros((r[3], r[2], 3), dtype=np.float32)
    cv2.fillConvexPoly(mask, np.int32(tRect), (1.0, 1.0, 1.0), 16, 0)

    img1Rect = img1[r1[1] : r1[1] + r1[3], r1[0] : r1[0] + r1[2]]
    img2Rect = img2[r2[1] : r2[1] + r2[3], r2[0] : r2[0] + r2[2]]

    size = (r[2], r[3])
    warpImage1 = applyAffineTransform(img1Rect, t1Rect, tRect, size)
    warpImage2 = applyAffineTransform(img2Rect, t2Rect, tRect, size)

    # Alpha blend rectangular patches
    imgRect = (1.0 - alpha) * warpImage1 + alpha * warpImage2

    # Copy triangular region of the rectangular patch to the output image
    img[r[1] : r[1] + r[3], r[0] : r[0] + r[2]] = (
        img[r[1] : r[1] + r[3], r[0] : r[0] + r[2]] * (1 - mask) + imgRect * mask
    )


def processFrame(img1, img2, alpha, points1, points2):
    img1 = np.float32(img1)
    img2 = np.float32(img2)

    points = []

    # Weighted average point coordinates
    for i in range(0, len(points1)):
        x = (1 - alpha) * points1[i][0] + alpha * points2[i][0]
        y = (1 - alpha) * points1[i][1] + alpha * points2[i][1]
        points.append((x, y))

    rect = (0, 0, max(img1.shape[1], img2.shape[1]), max(img1.shape[0], img2.shape[0]))
    tri = calculateDelaunayTriangles(rect, points)

    imgMorph = np.zeros(
        tuple(
            [max(img1.shape[0], img2.shape[0]), max(img1.shape[1], img2.shape[1]), 3]
        ),
        dtype=img1.dtype,
    )

    for x, y, z in tri:
        t1 = [points1[x], points1[y], points1[z]]
        t2 = [points2[x], points2[y], points2[z]]
        t = [points[x], points[y], points[z]]

        morphTriangle(img1, img2, imgMorph, t1, t2, t, alpha)

    return np.uint8(imgMorph)

def area(points):
    n = len(points) 
    a = 0

    for i in range(n):
        j = (i + 1) % n
        a += abs(points[i][0] * points[j][1] - points[j][0] * points[i][1])

    return 0.5 * a

def getMaxAreaFace(landmarks):
    max_area = -1
    max_face = None
    for face in landmarks:
        a = area(face[0])
        if a > max_area:
            max_area = a
            max_face = face[0]
    return max_face


if __name__ == "__main__":
    haarcascade = "haarcascade_frontalface_alt2.xml"
    LBFmodel = "lbfmodel.yaml"

    detector = cv2.CascadeClassifier(haarcascade)
    landmark_detector = cv2.face.createFacemarkLBF()
    landmark_detector.loadModel(LBFmodel)

    filename1 = ""
    filename2 = ""

    delta = 10
    duration = 0.15
    reverse = False

    img1 = cv2.imread(filename1)
    img2 = cv2.imread(filename2)

    img1 = image_resize(img1, height=800)
    img2 = image_resize(img2, height=800)

    new_shape = (max(img1.shape[0], img2.shape[0]), max(img1.shape[1], img2.shape[1]))

    img1 = resize(img1, new_shape, True)
    img2 = resize(img2, new_shape, True)

    # FROM DLIB

    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    faces1 = detector.detectMultiScale(gray1)
    faces2 = detector.detectMultiScale(gray2)
    _, landmarks1 = landmark_detector.fit(gray1, faces1)
    _, landmarks2 = landmark_detector.fit(gray2, faces2)

    points1 = []
    points2 = []

    points1 = getMaxAreaFace(landmarks1).tolist()
    points2 = getMaxAreaFace(landmarks2).tolist()

    points1 = points1[:61]
    points2 = points2[:61]

    # CORNER POINTS1
    points1.append([img1.shape[1] - 1, 0])
    points1.append([img1.shape[1] - 1, img1.shape[0] - 1])
    points1.append([0, img1.shape[0] - 1])
    points1.append([0, 0])

    # MIDDLE POINTS1
    points1.append([img1.shape[1] // 2 - 1, 0])
    points1.append([0, img1.shape[0] // 2 - 1])
    points1.append([img1.shape[1] // 2 - 1, img1.shape[0] - 1])
    points1.append([img1.shape[1] - 1, img1.shape[0] // 2 - 1])

    # CORNER POINTS2
    points2.append([img2.shape[1] - 1, 0])
    points2.append([img2.shape[1] - 1, img2.shape[0] - 1])
    points2.append([0, img2.shape[0] - 1])
    points2.append([0, 0])

    # MIDDLE POINTS2
    points2.append([img2.shape[1] // 2 - 1, 0])
    points2.append([0, img2.shape[0] // 2 - 1])
    points2.append([img2.shape[1] // 2 - 1, img2.shape[0] - 1])
    points2.append([img2.shape[1] - 1, img2.shape[0] // 2 - 1])

    images = []
    for i in range(0, 101, delta):
        alpha = min(i / 100, 1.0)
        frame = processFrame(img1, img2, alpha, points1, points2)
        images.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    if reverse:
        images += list(reversed(images))

    imageio.mimsave("output.gif", images, duration=duration)
