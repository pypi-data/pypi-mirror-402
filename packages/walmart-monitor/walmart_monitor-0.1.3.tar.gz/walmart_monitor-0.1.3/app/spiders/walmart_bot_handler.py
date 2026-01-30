#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Walmart 防爬验证处理器
专门处理 Walmart 网站的各种防爬验证场景
"""

import time
import logging
from typing import Optional, Callable, Any
from enum import Enum

from app.selectors.walmart_selectors import WalmartSelectors, WalmartTimeouts

logger = logging.getLogger(__name__)


class BotDetectionType(Enum):
    """防爬验证类型"""
    NONE = "none"                    # 无验证
    LOGO_CLICK = "logo_click"        # 需要点击 Logo 按钮
    CAPTCHA = "captcha"              # 验证码
    PRESS_HOLD = "press_hold"        # 按住按钮验证
    PUZZLE = "puzzle"                # 拼图验证
    BLOCKED = "blocked"              # 被封禁
    UNKNOWN = "unknown"              # 未知类型


class WalmartBotHandler:
    """Walmart 防爬验证处理器

    处理 Walmart 网站的各种防爬验证场景：
    1. Logo 点击验证 - 页面只显示 Logo，需要点击进入下一步
    2. 验证码 - 需要手动输入验证码
    3. 按住验证 - 需要按住按钮一段时间
    4. 拼图验证 - 需要拖动拼图

    使用方式：
        handler = WalmartBotHandler(page)
        if handler.detect():
            handler.handle()
    """

    # 验证页面特征选择器
    SELECTORS = {
        # Logo 点击验证
        'logo_click': {
            'indicators': [
                'a.header-logo',
                'a[aria-label*="Walmart"][href="/"]',
                'span.elc-icon-spark'
            ],
            'click_targets': [
                'a.header-logo',
                'a[aria-label*="Walmart"][href="/"]',
                'a[aria-label*="Save Money"]'
            ]
        },
        # 验证码
        'captcha': {
            'indicators': [
                '[data-testid="captcha"]',
                '#captcha-container',
                'input#captchacharacters',
                '.captcha-container'
            ]
        },
        # 按住验证
        'press_hold': {
            'indicators': [
                '[data-testid="press-and-hold"]',
                'text=Press and hold',
                'text=press & hold'
            ],
            'hold_targets': [
                '[data-testid="press-and-hold-button"]',
                'button:contains("Press")'
            ]
        },
        # 拼图验证
        'puzzle': {
            'indicators': [
                '[data-testid="puzzle-captcha"]',
                '.puzzle-container',
                'text=Slide to verify'
            ]
        },
        # 被封禁
        'blocked': {
            'indicators': [
                'text=Access Denied',
                'text=blocked',
                'text=unusual activity'
            ]
        }
    }

    def __init__(self, page, terminal_ui=None, on_captcha_callback: Optional[Callable] = None):
        """初始化防爬处理器

        Args:
            page: DrissionPage 页面对象
            terminal_ui: 终端UI实例（用于更新验证码计数）
            on_captcha_callback: 验证码回调函数
        """
        self.page = page
        self.terminal_ui = terminal_ui
        self.on_captcha_callback = on_captcha_callback

        # 统计数据
        self.stats = {
            'logo_click_count': 0,
            'captcha_count': 0,
            'press_hold_count': 0,
            'puzzle_count': 0,
            'blocked_count': 0,
            'success_count': 0,
            'fail_count': 0
        }

    def detect(self) -> BotDetectionType:
        """检测当前页面的防爬验证类型

        Returns:
            BotDetectionType: 验证类型
        """
        try:
            # 首先检查是否有正常的商品内容
            if self._has_product_content():
                return BotDetectionType.NONE

            # 检查各种验证类型
            if self._check_blocked():
                logger.warning("检测到访问被封禁")
                return BotDetectionType.BLOCKED

            if self._check_captcha():
                logger.info("检测到验证码页面")
                return BotDetectionType.CAPTCHA

            if self._check_press_hold():
                logger.info("检测到按住验证页面")
                return BotDetectionType.PRESS_HOLD

            if self._check_puzzle():
                logger.info("检测到拼图验证页面")
                return BotDetectionType.PUZZLE

            if self._check_logo_click():
                logger.info("检测到 Logo 点击验证页面")
                return BotDetectionType.LOGO_CLICK

            return BotDetectionType.NONE

        except Exception as e:
            logger.error(f"检测防爬验证类型时出错: {e}")
            return BotDetectionType.UNKNOWN

    def handle(self, detection_type: BotDetectionType = None) -> bool:
        """处理防爬验证

        Args:
            detection_type: 验证类型，如果为 None 则自动检测

        Returns:
            bool: 是否成功通过验证
        """
        if detection_type is None:
            detection_type = self.detect()

        if detection_type == BotDetectionType.NONE:
            return True

        logger.info(f"开始处理防爬验证: {detection_type.value}")

        handlers = {
            BotDetectionType.LOGO_CLICK: self._handle_logo_click,
            BotDetectionType.CAPTCHA: self._handle_captcha,
            BotDetectionType.PRESS_HOLD: self._handle_press_hold,
            BotDetectionType.PUZZLE: self._handle_puzzle,
            BotDetectionType.BLOCKED: self._handle_blocked,
            BotDetectionType.UNKNOWN: self._handle_unknown
        }

        handler = handlers.get(detection_type)
        if handler:
            success = handler()
            if success:
                self.stats['success_count'] += 1
            else:
                self.stats['fail_count'] += 1
            return success

        return False

    def _has_product_content(self) -> bool:
        """检查页面是否有商品内容"""
        try:
            # 检查商品标题
            if self.page.ele(WalmartSelectors.PageStatus.PRODUCT_TITLE, timeout=WalmartTimeouts.QUICK):
                return True

            # 检查购买区域
            if self.page.ele(WalmartSelectors.PageStatus.BUY_BOX, timeout=WalmartTimeouts.QUICK):
                return True

            # 检查搜索框（正常页面应该有）
            if self.page.ele(WalmartSelectors.PageStatus.SEARCH_BOX, timeout=WalmartTimeouts.QUICK):
                # 有搜索框但没有商品内容，可能是搜索结果页或其他页面
                # 需要进一步判断
                pass

            return False

        except Exception:
            return False

    def _check_logo_click(self) -> bool:
        """检查是否是 Logo 点击验证页面"""
        try:
            for selector in self.SELECTORS['logo_click']['indicators']:
                if self.page.ele(selector, timeout=WalmartTimeouts.QUICK):
                    # 确认没有商品内容
                    if not self._has_product_content():
                        return True
            return False
        except Exception:
            return False

    def _check_captcha(self) -> bool:
        """检查是否是验证码页面"""
        try:
            for selector in self.SELECTORS['captcha']['indicators']:
                if self.page.ele(selector, timeout=WalmartTimeouts.QUICK):
                    return True
            return False
        except Exception:
            return False

    def _check_press_hold(self) -> bool:
        """检查是否是按住验证页面"""
        try:
            for selector in self.SELECTORS['press_hold']['indicators']:
                if self.page.ele(selector, timeout=WalmartTimeouts.QUICK):
                    return True
            return False
        except Exception:
            return False

    def _check_puzzle(self) -> bool:
        """检查是否是拼图验证页面"""
        try:
            for selector in self.SELECTORS['puzzle']['indicators']:
                if self.page.ele(selector, timeout=WalmartTimeouts.QUICK):
                    return True
            return False
        except Exception:
            return False

    def _check_blocked(self) -> bool:
        """检查是否被封禁"""
        try:
            for selector in self.SELECTORS['blocked']['indicators']:
                if self.page.ele(selector, timeout=WalmartTimeouts.QUICK):
                    return True
            return False
        except Exception:
            return False

    def _handle_logo_click(self) -> bool:
        """处理 Logo 点击验证

        点击 Logo 按钮进入下一步验证

        Returns:
            bool: 是否成功
        """
        self.stats['logo_click_count'] += 1
        self._update_terminal_ui()

        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                # 尝试点击各种 Logo 选择器
                for selector in self.SELECTORS['logo_click']['click_targets']:
                    logo_button = self.page.ele(selector, timeout=WalmartTimeouts.SHORT)
                    if logo_button:
                        logger.info(f"点击 Logo 按钮: {selector} (第 {attempt} 次)")
                        logo_button.click()
                        time.sleep(WalmartTimeouts.MEDIUM)

                        # 检查结果
                        new_type = self.detect()
                        if new_type == BotDetectionType.NONE:
                            logger.info("Logo 点击验证通过")
                            return True
                        elif new_type == BotDetectionType.CAPTCHA:
                            logger.info("进入验证码页面")
                            return self._handle_captcha()
                        elif new_type == BotDetectionType.PRESS_HOLD:
                            logger.info("进入按住验证页面")
                            return self._handle_press_hold()

                        break

                time.sleep(WalmartTimeouts.NORMAL)

            except Exception as e:
                logger.warning(f"Logo 点击处理出错 (第 {attempt} 次): {e}")
                time.sleep(1)

        logger.warning("Logo 点击验证失败")
        return False

    def _handle_captcha(self) -> bool:
        """处理验证码

        等待用户手动输入验证码

        Returns:
            bool: 是否成功
        """
        self.stats['captcha_count'] += 1
        self._update_terminal_ui()

        logger.info("检测到验证码，等待手动输入...")

        max_wait_time = 120  # 最长等待2分钟
        start_time = time.time()

        while time.time() - start_time < max_wait_time:
            try:
                # 检查验证码是否还存在
                if not self._check_captcha():
                    # 验证码消失，检查是否通过
                    time.sleep(1)
                    if self._has_product_content() or self.detect() == BotDetectionType.NONE:
                        logger.info("验证码验证通过")
                        return True

                # 检查验证码输入框
                captcha_input = self.page.ele('input#captchacharacters', timeout=WalmartTimeouts.QUICK)
                if captcha_input:
                    input_value = captcha_input.attr('value') or ''
                    if len(input_value) >= 4:
                        # 尝试提交
                        self._try_submit_captcha()
                        time.sleep(1)

                time.sleep(0.5)

            except Exception as e:
                logger.debug(f"验证码处理过程出错: {e}")
                time.sleep(0.5)

        logger.warning("验证码等待超时")
        return False

    def _try_submit_captcha(self):
        """尝试提交验证码"""
        try:
            # 方式1: 点击 submit 按钮
            submit_btn = self.page.ele('tag:button@@type=submit', timeout=WalmartTimeouts.QUICK)
            if submit_btn:
                submit_btn.click()
                return

            # 方式2: 点击 input submit
            submit_input = self.page.ele('tag:input@@type=submit', timeout=WalmartTimeouts.QUICK)
            if submit_input:
                submit_input.click()
                return

            # 方式3: 按文本查找按钮
            for btn_text in ['Continue shopping', 'Submit', 'Continue', 'Verify']:
                btn = self.page.ele(f'text={btn_text}', timeout=WalmartTimeouts.QUICK)
                if btn:
                    btn.click()
                    return

            # 方式4: 按回车
            captcha_input = self.page.ele('input#captchacharacters', timeout=WalmartTimeouts.QUICK)
            if captcha_input:
                captcha_input.input('\n')

        except Exception as e:
            logger.debug(f"提交验证码出错: {e}")

    def _handle_press_hold(self) -> bool:
        """处理按住验证

        模拟按住按钮操作

        Returns:
            bool: 是否成功
        """
        self.stats['press_hold_count'] += 1
        self._update_terminal_ui()

        logger.info("检测到按住验证，尝试处理...")

        try:
            # 查找按住按钮
            for selector in self.SELECTORS['press_hold'].get('hold_targets', []):
                hold_button = self.page.ele(selector, timeout=WalmartTimeouts.SHORT)
                if hold_button:
                    logger.info(f"找到按住按钮: {selector}")

                    # 模拟按住操作
                    # DrissionPage 支持 hold 操作
                    hold_button.click.hold(duration=3)  # 按住3秒
                    time.sleep(WalmartTimeouts.MEDIUM)

                    # 检查结果
                    if self.detect() == BotDetectionType.NONE:
                        logger.info("按住验证通过")
                        return True

            # 如果自动处理失败，等待手动处理
            logger.info("自动按住失败，等待手动处理...")
            return self._wait_for_manual_verification(timeout=60)

        except Exception as e:
            logger.warning(f"按住验证处理出错: {e}")
            return self._wait_for_manual_verification(timeout=60)

    def _handle_puzzle(self) -> bool:
        """处理拼图验证

        拼图验证通常需要手动完成

        Returns:
            bool: 是否成功
        """
        self.stats['puzzle_count'] += 1
        self._update_terminal_ui()

        logger.info("检测到拼图验证，等待手动完成...")
        return self._wait_for_manual_verification(timeout=120)

    def _handle_blocked(self) -> bool:
        """处理被封禁

        Returns:
            bool: 始终返回 False
        """
        self.stats['blocked_count'] += 1
        logger.error("访问被封禁，无法继续")
        return False

    def _handle_unknown(self) -> bool:
        """处理未知验证类型

        Returns:
            bool: 是否成功
        """
        logger.warning("未知的验证类型，等待手动处理...")
        return self._wait_for_manual_verification(timeout=60)

    def _wait_for_manual_verification(self, timeout: int = 60) -> bool:
        """等待手动验证完成

        Args:
            timeout: 超时时间（秒）

        Returns:
            bool: 是否成功
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # 检查是否通过验证
                if self._has_product_content():
                    logger.info("手动验证通过")
                    return True

                if self.detect() == BotDetectionType.NONE:
                    logger.info("验证通过")
                    return True

                time.sleep(1)

            except Exception as e:
                logger.debug(f"等待验证过程出错: {e}")
                time.sleep(1)

        logger.warning("手动验证等待超时")
        return False

    def _update_terminal_ui(self):
        """更新终端UI的验证码计数"""
        if self.terminal_ui:
            try:
                self.terminal_ui.increment_captcha()
            except Exception:
                pass

    def get_stats(self) -> dict:
        """获取统计数据"""
        return self.stats.copy()

    def reset_stats(self):
        """重置统计数据"""
        for key in self.stats:
            self.stats[key] = 0
