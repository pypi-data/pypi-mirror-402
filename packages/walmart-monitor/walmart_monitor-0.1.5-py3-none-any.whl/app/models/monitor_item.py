#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
商品监控项数据模型
对应钉钉表格中的商品数据（WM-FIT / WM-Uriah Sheet）
"""

from dataclasses import dataclass
from typing import Literal


# 阈值类型
ThresholdType = Literal['percent', 'absolute']


@dataclass
class MonitorItem:
    """商品监控项数据模型

    对应钉钉表格列结构:
    - A列: 沃尔玛ID
    - B列: 亚马逊ASIN
    - C列: 价格监控开关 (0=关闭, 1=沃尔玛价高提醒, 2=亚马逊价高提醒)
    - D列: 价格阈值 (支持百分比如"20%"或具体数值如"5.5")
    - E列: 购物车监控开关 (0=关闭, 1=开启, 2=仅监控沃尔玛)
    """
    walmart_id: str              # 沃尔玛商品ID (A列)
    amazon_asin: str             # 亚马逊ASIN (B列)
    price_monitor_switch: int    # 价格监控开关 (C列)
    price_threshold: float       # 价格阈值 (D列)
    cart_monitor_switch: int     # 购物车监控开关 (E列)
    source_sheet: str            # 数据来源Sheet名称
    threshold_type: ThresholdType = 'percent'  # 阈值类型: percent=百分比, absolute=具体数值

    def __post_init__(self):
        """数据验证和类型转换"""
        # 确保ID和ASIN是字符串
        self.walmart_id = str(self.walmart_id).strip()
        self.amazon_asin = str(self.amazon_asin).strip()

        # 确保开关是整数
        self.price_monitor_switch = int(self.price_monitor_switch) if self.price_monitor_switch else 0
        self.cart_monitor_switch = int(self.cart_monitor_switch) if self.cart_monitor_switch else 0

        # 确保阈值是浮点数，默认10%
        try:
            self.price_threshold = float(self.price_threshold) if self.price_threshold else 10.0
        except (ValueError, TypeError):
            self.price_threshold = 10.0

    @property
    def walmart_url(self) -> str:
        """生成沃尔玛商品URL"""
        return f"https://www.walmart.com/ip/{self.walmart_id}"

    @property
    def amazon_url(self) -> str:
        """生成亚马逊商品URL"""
        return f"https://www.amazon.com/dp/{self.amazon_asin}"

    @property
    def is_price_monitor_enabled(self) -> bool:
        """价格监控是否启用"""
        return self.price_monitor_switch > 0

    @property
    def is_cart_monitor_enabled(self) -> bool:
        """购物车监控是否启用（包括仅监控沃尔玛的情况）"""
        return self.cart_monitor_switch in (1, 2)

    @property
    def is_cart_monitor_both(self) -> bool:
        """是否同时监控双平台购物车 (E列=1)"""
        return self.cart_monitor_switch == 1

    @property
    def is_cart_monitor_walmart_only(self) -> bool:
        """是否仅监控沃尔玛购物车 (E列=2)"""
        return self.cart_monitor_switch == 2

    @property
    def should_alert_walmart_higher(self) -> bool:
        """是否在沃尔玛价格更高时告警"""
        return self.price_monitor_switch == 1

    @property
    def should_alert_amazon_higher(self) -> bool:
        """是否在亚马逊价格更高时告警"""
        return self.price_monitor_switch == 2

    @property
    def should_alert_any_diff(self) -> bool:
        """是否在任意价格差异时告警（无论高低）"""
        return self.price_monitor_switch == 3

    def is_valid(self) -> bool:
        """检查数据是否有效"""
        return bool(self.walmart_id and self.amazon_asin)

    def __repr__(self) -> str:
        return (f"MonitorItem(walmart_id='{self.walmart_id}', "
                f"amazon_asin='{self.amazon_asin}', "
                f"price_monitor={self.price_monitor_switch}, "
                f"cart_monitor={self.cart_monitor_switch})")
