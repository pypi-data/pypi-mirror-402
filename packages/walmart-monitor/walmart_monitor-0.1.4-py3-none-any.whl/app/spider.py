import time
import json
import random
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from fake_useragent import UserAgent
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from DrissionPage import Chromium, ChromiumOptions
from DrissionPage.common import Settings
from DrissionPage.errors import PageDisconnectedError, ElementNotFoundError

# 尝试导入 pyautogui（用于真实鼠标操作，绕过 Shadow DOM）
try:
    import pyautogui
    pyautogui.FAILSAFE = False  # 禁用安全模式，避免移动到角落时中断
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False

from app.config import get_random_proxy, settings
from app.site_configs import AmazonSiteConfigs
from app.selectors import AmazonSelectors, WalmartSelectors
from .notifier import ding_talk_notifier

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


class AmazonSpider:
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

    def _init_browser(self, user_data_path: str):
        """初始化并返回一个配置好的浏览器和页面对象（单实例模式）"""
        co = ChromiumOptions()
        if self.proxy:
            logger.info(f"Using proxy: {self.proxy}")
            co.set_proxy(self.proxy)

        if user_data_path:
            logger.info(f"使用本地用户数据: {user_data_path}")
            co.set_user_data_path(user_data_path)
        else:
            logger.warning("未提供user_data_path，将使用临时用户数据。")

        # 反检测浏览器启动参数
        co.set_argument('--disable-dev-shm-usage')
        co.set_argument('--disable-blink-features=AutomationControlled')  # 隐藏自动化特征
        co.set_argument('--disable-extensions')  # 禁用扩展
        co.set_argument('--disable-infobars')  # 禁用信息栏
        co.set_argument('--disable-popup-blocking')  # 禁用弹窗拦截
        co.set_argument('--no-first-run')  # 跳过首次运行
        co.set_argument('--no-default-browser-check')  # 跳过默认浏览器检查

        # 重要：启用图片加载，禁用图片会被反爬系统检测
        co.no_imgs(False)
        co.no_js(False)   # 确保JS启用

        browser = Chromium(co)
        # 禁用单例模式后，latest_tab 返回的是 tab_id（字符串），需要用 get_tab() 获取对象
        page = browser.get_tab()

        # 使用 normal 加载模式，加载完整资源（反检测需要）
        page.set.load_mode.normal()
        page.set.window.max()
        # 设置较短的基础超时时间，针对性等待关键元素
        page.set.timeouts(base=3, page_load=30)

        # 设置找不到元素时的默认行为，避免抛出异常
        page.set.NoneElement_value(None, on_off=True)

        # 注入反检测 JavaScript
        self._inject_stealth_js(page)

        return browser, page

    def _inject_stealth_js(self, page):
        """注入反检测 JavaScript，隐藏自动化特征"""
        try:
            stealth_js = '''
            // 隐藏 webdriver 属性
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            // 模拟真实的 plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });

            // 模拟真实的 languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });

            // 添加 chrome 对象
            window.chrome = {
                runtime: {}
            };

            // 修改 permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            '''
            page.run_js(stealth_js)
            logger.debug("反检测 JavaScript 注入成功")
        except Exception as e:
            logger.warning(f"反检测 JavaScript 注入失败: {e}")

    def _init_worker_pool(self) -> int:
        """初始化多标签页工作池（单浏览器多标签页模式）

        在同一个浏览器中创建多个标签页，每个标签页作为一个独立的 worker。
        这种方式可以复用同一个用户数据目录，避免 Amazon 反爬检测。
        """
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

    def _get_site_config(self, url: str) -> Dict[str, str]:
        """根据URL获取站点配置信息"""
        return AmazonSiteConfigs.get_site_config(url)

    def _update_zip_code(self, url: str = None) -> bool:
        """根据不同站点修改送货地址邮编

        Returns:
            bool: 邮编设置是否成功
        """
        try:
            # 如果没有提供URL，尝试从当前页面获取
            if not url:
                url = self.page.url

            site_config = self._get_site_config(url)
            zip_code = site_config['zip_code']
            country = site_config['country']
            zip_input_type = site_config['zip_input_type']

            logger.info(f"为{country}站点设置邮编: {zip_code}")

            # 多种方式尝试打开邮编设置弹窗
            success = self._open_zip_code_modal()
            if not success:
                logger.warning("无法打开邮编设置弹窗，跳过邮编更新")
                return False

            # 根据不同站点类型处理邮编输入
            if zip_input_type == 'split' and country == 'CA':
                # 加拿大站点：分两个输入框
                self._handle_canada_zip_input(zip_code)
            else:
                # 其他站点：单个输入框
                self._handle_single_zip_input(
                    zip_code, site_config['zip_input_selector'])

            # 点击更新按钮
            update_btn = self.page.ele('#GLUXZipUpdate-announce', timeout=2)
            if update_btn:
                update_btn.click()
                # 短暂等待更新完成
                time.sleep(0.5)
                logger.info(f"邮编已更新为 {zip_code}")

                # 根据站点配置决定是否需要点击Done按钮
                has_done_button = site_config.get('has_done_button', True)  # 默认假设有Done按钮

                if has_done_button:
                    done_clicked = self._click_done_button()
                    if not done_clicked:
                        logger.debug("预期有Done按钮但未找到，可能页面结构有变化")
                else:
                    logger.debug(f"{country}站点无需Done按钮确认")

                # 进行最终验证
                verify_success = self._verify_zip_code_update(zip_code)
                if not verify_success:
                    logger.warning(f"邮编验证失败: {zip_code}")
                    return False
            else:
                logger.warning("未找到更新按钮")
                return False

            # 等待弹窗关闭或手动关闭弹窗
            self._close_zip_code_modal()

            # 刷新页面并短暂等待
            self.page.refresh()
            time.sleep(1)

            return True

        except Exception as e:
            logger.warning(f"修改地址失败: {e}")
            return False

    def _open_zip_code_modal(self) -> bool:
        """尝试多种方式打开邮编设置弹窗"""
        max_attempts = 3

        for attempt in range(1, max_attempts + 1):
            logger.debug(f"尝试打开邮编弹窗 - 第 {attempt} 次")

            try:
                # 方法1: 点击标准的位置链接
                location_link = self.page.ele(
                    '#nav-global-location-popover-link', timeout=3)
                if location_link and location_link.states.is_displayed:
                    logger.debug("尝试点击位置链接...")

                    # 滚动到元素可见区域
                    location_link.scroll.to_see()
                    time.sleep(0.5)

                    # 点击元素
                    location_link.click()

                    # 等待弹窗出现，使用更长的等待时间
                    if self._wait_for_modal_open():
                        return True

                # 方法2: 尝试点击整个位置区域
                logger.debug("尝试点击整个位置区域...")
                location_slot = self.page.ele(
                    '#nav-global-location-slot', timeout=2)
                if location_slot and location_slot.states.is_displayed:
                    location_slot.scroll.to_see()
                    time.sleep(0.5)
                    location_slot.click()

                    if self._wait_for_modal_open():
                        return True

                # 方法3: 使用JavaScript强制触发点击
                logger.debug("尝试使用JavaScript触发点击...")
                js_success = self._trigger_modal_with_js()
                if js_success and self._wait_for_modal_open():
                    return True

                # 方法4: 尝试模拟鼠标悬停然后点击
                logger.debug("尝试模拟鼠标悬停...")
                if location_link:
                    location_link.hover()
                    time.sleep(1)
                    location_link.click()

                    if self._wait_for_modal_open():
                        return True

                # 如果这次尝试失败，等待后重试
                if attempt < max_attempts:
                    logger.debug(f"第 {attempt} 次尝试失败，等待 2 秒后重试...")
                    time.sleep(2)

                    # 刷新页面重试（最后一次尝试前）
                    if attempt == max_attempts - 1:
                        logger.debug("刷新页面后重试...")
                        self.page.refresh()
                        self.page.wait.ele_displayed(
                            '#twotabsearchtextbox', timeout=5)
                        time.sleep(2)

            except Exception as e:
                logger.error(f"第 {attempt} 次尝试打开弹窗时出错: {e}")
                if attempt < max_attempts:
                    time.sleep(2)
                continue

        logger.warning("所有尝试都失败了，无法打开邮编设置弹窗")
        return False

    def _wait_for_modal_open(self, timeout: int = 8) -> bool:
        """等待模态弹窗打开"""
        try:
            # 检查多个可能的弹窗标识
            modal_indicators = [
                '#GLUXZipInputSection',           # 邮编输入区域（主要目标）
                '.a-popover-wrapper',             # 弹窗容器
                '[data-a-modal][style*="display"]',  # 显示的模态弹窗
                '#glow-modal',                    # Glow模态弹窗
                '.glow-modal-content',            # Glow模态内容
                '.a-popover-content'              # 弹窗内容
            ]

            start_time = time.time()
            while time.time() - start_time < timeout:
                for indicator in modal_indicators:
                    element = self.page.ele(indicator, timeout=0.5)
                    if element and element.states.is_displayed:
                        logger.debug(f"检测到弹窗元素: {indicator}")

                        # 如果检测到弹窗，再确认邮编输入区域
                        zip_section = self.page.ele(
                            '#GLUXZipInputSection', timeout=2)
                        if zip_section and zip_section.states.is_displayed:
                            logger.debug("邮编输入区域已显示")
                            return True

                        # 如果邮编区域还没显示，等待一下
                        time.sleep(1)
                        zip_section = self.page.ele(
                            '#GLUXZipInputSection', timeout=1)
                        if zip_section and zip_section.states.is_displayed:
                            return True

                time.sleep(0.5)

            return False

        except Exception as e:
            logger.error(f"等待弹窗打开时出错: {e}")
            return False

    def _trigger_modal_with_js(self) -> bool:
        """使用JavaScript触发模态弹窗"""
        try:
            js_code = """
            // 尝试多种JavaScript方法触发弹窗
            var success = false;
            
            // 方法1: 直接点击位置链接
            var link = document.getElementById('nav-global-location-popover-link');
            if (link) {
                link.click();
                success = true;
            }
            
            // 方法2: 触发模态弹窗的data-action
            var modalTrigger = document.querySelector('[data-a-modal]');
            if (modalTrigger && !success) {
                modalTrigger.click();
                success = true;
            }
            
            // 方法3: 尝试触发鼠标事件
            if (link && !success) {
                var event = new MouseEvent('click', {
                    view: window,
                    bubbles: true,
                    cancelable: true
                });
                link.dispatchEvent(event);
                success = true;
            }
            
            return success;
            """

            result = self.page.run_js(js_code)
            logger.debug(f"JavaScript触发结果: {result}")
            return bool(result)

        except Exception as e:
            logger.error(f"JavaScript触发失败: {e}")
            return False

    def _click_done_button(self):
        """专门点击Done按钮确认邮编更新（如果存在）"""
        try:
            # 尝试多种Done按钮选择器
            done_selectors = [
                'button[name="glowDoneButton"]',
                '.a-button-text:contains("Done")',
                '.a-button-primary .a-button-text:contains("Done")',
                '[data-action="a-popover-close"] .a-button-text:contains("Done")',
                '.a-popover-footer button:contains("Done")'
            ]

            for selector in done_selectors:
                done_btn = self.page.ele(selector, timeout=1)
                if done_btn and done_btn.states.is_displayed:
                    logger.debug(f"找到Done按钮: {selector}")
                    done_btn.click()
                    time.sleep(1)
                    logger.info("已点击Done按钮确认邮编更新")
                    return True

            # 不报告警告，因为某些站点（如加拿大）没有Done按钮是正常的
            logger.debug("当前站点没有Done按钮")
            return False

        except Exception as e:
            logger.debug(f"检查Done按钮时出错: {e}")
            return False

    def _verify_zip_code_update(self, expected_zip: str) -> bool:
        """严格验证邮编是否更新成功

        Args:
            expected_zip: 期望的邮编

        Returns:
            bool: 验证是否成功
        """
        max_retries = 2  # 减少重试次数

        for attempt in range(1, max_retries + 1):
            try:
                # 短暂等待页面更新
                time.sleep(0.5)

                # 方法1: 检查导航栏的位置显示（最可靠）
                location_selectors = [
                    '#glow-ingress-line2',  # 主要位置显示
                    '#nav-global-location-data-modal-action',
                    '#nav-global-location-slot .nav-line-2',
                ]

                for selector in location_selectors:
                    location_element = self.page.ele(selector, timeout=0.5)
                    if location_element:
                        location_text = location_element.text.strip()
                        # 提取邮编部分进行比较（处理不同格式）
                        expected_zip_normalized = expected_zip.replace(' ', '').upper()
                        location_text_normalized = location_text.replace(' ', '').upper()

                        if expected_zip_normalized in location_text_normalized:
                            logger.info(f"邮编验证成功 (第{attempt}次): {expected_zip}")
                            return True
                        else:
                            logger.debug(f"位置显示: '{location_text}', 期望: '{expected_zip}'")

                # 方法2: 检查弹窗是否已关闭（间接验证，快速通过）
                zip_modal = self.page.ele('#GLUXZipInputSection', timeout=0.3)
                if not zip_modal:
                    logger.info(f"邮编弹窗已关闭，视为设置成功: {expected_zip}")
                    return True

                if attempt < max_retries:
                    logger.debug(f"邮编验证第{attempt}次未通过，等待重试...")
                    time.sleep(0.5)

            except Exception as e:
                logger.debug(f"邮编验证第{attempt}次出错: {e}")
                if attempt < max_retries:
                    time.sleep(0.5)

        logger.warning(f"邮编验证失败，已尝试{max_retries}次: {expected_zip}")
        return False

    def _close_zip_code_modal(self):
        """关闭邮编设置弹窗"""
        try:
            # 尝试多种方式关闭弹窗
            close_methods = [
                # 点击关闭按钮
                '.a-popover-close',
                '.a-button-close',
                '[data-action="a-popover-close"]',
            ]

            for method in close_methods:
                close_btn = self.page.ele(method, timeout=0.3)
                if close_btn:
                    logger.debug(f"尝试关闭弹窗: {method}")
                    close_btn.click()
                    time.sleep(0.3)
                    # 检查弹窗是否已关闭
                    if not self.page.ele('#GLUXZipInputSection', timeout=0.3):
                        logger.debug("弹窗已关闭")
                        return

            # 如果以上方法都不行，尝试按ESC键
            logger.debug("尝试按ESC键关闭弹窗")
            self.page.key.esc()
            time.sleep(0.3)

        except Exception as e:
            logger.debug(f"关闭弹窗时出错: {e}")
            # 不抛出异常，因为这不是关键操作

    def _handle_canada_zip_input(self, zip_code: str):
        """处理加拿大站点的分割式邮编输入 (如: V5C 6N5)"""
        try:
            # 加拿大邮编格式: "V5C 6N5" -> 分为 "V5C" 和 "6N5"
            zip_parts = zip_code.strip().split()
            if len(zip_parts) != 2:
                logger.warning(f"加拿大邮编格式不正确: {zip_code}")
                return

            first_part, second_part = zip_parts

            # 尝试多种选择器找到第一个输入框
            first_input_selectors = [
                '#GLUXZipUpdateInput_0',
                'input[id*="ZipUpdateInput_0"]',
                'input[maxlength="3"]:first-of-type',
                '#GLUXZipInputSection input:first-of-type'
            ]

            zip_input_0 = None
            for selector in first_input_selectors:
                zip_input_0 = self.page.wait.ele_displayed(selector, timeout=2)
                if zip_input_0:
                    logger.debug(f"找到第一个输入框: {selector}")
                    break

            if zip_input_0:
                # 清空并输入第一部分
                zip_input_0.clear()
                time.sleep(0.5)  # 短暂等待
                zip_input_0.input(first_part)
                logger.debug(f"输入第一部分邮编: {first_part}")
            else:
                logger.warning("未找到第一个邮编输入框")
                return

            # 尝试多种选择器找到第二个输入框
            second_input_selectors = [
                '#GLUXZipUpdateInput_1',
                'input[id*="ZipUpdateInput_1"]',
                'input[maxlength="3"]:last-of-type',
                '#GLUXZipInputSection input:last-of-type'
            ]

            zip_input_1 = None
            for selector in second_input_selectors:
                zip_input_1 = self.page.wait.ele_displayed(selector, timeout=2)
                if zip_input_1:
                    logger.debug(f"找到第二个输入框: {selector}")
                    break

            if zip_input_1:
                # 清空并输入第二部分
                zip_input_1.clear()
                time.sleep(0.5)  # 短暂等待
                zip_input_1.input(second_part)
                logger.debug(f"输入第二部分邮编: {second_part}")
            else:
                logger.warning("未找到第二个邮编输入框")
                return

        except Exception as e:
            logger.error(f"处理加拿大邮编输入失败: {e}")

    def _handle_single_zip_input(self, zip_code: str, selector: str):
        """处理单个邮编输入框"""
        try:
            # 尝试多种选择器找到输入框
            input_selectors = [
                selector,  # 主要选择器
                '#GLUXZipUpdateInput',
                'input[id*="ZipUpdateInput"]',
                '#GLUXZipInputSection input[type="text"]',
                '.a-input-text[maxlength]'
            ]

            zip_input = None
            for sel in input_selectors:
                zip_input = self.page.wait.ele_displayed(sel, timeout=2)
                if zip_input:
                    logger.debug(f"找到邮编输入框: {sel}")
                    break

            if zip_input:
                # 清空并输入邮编
                zip_input.clear()
                time.sleep(0.5)  # 短暂等待确保清空完成
                zip_input.input(zip_code)
                logger.debug(f"输入邮编: {zip_code}")

                # 验证输入是否成功（延迟验证，给页面更新时间）
                time.sleep(1)
                current_value = zip_input.attr('value') or zip_input.text
                if current_value and zip_code in current_value:
                    logger.debug("邮编输入验证成功")
                else:
                    # 不立即报告失败，可能需要等待Done按钮点击后才能正确验证
                    logger.debug(
                        f"邮编输入初步验证，期望: {zip_code}, 当前: {current_value}")
            else:
                logger.warning(f"未找到邮编输入框，尝试的选择器: {input_selectors}")

        except Exception as e:
            logger.error(f"处理单个邮编输入失败: {e}")

    def _quick_page_status_check(self) -> str:
        """快速检查页面状态，返回页面类型

        注意：此方法只做快速预检，不做库存判断。
        库存状态由 _check_stock_status 方法精确判断。
        """
        try:
            # 只检查验证码和购物提示，不在这里判断库存状态
            # 库存状态需要更精确的判断，交给 _check_stock_status 处理

            # 检查沃尔玛反爬验证页面（Robot or human?）
            for selector in WalmartSelectors.RobotCheck.DETECTION_SELECTORS:
                if self.page.ele(selector, timeout=0.5):
                    return 'walmart_robot_check'

            # 检查验证码
            if self.page.ele('#captchacharacters', timeout=0.5):
                return 'captcha'

            # 检查购物提示
            if self.page.ele('text:Click the button below to continue shopping', timeout=0.5):
                return 'shopping_prompt'

            # 检查是否是产品页面
            if self.page.ele('#productTitle', timeout=0.5):
                return 'product_page'

            return 'normal'

        except Exception as e:
            logger.debug(f"页面状态检查出错: {e}")
            return 'unknown'

    def _check_stock_status(self) -> Dict[str, Any]:
        """检查商品库存状态，区分无库存和购物车按钮丢失"""
        try:
            # 检查无库存情况
            stock_indicators = {
                # 无库存的主要标识
                'out_of_stock_box': self.page.ele('#outOfStock', timeout=0.5),
                'currently_unavailable': self.page.ele('text=Currently unavailable.', timeout=0.5),
                'back_in_stock': self.page.ele('text:We don\'t know when or if this item will be back in stock', timeout=0.5),

                # 购物车按钮丢失的标识
                'unqualified_buybox': self.page.ele('#unqualifiedBuyBox', timeout=0.5),
                'see_all_buying_options': self.page.ele('text=See All Buying Options', timeout=0.5),
                'buybox_see_all': self.page.ele('#buybox-see-all-buying-choices', timeout=0.5),
            }

            # 检查无库存情况
            if (stock_indicators['out_of_stock_box'] or
                stock_indicators['currently_unavailable'] or
                    stock_indicators['back_in_stock']):
                return {
                    'status': 'out_of_stock',
                    'message': '商品无库存',
                    'details': 'Currently unavailable - 商品暂时无库存'
                }

            # 检查购物车按钮丢失情况（包括明显的按钮丢失标识）
            if (stock_indicators['unqualified_buybox'] or
                stock_indicators['see_all_buying_options'] or
                    stock_indicators['buybox_see_all']):
                return {
                    'status': 'cart_button_missing',
                    'message': '购物车按钮丢失',
                    'details': 'See All Buying Options - 购物车按钮不可用'
                }

            # 新增：检查购物车按钮存在但卖家非官方的情况
            # 这个检查会在主流程中的_check_add_to_cart_button方法中处理
            # 这里只是预留接口，实际逻辑在_check_add_to_cart_button中

            return {
                'status': 'normal',
                'message': '正常状态',
                'details': '商品页面正常'
            }

        except Exception as e:
            logger.debug(f"库存状态检查出错: {e}")
            return {
                'status': 'unknown',
                'message': '状态未知',
                'details': f'检查出错: {e}'
            }

    def _send_notification(self, result: Dict[str, Any]):
        """根据检测结果发送相应的通知"""
        try:
            url = result.get('url', '未知链接')
            status = result.get('status', 'unknown')
            message = result.get('message', '未知异常')
            details = result.get('details', '无详细信息')

            current_time = self._get_current_time()

            if status == 'out_of_stock':
                # 商品库存异常提醒
                title = "商品库存异常提醒"
                text = f"""### 📦 商品库存异常提醒

**商品链接**: {url}

**商品状态**: 无库存

**检测时间**: {current_time}"""

            elif status == 'cart_button_missing':
                # 购物车异常提醒 - 需要@所有人
                title = "购物车异常提醒"
                
                # 检查详细信息，区分不同的购物车丢失原因
                if '非官方卖家' in details:
                    text = f"""### 🛒 购物车异常提醒

**商品链接**: {url}

**商品状态**: 购物车按钮丢失（非官方卖家）

**检测时间**: {current_time}

⚠️ **紧急提醒**: 检测到非官方卖家，购物车功能异常，请立即处理！"""
                else:
                    text = f"""### 🛒 购物车异常提醒

**商品链接**: {url}

**商品状态**: 购物车按钮丢失

**检测时间**: {current_time}

⚠️ **紧急提醒**: 购物车功能异常，请立即处理！"""

            else:
                # 商品页未知异常提醒
                title = "商品页未知异常提醒"
                text = f"""### ❓ 商品页未知异常提醒

**商品链接**: {url}

**商品状态**: 未知异常

**检测时间**: {current_time}"""

            # 发送钉钉通知，购物车按钮丢失需要@所有人
            is_at_all = (status == 'cart_button_missing')
            ding_talk_notifier.send_markdown(title, text, is_at_all=is_at_all)

            if is_at_all:
                logger.info(f"已发送{status}类型通知(@所有人): {url}")
            else:
                logger.info(f"已发送{status}类型通知: {url}")

        except Exception as e:
            logger.error(f"发送通知失败: {e}")
            # 发送简化通知作为兜底
            try:
                title = "商品页未知异常提醒"
                text = f"""### ❓ 商品页未知异常提醒

**商品链接**: {url}

**商品状态**: 检测异常，请手动核查

**检测时间**: {self._get_current_time()}"""
                ding_talk_notifier.send_markdown(title, text, is_at_all=False)
            except Exception as e:
                logger.error(f"兜底通知也发送失败: {e}")

    def _handle_captcha(self):
        """循环处理验证码，直到页面正常

        优化：快速检测验证码输入框内容，一旦输入完成立即点击确认按钮
        """
        max_wait_time = 120  # 最长等待2分钟
        start_time = time.time()

        while self.page.ele('#captchacharacters', timeout=0.5):
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
                    captcha_input = self.page.ele('#captchacharacters', timeout=0.3)
                    if not captcha_input:
                        # 验证码页面已消失，可能已经通过
                        captcha_solved = True
                        break

                    # 获取输入框的值
                    input_value = captcha_input.attr('value') or ''

                    # Amazon 验证码通常是6个字符
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
                            if not self.page.ele('#captchacharacters', timeout=0.5):
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
                # 短暂等待页面加载，不需要等太久
                time.sleep(0.5)
                break
            else:
                # 超时，刷新页面重试
                logger.warning("验证码等待超时，刷新页面重试")
                self.page.refresh()
                time.sleep(2)
                start_time = time.time()  # 重置计时

    def _handle_shopping_prompt(self):
        """处理"继续购物"的提示"""
        try:
            shopping_prompt = self.page.ele(
                'text:Click the button below to continue shopping', timeout=5)
            if shopping_prompt:
                logger.info("检测到'继续购物'提示，正在点击按钮...")
                continue_button = self.page.ele('text:Continue shopping')
                continue_button.click()
                self.page.wait.load_start()
                logger.info("已点击'继续购物'按钮。")
        except ElementNotFoundError:
            # 没有找到提示，是正常情况
            pass
        except Exception as e:
            logger.error("处理'继续购物'提示时出错。", exc_info=True)

    def _handle_walmart_robot_check(self):
        """处理沃尔玛反爬验证页面（Robot or human?）

        支持两种类型的验证：
        1. 点击 logo 按钮类型
        2. Press and Hold 长按按钮类型
        """
        max_attempts = 3

        for attempt in range(1, max_attempts + 1):
            try:
                # 检查是否还在反爬验证页面
                is_robot_check = False
                for selector in WalmartSelectors.RobotCheck.DETECTION_SELECTORS:
                    if self.page.ele(selector, timeout=0.5):
                        is_robot_check = True
                        break

                if not is_robot_check:
                    logger.info("沃尔玛反爬验证已通过")
                    return True

                logger.info(f"检测到沃尔玛反爬验证页面 (第{attempt}次尝试)")

                # 更新终端UI（如果有）
                if self.terminal_ui:
                    self.terminal_ui.increment_captcha()

                # 检测是否是 Press and Hold 类型的验证
                if self._is_press_hold_captcha():
                    logger.info("检测到 Press and Hold 类型验证")
                    success = self._handle_press_hold_captcha()
                else:
                    logger.info("检测到点击 Logo 类型验证")
                    success = self._handle_click_logo_captcha()

                if success:
                    # 等待页面跳转
                    time.sleep(2)

                    # 检查是否通过验证
                    still_robot_check = False
                    for selector in WalmartSelectors.RobotCheck.DETECTION_SELECTORS:
                        if self.page.ele(selector, timeout=0.5):
                            still_robot_check = True
                            break

                    if not still_robot_check:
                        logger.info("沃尔玛反爬验证已通过")
                        return True
                    else:
                        logger.warning(f"操作后仍在反爬验证页面，重试中...")
                        time.sleep(1)
                else:
                    logger.warning("验证操作失败，尝试刷新页面")
                    self.page.refresh()
                    time.sleep(2)

            except Exception as e:
                logger.error(f"处理沃尔玛反爬验证时出错: {e}")
                time.sleep(1)

        logger.error(f"沃尔玛反爬验证处理失败，已尝试{max_attempts}次")
        return False

    def _is_press_hold_captcha(self) -> bool:
        """检测是否是 Press and Hold 类型的验证"""
        # 检测 "Activate and hold the button" 文本
        if self.page.ele(WalmartSelectors.RobotCheck.PRESS_HOLD_TEXT, timeout=0.5):
            return True
        # 检测长按按钮
        for selector in WalmartSelectors.RobotCheck.HOLD_BUTTON_SELECTORS:
            if self.page.ele(selector, timeout=0.3):
                return True
        return False

    def _handle_press_hold_captcha(self) -> bool:
        """处理 Press and Hold 类型的验证

        使用多种方法尝试绕过 PerimeterX 的 Press and Hold 验证。
        注意：PerimeterX 使用 closed Shadow DOM，需要使用系统级鼠标操作。

        方法优先级：
        1. pyautogui（系统级真实鼠标操作，最可靠）
        2. CDP 鼠标事件
        3. DrissionPage actions
        """
        try:
            # 查找 #px-captcha 容器
            hold_element = None
            for selector in WalmartSelectors.RobotCheck.HOLD_BUTTON_SELECTORS:
                hold_element = self.page.ele(selector, timeout=2)
                if hold_element:
                    logger.info(f"找到验证元素: {selector}")
                    break

            if not hold_element:
                logger.warning("未找到 #px-captcha 验证元素")
                return False

            # 打印元素信息用于调试
            logger.debug(f"元素标签: {hold_element.tag}, 元素ID: {hold_element.attr('id')}")

            # 滚动到元素可见
            hold_element.scroll.to_see()
            time.sleep(random.uniform(0.8, 1.2))

            # 获取元素在屏幕上的绝对坐标
            rect = hold_element.rect
            # 获取浏览器窗口位置
            screen_x = rect.screen_location[0] + rect.size[0] // 2
            screen_y = rect.screen_location[1] + rect.size[1] // 2
            logger.info(f"元素屏幕坐标: ({screen_x}, {screen_y})")

            # 方法1: 使用 pyautogui 进行真实系统级鼠标操作（最可靠）
            if PYAUTOGUI_AVAILABLE:
                logger.info("尝试方法1: pyautogui 系统级鼠标操作...")
                try:
                    # 移动鼠标到元素位置
                    pyautogui.moveTo(screen_x, screen_y, duration=random.uniform(0.3, 0.5))
                    time.sleep(random.uniform(0.2, 0.4))

                    # 按下鼠标左键
                    pyautogui.mouseDown(button='left')
                    logger.info("pyautogui: 鼠标按下")

                    # 长按时间：PerimeterX 通常需要 10-15 秒
                    hold_duration = random.uniform(10, 15)
                    logger.info(f"pyautogui: 长按中，持续 {hold_duration:.1f} 秒...")
                    time.sleep(hold_duration)

                    # 释放鼠标
                    pyautogui.mouseUp(button='left')
                    logger.info("pyautogui: 鼠标释放")

                    time.sleep(2)

                    # 检查是否成功
                    if not self.page.ele('text:Robot or human?', timeout=2):
                        logger.info("方法1成功，验证已通过")
                        return True
                    else:
                        logger.warning("方法1: 长按后验证仍存在")
                except Exception as e:
                    logger.warning(f"方法1失败: {e}")
            else:
                logger.warning("pyautogui 不可用，跳过方法1")

            # 方法2: 使用 CDP 直接发送鼠标事件
            logger.info("尝试方法2: CDP 鼠标事件...")
            # 使用页面内坐标（不是屏幕坐标）
            page_x = rect.midpoint[0]
            page_y = rect.midpoint[1]
            try:
                # 发送 mousePressed 事件
                self.page.run_cdp('Input.dispatchMouseEvent',
                    type='mousePressed',
                    x=page_x,
                    y=page_y,
                    button='left',
                    clickCount=1
                )
                logger.info("CDP: 鼠标按下")

                # 保持按住状态
                hold_duration = random.uniform(10, 13)
                logger.info(f"CDP: 长按中，持续 {hold_duration:.1f} 秒...")
                time.sleep(hold_duration)

                # 发送 mouseReleased 事件
                self.page.run_cdp('Input.dispatchMouseEvent',
                    type='mouseReleased',
                    x=page_x,
                    y=page_y,
                    button='left',
                    clickCount=1
                )
                logger.info("CDP: 鼠标释放")

                time.sleep(2)

                # 检查是否成功
                if not self.page.ele('text:Robot or human?', timeout=2):
                    logger.info("方法2成功，验证已通过")
                    return True
                else:
                    logger.warning("方法2: 长按后验证仍存在")
            except Exception as e:
                logger.warning(f"方法2失败: {e}")

            # 方法3: 使用 DrissionPage actions
            logger.info("尝试方法3: DrissionPage actions 长按...")
            try:
                self.page.actions.move_to(hold_element)
                time.sleep(0.3)
                self.page.actions.hold(hold_element)
                hold_duration = random.uniform(10, 13)
                logger.info(f"actions: 长按中，持续 {hold_duration:.1f} 秒...")
                time.sleep(hold_duration)
                self.page.actions.release()
                logger.info("方法3: 长按操作完成")
                time.sleep(2)

                # 检查是否成功
                if not self.page.ele('text:Robot or human?', timeout=2):
                    logger.info("方法3成功，验证已通过")
                    return True
            except Exception as e:
                logger.warning(f"方法3失败: {e}")

            # 所有方法都尝试过了
            logger.warning("所有长按方法都已尝试，等待验证结果...")
            time.sleep(random.uniform(1, 2))
            return True

        except Exception as e:
            logger.error(f"处理长按验证时出错: {e}", exc_info=True)
            return False

    def _handle_click_logo_captcha(self) -> bool:
        """处理点击 Logo 类型的验证"""
        try:
            # 尝试点击logo按钮
            for selector in WalmartSelectors.RobotCheck.CLICK_SELECTORS:
                btn = self.page.ele(selector, timeout=1)
                if btn:
                    logger.debug(f"找到按钮: {selector}")
                    # 滚动到元素可见
                    btn.scroll.to_see()
                    time.sleep(random.uniform(0.2, 0.4))
                    btn.click()
                    logger.info(f"已点击沃尔玛反爬验证按钮: {selector}")
                    return True

            logger.warning("未找到可点击的 Logo 按钮")
            return False

        except Exception as e:
            logger.error(f"处理点击Logo验证时出错: {e}")
            return False

    def _check_cart_button_exists_physically(self) -> bool:
        """纯粹检查购物车按钮的物理存在性，不考虑卖家因素"""
        try:
            # 复用原有的购物车按钮检测逻辑，但不检查卖家
            
            # 方法1: 直接ID检测
            direct_ids = ['add-to-cart-button', 'add-to-cart-button-ubb']
            for btn_id in direct_ids:
                element = self.page.ele(f'#{btn_id}', timeout=0.5)
                if element:
                    logger.debug(f"物理检测: 找到购物车按钮 #{btn_id}")
                    return True

            # 方法2: name属性检测
            name_attrs = ['submit.add-to-cart', 'submit.add-to-cart-ubb']
            for name_attr in name_attrs:
                element = self.page.ele(f'@name={name_attr}', timeout=0.5)
                if element:
                    logger.debug(f"物理检测: 通过name属性找到 @name={name_attr}")
                    return True

            # 方法3: span容器检测
            span_ids = ['submit.add-to-cart', 'submit.add-to-cart-ubb']
            for span_id in span_ids:
                element = self.page.ele(f'@@tag()=span@@id={span_id}', timeout=0.5)
                if element:
                    logger.debug(f"物理检测: 通过span容器找到 @@tag()=span@@id={span_id}")
                    return True

            # 方法4: 文本内容检测
            text_elements = self.page.eles('text=Add to Cart', timeout=0.5)
            for element in text_elements:
                button_text = element.parent('.a-button-text')
                if button_text and button_text.parent('.a-button-inner'):
                    logger.debug("物理检测: 通过文本内容找到按钮")
                    return True

            return False

        except Exception as e:
            logger.debug(f"物理检测购物车按钮时出错: {e}")
            return False

    def _check_official_seller(self) -> bool:
        """检查卖家是否为官方卖家

        使用 AmazonSelectors.Seller.OFFICIAL_SELLERS 中定义的官方卖家列表
        支持所有亚马逊站点和官方业务线
        """
        try:
            # 使用统一配置的官方卖家列表
            official_sellers = AmazonSelectors.Seller.OFFICIAL_SELLERS

            # 使用统一配置的卖家选择器
            seller_selectors = AmazonSelectors.Seller.ALL

            for selector in seller_selectors:
                seller_element = self.page.ele(selector, timeout=0.5)
                if seller_element:
                    # 获取卖家文本，去除首尾空格并转换为小写
                    seller_text_raw = seller_element.text.strip()
                    seller_text_normalized = seller_text_raw.lower()

                    logger.debug(f"找到卖家信息: '{seller_text_raw}' (标准化后: '{seller_text_normalized}')")

                    # 检查是否为官方卖家（忽略大小写，使用包含匹配）
                    # 注意：使用包含匹配而非精确匹配，因为卖家名称可能带有后缀如 "Store"
                    for official_seller in official_sellers:
                        if official_seller in seller_text_normalized:
                            logger.info(f"验证通过: 官方卖家 - {seller_text_raw} (匹配: {official_seller})")
                            return True

                    logger.warning(f"非官方卖家: {seller_text_raw}")
                    return False

            # 如果没有找到卖家信息，记录警告但不阻断流程
            logger.warning("未找到卖家信息，可能页面结构有变化")
            return False

        except Exception as e:
            logger.error(f"检查官方卖家时出错: {e}")
            return False

    def _extract_price(self) -> Optional[float]:
        """提取商品价格

        使用 AmazonSelectors.Price 中定义的多种选择器按优先级尝试
        返回浮点数价格或None
        """
        try:
            # 方法1: 使用屏幕阅读器版本（最可靠）
            offscreen_price = self.page.ele(AmazonSelectors.Price.OFFSCREEN_PRICE, timeout=0.5)
            if offscreen_price:
                price_text = offscreen_price.text.strip()
                logger.debug(f"找到offscreen价格: {price_text}")
                # 解析价格文本 (如 "$109.05")
                price_value = self._parse_price_text(price_text)
                if price_value:
                    logger.info(f"成功提取价格: ${price_value}")
                    return price_value

            # 方法2: 在价格区域内查找offscreen
            core_price_area = self.page.ele(AmazonSelectors.Price.CORE_PRICE_DIV, timeout=0.5)
            if core_price_area:
                offscreen = core_price_area.ele('.a-offscreen', timeout=0.3)
                if offscreen:
                    price_text = offscreen.text.strip()
                    logger.debug(f"在核心价格区域找到价格: {price_text}")
                    price_value = self._parse_price_text(price_text)
                    if price_value:
                        logger.info(f"成功提取价格: ${price_value}")
                        return price_value

            # 方法3: 拼接整数和小数部分
            price_whole_elem = self.page.ele(AmazonSelectors.Price.PRICE_WHOLE, timeout=0.5)
            if price_whole_elem:
                price_whole = price_whole_elem.text.strip().replace('.', '')  # 移除小数点分隔符
                price_fraction_elem = self.page.ele(AmazonSelectors.Price.PRICE_FRACTION, timeout=0.3)

                if price_fraction_elem:
                    price_fraction = price_fraction_elem.text.strip()
                    price_text = f"{price_whole}.{price_fraction}"
                else:
                    price_text = f"{price_whole}.00"

                logger.debug(f"通过拼接获得价格: {price_text}")
                price_value = self._parse_price_text(price_text)
                if price_value:
                    logger.info(f"成功提取价格: ${price_value}")
                    return price_value

            logger.warning("未能提取到商品价格")
            return None

        except Exception as e:
            logger.error(f"提取价格时出错: {e}")
            return None

    def _parse_price_text(self, price_text: str) -> Optional[float]:
        """解析价格文本为浮点数

        Args:
            price_text: 价格文本，如 "$109.05", "109.05", "$1,234.56"

        Returns:
            浮点数价格或None
        """
        try:
            if not price_text:
                return None

            # 移除货币符号、逗号、空格
            cleaned = price_text.replace('$', '').replace(',', '').replace(' ', '').strip()

            # 转换为浮点数
            price_value = float(cleaned)

            # 验证价格合理性
            if price_value < 0 or price_value > 100000:
                logger.warning(f"价格值异常: {price_value}")
                return None

            return price_value

        except (ValueError, AttributeError) as e:
            logger.debug(f"解析价格文本失败: {price_text}, 错误: {e}")
            return None

    def _check_add_to_cart_button(self) -> bool:
        """专门检测添加购物车按钮的方法，兼容多种HTML结构，使用DrissionPage优化语法"""
        try:
            cart_button_found = False
            
            # 方法1: 使用DrissionPage优化语法 - 直接ID检测（最精确且快速）
            direct_ids = ['add-to-cart-button', 'add-to-cart-button-ubb']
            for btn_id in direct_ids:
                # 使用#语法，更简洁
                element = self.page.ele(f'#{btn_id}', timeout=0.5)
                if element:
                    logger.info(f"方法1成功: 找到添加购物车按钮 #{btn_id}")
                    cart_button_found = True
                    break

            # 方法2: 使用@属性匹配 - name属性检测
            if not cart_button_found:
                name_attrs = ['submit.add-to-cart', 'submit.add-to-cart-ubb']
                for name_attr in name_attrs:
                    # 使用DrissionPage的@语法
                    element = self.page.ele(f'@name={name_attr}', timeout=0.5)
                    if element:
                        logger.info(f"方法2成功: 通过name属性找到 @name={name_attr}")
                        cart_button_found = True
                        break

            # 方法3: 使用@@多属性匹配 - span容器检测
            if not cart_button_found:
                span_ids = ['submit.add-to-cart', 'submit.add-to-cart-ubb']
                for span_id in span_ids:
                    # 使用DrissionPage的多属性语法
                    element = self.page.ele(
                        f'@@tag()=span@@id={span_id}', timeout=0.5)
                    if element:
                        logger.info(
                            f"方法3成功: 通过span容器找到 @@tag()=span@@id={span_id}")
                        cart_button_found = True
                        break

            # 方法4: 使用链式查找 - 通过购物车图标结构检测
            if not cart_button_found:
                cart_icons = self.page.eles('.a-icon-cart', timeout=1)
                for icon in cart_icons:
                    # 使用链式查找，检查父级结构
                    button_span = icon.parent(
                        '.a-button-inner').parent('.a-button')
                    if button_span:
                        btn_id = button_span.attr('id') or ''
                        if 'add-to-cart' in btn_id:
                            logger.info("方法4成功: 通过购物车图标结构找到按钮")
                            cart_button_found = True
                            break

            # 方法5: 使用text语法 - 文本内容检测
            if not cart_button_found:
                # 使用DrissionPage的text语法，更精确
                text_elements = self.page.eles('text=Add to Cart', timeout=0.5)
                for element in text_elements:
                    # 检查是否在正确的按钮结构中
                    button_text = element.parent('.a-button-text')
                    if button_text and button_text.parent('.a-button-inner'):
                        logger.info("方法5成功: 通过文本内容找到按钮")
                        cart_button_found = True
                        break

            # 方法6: 使用属性模糊匹配 - aria-labelledby检测
            if not cart_button_found:
                # 使用:模糊匹配语法
                aria_elements = self.page.eles(
                    '@aria-labelledby:add-to-cart', timeout=0.5)
                for element in aria_elements:
                    if element.tag == 'input':
                        name_attr = element.attr('name') or ''
                        if 'submit' in name_attr:
                            logger.info("方法6成功: 通过aria-labelledby找到按钮")
                            cart_button_found = True
                            break

            # 方法7: 兜底检查 - 在购买区域查找任何相关按钮
            if not cart_button_found:
                # 使用tag语法结合@@多属性匹配
                buybox_areas = ['#desktop_buybox', '#buybox', '.buybox-container']
                for area_selector in buybox_areas:
                    area = self.page.ele(area_selector, timeout=0.5)
                    if area:
                        # 在区域内查找包含"cart"或"Cart"的按钮
                        cart_buttons = area.eles(
                            '@@tag()=input@@value:Cart', timeout=0.5)
                        if cart_buttons:
                            logger.info(f"方法7成功: 在{area_selector}区域找到购物车按钮")
                            cart_button_found = True
                            break

            # 如果找到了购物车按钮，还需要验证卖家
            if cart_button_found:
                is_official_seller = self._check_official_seller()
                if not is_official_seller:
                    logger.warning("购物车按钮存在但卖家非官方，视为购物车按钮丢失")
                    return False
                else:
                    logger.info("购物车按钮存在且卖家为官方卖家")
                    return True
            
            return False

        except Exception as e:
            logger.debug(f"检测添加购物车按钮时出错: {e}")
            return False

    def check_product_page(self, url: str) -> Dict[str, Any]:
        """检查单个商品页面并返回结果"""
        try:
            self.page.get(url)

            # 使用快速状态检查，提前处理特殊情况
            page_status = self._quick_page_status_check()

            if page_status == 'walmart_robot_check':
                self._handle_walmart_robot_check()
            elif page_status == 'captcha':
                self._handle_captcha()
            elif page_status == 'shopping_prompt':
                self._handle_shopping_prompt()

            result = 0
            stock_status = None

            try:
                # 优化等待策略：只等待关键区域加载，不等待整个页面
                key_areas = ['#desktop_buybox', '#buybox', '.buybox-container',
                             '#addToCart_feature_div', '#outOfStock', '#unqualifiedBuyBox']

                # 尝试等待任一关键区域加载完成
                for area_selector in key_areas:
                    if self.page.wait.ele_displayed(area_selector, timeout=2):
                        logger.debug(f"关键区域已加载: {area_selector}")
                        break
                else:
                    # 如果关键区域都没加载，等待产品标题确认是产品页面
                    if not self.page.wait.ele_displayed('#productTitle', timeout=3):
                        logger.warning("页面加载异常，可能不是产品页面")
                        return {"url": url, "result": -1, "status": "page_error"}

                # 检查库存状态（无库存 vs 购物车按钮丢失）
                stock_check = self._check_stock_status()
                stock_status = stock_check['status']

                if stock_status == 'out_of_stock':
                    logger.warning(f"检测到商品无库存: {stock_check['details']}")
                    return {
                        "url": url,
                        "result": 0,
                        "status": "out_of_stock",
                        "message": stock_check['message'],
                        "details": stock_check['details']
                    }
                elif stock_status == 'cart_button_missing':
                    logger.warning(f"检测到购物车按钮丢失: {stock_check['details']}")
                    return {
                        "url": url,
                        "result": 0,
                        "status": "cart_button_missing",
                        "message": stock_check['message'],
                        "details": stock_check['details']
                    }

                # 首先检测添加购物车按钮（优化后的方法）
                # 注意：_check_add_to_cart_button 现在会同时检查按钮存在性和卖家是否为官方
                cart_button_result = self._check_add_to_cart_button()
                if cart_button_result:
                    result = 1
                else:
                    # 如果_check_add_to_cart_button返回False，可能是：
                    # 1. 真的没有购物车按钮
                    # 2. 有购物车按钮但卖家非官方
                    # 我们需要进一步检查是否是卖家问题
                    
                    # 先检查是否真的有购物车按钮（不考虑卖家）
                    has_cart_button_physically = self._check_cart_button_exists_physically()
                    if has_cart_button_physically:
                        # 有按钮但卖家非官方，返回购物车按钮丢失状态
                        logger.warning("检测到购物车按钮存在但卖家非官方")
                        return {
                            "url": url,
                            "result": 0,
                            "status": "cart_button_missing",
                            "message": "购物车按钮丢失（非官方卖家）",
                            "details": "购物车按钮存在但卖家非官方，视为购物车功能异常"
                        }

                # 如果没找到添加购物车按钮，检查Buy Now按钮（使用优化语法）
                if result == 0:
                    # 使用DrissionPage优化语法，并行检测多种Buy Now按钮
                    buy_now_checks = [
                        '#buy-now-button',                    # ID匹配
                        '@name=submit.buy-now',              # name属性匹配
                        'text=Buy Now',                      # 精确文本匹配
                        '@title:Buy Now',                    # title属性模糊匹配
                        '@@tag()=input@@value:Buy Now',      # 多属性匹配
                    ]

                    for selector in buy_now_checks:
                        element = self.page.ele(selector, timeout=0.3)
                        if element:
                            logger.info(f"找到Buy Now按钮: {selector}")
                            result = 1
                            break

                # 最后的兜底检查：在购买区域查找任何购买按钮
                if result == 0:
                    buybox_containers = [
                        '#desktop_buybox', '#buybox', '.buybox-container', '#addToCart_feature_div']
                    for container_selector in buybox_containers:
                        container = self.page.ele(
                            container_selector, timeout=0.3)
                        if container:
                            # 使用DrissionPage语法在容器内查找，更精确的匹配
                            purchase_buttons = [
                                '@@tag()=input@@type=submit',    # 提交按钮
                                'tag:button',                    # 普通按钮
                                '.a-button',                     # Amazon按钮样式
                                '@value:Cart',                   # 包含Cart的按钮
                                '@value:Buy',                    # 包含Buy的按钮
                                'text:Add to Cart',              # 文本匹配
                            ]

                            for btn_selector in purchase_buttons:
                                if container.ele(btn_selector, timeout=0.2):
                                    logger.info(
                                        f"在容器 {container_selector} 中找到购买按钮: {btn_selector}")
                                    result = 1
                                    break

                            if result == 1:
                                break

            except Exception as e:
                logger.error(f"检测购买按钮时出错: {e}")
                return {"url": url, "result": -1, "error": str(e)}

            # 提取价格（无论购物车状态如何都尝试提取）
            price = self._extract_price()

            # 构建返回结果
            # result=1: 成功找到购物车按钮
            # result=0: 无库存或购物车丢失（确认的异常状态）
            # result=-1: 其他异常（页面加载问题等）
            if result == 1:
                return {"url": url, "result": 1, "price": price}
            elif stock_status == "out_of_stock":
                return {"url": url, "result": 0, "status": "out_of_stock", "price": price}
            elif stock_status == "cart_button_missing":
                return {"url": url, "result": 0, "status": "cart_button_missing", "price": price}
            else:
                # 未知情况，标记为其他异常
                return {"url": url, "result": -1, "status": "unknown", "price": price}

        except PageDisconnectedError as e:
            logger.error(f"浏览器或标签页连接中断: {e}", exc_info=True)
            raise  # 抛出异常，让上层处理
        except Exception as e:
            logger.error(f"处理URL {url} 时发生未知错误: {e}", exc_info=True)
            return {"url": url, "result": -1, "error": str(e)}

    def _detect_and_set_zip_code(self, url: str) -> bool:
        """检测URL对应的站点并设置相应邮编

        Args:
            url: 用于检测站点的URL

        Returns:
            bool: 邮编设置是否成功
        """
        try:
            site_config = self._get_site_config(url)
            country = site_config['country']
            country_name = site_config.get('country_name', country)
            homepage = site_config['homepage']

            logger.info(f"检测到{country_name}({country})站点，访问首页: {homepage}")
            self.page.get(homepage)

            # 快速处理初始页面状态
            initial_status = self._quick_page_status_check()
            if initial_status == 'captcha':
                self._handle_captcha()
            elif initial_status == 'shopping_prompt':
                self._handle_shopping_prompt()

            # 设置对应站点的邮编，并返回结果
            success = self._update_zip_code(homepage)
            if success:
                logger.info(f"{country_name}站点邮编设置成功")
            else:
                logger.error(f"{country_name}站点邮编设置失败")
            return success

        except Exception as e:
            logger.error(f"检测并设置邮编失败: {e}")
            return False

    def run(self, url_list: List[str], data_source: str = "unknown") -> List[Dict[str, Any]]:
        """执行整个爬取任务并返回结果列表"""
        if not url_list:
            logger.warning("URL列表为空")
            return []

        # 发送任务开始通知
        self._send_start_notification(len(url_list), data_source)

        # 根据并发数选择执行模式
        if self.concurrency > 1:
            return self._run_concurrent(url_list)
        else:
            return self._run_sequential(url_list)

    def _run_concurrent(self, url_list: List[str]) -> List[Dict[str, Any]]:
        """并发执行模式：使用多浏览器实例"""
        logger.info(f"启动并发模式: {self.concurrency} 个浏览器实例")

        # 初始化浏览器实例池
        worker_count = self._init_worker_pool()
        if worker_count == 0:
            logger.error("没有可用的浏览器实例，回退到单实例模式")
            self.browser, self.page = self._init_browser(self.user_data_path)
            return self._run_sequential(url_list)

        # 为每个 worker 设置邮编（串行初始化，带超时保护）
        first_url = url_list[0]
        site_config = self._get_site_config(first_url)
        logger.info(f"为所有标签页设置邮编: {site_config['country']}")

        # 串行初始化邮编，每个 worker 有独立的超时保护
        zip_results = []
        ZIP_CODE_TIMEOUT = 90  # 单个 worker 邮编设置超时时间（秒），包含可能的验证码处理时间

        for i, worker in enumerate(self.workers):
            logger.info(f"正在为 Worker-{worker.worker_id} 设置邮编 ({i+1}/{len(self.workers)})")

            # 使用线程池实现超时控制
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self._setup_worker_zip_code, worker, first_url)
                try:
                    success = future.result(timeout=ZIP_CODE_TIMEOUT)
                    zip_results.append(success)
                except Exception as e:
                    logger.error(f"Worker-{worker.worker_id}: 邮编设置超时或异常: {e}")
                    worker._zip_code_set = False
                    zip_results.append(False)

            # 每个 worker 初始化后短暂等待，避免触发反爬
            if i < len(self.workers) - 1:
                time.sleep(random.uniform(1, 2))

        # 检查邮编设置成功率
        success_count = sum(1 for r in zip_results if r)
        total_workers = len(self.workers)

        if success_count == 0:
            logger.error("所有浏览器实例邮编设置失败，任务终止")
            self._close_worker_pool()
            # 发送失败通知
            ding_talk_notifier.send_markdown(
                "任务启动失败",
                "### 任务启动失败\n\n**原因**: 所有浏览器实例邮编设置失败\n\n请检查网络连接和Amazon页面状态",
                is_at_all=True
            )
            return []

        if success_count < total_workers:
            logger.warning(f"部分浏览器邮编设置失败: {success_count}/{total_workers}")
            # 移除邮编设置失败的 worker
            failed_worker_ids = [
                w.worker_id for w, success in zip(self.workers, zip_results) if not success
            ]
            self.workers = [w for w in self.workers if w._zip_code_set]
            logger.info(f"已移除失败的Worker: {failed_worker_ids}，剩余 {len(self.workers)} 个可用实例")

        logger.info(f"邮编设置完成: {success_count}/{total_workers} 个实例就绪")

        # 准备结果容器
        results = [None] * len(url_list)
        failed_items = []  # (index, url) 元组列表

        # 统计
        with self._stats_lock:
            self.stats['total_pages'] = len(url_list)

        # 并发执行检测
        logger.info(f"开始并发检测 {len(url_list)} 个URL")

        with ThreadPoolExecutor(max_workers=len(self.workers)) as executor:
            # 提交所有任务
            future_to_item = {}
            for idx, url in enumerate(url_list):
                worker_idx = idx % len(self.workers)
                worker = self.workers[worker_idx]
                future = executor.submit(self._worker_check_url, worker, url, idx)
                future_to_item[future] = (idx, url)

            # 收集结果
            for future in as_completed(future_to_item):
                idx, url = future_to_item[future]
                try:
                    result = future.result()
                    results[idx] = result

                    # 更新统计和处理结果
                    self._process_result(result, failed_items, idx)

                except Exception as e:
                    logger.error(f"处理URL {url} 时发生错误: {e}")
                    error_result = {"url": url, "result": -1, "error": str(e)}
                    results[idx] = error_result
                    with self._stats_lock:
                        self.stats['failed_detections'] += 1
                    if self.terminal_ui:
                        self.terminal_ui.update(url=url, status="failed")

        # 第二轮：重试失败的URL（串行执行，使用第一个 worker）
        # result=0（疑似库存/购物车问题）或 result=-1（页面异常）都需要重试
        third_round_items = []  # 收集需要第三轮重试的URL (result=-1)

        if failed_items and self.workers:
            logger.info(f"=== 第二轮重试开始 ===")
            logger.info(f"待重试URL数量: {len(failed_items)}")
            worker = self.workers[0]

            for retry_idx, (original_idx, url) in enumerate(failed_items, 1):
                logger.info(f"第二轮重试进度: {retry_idx}/{len(failed_items)} - {url}")
                try:
                    retry_res = self._worker_check_url(worker, url, original_idx)
                    original_result = results[original_idx]
                    original_status = original_result.get("status", "unknown") if original_result else "unknown"

                    if retry_res.get("result") == 1:
                        # 重试成功，更新统计
                        with self._stats_lock:
                            if original_status == "cart_button_missing":
                                self.stats['cart_button_missing_count'] -= 1
                            elif original_status == "out_of_stock":
                                self.stats['out_of_stock_count'] -= 1
                            else:
                                self.stats['failed_detections'] -= 1
                            self.stats['successful_detections'] += 1

                        if self.terminal_ui:
                            self.terminal_ui.correct_stats(original_status)

                        results[original_idx] = retry_res
                        logger.info(f"第二轮重试成功: {url}")

                    elif retry_res.get("result") == 0:
                        # 确认异常状态（无库存/购物车丢失），发送通知
                        results[original_idx] = retry_res
                        new_status = retry_res.get("status", "unknown")

                        # 更新统计：从原状态转移到新状态
                        with self._stats_lock:
                            # 减少原状态计数
                            if original_status == "cart_button_missing":
                                self.stats['cart_button_missing_count'] -= 1
                            elif original_status == "out_of_stock":
                                self.stats['out_of_stock_count'] -= 1
                            else:
                                self.stats['failed_detections'] -= 1

                            # 增加新状态计数
                            if new_status == "out_of_stock":
                                self.stats['out_of_stock_count'] += 1
                            elif new_status == "cart_button_missing":
                                self.stats['cart_button_missing_count'] += 1
                            else:
                                self.stats['failed_detections'] += 1

                        logger.warning(f"第二轮确认异常: {url} -> {new_status}")
                        self._send_notification(retry_res)
                        self._add_to_exceptions_buffer(retry_res)

                    else:
                        # result == -1，页面异常，加入第三轮重试队列
                        results[original_idx] = retry_res
                        third_round_items.append((original_idx, url))
                        logger.warning(f"第二轮仍为页面异常(result=-1)，加入第三轮: {url}")

                    time.sleep(random.uniform(1.0, 2.0))

                except Exception as e:
                    logger.error(f"第二轮重试 {url} 时发生错误: {e}")
                    results[original_idx] = {"url": url, "result": -1, "error": str(e)}
                    third_round_items.append((original_idx, url))

            logger.info(f"=== 第二轮重试完成 ===")
            logger.info(f"第三轮待重试URL数量: {len(third_round_items)}")

        # 第三轮：针对 result=-1 的URL，重启浏览器重试
        if third_round_items:
            logger.info(f"=== 第三轮浏览器重启重试开始 ===")
            logger.info(f"待重试URL数量: {len(third_round_items)}")
            results = self._retry_with_browser_restart(
                third_round_items, results, url_list, max_retries=settings.BROWSER_RESTART_MAX_RETRIES
            )
        else:
            logger.info("没有 result=-1 的URL，跳过第三轮重试")

        return [r for r in results if r is not None]

    def _retry_with_browser_restart(
        self,
        error_items: List[Tuple[int, str]],
        results: List[Dict[str, Any]],
        url_list: List[str],
        max_retries: int = 5
    ) -> List[Dict[str, Any]]:
        """针对未知异常的URL，通过重启浏览器进行重试

        Args:
            error_items: (原始索引, url) 元组列表
            results: 结果列表
            url_list: 完整的URL列表（用于获取站点配置）
            max_retries: 最大重试轮数

        Returns:
            更新后的结果列表
        """
        if not error_items:
            return results

        logger.info(f"发现 {len(error_items)} 个未知异常URL，开始浏览器重启重试（最多{max_retries}轮）")

        # 获取第一个URL用于设置邮编
        first_url = url_list[0] if url_list else error_items[0][1]
        remaining_items = error_items.copy()

        for retry_round in range(1, max_retries + 1):
            if not remaining_items:
                logger.info("所有异常URL已处理完成")
                break

            logger.info(f"=== 浏览器重启重试 第{retry_round}/{max_retries}轮 ===")
            logger.info(f"待重试URL数量: {len(remaining_items)}")

            try:
                # 1. 关闭当前浏览器
                logger.info("正在关闭当前浏览器...")
                self._close_worker_pool()
                if self.browser:
                    try:
                        self.browser.quit()
                    except Exception as e:
                        logger.warning(f"关闭浏览器时出错: {e}")
                    self.browser = None
                    self._page = None

                # 等待一段时间，让系统资源释放
                time.sleep(random.uniform(3, 5))

                # 2. 重新初始化浏览器
                logger.info("正在重新初始化浏览器...")
                self.browser, self._page = self._init_browser(self.user_data_path)

                # 3. 设置邮编
                logger.info("正在设置邮编...")
                zip_success = self._detect_and_set_zip_code(first_url)
                if not zip_success:
                    logger.error(f"第{retry_round}轮: 邮编设置失败，跳过本轮重试")
                    continue

                # 4. 重试每个异常URL
                still_failed = []
                for item_idx, (original_idx, url) in enumerate(remaining_items, 1):
                    logger.info(f"第{retry_round}轮重试进度: {item_idx}/{len(remaining_items)} - {url}")

                    try:
                        retry_res = self.check_product_page(url)
                        logger.info(f"重试结果: {retry_res}")

                        if retry_res.get("result") == 1:
                            # 重试成功
                            with self._stats_lock:
                                # 第三轮进入的都是 result=-1，统计在 failed_detections
                                self.stats['failed_detections'] -= 1
                                self.stats['successful_detections'] += 1

                            if self.terminal_ui:
                                self.terminal_ui.correct_stats("failed")

                            results[original_idx] = retry_res
                            logger.info(f"第{retry_round}轮重试成功: {url}")

                        elif retry_res.get("result") == 0:
                            # 检测到异常状态（无库存/购物车丢失等）
                            results[original_idx] = retry_res
                            status = retry_res.get("status", "unknown")

                            with self._stats_lock:
                                # 第三轮进入的都是 result=-1，统计在 failed_detections
                                self.stats['failed_detections'] -= 1
                                if status == "out_of_stock":
                                    self.stats['out_of_stock_count'] += 1
                                elif status == "cart_button_missing":
                                    self.stats['cart_button_missing_count'] += 1
                                else:
                                    # 其他异常状态，保持在 failed_detections
                                    self.stats['failed_detections'] += 1

                            logger.warning(f"第{retry_round}轮确认异常状态: {url} -> {status}")
                            self._send_notification(retry_res)
                            self._add_to_exceptions_buffer(retry_res)

                        else:
                            # 仍然是未知异常，加入下一轮重试
                            still_failed.append((original_idx, url))
                            logger.warning(f"第{retry_round}轮仍然失败: {url}")

                        # 重试间隔
                        time.sleep(random.uniform(2, 4))

                    except Exception as e:
                        logger.error(f"第{retry_round}轮重试 {url} 时发生错误: {e}")
                        still_failed.append((original_idx, url))

                # 更新待重试列表
                remaining_items = still_failed
                logger.info(f"第{retry_round}轮完成，剩余 {len(remaining_items)} 个异常URL")

            except Exception as e:
                logger.error(f"第{retry_round}轮浏览器重启重试过程出错: {e}")
                # 出错后继续下一轮

        # 所有轮次完成后，处理仍然失败的URL
        if remaining_items:
            logger.error(f"经过{max_retries}轮重试，仍有 {len(remaining_items)} 个URL失败")
            for original_idx, url in remaining_items:
                result = results[original_idx]
                if result:
                    self._send_notification(result)
                    self._add_to_exceptions_buffer(result)

        return results

    def _worker_check_url(self, worker: TabWorker, url: str, idx: int) -> Dict[str, Any]:
        """使用指定的 worker 检测单个 URL（线程安全版本）

        Args:
            worker: 浏览器工作实例
            url: 要检测的URL
            idx: URL在列表中的索引

        Returns:
            Dict: 检测结果
        """
        # 检查 worker 邮编状态
        if not worker._zip_code_set:
            logger.warning(f"Worker-{worker.worker_id}: 邮编未设置，尝试重新设置")
            # 尝试重新设置邮编
            if not self._setup_worker_zip_code(worker, url):
                logger.error(f"Worker-{worker.worker_id}: 邮编重新设置失败，跳过此URL")
                return {"url": url, "result": -1, "error": "邮编设置失败，无法检测"}

        # 设置当前线程的 page 对象
        _thread_local.page = worker.page
        try:
            result = self.check_product_page(url)
            logger.debug(f"Worker-{worker.worker_id}: 检测完成 {url}")
            return result
        except Exception as e:
            logger.error(f"Worker-{worker.worker_id}: 检测 {url} 失败: {e}")
            return {"url": url, "result": -1, "error": str(e)}
        finally:
            # 清理线程局部变量
            _thread_local.page = None

    def _setup_worker_zip_code(self, worker: TabWorker, url: str) -> bool:
        """为单个 worker 设置邮编（线程安全版本）

        Args:
            worker: 浏览器工作实例
            url: 用于检测站点的URL

        Returns:
            bool: 邮编设置是否成功
        """
        # 设置当前线程的 page 对象
        _thread_local.page = worker.page
        try:
            success = self._detect_and_set_zip_code(url)
            if success:
                worker._zip_code_set = True
                logger.info(f"Worker-{worker.worker_id}: 邮编设置成功")
                return True
            else:
                worker._zip_code_set = False
                logger.error(f"Worker-{worker.worker_id}: 邮编设置失败")
                return False
        except Exception as e:
            worker._zip_code_set = False
            logger.error(f"Worker-{worker.worker_id}: 邮编设置异常: {e}")
            return False
        finally:
            # 清理线程局部变量
            _thread_local.page = None

    def _process_result(self, result: Dict[str, Any], failed_items: List, idx: int):
        """处理单个检测结果"""
        url = result.get('url', '')
        ui_status = "success"

        with self._stats_lock:
            if result.get("result") == 1:
                self.stats['successful_detections'] += 1
            elif result.get("result") == 0:
                status = result.get("status", "unknown")
                ui_status = status

                if status == "out_of_stock":
                    self.stats['out_of_stock_count'] += 1
                    # 无库存也加入重试列表进行二次验证，避免误判
                    failed_items.append((idx, url))
                    logger.warning(f"检测到商品无库存，加入重试列表验证: {url}")
                elif status == "cart_button_missing":
                    self.stats['cart_button_missing_count'] += 1
                    failed_items.append((idx, url))
                    logger.warning(f"检测到购物车按钮丢失，加入重试列表: {url}")
                else:
                    self.stats['failed_detections'] += 1
                    failed_items.append((idx, url))
                    logger.warning(f"首次检测失败，加入重试列表: {url}")
            else:
                # result == -1 的未知异常，也加入重试列表
                self.stats['failed_detections'] += 1
                failed_items.append((idx, url))
                ui_status = "failed"
                logger.warning(f"检测到未知异常(result=-1)，加入重试列表: {url}")

        # 更新终端UI
        if self.terminal_ui:
            self.terminal_ui.update(url=url, status=ui_status)

    def _run_sequential(self, url_list: List[str]) -> List[Dict[str, Any]]:
        """串行执行模式（原有逻辑）"""
        # 初始化：根据第一个URL检测站点并设置环境
        zip_code_set = False
        try:
            if url_list:
                first_url = url_list[0]
                zip_code_set = self._detect_and_set_zip_code(first_url)
            else:
                self.page.get("https://www.Amazon.com/")
                zip_code_set = self._update_zip_code("https://www.Amazon.com/")

        except Exception as e:
            logger.error(f"初始化设置失败: {e}")

        # 如果邮编设置失败，终止任务
        if not zip_code_set:
            logger.error("邮编设置失败，任务终止")
            ding_talk_notifier.send_markdown(
                "任务启动失败",
                "### 任务启动失败\n\n**原因**: 邮编设置失败\n\n请检查网络连接和Amazon页面状态",
                is_at_all=True
            )
            return []

        results = []
        failed_urls = []  # 记录失败的URL，用于批量重试
        current_site = None  # 跟踪当前站点

        # 第一轮检测：快速遍历所有URL
        for i, url in enumerate(url_list, 1):
            logger.info(f"检测进度：{i}/{len(url_list)} - {url}")
            self.stats['total_pages'] += 1

            try:
                # 检查是否需要切换站点
                url_site_config = self._get_site_config(url)
                url_country = url_site_config['country']

                if current_site != url_country:
                    logger.info(f"检测到站点切换: {current_site} -> {url_country}")
                    site_switch_success = self._detect_and_set_zip_code(url)
                    if site_switch_success:
                        current_site = url_country
                        # 站点切换后稍微等待一下
                        time.sleep(1)
                    else:
                        logger.error(f"站点切换失败: {url_country}，跳过此URL")
                        results.append({"url": url, "result": -1, "error": "站点切换邮编设置失败"})
                        self.stats['failed_detections'] += 1
                        if self.terminal_ui:
                            self.terminal_ui.update(url=url, status="failed")
                        continue

                res = self.check_product_page(url)
                logger.info(f"检测结果: {res}")

                # 确定状态用于终端UI更新
                ui_status = "success"
                if res.get("result") == 1:
                    self.stats['successful_detections'] += 1
                elif res.get("result") == 0:
                    # 根据不同状态更新统计
                    status = res.get("status", "unknown")
                    ui_status = status
                    if status == "out_of_stock":
                        self.stats['out_of_stock_count'] += 1
                        # 无库存也加入重试列表进行二次验证，避免误判
                        failed_urls.append(url)
                        logger.warning(f"检测到商品无库存，加入重试列表验证: {url}")
                    elif status == "cart_button_missing":
                        self.stats['cart_button_missing_count'] += 1
                        failed_urls.append(url)
                        logger.warning(f"检测到购物车按钮丢失，加入重试列表: {url}")
                    else:
                        self.stats['failed_detections'] += 1
                        failed_urls.append(url)
                        logger.warning(f"首次检测失败，加入重试列表: {url}")
                else:
                    # result == -1，页面异常
                    self.stats['failed_detections'] += 1
                    failed_urls.append(url)
                    ui_status = "failed"
                    logger.warning(f"检测到页面异常(result=-1)，加入重试列表: {url}")

                # 更新终端UI
                if self.terminal_ui:
                    self.terminal_ui.update(url=url, status=ui_status)

                results.append(res)

                # 添加随机延迟，避免请求过于频繁
                if i < len(url_list):  # 不是最后一个URL
                    time.sleep(random.uniform(0.5, 1.5))

            except PageDisconnectedError:
                logger.error("检测中断，浏览器已关闭。")
                break
            except Exception as e:
                logger.error(f"处理URL {url} 时发生错误: {e}")
                results.append({"url": url, "result": -1, "error": str(e)})
                self.stats['failed_detections'] += 1
                # 更新终端UI（失败状态）
                if self.terminal_ui:
                    self.terminal_ui.update(url=url, status="failed")

        # 第二轮：对失败的URL进行重试
        # result=0（疑似库存/购物车问题）或 result=-1（页面异常）都需要重试
        third_round_items = []  # 收集需要第三轮重试的URL (result=-1)

        if failed_urls:
            logger.info(f"=== 第二轮重试开始 ===")
            logger.info(f"待重试URL数量: {len(failed_urls)}")

            for retry_count, url in enumerate(failed_urls, 1):
                logger.info(f"第二轮重试进度: {retry_count}/{len(failed_urls)} - {url}")
                try:
                    # 找到原始结果的索引
                    original_index = next(i for i, res in enumerate(
                        results) if res['url'] == url)

                    # 重试检测
                    retry_res = self.check_product_page(url)
                    logger.info(f"第二轮重试结果: {retry_res}")

                    original_result = results[original_index]
                    original_status = original_result.get("status", "unknown") if original_result else "unknown"

                    if retry_res.get("result") == 1:
                        # 重试成功，更新统计
                        if original_status == "cart_button_missing":
                            self.stats['cart_button_missing_count'] -= 1
                        elif original_status == "out_of_stock":
                            self.stats['out_of_stock_count'] -= 1
                        else:
                            self.stats['failed_detections'] -= 1

                        self.stats['successful_detections'] += 1

                        if self.terminal_ui:
                            self.terminal_ui.correct_stats(original_status)

                        results[original_index] = retry_res
                        logger.info(f"第二轮重试成功: {url}")

                    elif retry_res.get("result") == 0:
                        # 确认异常状态（无库存/购物车丢失），发送通知
                        results[original_index] = retry_res
                        new_status = retry_res.get("status", "unknown")

                        # 更新统计：从原状态转移到新状态
                        if original_status == "cart_button_missing":
                            self.stats['cart_button_missing_count'] -= 1
                        elif original_status == "out_of_stock":
                            self.stats['out_of_stock_count'] -= 1
                        else:
                            self.stats['failed_detections'] -= 1

                        if new_status == "out_of_stock":
                            self.stats['out_of_stock_count'] += 1
                        elif new_status == "cart_button_missing":
                            self.stats['cart_button_missing_count'] += 1
                        else:
                            self.stats['failed_detections'] += 1

                        logger.warning(f"第二轮确认异常: {url} -> {new_status}")
                        self._send_notification(retry_res)
                        self._add_to_exceptions_buffer(retry_res)

                    else:
                        # result == -1，页面异常，加入第三轮重试队列
                        results[original_index] = retry_res
                        third_round_items.append((original_index, url))
                        logger.warning(f"第二轮仍为页面异常(result=-1)，加入第三轮: {url}")

                    # 重试间隔稍长一些
                    if retry_count < len(failed_urls):
                        time.sleep(random.uniform(1.0, 2.0))

                except Exception as e:
                    logger.error(f"第二轮重试 {url} 时发生错误: {e}")
                    # 确保结果标记为 -1，以便第三轮重试
                    try:
                        original_index = next(i for i, res in enumerate(results) if res['url'] == url)
                        results[original_index] = {"url": url, "result": -1, "error": str(e)}
                        third_round_items.append((original_index, url))
                    except StopIteration:
                        logger.error(f"无法找到URL {url} 的原始索引")

            logger.info(f"=== 第二轮重试完成 ===")
            logger.info(f"第三轮待重试URL数量: {len(third_round_items)}")

        # 第三轮：针对 result=-1 的URL，重启浏览器重试
        if third_round_items:
            logger.info(f"=== 第三轮浏览器重启重试开始 ===")
            logger.info(f"待重试URL数量: {len(third_round_items)}")
            results = self._retry_with_browser_restart(
                third_round_items, results, url_list, max_retries=settings.BROWSER_RESTART_MAX_RETRIES
            )
        else:
            logger.info("没有 result=-1 的URL，跳过第三轮重试")

        return results

    def _add_to_exceptions_buffer(self, result: Dict[str, Any]):
        """添加异常到缓冲区（线程安全）"""
        if result.get('status') != 'success' and result.get('result') != 1:
            with self._exceptions_lock:
                self._exceptions_buffer.append(result)

    def _flush_exceptions_to_history(self):
        """将异常缓冲区写入历史记录"""
        try:
            if not self._exceptions_buffer:
                return

            # 检查是否启用历史记录
            if not settings.HISTORY_RECORD_ENABLED:
                logger.debug("历史记录功能已禁用")
                return

            from app.history_recorder import history_recorder
            with self._exceptions_lock:
                if self._exceptions_buffer:
                    success = history_recorder.record_batch(self._exceptions_buffer)
                    if success:
                        logger.info(f"已将 {len(self._exceptions_buffer)} 条异常记录到钉钉表格")
                    self._exceptions_buffer.clear()

        except Exception as e:
            logger.warning(f"写入历史记录失败: {e}")

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

    def close(self, send_notification: bool = True):
        """关闭浏览器并输出统计信息

        Args:
            send_notification: 是否发送钉钉完成通知（双平台模式下应设为 False）
        """
        # 写入异常历史记录
        self._flush_exceptions_to_history()

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
        logger.info(
            f"平均每页: {elapsed_time/max(self.stats['total_pages'], 1):.1f}秒")

        # 输出详细分析
        total_issues = self.stats['failed_detections'] + \
            self.stats['out_of_stock_count'] + \
            self.stats['cart_button_missing_count']
        if total_issues > 0:
            logger.info("=== 异常分析 ===")
            logger.info(
                f"库存问题占比: {(self.stats['out_of_stock_count']/total_issues)*100:.1f}%")
            logger.info(
                f"功能问题占比: {(self.stats['cart_button_missing_count']/total_issues)*100:.1f}%")
            logger.info(
                f"其他问题占比: {(self.stats['failed_detections']/total_issues)*100:.1f}%")

        # 发送任务完成通知（可选）
        if send_notification:
            self._send_completion_notification(
                elapsed_time, success_rate, total_issues)

        logger.info("3秒后自动关闭浏览器")
        time.sleep(3)

        # 关闭浏览器实例（统一处理）
        # 先关闭所有工作标签页
        if self.workers:
            self._close_worker_pool()

        # 再关闭主浏览器
        if self.browser:
            try:
                self.browser.quit()
                logger.info("主浏览器已关闭")
            except Exception as e:
                logger.warning(f"关闭主浏览器失败: {e}")
            finally:
                self.browser = None
                self._page = None

    def _send_completion_notification(self, elapsed_time: float, success_rate: float, total_issues: int):
        """发送任务完成通知"""
        try:
            completion_time = self._get_current_time()

            # 构建异常分析部分
            analysis_text = ""
            if total_issues > 0:
                stock_ratio = (
                    self.stats['out_of_stock_count']/total_issues)*100
                cart_ratio = (
                    self.stats['cart_button_missing_count']/total_issues)*100
                other_ratio = (
                    self.stats['failed_detections']/total_issues)*100

                analysis_text = f"""---

### 📊 异常分析

**库存问题占比**: {stock_ratio:.1f}%

**丢失购物车占比**: {cart_ratio:.1f}%

**其他异常占比**: {other_ratio:.1f}%"""

            title = "检测任务完成"
            text = f"""### 🎯 检测任务完成

**总页面数**: {self.stats['total_pages']}

**通过检测**: {self.stats['successful_detections']}

**商品无库存**: {self.stats['out_of_stock_count']}

**购物车按钮丢失**: {self.stats['cart_button_missing_count']}

**页面异常检测**: {self.stats['failed_detections']}

**正常率**: {success_rate:.1f}%

**总耗时**: {elapsed_time:.1f}秒

**平均每页**: {elapsed_time/max(self.stats['total_pages'], 1):.1f}秒

{analysis_text}

**完成时间**: {completion_time}"""

            ding_talk_notifier.send_markdown(title, text, is_at_all=False)
            logger.info("已发送任务完成通知")

        except Exception as e:
            logger.error(f"发送任务完成通知失败: {e}")

    def _send_start_notification(self, url_count: int, data_source: str = "unknown"):
        """发送任务开始通知"""
        try:
            start_time = self._get_current_time()
            # 预计耗时（每个商品约10秒）
            estimated_minutes = round(url_count * 10 / 60)

            # 数据来源显示文本映射
            data_source_text_map = {
                "request_body": "📋 请求参数",
                "dingtalk_doc_api": "📋 钉钉文档API",
                "dingtalk_backup_file": "📋 钉钉文档备份",
                "product_urls_file": "📋 本地文件",
                "unknown": "📋 未知来源"
            }
            data_source_text = data_source_text_map.get(data_source, f"📋 {data_source}")

            title = "监控任务状态"
            text = f"""### 🚀 监控任务状态

**任务执行**: ✅ 已启用

**数据来源**: {data_source_text}

**商品抓取**: ✅ 已获取 {url_count} 个商品页

**预计耗时**: ⏱ {estimated_minutes} 分钟

**启动时间**: {start_time}

---

**正在进行**: ⏳ 正在执行店铺购物车检查，请等待检查结果"""

            ding_talk_notifier.send_markdown(title, text, is_at_all=False)
            logger.info("已发送任务开始通知")

        except Exception as e:
            logger.error(f"发送任务开始通知失败: {e}")


def _is_running_in_web_server() -> bool:
    """检测是否在 Web 服务器环境下运行（uvicorn/gunicorn 等）"""
    import sys
    # 检查命令行参数
    for arg in sys.argv:
        if 'uvicorn' in arg.lower() or 'gunicorn' in arg.lower():
            return True
    # 检查是否有 uvicorn 模块被导入
    if 'uvicorn' in sys.modules:
        return True
    return False


def run_task(url_list: List[str], data_source: str = "unknown") -> List[Dict[str, Any]]:
    """任务执行的入口函数

    Args:
        url_list: 要处理的URL列表
        data_source: 数据来源标识
    """
    # 终端UI功能：
    # - 在 Web 服务模式下自动禁用（与 uvicorn 日志冲突）
    # - 独立脚本模式下可通过 ENABLE_TERMINAL_UI=true 启用
    terminal_ui = None
    ui_handler = None
    original_handlers = []

    enable_terminal_ui = settings.ENABLE_TERMINAL_UI if hasattr(settings, 'ENABLE_TERMINAL_UI') else False

    # 在 Web 服务器环境下自动禁用终端 UI
    if _is_running_in_web_server():
        if enable_terminal_ui:
            logger.info("检测到 Web 服务器环境，自动禁用终端UI（使用 /task/progress API 查询进度）")
        enable_terminal_ui = False

    if enable_terminal_ui:
        try:
            from app.terminal_ui import create_terminal_ui, TerminalLogHandler
            terminal_ui = create_terminal_ui()

            # 保存并移除原有的 StreamHandler，避免日志重复输出
            root_logger = logging.getLogger()
            original_handlers = [h for h in root_logger.handlers if isinstance(h, logging.StreamHandler)]
            for h in original_handlers:
                root_logger.removeHandler(h)

            # 添加终端UI日志处理器
            ui_handler = TerminalLogHandler(terminal_ui)
            ui_handler.setLevel(logging.INFO)
            root_logger.addHandler(ui_handler)

            # 启动终端UI
            terminal_ui.start(len(url_list), data_source)
        except ImportError:
            logger.info("终端UI模块未安装，使用标准日志输出")
        except Exception as e:
            logger.warning(f"终端UI初始化失败: {e}，使用标准日志输出")
            terminal_ui = None

    # 如何找到：在Chrome地址栏输入 chrome://version ，查看"个人资料路径"
    # 从环境变量读取Chrome用户数据路径
    user_data_path = settings.CHROME_USER_DATA_PATH
    if not user_data_path:
        logger.warning("未配置CHROME_USER_DATA_PATH环境变量，将使用临时用户数据")
        user_data_path = None

    # 获取并发配置
    concurrency = settings.SPIDER_CONCURRENCY if hasattr(settings, 'SPIDER_CONCURRENCY') else 1
    if concurrency > 1:
        logger.info(f"启用并发模式: {concurrency} 个标签页")

    spider = None
    try:
        spider = AmazonSpider(
            user_data_path=user_data_path,
            terminal_ui=terminal_ui,
            concurrency=concurrency
        )
        return spider.run(url_list, data_source=data_source)
    finally:
        if spider:
            spider.close()
        if terminal_ui:
            terminal_ui.stop()
        # 恢复原有的日志处理器
        if ui_handler:
            logging.getLogger().removeHandler(ui_handler)
        for h in original_handlers:
            logging.getLogger().addHandler(h)
