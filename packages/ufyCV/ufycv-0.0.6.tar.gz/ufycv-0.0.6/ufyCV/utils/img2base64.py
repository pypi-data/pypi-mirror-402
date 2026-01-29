# -*- encoding: utf-8 -*-
"""
@File    :   img2base64.py
@Time    :   2026/01/13 16:40:18
@Author  :   ufy
@Contact :   antarm@outlook.com
@Version :   v1.0
@Desc    :   None
@Quotes  :   None
"""
# here put the import lib
import base64

import cv2
import numpy as np


def img_to_base64(img: np.ndarray) -> str:
    """
    Convert an image to a base64 encoded string.

    Args:
        img (np.ndarray): Image as a numpy array.

    Returns:
        str: Base64 encoded string of the image.
    """
    img_bytes = img.tobytes()
    return base64.b64encode(img_bytes).decode("utf-8")


def base64_to_img(base64_string: str) -> np.ndarray:
    """
    Convert a base64 encoded string to an image.

    Args:
        base64_string (str): Base64 encoded string of the image.

    Returns:
        np.ndarray: Image as a numpy array.
    """
    return base64.b64decode(base64_string)


if __name__ == "__main__":
    # test
    img_str = img_to_base64(cv2.imread("test.jpg"))
    img = base64_to_img(img_str)
    cv2.imwrite("test_out.jpg", img)
