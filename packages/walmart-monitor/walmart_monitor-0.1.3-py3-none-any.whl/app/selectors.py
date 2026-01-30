#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
选择器集中管理模块
统一管理所有 CSS/XPath 选择器，便于维护和更新
"""


class AmazonSelectors:
    """Amazon 页面选择器"""

    # === 页面状态检测 ===
    class PageStatus:
        CAPTCHA = '#captchacharacters'
        SHOPPING_PROMPT = 'text:Click the button below to continue shopping'
        CONTINUE_SHOPPING = 'text:Continue shopping'
        PRODUCT_TITLE = '#productTitle'
        SEARCH_BOX = '#twotabsearchtextbox'

    # === 价格选择器 ===
    class Price:
        # 主要价格区域
        CORE_PRICE_DIV = '#corePrice_feature_div'

        # 完整价格（屏幕阅读器版本，最可靠）
        OFFSCREEN_PRICE = '.a-price .a-offscreen'

        # 价格容器
        PRICE_SPAN = 'span.a-price'

        # 价格组件（需要拼接）
        PRICE_SYMBOL = '.a-price-symbol'
        PRICE_WHOLE = '.a-price-whole'
        PRICE_FRACTION = '.a-price-fraction'

        # 备用选择器
        PRICE_TO_PAY = '.a-price.a-text-price'
        PRICE_DATA_PRICE = '[data-a-size="xl"] .a-price'

        # 所有价格选择器（按优先级排序）
        ALL = [
            '.a-price .a-offscreen',           # 最可靠：屏幕阅读器版本
            '#corePrice_feature_div .a-offscreen',  # 指定区域内查找
            'span.a-price .a-offscreen',       # 通用价格容器
            '.a-price-whole',                  # 整数部分（需要拼接小数）
        ]

    # === 库存状态 ===
    class Stock:
        OUT_OF_STOCK_BOX = '#outOfStock'
        CURRENTLY_UNAVAILABLE = 'text=Currently unavailable.'
        BACK_IN_STOCK = "text:We don't know when or if this item will be back in stock"
        UNQUALIFIED_BUYBOX = '#unqualifiedBuyBox'
        SEE_ALL_BUYING_OPTIONS = 'text=See All Buying Options'
        BUYBOX_SEE_ALL = '#buybox-see-all-buying-choices'

    # === 购物车按钮 ===
    class CartButton:
        # 直接ID选择器
        ADD_TO_CART = '#add-to-cart-button'
        ADD_TO_CART_UBB = '#add-to-cart-button-ubb'

        # name属性选择器
        SUBMIT_ADD_TO_CART = '@name=submit.add-to-cart'
        SUBMIT_ADD_TO_CART_UBB = '@name=submit.add-to-cart-ubb'

        # span容器选择器
        SPAN_ADD_TO_CART = '@@tag()=span@@id=submit.add-to-cart'
        SPAN_ADD_TO_CART_UBB = '@@tag()=span@@id=submit.add-to-cart-ubb'

        # 购物车图标
        CART_ICON = '.a-icon-cart'

        # 文本匹配
        TEXT_ADD_TO_CART = 'text=Add to Cart'

        # aria属性
        ARIA_ADD_TO_CART = '@aria-labelledby:add-to-cart'

        # 所有直接ID（用于快速检测）
        DIRECT_IDS = ['add-to-cart-button', 'add-to-cart-button-ubb']

        # 所有name属性
        NAME_ATTRS = ['submit.add-to-cart', 'submit.add-to-cart-ubb']

        # 所有span ID
        SPAN_IDS = ['submit.add-to-cart', 'submit.add-to-cart-ubb']

    # === Buy Now 按钮 ===
    class BuyNow:
        BUTTON_ID = '#buy-now-button'
        SUBMIT_NAME = '@name=submit.buy-now'
        TEXT = 'text=Buy Now'
        TITLE = '@title:Buy Now'
        INPUT_VALUE = '@@tag()=input@@value:Buy Now'

        # 所有选择器列表
        ALL = [
            '#buy-now-button',
            '@name=submit.buy-now',
            'text=Buy Now',
            '@title:Buy Now',
            '@@tag()=input@@value:Buy Now'
        ]

    # === 购买区域容器 ===
    class BuyBox:
        DESKTOP = '#desktop_buybox'
        MAIN = '#buybox'
        CONTAINER = '.buybox-container'
        ADD_TO_CART_DIV = '#addToCart_feature_div'

        # 所有容器选择器
        ALL = ['#desktop_buybox', '#buybox', '.buybox-container', '#addToCart_feature_div']

        # 容器内按钮选择器
        INNER_BUTTONS = [
            '@@tag()=input@@type=submit',
            'tag:button',
            '.a-button',
            '@value:Cart',
            '@value:Buy',
            'text:Add to Cart'
        ]

    # === 卖家信息 ===
    class Seller:
        PROFILE_TRIGGER = '#sellerProfileTriggerId'
        OFFER_DISPLAY = '.offer-display-feature-text-message'
        OFFER_LINK = '.offer-display-feature-text a'
        SELLER_LINK = 'a[href*="seller"]'
        SMALL_LINK = '.a-size-small.a-link-normal'

        # 所有选择器列表
        ALL = [
            '#sellerProfileTriggerId',
            '.offer-display-feature-text-message',
            '.offer-display-feature-text a',
            'a[href*="seller"]',
            '.a-size-small.a-link-normal'
        ]

        # 官方卖家列表（小写，用于包含匹配）
        # 注意：这些是亚马逊各个站点和官方业务线的卖家名称
        OFFICIAL_SELLERS = [
            'amazon.com',           # 美国亚马逊主站
            'amazon.ca',            # 加拿大亚马逊
            'amazon.co.uk',         # 英国亚马逊
            'amazon.de',            # 德国亚马逊
            'amazon.fr',            # 法国亚马逊
            'amazon.it',            # 意大利亚马逊
            'amazon.es',            # 西班牙亚马逊
            'amazon.co.jp',         # 日本亚马逊
            'amazon.cn',            # 中国亚马逊
            'amazon.in',            # 印度亚马逊
            'amazon.com.mx',        # 墨西哥亚马逊
            'amazon.com.br',        # 巴西亚马逊
            'amazon.com.au',        # 澳大利亚亚马逊
            'amazon.nl',            # 荷兰亚马逊
            'amazon.sg',            # 新加坡亚马逊
            'amazon.ae',            # 阿联酋亚马逊
            'amazon.sa',            # 沙特阿拉伯亚马逊
            'amazon.se',            # 瑞典亚马逊
            'fusa official',        # FUSA官方
            'ftl official',         # FTL官方
            'woot',                 # Woot（亚马逊子公司）
            'amazon resale',        # 亚马逊二手翻新
            'amazon warehouse',     # 亚马逊仓库优惠
        ]

    # === 邮编设置 ===
    class ZipCode:
        # 位置链接
        LOCATION_LINK = '#nav-global-location-popover-link'
        LOCATION_SLOT = '#nav-global-location-slot'
        LOCATION_DATA = '#nav-global-location-data-modal-action'

        # 邮编输入区域
        ZIP_INPUT_SECTION = '#GLUXZipInputSection'
        ZIP_UPDATE_INPUT = '#GLUXZipUpdateInput'
        ZIP_UPDATE_INPUT_0 = '#GLUXZipUpdateInput_0'
        ZIP_UPDATE_INPUT_1 = '#GLUXZipUpdateInput_1'
        ZIP_UPDATE_BUTTON = '#GLUXZipUpdate-announce'

        # 弹窗相关
        POPOVER_WRAPPER = '.a-popover-wrapper'
        MODAL = '[data-a-modal][style*="display"]'
        GLOW_MODAL = '#glow-modal'
        GLOW_MODAL_CONTENT = '.glow-modal-content'
        POPOVER_CONTENT = '.a-popover-content'

        # 关闭按钮
        POPOVER_CLOSE = '.a-popover-close'
        BUTTON_CLOSE = '.a-button-close'
        CLOSE_ACTION = '[data-action="a-popover-close"]'

        # Done按钮选择器
        DONE_SELECTORS = [
            'button[name="glowDoneButton"]',
            '.a-button-text:contains("Done")',
            '.a-button-primary .a-button-text:contains("Done")',
            '[data-action="a-popover-close"] .a-button-text:contains("Done")',
            '.a-popover-footer button:contains("Done")'
        ]

        # 弹窗指示器
        MODAL_INDICATORS = [
            '#GLUXZipInputSection',
            '.a-popover-wrapper',
            '[data-a-modal][style*="display"]',
            '#glow-modal',
            '.glow-modal-content',
            '.a-popover-content'
        ]

        # 输入框选择器（按优先级）
        INPUT_SELECTORS = [
            '#GLUXZipUpdateInput',
            'input[id*="ZipUpdateInput"]',
            '#GLUXZipInputSection input[type="text"]',
            '.a-input-text[maxlength]'
        ]

        # 加拿大第一个输入框
        CA_INPUT_0_SELECTORS = [
            '#GLUXZipUpdateInput_0',
            'input[id*="ZipUpdateInput_0"]',
            'input[maxlength="3"]:first-of-type',
            '#GLUXZipInputSection input:first-of-type'
        ]

        # 加拿大第二个输入框
        CA_INPUT_1_SELECTORS = [
            '#GLUXZipUpdateInput_1',
            'input[id*="ZipUpdateInput_1"]',
            'input[maxlength="3"]:last-of-type',
            '#GLUXZipInputSection input:last-of-type'
        ]


class WalmartSelectors:
    """Walmart 页面选择器"""

    # === 反爬验证页面 ===
    class RobotCheck:
        # 检测特征：页面标题包含 "Robot or human?"
        HEADING = 'css:h1.sign-in-widget'
        HEADING_TEXT = 'text:Robot or human?'

        # 需要点击的按钮（header-logo 链接）
        LOGO_BUTTON = 'css:a.header-logo'
        LOGO_BUTTON_ARIA = '@aria-label=Walmart. Save Money. Live Better. Home Page'

        # 所有检测选择器
        DETECTION_SELECTORS = [
            'text:Robot or human?',
            'css:h1.sign-in-widget',
        ]

        # 所有点击选择器（按优先级）- 用于点击logo类型的验证
        CLICK_SELECTORS = [
            'css:a.header-logo',
            '@aria-label=Walmart. Save Money. Live Better. Home Page',
            'css:a[href="/"]',
        ]

        # Press and Hold 类型验证的检测文本
        PRESS_HOLD_TEXT = 'text:Activate and hold the button'

        # 需要长按的元素选择器（按优先级）
        # 注意：PerimeterX 使用 closed Shadow DOM，无法直接访问内部按钮
        # 必须对外层容器 #px-captcha 进行长按操作
        HOLD_BUTTON_SELECTORS = [
            '#px-captcha',                           # PerimeterX 验证容器（最重要！）
            'css:#px-captcha',                       # CSS 选择器格式
            'css:div#px-captcha',                    # 更精确的 div 选择器
            'css:.re-captcha #px-captcha',           # 在 re-captcha 容器内查找
        ]


class Timeouts:
    """超时配置"""
    QUICK = 0.3
    SHORT = 0.5
    NORMAL = 1
    MEDIUM = 2
    LONG = 3
    PAGE_LOAD = 5
    MODAL_WAIT = 8
