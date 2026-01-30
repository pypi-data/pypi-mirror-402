#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爬虫基类
提取 Amazon 和 Walmart 爬虫的公共逻辑
"""

import time
import random
import logging
import threading
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from DrissionPage import Chromium, ChromiumOptions
from DrissionPage.common import Settings
from DrissionPage.errors import PageDisconnectedError

from app.config import get_random_proxy, settings

logger = logging.getLogger(__name__)

# 线程局部变量，用于存储当前线程的 tab 对象
_thread_local = threading.local()

# 禁用标签页单例模式，允许多个对象操作不同标签页
Settings.set_singleton_tab_obj(False)


class TabWorker:
    """单个标签页工作实例，用于并发爬取（同一浏览器内的多标签页）"""

    def __init__(self, worker_id: int, tab):
        self.worker_id = worker_id
        self.tab = tab  # DrissionPage 的标签页对象
        self._zip_code_set = False
        self._current_site = None

    @property
    def page(self):
        """兼容旧代码，返回标签页对象"""
        return self.tab


class BaseSpider(ABC):
    """爬虫基类 - 提供浏览器管理、并发控制、重试机制等公共功能"""

    def __init__(self, user_data_path: str = None, terminal_ui=None, concurrency: int = 1):
        self.user_data_path = user_data_path
        self.proxy = get_random_proxy()
        self.terminal_ui = terminal_ui
        self.concurrency = max(1, concurrency)

        # 并发模式：使用单浏览器多标签页
        self.workers: List[TabWorker] = []
        self._stats_lock = threading.Lock()
        self._results_lock = threading.Lock()
        self._exceptions_buffer = []
        self._exceptions_lock = threading.Lock()

        # 浏览器实例（所有模式共用）
        self.browser = None
        self._page = None  # 主标签页

        # 初始化浏览器（统一初始化）
        self.browser, self._page = self._init_browser(user_data_path)

        # 性能统计
        self.stats = {
            'total_pages': 0,
            'successful_detections': 0,
            'failed_detections': 0,
            'out_of_stock_count': 0,
            'cart_button_missing_count': 0,
            'captcha_encounters': 0,
            'start_time': time.time()
        }

    @property
    def page(self):
        """获取当前线程的 page 对象（线程安全）"""
        # 优先使用线程局部变量中的 page（并发模式）
        thread_page = getattr(_thread_local, 'page', None)
        if thread_page is not None:
            return thread_page
        # 回退到实例变量（单实例模式）
        return self._page

    @page.setter
    def page(self, value):
        """设置 page（兼容旧代码）"""
        self._page = value

    def _init_browser(self, user_data_path: str) -> Tuple[Chromium, Any]:
        """初始化并返回一个配置好的浏览器和页面对象"""
        co = ChromiumOptions()
        if self.proxy:
            logger.info(f"Using proxy: {self.proxy}")
            co.set_proxy(self.proxy)

        if user_data_path:
            logger.info(f"使用本地用户数据: {user_data_path}")
            co.set_user_data_path(user_data_path)
        else:
            logger.warning("未提供user_data_path，将使用临时用户数据。")

        # 增强反检测配置
        co.set_argument('--disable-dev-shm-usage')
        co.set_argument('--disable-blink-features=AutomationControlled')  # 反检测
        co.set_argument('--disable-extensions')  # 禁用扩展
        co.set_argument('--disable-infobars')  # 禁用信息栏
        co.set_argument('--disable-notifications')  # 禁用通知
        co.set_argument('--disable-popup-blocking')  # 禁用弹窗拦截
        co.set_argument('--no-sandbox')  # 禁用沙箱（某些环境需要）
        co.set_argument('--disable-gpu')  # 禁用GPU加速

        # 关键：设置真实的User-Agent（模拟真实浏览器）
        co.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')

        # 关键：不禁用图片，Walmart可能检测这个
        co.no_imgs(False)  # 启用图片加载（防止被检测）
        co.no_js(False)   # 确保JS启用

        browser = Chromium(co)
        page = browser.get_tab()

        # 注入JavaScript隐藏自动化特征（关键反检测）
        page.run_js('''
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            window.chrome = {runtime: {}};
        ''')

        # 关键改变：使用normal模式而非eager，等待页面完全加载
        page.set.load_mode.normal()  # 等待页面完全加载（包括JS执行）
        page.set.window.max()
        # 增加超时时间，给JS更多执行时间
        page.set.timeouts(base=5, page_load=30)

        # 设置找不到元素时的默认行为，避免抛出异常
        page.set.NoneElement_value(None, on_off=True)

        return browser, page

    def _init_worker_pool(self) -> int:
        """初始化多标签页工作池（单浏览器多标签页模式）"""
        logger.info(f"初始化 {self.concurrency} 个标签页...")

        # 第一个 worker 使用主标签页
        main_worker = TabWorker(worker_id=0, tab=self._page)
        self.workers.append(main_worker)
        logger.info(f"Worker-0: 使用主标签页")

        # 创建额外的标签页
        for i in range(1, self.concurrency):
            try:
                new_tab = self.browser.new_tab()
                # 设置标签页的加载策略和超时
                new_tab.set.load_mode.eager()
                new_tab.set.timeouts(base=5, page_load=30)
                new_tab.set.NoneElement_value(None, on_off=True)

                worker = TabWorker(worker_id=i, tab=new_tab)
                self.workers.append(worker)
                logger.info(f"Worker-{i}: 新标签页创建成功")
            except Exception as e:
                logger.warning(f"Worker-{i}: 创建标签页失败: {e}")

        success_count = len(self.workers)
        logger.info(f"成功初始化 {success_count}/{self.concurrency} 个标签页")
        return success_count

    def _close_worker_pool(self):
        """关闭所有工作标签页（保留主标签页）"""
        for worker in self.workers:
            if worker.worker_id > 0:  # 不关闭主标签页
                try:
                    worker.tab.close()
                    logger.debug(f"Worker-{worker.worker_id}: 标签页已关闭")
                except Exception as e:
                    logger.warning(f"Worker-{worker.worker_id}: 关闭标签页失败: {e}")
        self.workers.clear()
        logger.info("所有工作标签页已关闭")

    def _get_current_time(self) -> str:
        """获取当前格式化时间"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _handle_captcha(self, captcha_selector: str = '#captchacharacters'):
        """循环处理验证码，直到页面正常

        Args:
            captcha_selector: 验证码输入框选择器
        """
        max_wait_time = 120  # 最长等待2分钟
        start_time = time.time()

        while self.page.ele(captcha_selector, timeout=0.5):
            self.stats['captcha_encounters'] += 1
            logger.info("检测到验证码页面，等待手动输入...")

            # 更新终端UI验证码计数
            if self.terminal_ui:
                self.terminal_ui.increment_captcha()

            # 快速轮询检测验证码输入框
            captcha_solved = False
            while time.time() - start_time < max_wait_time:
                try:
                    # 检查验证码输入框
                    captcha_input = self.page.ele(captcha_selector, timeout=0.3)
                    if not captcha_input:
                        # 验证码页面已消失，可能已经通过
                        captcha_solved = True
                        break

                    # 获取输入框的值
                    input_value = captcha_input.attr('value') or ''

                    # 验证码通常是4-6个字符
                    if len(input_value) >= 4:
                        logger.info(f"检测到验证码已输入: {len(input_value)} 个字符，尝试点击确认按钮")

                        # 尝试多种方式点击确认按钮
                        submit_clicked = False

                        # 方式1: 通过 button type=submit
                        submit_btn = self.page.ele('tag:button@@type=submit', timeout=0.3)
                        if submit_btn:
                            submit_btn.click()
                            submit_clicked = True
                            logger.info("已点击 submit 按钮")

                        # 方式2: 通过 input type=submit
                        if not submit_clicked:
                            submit_input = self.page.ele('tag:input@@type=submit', timeout=0.3)
                            if submit_input:
                                submit_input.click()
                                submit_clicked = True
                                logger.info("已点击 input submit")

                        # 方式3: 通过文本匹配
                        if not submit_clicked:
                            for btn_text in ['Continue shopping', 'Submit', 'Continue', 'Try different image']:
                                btn = self.page.ele(f'text:{btn_text}', timeout=0.2)
                                if btn:
                                    btn.click()
                                    submit_clicked = True
                                    logger.info(f"已点击 '{btn_text}' 按钮")
                                    break

                        if submit_clicked:
                            # 等待页面响应
                            time.sleep(1)
                            # 检查是否还在验证码页面
                            if not self.page.ele(captcha_selector, timeout=0.5):
                                captcha_solved = True
                                break
                        else:
                            # 没找到按钮，可能需要按回车
                            captcha_input.input('\n')
                            time.sleep(1)

                    # 短暂等待后继续检测（快速轮询）
                    time.sleep(0.3)

                except Exception as e:
                    logger.debug(f"验证码检测过程出错: {e}")
                    time.sleep(0.5)

            if captcha_solved:
                logger.info("验证码已通过")
                time.sleep(0.5)
                break
            else:
                # 超时，刷新页面重试
                logger.warning("验证码等待超时，刷新页面重试")
                self.page.refresh()
                time.sleep(2)
                start_time = time.time()  # 重置计时

    def _update_stats_thread_safe(self, status: str, increment: bool = True):
        """线程安全地更新统计数据"""
        with self._stats_lock:
            delta = 1 if increment else -1
            if status == "success":
                self.stats['successful_detections'] += delta
            elif status == "out_of_stock":
                self.stats['out_of_stock_count'] += delta
            elif status == "cart_button_missing":
                self.stats['cart_button_missing_count'] += delta
            else:
                self.stats['failed_detections'] += delta

    def _add_to_exceptions_buffer(self, result: Dict[str, Any]):
        """添加异常到缓冲区（线程安全）"""
        if result.get('status') != 'success' and result.get('result') != 1:
            with self._exceptions_lock:
                self._exceptions_buffer.append(result)

    @abstractmethod
    def check_product_page(self, url: str) -> Dict[str, Any]:
        """检查单个商品页面并返回结果 - 子类必须实现"""
        pass

    @abstractmethod
    def _get_site_config(self, url: str) -> Dict[str, str]:
        """根据URL获取站点配置信息 - 子类必须实现"""
        pass

    def close(self):
        """关闭浏览器并输出统计信息"""
        # 输出性能统计
        elapsed_time = time.time() - self.stats['start_time']
        success_rate = (
            self.stats['successful_detections'] / max(self.stats['total_pages'], 1)) * 100

        logger.info("=== 检测任务完成 ===")
        logger.info(f"总页面数: {self.stats['total_pages']}")
        logger.info(f"成功检测: {self.stats['successful_detections']}")
        logger.info(f"失败检测: {self.stats['failed_detections']}")
        logger.info(f"商品无库存: {self.stats['out_of_stock_count']}")
        logger.info(f"购物车按钮丢失: {self.stats['cart_button_missing_count']}")
        logger.info(f"验证码次数: {self.stats['captcha_encounters']}")
        logger.info(f"正常率: {success_rate:.1f}%")
        logger.info(f"总耗时: {elapsed_time:.1f}秒")
        logger.info(f"平均每页: {elapsed_time/max(self.stats['total_pages'], 1):.1f}秒")

        logger.info("3秒后自动关闭浏览器")
        time.sleep(3)

        # 关闭浏览器实例
        if self.workers:
            self._close_worker_pool()

        if self.browser:
            try:
                self.browser.quit()
                logger.info("主浏览器已关闭")
            except Exception as e:
                logger.warning(f"关闭主浏览器失败: {e}")
            finally:
                self.browser = None
                self._page = None

    def get_stats(self) -> Dict[str, Any]:
        """获取当前统计数据"""
        with self._stats_lock:
            return self.stats.copy()


def set_thread_page(page):
    """设置当前线程的 page 对象"""
    _thread_local.page = page


def clear_thread_page():
    """清除当前线程的 page 对象"""
    _thread_local.page = None
