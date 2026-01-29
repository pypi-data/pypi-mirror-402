# -*- encoding: utf-8 -*-
"""
@File    :   yolo_postprocess.py
@Time    :   2026/01/18 09:59:06
@Author  :   ufy
@Contact :   antarm@outlook.com
@Version :   v1.0
@Desc    :   None
@Quotes  :   None
"""
# here put the import lib

from typing import List

import cv2
import numpy as np
import torch
from ultralytics.engine.results import Results


def is_in_region(
    cx: float,
    cy: float,
    w: int,
    h: int,
    regionVertex: List[List[float]] = [[0, 0], [1, 0], [1, 1], [0, 1]],
) -> bool:
    """
    Check if a given point (cx, cy) is within a specified region defined by a list of vertices.

    Parameters:
    cx (float): The x-coordinate of the point to check.
    cy (float): The y-coordinate of the point to check.
    w (int): The width of the image or region.
    h (int): The height of the image or region.
    regionVertex (List[List[float]]): A list of vertices defining the region. Each vertex is represented as a list of two floats [x, y]. x,y are normalized to the range [0, 1].

    Returns:
    bool: True if the point (cx, cy) is within the specified region, False otherwise.
    """
    assert len(regionVertex) >= 3, "Region must be defined by at least three vertices"
    assert all(len(vertex) == 2 for vertex in regionVertex), "Each vertex must have two coordinates [x, y]"
    mask = np.zeros((w, h))
    points = np.array(regionVertex) * [w, h]
    points = points.astype(int)
    cv2.fillConvexPoly(mask, points.astype(np.int32), 1)
    cx, cy = int(cx * w), int(cy * h)
    cx, cy = min(cx, w - 1), min(cy, h - 1)

    # return mask[cy, cx]
    return mask[cx, cy]


def region_filter(
    res: Results,
    regionVertex: List[List[float]] = [[0.05, 0.05], [0.95, 0.05], [0.95, 0.95], [0.05, 0.95]],
) -> Results:
    """
    Filters detection results based on a specified region, keeping only bounding boxes within the region

    Args:
        res (Results): Object containing detection results with bounding box information
        regionVertex (List[List[float]]): List of vertex coordinates defining the filtering region

    Returns:
        Results: Filtered detection results containing only bounding boxes within the specified region
    """

    assert len(regionVertex) >= 3, "Region must be defined by at least three vertices"
    assert all(len(vertex) == 2 for vertex in regionVertex), "Each vertex must have two coordinates [x, y]"

    # Initialize filter flag array to identify which bounding boxes are within the region
    f = [False for i in range(len(res.boxes.cls))]
    count = 0

    # Iterate through all bounding boxes, calculate center point and check if it's within the specified region
    for xyxy in res.boxes.xyxyn:
        cx, cy = (xyxy[0] + xyxy[2]) / 2, (xyxy[1] + xyxy[3]) / 2
        if is_in_region(cx, cy, 512, 512, regionVertex=regionVertex):
            f[count] = True
        count += 1

    # Retain only the filtered bounding box data based on the filter flags
    copy_data = torch.clone(res.boxes.data)
    res.boxes.data = copy_data[f]
    print(f"region:{res.boxes.data}")
    return res


def size_filter(res: Results, size: List[float] = [40, 320, 40, 320]) -> Results:
    """
    Filter detection results based on specified size parameters, keeping only bounding boxes within the area range

    Args:
        res (Results): Object containing detection results with bounding box information
        size (List[float]): Size filtering parameters in format [min_w, max_w, min_h, max_h] where:
                           - min_w: minimum width allowed
                           - max_w: maximum width allowed
                           - min_h: minimum height allowed
                           - max_h: maximum height allowed

    Returns:
        Results: Filtered detection results containing only bounding boxes within the specified size range
    """

    assert len(size) == 4, "Size parameter must be in the format [min_w, max_w, min_h, max_h]"

    # Initialize filter flag array to identify which bounding boxes meet size criteria
    f = [False for i in range(len(res.boxes.cls))]
    count = 0

    # Iterate through each detected object
    for xyxy in res.boxes.xyxy:
        # Calculate object's width and height
        w, h = xyxy[2] - xyxy[0], xyxy[3] - xyxy[1]

        # Size filtering -- convert to area filtering
        # Area should be between size[0]*size[2] (min area) and size[1]*size[3] (max area)
        if (w * h >= size[0] * size[2]) and (w * h <= size[1] * size[3]):
            f[count] = True
        count += 1

    # Copy and apply filtered detection data
    copy_data = torch.clone(res.boxes.data)
    res.boxes.data = copy_data[f]
    print(f"size:{res.boxes.data}")
    return res


def labels_filter(res: Results, target_labels: list[str]) -> Results:
    """
    Filter detection results based on specified target labels, keeping only bounding boxes with those labels

    Args:
        res (Results): Object containing detection results with bounding box information
        target_labels (List[str]): List of target labels to retain in the results

    Returns:
        Results: Filtered detection results containing only bounding boxes with specified target labels
    """

    # Initialize filter flag array to identify which bounding boxes match target labels
    f = [False for i in range(len(res.boxes.cls))]
    count = 0

    # Iterate through each detected object
    for cls_id in res.boxes.cls:
        label = res.names.get(int(cls_id), "unknown")
        if label in target_labels:
            f[count] = True
        count += 1

    # Copy and apply filtered detection data
    copy_data = torch.clone(res.boxes.data)
    res.boxes.data = copy_data[f]
    print(f"labels:{res.boxes.data}")
    return res


def results_to_alarms(res: Results) -> dict:
    """
    Convert YOLO detection results to alarm format data

    Args:
        res (Results): Detection results object containing boxes(cls, conf, xyxyn) and names attributes

    Returns:
        dict: Alarm data dictionary containing status field, and data field when detections exist
              - status: "alarm" if targets are detected, "normal" if no targets are detected
              - data: List of detected target information (only exists when there are detection results)
    """

    alarm = {}
    data = []

    # Iterate through class, confidence and coordinate information of detection boxes to construct detection data list
    for i, p, xyxy in zip(res.boxes.cls, res.boxes.conf, res.boxes.xyxyn):
        label = res.names[int(i)]
        data.append({"label": label, "score": p.item(), "box": xyxy.numpy().tolist()})

    # Set alarm status based on whether detection data exists
    if len(data) > 0:
        alarm["data"] = data
        alarm["status"] = "alarm"
    else:
        alarm["status"] = "normal"
    return alarm
