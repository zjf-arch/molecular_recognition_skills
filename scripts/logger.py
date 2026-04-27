#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志记录器模块 - 简化版，兼容Windows
"""

import logging
import sys
from pathlib import Path

# 创建日志记录器
logger = logging.getLogger('skills')
logger.setLevel(logging.INFO)

# 控制台输出
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# 日志格式
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)