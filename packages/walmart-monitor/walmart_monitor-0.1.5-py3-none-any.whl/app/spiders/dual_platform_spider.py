#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
双平台协调爬虫
协调 Amazon 和 Walmart 两个平台的商品检测
"""

import time
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.models import MonitorItem, DetectionResult
from app.config import settings

logger = logging.getLogger(__name__)


class DualPlatformSpider:
    """双平台协调爬虫

    协调 Amazon 和 Walmart 两个平台的商品检测，
    合并结果并计算价格差异。
    """

    def __init__(self, user_data_path: str = None, terminal_ui=None, concurrency: int = 1):
        """初始化双平台爬虫

        Args:
            user_data_path: Chrome 用户数据路径
            terminal_ui: 终端UI实例
            concurrency: 并发数
        """
        self.user_data_path = user_data_path
        self.terminal_ui = terminal_ui
        self.concurrency = concurrency

        # 延迟初始化爬虫实例
        self._amazon_spider = None
        self._walmart_spider = None

        # 统计数据
        self.stats = {
            'total_items': 0,
            'amazon_success': 0,
            'amazon_failed': 0,
            'walmart_success': 0,
            'walmart_failed': 0,
            'price_alerts': 0,
            'cart_alerts': 0,
            'start_time': None
        }

    @property
    def amazon_spider(self):
        """延迟加载 Amazon 爬虫"""
        if self._amazon_spider is None:
            # 导入放在这里避免循环导入
            from app.spider import AmazonSpider
            self._amazon_spider = AmazonSpider(
                user_data_path=self.user_data_path,
                terminal_ui=self.terminal_ui,
                concurrency=1  # Amazon 使用单标签页
            )
        return self._amazon_spider

    @property
    def walmart_spider(self):
        """延迟加载 Walmart 爬虫"""
        if self._walmart_spider is None:
            from app.spiders.walmart_spider import WalmartSpider
            self._walmart_spider = WalmartSpider(
                user_data_path=self.user_data_path,
                terminal_ui=self.terminal_ui,
                concurrency=1  # Walmart 使用单标签页
            )
        return self._walmart_spider

    def check_item(self, item: MonitorItem) -> DetectionResult:
        """检测单个商品项（双平台）

        Args:
            item: 监控项

        Returns:
            DetectionResult: 检测结果
        """
        item_id = f"{item.walmart_id}/{item.amazon_asin}"
        logger.info(f"开始检测商品: {item_id}")

        # 初始化结果
        result = DetectionResult(
            monitor_item=item,
            detected_at=datetime.now()
        )

        # 检测 Amazon
        try:
            amazon_result = self.amazon_spider.check_product_page(item.amazon_url)
            result.amazon_cart_status = self._map_amazon_status(amazon_result)
            result.amazon_price = self._extract_amazon_price(amazon_result)

            amazon_status = 'success' if result.amazon_cart_status == 'normal' else 'failed'

            if result.amazon_cart_status == 'normal':
                self.stats['amazon_success'] += 1
            else:
                self.stats['amazon_failed'] += 1

            # 更新终端UI - Amazon平台
            if self.terminal_ui:
                self.terminal_ui.update(
                    item_id=item_id,
                    platform='amazon',
                    status=amazon_status
                )

        except Exception as e:
            logger.error(f"Amazon 检测失败: {e}")
            result.amazon_cart_status = 'error'
            result.amazon_error = str(e)
            self.stats['amazon_failed'] += 1

            # 更新终端UI - Amazon失败
            if self.terminal_ui:
                self.terminal_ui.update(
                    item_id=item_id,
                    platform='amazon',
                    status='failed'
                )

        # 添加延迟，避免请求过于频繁
        time.sleep(1)

        # 检测 Walmart
        try:
            walmart_result = self.walmart_spider.check_product_page(item.walmart_url)
            result.walmart_cart_status = self._map_walmart_status(walmart_result)
            result.walmart_price = walmart_result.get('price')

            walmart_status = 'success' if result.walmart_cart_status == 'normal' else 'failed'

            if result.walmart_cart_status == 'normal':
                self.stats['walmart_success'] += 1
            else:
                self.stats['walmart_failed'] += 1

            # 更新终端UI - Walmart平台
            if self.terminal_ui:
                self.terminal_ui.update(
                    item_id=item_id,
                    platform='walmart',
                    status=walmart_status
                )

        except Exception as e:
            logger.error(f"Walmart 检测失败: {e}")
            result.walmart_cart_status = 'error'
            result.walmart_error = str(e)
            self.stats['walmart_failed'] += 1

            # 更新终端UI - Walmart失败
            if self.terminal_ui:
                self.terminal_ui.update(
                    item_id=item_id,
                    platform='walmart',
                    status='failed'
                )

        # 计算价格差异（在 DetectionResult.__post_init__ 中自动计算）
        result._calculate_price_diff()

        # 检查告警并更新统计
        has_cart_alert = result.should_alert_cart()
        has_price_alert = result.should_alert_price()

        if has_cart_alert:
            self.stats['cart_alerts'] += 1
        if has_price_alert:
            self.stats['price_alerts'] += 1

        # 更新终端UI - 告警信息（如果有）
        if self.terminal_ui and (has_cart_alert or has_price_alert):
            self.terminal_ui.update(
                item_id=item_id,
                has_cart_alert=has_cart_alert,
                has_price_alert=has_price_alert
            )

        logger.info(f"检测完成: {result}")
        return result

    def _map_amazon_status(self, result: Dict[str, Any]) -> str:
        """映射 Amazon 检测结果到状态"""
        if result.get('result') == 1:
            return 'normal'

        status = result.get('status', 'error')
        status_map = {
            'out_of_stock': 'out_of_stock',
            'cart_button_missing': 'missing',
            'page_error': 'error',
            'unknown': 'error'
        }
        return status_map.get(status, 'error')

    def _map_walmart_status(self, result: Dict[str, Any]) -> str:
        """映射 Walmart 检测结果到状态"""
        if result.get('result') == 1:
            return 'normal'

        status = result.get('status', 'error')
        status_map = {
            'not_available': 'not_available',
            'cart_missing': 'missing',
            'page_error': 'error',
            'error': 'error'
        }
        return status_map.get(status, 'error')

    def _extract_amazon_price(self, result: Dict[str, Any]) -> Optional[float]:
        """从 Amazon 检测结果中提取价格

        注意：当前 Amazon 爬虫可能没有返回价格，
        需要在 AmazonSpider 中添加价格提取功能
        """
        return result.get('price')

    def run(self, items: List[MonitorItem], data_source: str = "unknown") -> List[DetectionResult]:
        """执行批量检测任务

        Args:
            items: 监控项列表
            data_source: 数据来源标识

        Returns:
            List[DetectionResult]: 检测结果列表
        """
        if not items:
            logger.warning("监控项列表为空")
            return []

        self.stats['total_items'] = len(items)
        self.stats['start_time'] = time.time()

        logger.info(f"开始双平台检测任务: {len(items)} 个商品, 来源: {data_source}")

        results = []
        for i, item in enumerate(items, 1):
            logger.info(f"检测进度: {i}/{len(items)}")

            try:
                result = self.check_item(item)
                results.append(result)

                # 标记商品检测完成（两个平台都检测完）
                if self.terminal_ui:
                    item_id = f"{item.walmart_id}/{item.amazon_asin}"
                    self.terminal_ui.update_item_completed(item_id=item_id)

            except Exception as e:
                logger.error(f"检测商品 {item.walmart_id}/{item.amazon_asin} 失败: {e}")
                # 创建错误结果
                error_result = DetectionResult(
                    monitor_item=item,
                    amazon_cart_status='error',
                    amazon_error=str(e),
                    walmart_cart_status='error',
                    walmart_error=str(e),
                    detected_at=datetime.now()
                )
                results.append(error_result)

                # 标记商品检测完成（即使失败）
                if self.terminal_ui:
                    item_id = f"{item.walmart_id}/{item.amazon_asin}"
                    self.terminal_ui.update_item_completed(item_id=item_id)

            # 添加随机延迟
            if i < len(items):
                time.sleep(2)

        # 输出统计
        self._log_stats()

        return results

    def _log_stats(self):
        """输出统计信息"""
        elapsed = time.time() - self.stats['start_time'] if self.stats['start_time'] else 0

        logger.info("=== 双平台检测任务完成 ===")
        logger.info(f"总商品数: {self.stats['total_items']}")
        logger.info(f"Amazon 成功: {self.stats['amazon_success']}, 失败: {self.stats['amazon_failed']}")
        logger.info(f"Walmart 成功: {self.stats['walmart_success']}, 失败: {self.stats['walmart_failed']}")
        logger.info(f"购物车告警: {self.stats['cart_alerts']}")
        logger.info(f"价格告警: {self.stats['price_alerts']}")
        logger.info(f"总耗时: {elapsed:.1f}秒")

    def close(self):
        """关闭所有爬虫实例"""
        if self._amazon_spider:
            try:
                # 双平台模式下禁用 Amazon 爬虫的完成通知，使用统一的 BatchNotifier
                self._amazon_spider.close(send_notification=False)
            except Exception as e:
                logger.warning(f"关闭 Amazon 爬虫失败: {e}")

        if self._walmart_spider:
            try:
                self._walmart_spider.close()
            except Exception as e:
                logger.warning(f"关闭 Walmart 爬虫失败: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
