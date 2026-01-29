# -*- encoding: utf-8 -*-
"""
@File    :   detection.py
@Time    :   2026/01/15 14:19:23
@Author  :   ufy
@Contact :   antarm@outlook.com
@Version :   v1.0
@Desc    :   None
@Quotes  :   None
"""
# here put the import lib


import re
from typing import List, Union

import cv2
import numpy as np
from tritonclient.grpc import InferenceServerClient as TritonClient
from ultralytics import YOLO
from ultralytics.engine.results import Results

from core.yolo_postprocess import labels_filter, region_filter, size_filter
from utils.img2base64 import img_to_base64


class TritonYOLO:

    def __init__(
        self,
        model_name: str,
        model_version: str = "1",
        url: str = "localhost:8001",
        task: str = "detect",
    ):
        """
        Initialize the model client object

        Args:
            model_name (str): Name of the model
            model_version (str, optional): Model version, defaults to "1"
            url (str, optional): Triton server address, defaults to "localhost:8001"
            task (str, optional): Task type, defaults to "detect"

        Returns:
            None
        """
        # Initialize Triton client and server configuration information
        self.url = url
        self.model_name = model_name
        self.model_version = model_version
        self.triton_client = TritonClient(url=self.url)
        # Create YOLO model instance
        self.model = YOLO(model=f"{url}/{model_name}/{model_version}", task=task, verbose=True)

    def predict_one(
        self, names: dict, img: np.ndarray, conf: float = 0.25, iou: float = 0.45, max_det: int = 1000
    ) -> Results:
        res = self.model.predict(source=img, conf=conf, iou=iou, max_det=max_det)[0]
        res.names = names
        return res

    def plot_results_one(
        self,
        res: Results,
        regionVertex: list[list[float]] = [[0.05, 0.05], [0.95, 0.05], [0.95, 0.95], [0.05, 0.95]],
        use_base64: bool = True,
    ) -> Union[np.ndarray, str]:
        annotated_frame = res.plot()

        w, h = annotated_frame.shape[1], annotated_frame.shape[0]
        vertex = (np.array(regionVertex) * [w, h]).astype(int)
        annotated_frame = cv2.polylines(annotated_frame, [vertex], isClosed=True, color=(0, 0, 255), thickness=5)

        if use_base64:
            annotated_frame = img_to_base64(annotated_frame)

        return annotated_frame

    def post_process_one(
        self,
        res: Results,
        target_labels: list[str],
        regionVertex: list[list[float]],
        size: list[float] = [40, 320, 40, 320],
    ) -> List[Union[np.ndarray, str]]:
        """
        Post-process the detection results by applying label filtering, region filtering and size filtering.

        Args:
            results (List[Results]): List of detection results from the model
            target_labels (list[str]): List of target label names to filter detections
            regionVertex (list[list[float]]): List of vertex coordinates defining the region of interest for filtering
            size (list[float]): Size parameters for filtering detections based on dimensions

        Returns:
            List[Union[np.ndarray, str]]: List of filtered detection results after applying all filters
        """

        result = labels_filter(res, target_labels)
        result = region_filter(result, regionVertex)
        result = size_filter(result, size)

        return result
