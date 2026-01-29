# -*- encoding: utf-8 -*-
"""
@File    :   risk_recognition.py
@Time    :   2026/01/15 15:51:01
@Author  :   ufy
@Contact :   antarm@outlook.com
@Version :   v1.0
@Desc    :   Risk Recognition Functions
@Quotes  :   None
"""
# here put the import lib


from ast import mod

import numpy as np

from ufyCV.core.yolo import TritonYOLO
from ufyCV.core.yolo_postprocess import results_to_alarms

models: dict[str, TritonYOLO] = {}


def without_helmet(
    img: np.ndarray,
    model_name: str = "noHelmet_person",
    model_version: str = "1",
    names: dict = {0: "H", 1: "NH", 2: "unkown"},
    target_labels: list[str] = ["NH"],
    use_base64=True,
    url="localhost:8001",
    task: str = "detect",
    conf: float = 0.5,
    iou: float = 0.45,
    max_det: int = 1000,
    regionVertex: list[list[float]] = [[0, 0], [1, 0], [1, 1], [0, 1]],
    size: list[float] = [40, 320, 40, 320],
) -> dict:
    """
    施工安全帽检测，适用于识别未佩戴安全帽的风险。"""
    return yolo_detect_risk(
        img=img,
        model_name=model_name,
        model_version=model_version,
        names=names,
        target_labels=target_labels,
        use_base64=use_base64,
        url=url,
        task=task,
        conf=conf,
        iou=iou,
        max_det=max_det,
        regionVertex=regionVertex,
        size=size,
    )


def without_WU_and_RV(
    img: np.ndarray,
    model_name: str,
    model_version: str = "clothes",
    names: dict = {0: "RV", 1: "WU", 2: "unkown", 3: "NRVWU"},
    target_labels: list[str] = ["NWURV"],
    use_base64=True,
    url="localhost:8001",
    task: str = "detect",
    conf: float = 0.5,
    iou: float = 0.45,
    max_det: int = 1000,
    regionVertex: list[list[float]] = [[0, 0], [1, 0], [1, 1], [0, 1]],
    size: list[float] = [40, 320, 40, 320],
) -> dict:
    """
    工作服和反光衣检测，适用于识别未穿工作服和反光衣的风险。"""
    return yolo_detect_risk(
        img=img,
        model_name=model_name,
        model_version=model_version,
        names=names,
        target_labels=target_labels,
        use_base64=use_base64,
        url=url,
        task=task,
        conf=conf,
        iou=iou,
        max_det=max_det,
        regionVertex=regionVertex,
        size=size,
    )


def without_safety_rope(
    img: np.ndarray,
    model_name: str = "safe_belt",
    model_version: str = "1",
    names: dict = {0: "SR", 1: "NSR", 2: "unkown"},
    target_labels: list[str] = ["NSR"],
    use_base64=True,
    url="localhost:8001",
    task: str = "detect",
    conf: float = 0.5,
    iou: float = 0.45,
    max_det: int = 1000,
    regionVertex: list[list[float]] = [[0, 0], [1, 0], [1, 1], [0, 1]],
    size: list[float] = [40, 320, 40, 320],
) -> dict:
    """
    高空安全绳检测，适用于识别高空作业中未系安全绳的风险。
    """
    return yolo_detect_risk(
        img=img,
        model_name=model_name,
        model_version=model_version,
        names=names,
        target_labels=target_labels,
        use_base64=use_base64,
        url=url,
        task=task,
        conf=conf,
        iou=iou,
        max_det=max_det,
        regionVertex=regionVertex,
        size=size,
    )


def fire_smoke(
    img: np.ndarray,
    model_name: str = "fire_smoke",
    model_version: str = "1",
    names: dict = {0: "fire", 1: "smoke"},
    target_labels: list[str] = ["fire", "smoke"],
    use_base64=True,
    url="localhost:8001",
    task: str = "detect",
    conf: float = 0.5,
    iou: float = 0.45,
    max_det: int = 1000,
    regionVertex: list[list[float]] = [[0, 0], [1, 0], [1, 1], [0, 1]],
    size: list[float] = [40, 320, 40, 320],
) -> dict:
    """
    火灾烟雾检测，适用于识别火灾初期的火焰和烟雾。"""
    return yolo_detect_risk(
        img=img,
        model_name=model_name,
        model_version=model_version,
        names=names,
        target_labels=target_labels,
        use_base64=use_base64,
        url=url,
        task=task,
        conf=conf,
        iou=iou,
        max_det=max_det,
        regionVertex=regionVertex,
        size=size,
    )


def without_guardrail(img: np.ndarray) -> dict:
    """
    识别图片中不带护栏的风险（如深基坑、临边、洞口等）

    参数:
        img (np.ndarray): 输入的图像数组
    """
    pass


def illegal_parking_veihicle(
    img: np.ndarray,
    model_name: str = "parking",
    model_version: str = "1",
    names: dict = {0: "vehicle"},
    target_labels: list[str] = ["vehicle"],
    use_base64=True,
    url="localhost:8001",
    task: str = "detect",
    conf: float = 0.5,
    iou: float = 0.45,
    max_det: int = 1000,
    regionVertex: list[list[float]] = [[0, 0], [1, 0], [1, 1], [0, 1]],
    size: list[float] = [40, 320, 40, 320],
) -> dict:
    """
    车辆违停，适用于识别工地、消防通道等区域的违停车辆。
    """
    return yolo_detect_risk(
        img=img,
        model_name=model_name,
        model_version=model_version,
        names=names,
        target_labels=target_labels,
        use_base64=use_base64,
        url=url,
        task=task,
        conf=conf,
        iou=iou,
        max_det=max_det,
        regionVertex=regionVertex,
        size=size,
    )


def speeding_veihicle(img: np.ndarray) -> dict:
    """
    识别图片中超速车辆

    参数:
        img (np.ndarray): 输入的图像数组

    """
    pass


def collapse_risk(img: np.ndarray) -> dict:
    """
    识别图片中存在坍塌风险的区域

    参数:
        img (np.ndarray): 输入的图像数组

    """
    pass


# 人员入侵
def visual_fence(
    img: np.ndarray,
    model_name: str = "ufy",
    model_version: str = "1",
    names: dict = {
        0: "P",
        1: "bicycle",
        2: "car",
        3: "motorcycle",
        4: "airplane",
        5: "bus",
        6: "train",
        7: "truck",
        8: "boat",
        9: "traffic light",
        10: "fire hydrant",
        11: "stop sign",
        12: "parking meter",
        13: "bench",
        14: "bird",
        15: "cat",
        16: "dog",
        17: "horse",
        18: "sheep",
        19: "cow",
        20: "elephant",
        21: "bear",
        22: "zebra",
        23: "giraffe",
        24: "backpack",
        25: "umbrella",
        26: "handbag",
        27: "tie",
        28: "suitcase",
        29: "frisbee",
        30: "skis",
        31: "snowboard",
        32: "sports ball",
        33: "kite",
        34: "baseball bat",
        35: "baseball glove",
        36: "skateboard",
        37: "surfboard",
        38: "tennis racket",
        39: "bottle",
        40: "wine glass",
        41: "cup",
        42: "fork",
        43: "knife",
        44: "spoon",
        45: "bowl",
        46: "banana",
        47: "apple",
        48: "sandwich",
        49: "orange",
        50: "broccoli",
        51: "carrot",
        52: "hot dog",
        53: "pizza",
        54: "donut",
        55: "cake",
        56: "chair",
        57: "couch",
        58: "potted plant",
        59: "bed",
        60: "dining table",
        61: "toilet",
        62: "tv",
        63: "laptop",
        64: "mouse",
        65: "remote",
        66: "keyboard",
        67: "cell phone",
        68: "microwave",
        69: "oven",
        70: "toaster",
        71: "sink",
        72: "refrigerator",
        73: "book",
        74: "clock",
        75: "vase",
        76: "scissors",
        77: "teddy bear",
        78: "hair drier",
        79: "toothbrush",
    },
    target_labels: list[str] = ["P"],
    use_base64=True,
    url="localhost:8001",
    task: str = "detect",
    conf: float = 0.5,
    iou: float = 0.45,
    max_det: int = 1000,
    regionVertex: list[list[float]] = [[0, 0], [1, 0], [1, 1], [0, 1]],
    size: list[float] = [40, 320, 40, 320],
) -> dict:
    """
    视觉电子围栏，检测图像中是否有人员入侵。适用于检测周界入侵、翻越围栏等。

    参数说明参考：yolo_detect_risk函数。
    """
    return yolo_detect_risk(
        img=img,
        model_name=model_name,
        model_version=model_version,
        names=names,
        target_labels=target_labels,
        use_base64=use_base64,
        url=url,
        task=task,
        conf=conf,
        iou=iou,
        max_det=max_det,
        regionVertex=regionVertex,
        size=size,
    )


def personal_fall(
    img: np.ndarray,
    model_name: str = "person_fall",
    model_version: str = "1",
    names: dict = {0: "P", 1: "PF", 2: "other"},
    target_labels: list[str] = ["PF"],
    use_base64=True,
    url="localhost:8001",
    task: str = "detect",
    conf: float = 0.5,
    iou: float = 0.45,
    max_det: int = 1000,
    regionVertex: list[list[float]] = [[0, 0], [1, 0], [1, 1], [0, 1]],
    size: list[float] = [40, 320, 40, 320],
) -> dict:
    """
    人员跌倒，适用于中暑、触电、绊倒等，导致的人员倒地。
    """
    return yolo_detect_risk(
        img=img,
        model_name=model_name,
        model_version=model_version,
        names=names,
        target_labels=target_labels,
        use_base64=use_base64,
        url=url,
        task=task,
        conf=conf,
        iou=iou,
        max_det=max_det,
        regionVertex=regionVertex,
        size=size,
    )


def yolo_detect_risk(
    img: np.ndarray,
    model_name: str,
    model_version: str,
    names: dict,
    target_labels: list[str],
    use_base64=True,
    url="localhost:8001",
    task: str = "detect",
    conf: float = 0.5,
    iou: float = 0.45,
    max_det: int = 1000,
    regionVertex: list[list[float]] = [[0, 0], [1, 0], [1, 1], [0, 1]],
    size: list[float] = [40, 320, 40, 320],
) -> dict:
    """
    Uses YOLO model for risk detection, returning processed image results and alarm information

    Parameters:
        img (np.ndarray): Input image array
        model_name (str): Name of the model
        model_version (str): Model version number
        names (dict): Label name mapping dictionary
        target_labels (list[str]): Target label list
        use_base64 (bool): Whether to use base64 encoding for output image, default is True
        url (str): Triton server address, default is "localhost:8001"
        task (str): Task type, default is "detect"
        conf (float): Confidence threshold, default is 0.5
        iou (float): IOU threshold, default is 0.45
        max_det (int): Maximum detection count, default is 1000
        regionVertex (list[list[float]]): Region vertex coordinates, default is full image range
        size (list[float]): Size parameters, default is [40, 320, 40, 320]

    Returns:
        dict: Contains image result and alarm result
            - img_res: Processed image result
            - alarm_res: Alarm information result
    """
    # Check if model is loaded, create new TritonYOLO model instance if not loaded
    if model_name not in models:
        models[model_name] = TritonYOLO(model_name=model_name, model_version=model_version, url=url, task=task)
    model = models[model_name]

    # Execute model prediction
    results = model.predict(img, conf=conf, iou=iou, max_det=max_det)

    # Post-process prediction results
    results = model.post_process(results=results, target_labels=target_labels, regionVertex=regionVertex, size=size)

    # Draw detection results and return image
    img_res = model.plot_results(names=names, results=results, use_base64=use_base64)

    # Convert detection results to alarm format
    alarm_res = results_to_alarms(results)

    # Build output dictionary
    out = {
        "img_res": img_res,
        "alarm_res": alarm_res,
    }
    return out
