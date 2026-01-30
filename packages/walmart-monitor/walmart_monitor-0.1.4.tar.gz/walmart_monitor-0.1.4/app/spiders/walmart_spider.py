#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Walmart 商品检测爬虫
实现 Walmart 平台的购物车状态检测和价格提取
"""

import re
import time
import logging
from typing import Dict, Any, Optional

from .base_spider import BaseSpider, set_thread_page, clear_thread_page
from .walmart_bot_handler import WalmartBotHandler, BotDetectionType
from app.selectors.walmart_selectors import WalmartSelectors, WalmartTimeouts

logger = logging.getLogger(__name__)


class WalmartSiteConfigs:
    """Walmart 站点配置"""

    SITE_CONFIGS = {
        'walmart.com': {
            'zip_code': '10001',
            'country': 'US',
            'country_name': '美国',
            'homepage': 'https://www.walmart.com/',
            'currency': 'USD'
        }
    }

    @classmethod
    def get_site_config(cls, url: str) -> Dict[str, str]:
        """根据URL获取站点配置"""
        # 目前只支持美国站点
        return cls.SITE_CONFIGS.get('walmart.com', cls.SITE_CONFIGS['walmart.com'])


class WalmartSpider(BaseSpider):
    """Walmart 商品检测爬虫

    实现功能：
    - 购物车状态检测（Add to Cart 按钮）
    - 价格提取
    - 商品可用性检测
    - 防爬验证处理
    """

    def __init__(self, user_data_path: str = None, terminal_ui=None, concurrency: int = 1):
        super().__init__(user_data_path, terminal_ui, concurrency)
        self.selectors = WalmartSelectors
        self.site_configs = WalmartSiteConfigs

        # 初始化防爬处理器（延迟初始化，因为 page 可能还没准备好）
        self._bot_handler = None

    @property
    def bot_handler(self) -> WalmartBotHandler:
        """获取防爬处理器（延迟初始化）"""
        if self._bot_handler is None:
            self._bot_handler = WalmartBotHandler(
                page=self.page,
                terminal_ui=self.terminal_ui
            )
        return self._bot_handler

    def _get_site_config(self, url: str) -> Dict[str, str]:
        """根据URL获取站点配置信息"""
        return self.site_configs.get_site_config(url)

    def check_product_page(self, url: str) -> Dict[str, Any]:
        """检查单个 Walmart 商品页面并返回结果

        Args:
            url: Walmart 商品页面 URL

        Returns:
            Dict: 检测结果
                - url: 商品URL
                - result: 1=正常, 0=异常, -1=页面错误
                - status: 状态描述
                - price: 商品价格（如果提取成功）
        """
        try:
            logger.info(f"开始检测 Walmart 商品: {url}")
            self.page.get(url)

            # 关键改进：等待文档完全加载（包括JS执行）
            logger.debug("等待页面DOM加载完成...")
            self.page.wait.doc_loaded(timeout=10)

            # 额外等待，让动态内容渲染
            time.sleep(WalmartTimeouts.NORMAL)

            # 使用防爬处理器检测和处理验证
            self._bot_handler = WalmartBotHandler(
                page=self.page,
                terminal_ui=self.terminal_ui
            )

            detection_type = self.bot_handler.detect()
            if detection_type != BotDetectionType.NONE:
                logger.info(f"检测到防爬验证: {detection_type.value}")
                if not self.bot_handler.handle(detection_type):
                    return {
                        "url": url,
                        "result": -1,
                        "status": "bot_detection",
                        "message": f"防爬验证未通过: {detection_type.value}"
                    }
                time.sleep(WalmartTimeouts.NORMAL)

            # 检测购物车状态
            cart_result = self._check_cart_status()

            # 提取价格（带重试机制）
            price = self._extract_price_with_retry()

            # 构建返回结果
            result = {
                "url": url,
                "result": cart_result['result'],
                "status": cart_result['status'],
                "message": cart_result.get('message', ''),
                "price": price
            }

            logger.info(f"Walmart 检测完成: {result}")
            return result

        except Exception as e:
            logger.error(f"检测 Walmart 商品 {url} 时发生错误: {e}")
            return {
                "url": url,
                "result": -1,
                "status": "error",
                "error": str(e)
            }

    def _extract_price_with_retry(self, max_retries: int = 3) -> Optional[float]:
        """带重试机制的价格提取

        Args:
            max_retries: 最大重试次数

        Returns:
            Optional[float]: 提取到的价格或None
        """
        for attempt in range(max_retries):
            logger.debug(f"价格提取尝试 {attempt + 1}/{max_retries}")

            # 每次重试前滚动页面（模拟人类行为，触发懒加载）
            if attempt > 0:
                logger.debug("滚动页面触发懒加载...")
                self.page.scroll.to_half()
                time.sleep(1)
                self.page.scroll.to_top()
                time.sleep(1)

            price = self._extract_price()
            if price is not None:
                return price

            logger.debug(f"第 {attempt + 1} 次尝试未获取到价格")
            time.sleep(1)

        logger.warning(f"经过 {max_retries} 次尝试仍未获取到价格")
        return None

    def _check_cart_status(self) -> Dict[str, Any]:
        """检测 Walmart 购物车状态

        Returns:
            Dict: 检测结果
                - result: 1=正常, 0=异常
                - status: 状态类型
                - message: 状态描述
        """
        try:
            # 首先检查是否有 "Not Available" 状态
            for unavailable_selector in self.selectors.Stock.ALL_UNAVAILABLE:
                if self.page.ele(unavailable_selector, timeout=WalmartTimeouts.SHORT):
                    logger.warning(f"检测到商品不可用: {unavailable_selector}")
                    return {
                        'result': 0,
                        'status': 'not_available',
                        'message': '商品不可用'
                    }

            # 检测 Add to Cart 按钮
            for atc_selector in self.selectors.CartButton.ALL:
                atc_button = self.page.ele(atc_selector, timeout=WalmartTimeouts.SHORT)
                if atc_button:
                    logger.info(f"找到 Add to Cart 按钮: {atc_selector}")
                    return {
                        'result': 1,
                        'status': 'normal',
                        'message': '购物车正常'
                    }

            # 没有找到 ATC 按钮，检查是否有购买区域
            buy_box = self.page.ele(self.selectors.PageStatus.BUY_BOX, timeout=WalmartTimeouts.SHORT)
            if buy_box:
                # 有购买区域但没有 ATC 按钮，可能是购物车丢失
                logger.warning("有购买区域但未找到 Add to Cart 按钮")
                return {
                    'result': 0,
                    'status': 'cart_missing',
                    'message': '购物车按钮丢失'
                }

            # 没有购买区域，可能是页面异常
            logger.warning("未找到购买区域")
            return {
                'result': -1,
                'status': 'page_error',
                'message': '页面结构异常'
            }

        except Exception as e:
            logger.error(f"检测购物车状态时出错: {e}")
            return {
                'result': -1,
                'status': 'error',
                'message': str(e)
            }

    def _extract_price(self) -> Optional[float]:
        """提取 Walmart 商品价格

        Returns:
            Optional[float]: 商品价格，提取失败返回 None
        """
        try:
            # 按优先级尝试不同的价格选择器
            for price_selector in self.selectors.Price.ALL:
                logger.debug(f"尝试价格选择器: {price_selector}")
                # 优化：第一个选择器通常能成功，使用SHORT timeout即可
                price_element = self.page.ele(price_selector, timeout=WalmartTimeouts.SHORT)
                if price_element:
                    price_text = price_element.text
                    logger.debug(f"找到价格元素，文本: '{price_text}'")
                    if price_text:
                        price = self._parse_price(price_text)
                        if price is not None:
                            logger.info(f"提取到价格: ${price:.2f} (选择器: {price_selector})")
                            return price
                        else:
                            logger.debug(f"价格解析失败: {price_text}")
                else:
                    logger.debug(f"选择器未匹配到元素: {price_selector}")

            logger.warning("未能提取到价格")
            return None

        except Exception as e:
            logger.error(f"提取价格失败: {e}", exc_info=True)
            return None

    def _parse_price(self, price_text: str) -> Optional[float]:
        """解析价格文本

        Args:
            price_text: 价格文本，如 "$224.63" 或 "224.63"

        Returns:
            Optional[float]: 解析后的价格
        """
        if not price_text:
            return None

        try:
            # 移除空白字符
            price_text = price_text.strip()

            # 使用正则表达式提取数字
            # 匹配格式: $224.63, 224.63, $1,234.56, 1,234.56
            match = re.search(r'\$?([\d,]+\.?\d*)', price_text)
            if match:
                price_str = match.group(1).replace(',', '')
                return float(price_str)

            return None

        except (ValueError, AttributeError) as e:
            logger.debug(f"价格解析失败: {price_text}, 错误: {e}")
            return None

    def check_cart_and_price(self, url: str) -> Dict[str, Any]:
        """检测购物车状态并提取价格（便捷方法）

        Args:
            url: Walmart 商品 URL

        Returns:
            Dict: 包含购物车状态和价格的结果
        """
        return self.check_product_page(url)

    def run(self, url_list: list, data_source: str = "unknown") -> list:
        """执行批量检测任务

        Args:
            url_list: URL 列表
            data_source: 数据来源标识

        Returns:
            list: 检测结果列表
        """
        if not url_list:
            logger.warning("URL列表为空")
            return []

        results = []
        self.stats['total_pages'] = len(url_list)

        for i, url in enumerate(url_list, 1):
            logger.info(f"检测进度: {i}/{len(url_list)} - {url}")

            result = self.check_product_page(url)
            results.append(result)

            # 更新统计
            if result.get('result') == 1:
                self.stats['successful_detections'] += 1
            elif result.get('result') == 0:
                status = result.get('status', 'unknown')
                if status == 'not_available':
                    self.stats['out_of_stock_count'] += 1
                elif status == 'cart_missing':
                    self.stats['cart_button_missing_count'] += 1
                else:
                    self.stats['failed_detections'] += 1
            else:
                self.stats['failed_detections'] += 1

            # 更新终端UI
            if self.terminal_ui:
                self.terminal_ui.update(url=url, status=result.get('status', 'unknown'))

            # 添加随机延迟
            if i < len(url_list):
                time.sleep(1 + (i % 3) * 0.5)  # 1-2.5秒随机延迟

        return results
