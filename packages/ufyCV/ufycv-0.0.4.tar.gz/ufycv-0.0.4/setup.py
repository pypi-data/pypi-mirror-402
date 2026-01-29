# -*- encoding: utf-8 -*-
"""
@File    :   setup.py
@Time    :   2026/01/17 09:39:43
@Author  :   ufy
@Contact :   antarm@outlook.com
@Version :   v1.0
@Desc    :   None
@Quotes  :   None
"""
# here put the import lib

from setuptools import find_packages, setup

setup(
    name="ufyCV",
    version="0.0.4",
    description="a python package for computer vision",
    author="ufy",
    author_email="antarm@outlook.com",
    url="https://github.com/ufy2024/ufyCV.git",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "torch",
        "ultralytics==8.2.31",
        "tritonclient[all]",
        "opencv-python",
    ],
)
