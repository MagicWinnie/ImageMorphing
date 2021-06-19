import numpy as np
import cv2


def image_resize(image, width=None, height=None, inter=cv2.INTER_AREA):
    dim = None
    (h, w) = image.shape[:2]
    if width is None and height is None:
        return image
    if width is None:
        r = height / float(h)
        dim = (int(w * r), height)
    else:
        r = width / float(w)
        dim = (width, int(h * r))
    resized = cv2.resize(image, dim, interpolation=inter)
    return resized


def resize(img, new_shape, scale=False):
    if scale:
        if img.shape[1] - new_shape[1] < img.shape[0] - new_shape[0]:
            img = image_resize(img, height=new_shape[0])
        else:
            img = image_resize(img, width=new_shape[1])

    delta_w = new_shape[1] - img.shape[1]
    delta_h = new_shape[0] - img.shape[0]
    top, bottom = delta_h//2, delta_h - delta_h//2
    left, right = delta_w//2, delta_w - delta_w//2

    result = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=(255, 255, 255))

    result = cv2.resize(result, (new_shape[1], new_shape[0]))
    return result
