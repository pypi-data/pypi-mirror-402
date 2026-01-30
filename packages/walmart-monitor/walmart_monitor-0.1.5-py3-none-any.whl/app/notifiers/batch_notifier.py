#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量通知器
收集检测结果并发送汇总通知
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.models import DetectionResult
from app.notifier import DingTalkNotifier

logger = logging.getLogger(__name__)


class BatchNotifier:
    """批量通知器

    收集检测过程中的异常结果，在检测完成后发送汇总通知。

    通知规则：
    - 购物车异常：E列=1 且任一平台购物车状态异常 → @所有人
    - 购物车异常：E列=2 且沃尔玛购物车状态异常 → @所有人（忽略亚马逊状态）
    - 沃尔玛价高：C列=1 且差异>阈值 → 不@所有人
    - 亚马逊价高：C列=2 且差异>阈值 → 不@所有人
    - 阈值支持百分比（如20%）和具体数值（如5.5）
    """

    def __init__(self, notifier: DingTalkNotifier = None):
        """初始化批量通知器

        Args:
            notifier: 钉钉通知器实例
        """
        self.notifier = notifier or DingTalkNotifier()

        # 是否启用批量通知
        self.enabled = os.getenv('BATCH_NOTIFICATION_ENABLED', 'true').lower() == 'true'

        # 收集的异常结果
        self._cart_alerts: List[DetectionResult] = []  # 购物车异常
        self._price_alerts: List[DetectionResult] = []  # 价格异常

        # 统计数据
        self._total_checked = 0
        self._start_time: Optional[datetime] = None

        logger.info(f"BatchNotifier 初始化，启用状态: {self.enabled}")

    def start_batch(self):
        """开始新的批量检测"""
        self._cart_alerts.clear()
        self._price_alerts.clear()
        self._total_checked = 0
        self._start_time = datetime.now()
        logger.debug("开始新的批量检测")

    def collect(self, result: DetectionResult):
        """收集单个检测结果

        Args:
            result: 检测结果
        """
        self._total_checked += 1

        # 检查购物车异常
        if result.should_alert_cart():
            self._cart_alerts.append(result)
            logger.debug(f"收集购物车异常: {result.monitor_item.walmart_id}")

        # 检查价格异常
        if result.should_alert_price():
            self._price_alerts.append(result)
            logger.debug(f"收集价格异常: {result.monitor_item.walmart_id}")

    def collect_batch(self, results: List[DetectionResult]):
        """批量收集检测结果

        Args:
            results: 检测结果列表
        """
        for result in results:
            self.collect(result)

    def send_summary(self) -> bool:
        """发送汇总通知

        Returns:
            bool: 是否成功发送
        """
        if not self.enabled:
            logger.info("批量通知已禁用，跳过发送")
            return True

        if not self.notifier.bot:
            logger.warning("钉钉通知器未初始化，跳过发送")
            return False

        # 如果没有异常，发送正常汇总
        if not self._cart_alerts and not self._price_alerts:
            return self._send_normal_summary()

        # 有异常，发送异常汇总
        return self._send_alert_summary()

    def _send_normal_summary(self) -> bool:
        """发送正常汇总通知"""
        try:
            elapsed = self._get_elapsed_time()

            title = "✅ 双平台检测完成"
            text = f"""### ✅ 双平台检测完成

**检测时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**检测结果**:
- 总检测数: {self._total_checked}
- 购物车异常: 0
- 价格异常: 0

**耗时**: {elapsed}

> 所有商品状态正常
"""
            self.notifier.send_markdown(title, text, is_at_all=False)
            logger.info("正常汇总通知已发送")
            return True

        except Exception as e:
            logger.error(f"发送正常汇总通知失败: {e}")
            return False

    def _send_alert_summary(self) -> bool:
        """发送异常汇总通知"""
        try:
            # 判断是否需要 @所有人（购物车异常时需要）
            is_at_all = len(self._cart_alerts) > 0

            elapsed = self._get_elapsed_time()

            title = "⚠️ 双平台检测异常"
            text = f"""### ⚠️ 双平台检测异常

**检测时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**检测概况**:
- 总检测数: {self._total_checked}
- 购物车异常: {len(self._cart_alerts)}
- 价格异常: {len(self._price_alerts)}

**耗时**: {elapsed}

"""
            # 添加购物车异常详情
            if self._cart_alerts:
                text += self._format_cart_alerts()

            # 添加价格异常详情
            if self._price_alerts:
                text += self._format_price_alerts()

            self.notifier.send_markdown(title, text, is_at_all=is_at_all)
            logger.info(f"异常汇总通知已发送，@所有人: {is_at_all}")
            return True

        except Exception as e:
            logger.error(f"发送异常汇总通知失败: {e}")
            return False

    def _format_cart_alerts(self) -> str:
        """格式化购物车异常列表"""
        text = "\n---\n\n#### 🛒 购物车异常\n\n"

        for result in self._cart_alerts[:10]:  # 最多显示10条
            item = result.monitor_item
            amazon_status = self._get_status_emoji(result.amazon_cart_status)
            walmart_status = self._get_status_emoji(result.walmart_cart_status)

            # 显示监控模式
            monitor_mode = "仅WM" if item.is_cart_monitor_walmart_only else "双平台"

            text += f"- **{item.walmart_id}** / {item.amazon_asin} ({monitor_mode})\n"

            # E列=2时只显示Walmart状态
            if item.is_cart_monitor_walmart_only:
                text += f"  - Walmart: {walmart_status} {self._get_status_text(result.walmart_cart_status)}\n"
            else:
                text += f"  - Amazon: {amazon_status} {self._get_status_text(result.amazon_cart_status)}\n"
                text += f"  - Walmart: {walmart_status} {self._get_status_text(result.walmart_cart_status)}\n"

        if len(self._cart_alerts) > 10:
            text += f"\n> 还有 {len(self._cart_alerts) - 10} 条购物车异常未显示\n"

        return text

    def _format_price_alerts(self) -> str:
        """格式化价格异常列表"""
        text = "\n---\n\n#### 💰 价格异常\n\n"

        for result in self._price_alerts[:10]:  # 最多显示10条
            item = result.monitor_item

            # 格式化价格
            amazon_price = f"${result.amazon_price:.2f}" if result.amazon_price else "-"
            walmart_price = f"${result.walmart_price:.2f}" if result.walmart_price else "-"

            # 格式化差异
            if result.price_diff_percent is not None:
                sign = '+' if result.price_diff_percent >= 0 else ''
                diff_str = f"{sign}{result.price_diff_percent:.1f}%"
            else:
                diff_str = "-"

            # 计算绝对差异
            if result.amazon_price and result.walmart_price:
                abs_diff = result.walmart_price - result.amazon_price
                abs_diff_str = f"${abs_diff:+.2f}"
            else:
                abs_diff_str = "-"

            # 判断哪个平台价高
            if item.price_monitor_switch == 1:
                alert_type = "沃尔玛价高"
            elif item.price_monitor_switch == 2:
                alert_type = "亚马逊价高"
            else:
                alert_type = "价格差异"

            # 显示阈值类型
            if item.threshold_type == 'absolute':
                threshold_str = f">${item.price_threshold:.2f}"
            else:
                threshold_str = f">{item.price_threshold:.1f}%"

            text += f"- **{item.walmart_id}** / {item.amazon_asin}\n"
            text += f"  - Amazon: {amazon_price} | Walmart: {walmart_price}\n"
            text += f"  - 差异: {diff_str} ({abs_diff_str}) | 阈值: {threshold_str} ({alert_type})\n"

        if len(self._price_alerts) > 10:
            text += f"\n> 还有 {len(self._price_alerts) - 10} 条价格异常未显示\n"

        return text

    def _get_status_emoji(self, status: str) -> str:
        """获取状态对应的 emoji"""
        emoji_map = {
            'normal': '✅',
            'missing': '❌',
            'out_of_stock': '📦',
            'not_available': '🚫',
            'error': '⚠️'
        }
        return emoji_map.get(status, '❓')

    def _get_status_text(self, status: str) -> str:
        """获取状态对应的文本"""
        text_map = {
            'normal': '正常',
            'missing': '购物车丢失',
            'out_of_stock': '无库存',
            'not_available': '不可用',
            'error': '检测失败'
        }
        return text_map.get(status, status)

    def _get_elapsed_time(self) -> str:
        """获取耗时字符串"""
        if not self._start_time:
            return "-"

        elapsed = (datetime.now() - self._start_time).total_seconds()

        if elapsed < 60:
            return f"{elapsed:.1f}秒"
        elif elapsed < 3600:
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            return f"{minutes}分{seconds}秒"
        else:
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            return f"{hours}小时{minutes}分"

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'enabled': self.enabled,
            'total_checked': self._total_checked,
            'cart_alerts': len(self._cart_alerts),
            'price_alerts': len(self._price_alerts),
            'start_time': self._start_time.isoformat() if self._start_time else None,
            'elapsed': self._get_elapsed_time()
        }

    def send_immediate_alert(self, result: DetectionResult, alert_type: str = 'cart'):
        """立即发送单条告警（用于紧急情况）

        Args:
            result: 检测结果
            alert_type: 告警类型 ('cart' 或 'price')
        """
        if not self.notifier.bot:
            return

        item = result.monitor_item

        if alert_type == 'cart':
            title = "🚨 购物车异常告警"
            text = f"""### 🚨 购物车异常告警

**商品信息**:
- Walmart ID: {item.walmart_id}
- Amazon ASIN: {item.amazon_asin}
- 来源: {item.source_sheet}

**状态**:
- Amazon: {self._get_status_text(result.amazon_cart_status)}
- Walmart: {self._get_status_text(result.walmart_cart_status)}

**检测时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            self.notifier.send_markdown(title, text, is_at_all=True)

        elif alert_type == 'price':
            amazon_price = f"${result.amazon_price:.2f}" if result.amazon_price else "-"
            walmart_price = f"${result.walmart_price:.2f}" if result.walmart_price else "-"
            diff_str = f"{result.price_diff_percent:+.1f}%" if result.price_diff_percent else "-"

            title = "💰 价格异常告警"
            text = f"""### 💰 价格异常告警

**商品信息**:
- Walmart ID: {item.walmart_id}
- Amazon ASIN: {item.amazon_asin}
- 来源: {item.source_sheet}

**价格**:
- Amazon: {amazon_price}
- Walmart: {walmart_price}
- 差异: {diff_str}

**检测时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            self.notifier.send_markdown(title, text, is_at_all=False)
