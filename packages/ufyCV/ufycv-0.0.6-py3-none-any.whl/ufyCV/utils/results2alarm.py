# -*- encoding: utf-8 -*-
"""
@File    :   results2alarm.py
@Time    :   2026/01/17 09:56:31
@Author  :   ufy
@Contact :   antarm@outlook.com
@Version :   v1.0
@Desc    :   根据检测结果生成报警信息
@Quotes  :   None
"""
# here put the import lib

from ultralytics.engine.results import Results


def yolo_results_to_alarms(results: Results, target_labels: list[str], conf_threshold: float = 0.5) -> list[str]:
    """
    根据YOLO检测结果生成报警信息

    参数:
        results: YOLO检测结果对象
        names (dict): 模型输出的类别名称字典
        target_labels (list[str]): 需要报警的目标标签列表
        conf_threshold (float): 报警的置信度阈值，默认为0.5

    返回:
        list[str]: 报警信息列表
    """
    alarms = []
    for result in results:
        for box in result.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            label = result.names.get(cls_id, "unknown")
            if label in target_labels and conf >= conf_threshold:
                alarm_msg = f"Alarm: Detected {label} with confidence {conf:.2f}"
                alarms.append(alarm_msg)
    return alarms
