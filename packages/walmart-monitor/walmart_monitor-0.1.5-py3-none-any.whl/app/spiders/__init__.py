#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爬虫模块
提供 Amazon 和 Walmart 平台的商品检测爬虫
"""

from .base_spider import BaseSpider, TabWorker, set_thread_page, clear_thread_page
from .walmart_spider import WalmartSpider
from .walmart_bot_handler import WalmartBotHandler, BotDetectionType
from .dual_platform_spider import DualPlatformSpider

__all__ = [
    'BaseSpider',
    'TabWorker',
    'set_thread_page',
    'clear_thread_page',
    'WalmartSpider',
    'WalmartBotHandler',
    'BotDetectionType',
    'DualPlatformSpider'
]
