#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检测结果数据模型
存储双平台商品检测的完整结果
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Literal

from .monitor_item import MonitorItem


# 购物车状态类型
CartStatus = Literal['normal', 'missing', 'out_of_stock', 'not_available', 'error']


@dataclass
class DetectionResult:
    """检测结果数据模型

    存储单个商品在 Amazon 和 Walmart 两个平台的检测结果
    """
    monitor_item: MonitorItem

    # Amazon 检测结果
    amazon_cart_status: CartStatus = 'error'
    amazon_price: Optional[float] = None
    amazon_error: Optional[str] = None

    # Walmart 检测结果
    walmart_cart_status: CartStatus = 'error'
    walmart_price: Optional[float] = None
    walmart_error: Optional[str] = None

    # 价格分析
    price_diff_percent: Optional[float] = None

    # 时间戳
    detected_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """计算价格差异"""
        self._calculate_price_diff()

    def _calculate_price_diff(self):
        """计算价格差异百分比

        正值表示沃尔玛更贵，负值表示亚马逊更贵
        """
        if self.amazon_price and self.walmart_price and self.amazon_price > 0:
            self.price_diff_percent = (
                (self.walmart_price - self.amazon_price) / self.amazon_price
            ) * 100
        else:
            self.price_diff_percent = None

    @property
    def is_amazon_cart_normal(self) -> bool:
        """Amazon 购物车是否正常"""
        return self.amazon_cart_status == 'normal'

    @property
    def is_walmart_cart_normal(self) -> bool:
        """Walmart 购物车是否正常"""
        return self.walmart_cart_status == 'normal'

    @property
    def has_cart_issue(self) -> bool:
        """是否存在购物车问题"""
        return not self.is_amazon_cart_normal or not self.is_walmart_cart_normal

    @property
    def has_price_data(self) -> bool:
        """是否有完整的价格数据"""
        return self.amazon_price is not None and self.walmart_price is not None

    def should_alert_price(self) -> bool:
        """是否应该发送价格告警

        根据监控项的配置判断是否需要发送价格告警
        支持两种阈值类型：
        - percent: 百分比阈值，比较价格差异百分比
        - absolute: 具体数值阈值，比较价格差异绝对值
        """
        item = self.monitor_item

        # 价格监控未启用
        if not item.is_price_monitor_enabled:
            return False

        # 没有完整的价格数据
        if self.amazon_price is None or self.walmart_price is None:
            return False

        # 计算价格差异（绝对值）
        price_diff_absolute = self.walmart_price - self.amazon_price

        # 根据阈值类型判断
        if item.threshold_type == 'absolute':
            # 具体数值阈值：比较价格差异的绝对值
            # 沃尔玛价高提醒 (C列=1)
            if item.should_alert_walmart_higher:
                return price_diff_absolute > item.price_threshold

            # 亚马逊价高提醒 (C列=2)
            if item.should_alert_amazon_higher:
                return price_diff_absolute < -item.price_threshold

            # 任意价格差异提醒 (C列=3)
            if item.should_alert_any_diff:
                return abs(price_diff_absolute) > item.price_threshold
        else:
            # 百分比阈值：比较价格差异百分比
            if self.price_diff_percent is None:
                return False

            # 沃尔玛价高提醒 (C列=1)
            if item.should_alert_walmart_higher:
                return self.price_diff_percent > item.price_threshold

            # 亚马逊价高提醒 (C列=2)
            if item.should_alert_amazon_higher:
                return self.price_diff_percent < -item.price_threshold

            # 任意价格差异提醒 (C列=3)
            if item.should_alert_any_diff:
                return abs(self.price_diff_percent) > item.price_threshold

        return False

    def should_alert_cart(self) -> bool:
        """是否应该发送购物车告警

        根据监控项的配置判断是否需要发送购物车告警
        - E列=0: 关闭购物车监控
        - E列=1: 监控双平台购物车（Amazon和Walmart任一异常都告警）
        - E列=2: 仅监控沃尔玛购物车（只有Walmart异常才告警）
        """
        item = self.monitor_item

        # 购物车监控未启用
        if not item.is_cart_monitor_enabled:
            return False

        # E列=2: 仅监控沃尔玛购物车
        if item.is_cart_monitor_walmart_only:
            return not self.is_walmart_cart_normal

        # E列=1: 监控双平台购物车
        return self.has_cart_issue

    def get_amazon_cart_status_text(self) -> str:
        """获取 Amazon 购物车状态文本"""
        status_map = {
            'normal': '正常',
            'missing': '购物车丢失',
            'out_of_stock': '无库存',
            'not_available': '不可用',
            'error': '检测失败'
        }
        return status_map.get(self.amazon_cart_status, '未知')

    def get_walmart_cart_status_text(self) -> str:
        """获取 Walmart 购物车状态文本"""
        status_map = {
            'normal': '正常',
            'missing': '购物车丢失',
            'out_of_stock': '无库存',
            'not_available': '不可用',
            'error': '检测失败'
        }
        return status_map.get(self.walmart_cart_status, '未知')

    def get_price_diff_text(self) -> str:
        """获取价格差异文本"""
        if self.price_diff_percent is None:
            return 'N/A'

        sign = '+' if self.price_diff_percent >= 0 else ''
        return f"{sign}{self.price_diff_percent:.1f}%"

    def format_price(self, price: Optional[float]) -> str:
        """格式化价格显示"""
        if price is None:
            return 'N/A'
        return f"${price:.2f}"

    def __repr__(self) -> str:
        return (f"DetectionResult("
                f"walmart_id='{self.monitor_item.walmart_id}', "
                f"amazon_asin='{self.monitor_item.amazon_asin}', "
                f"amazon_cart='{self.amazon_cart_status}', "
                f"walmart_cart='{self.walmart_cart_status}', "
                f"price_diff={self.get_price_diff_text()})")
