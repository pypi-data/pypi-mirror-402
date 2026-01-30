#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志记录数据模型
对应钉钉表格 Res Sheet 的数据结构
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

from .detection_result import DetectionResult


@dataclass
class ResRecord:
    """Res Sheet 日志记录数据模型

    对应钉钉表格 Res Sheet 列结构:
    - A列: 日期
    - B列: 时间
    - C列: 亚马逊ASIN
    - D列: 沃尔玛ID
    - E列: 亚马逊价格
    - F列: 沃尔玛价格
    - G列: 价格差异
    - H列: 亚马逊购物车状态
    - I列: 沃尔玛购物车状态
    """
    date: str                    # 日期 (A列)
    time: str                    # 时间 (B列)
    amazon_asin: str             # 亚马逊ASIN (C列)
    walmart_id: str              # 沃尔玛ID (D列)
    amazon_price: str            # 亚马逊价格 (E列)
    walmart_price: str           # 沃尔玛价格 (F列)
    price_diff: str              # 价格差异 (G列)
    amazon_cart_status: str      # 亚马逊购物车状态 (H列)
    walmart_cart_status: str     # 沃尔玛购物车状态 (I列)

    @classmethod
    def from_detection_result(cls, result: DetectionResult) -> 'ResRecord':
        """从检测结果创建日志记录

        Args:
            result: 检测结果对象

        Returns:
            ResRecord: 日志记录对象
        """
        now = result.detected_at or datetime.now()

        return cls(
            date=now.strftime("%Y-%m-%d"),
            time=now.strftime("%H:%M:%S"),
            amazon_asin=result.monitor_item.amazon_asin,
            walmart_id=result.monitor_item.walmart_id,
            amazon_price=result.format_price(result.amazon_price),
            walmart_price=result.format_price(result.walmart_price),
            price_diff=result.get_price_diff_text(),
            amazon_cart_status=result.get_amazon_cart_status_text(),
            walmart_cart_status=result.get_walmart_cart_status_text()
        )

    def to_row(self) -> List[str]:
        """转换为表格行数据

        Returns:
            List[str]: 按列顺序排列的数据列表
        """
        return [
            self.date,
            self.time,
            self.amazon_asin,
            self.walmart_id,
            self.amazon_price,
            self.walmart_price,
            self.price_diff,
            self.amazon_cart_status,
            self.walmart_cart_status
        ]

    @staticmethod
    def get_headers() -> List[str]:
        """获取表头

        Returns:
            List[str]: 表头列表
        """
        return [
            '日期',
            '时间',
            '亚马逊ASIN',
            '沃尔玛ID',
            '亚马逊价格',
            '沃尔玛价格',
            '价格差异',
            '亚马逊购物车状态',
            '沃尔玛购物车状态'
        ]

    def __repr__(self) -> str:
        return (f"ResRecord({self.date} {self.time}, "
                f"ASIN={self.amazon_asin}, WM_ID={self.walmart_id}, "
                f"diff={self.price_diff})")
