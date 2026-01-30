#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
选择器模块
统一管理 Amazon 和 Walmart 页面的 CSS/XPath 选择器
"""

from .amazon_selectors import AmazonSelectors, AmazonTimeouts
from .walmart_selectors import WalmartSelectors, WalmartTimeouts

__all__ = [
    'AmazonSelectors',
    'AmazonTimeouts',
    'WalmartSelectors',
    'WalmartTimeouts'
]
