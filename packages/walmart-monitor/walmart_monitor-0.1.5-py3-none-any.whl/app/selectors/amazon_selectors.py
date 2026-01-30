#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Amazon 页面选择器
统一管理所有 Amazon 页面的 CSS/XPath 选择器
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

        # 官方卖家列表（小写）
        OFFICIAL_SELLERS = ['fusa official', 'ftl official', 'woot', 'amazon resale']

    # === 价格信息 ===
    class Price:
        """价格选择器 - 用于提取商品价格"""
        # 核心价格区域
        CORE_PRICE = '#corePrice_feature_div'

        # 隐藏的完整价格（最可靠）
        OFFSCREEN_PRICE = '.a-offscreen'

        # 价格组成部分
        PRICE_WHOLE = '.a-price-whole'
        PRICE_FRACTION = '.a-price-fraction'
        PRICE_SYMBOL = '.a-price-symbol'

        # 价格容器
        PRICE_CONTAINER = '.a-price'
        APEX_PRICE = '#apex_offerDisplay_desktop'

        # 备选价格选择器
        DEAL_PRICE = '#priceblock_dealprice'
        OUR_PRICE = '#priceblock_ourprice'
        SALE_PRICE = '#priceblock_saleprice'

        # 所有价格选择器（按优先级排序）
        ALL = [
            '#corePrice_feature_div .a-offscreen',
            '.a-price .a-offscreen',
            '#priceblock_ourprice',
            '#priceblock_dealprice',
            '#priceblock_saleprice',
            '.a-price-whole'
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


class AmazonTimeouts:
    """Amazon 超时配置"""
    QUICK = 0.3
    SHORT = 0.5
    NORMAL = 1
    MEDIUM = 2
    LONG = 3
    PAGE_LOAD = 5
    MODAL_WAIT = 8
