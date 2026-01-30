#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Walmart 页面选择器
统一管理所有 Walmart 页面的 CSS/XPath 选择器

基于需求文档中的 HTML 示例设计
"""


class WalmartSelectors:
    """Walmart 页面选择器"""

    # === 页面状态检测 ===
    class PageStatus:
        """页面状态检测选择器"""
        # 购买区域容器
        BUY_BOX = 'css:[data-testid="flex-container"].buy-box-container'
        BUY_BOX_ALT = '.buy-box-container'

        # 商品标题
        PRODUCT_TITLE = '@data-testid=product-title'
        PRODUCT_TITLE_ALT = 'css:h1[itemprop="name"]'

        # 验证码检测
        CAPTCHA = '@data-testid=captcha'
        CAPTCHA_ALT = '#captcha-container'

        # 搜索框（用于判断页面是否加载完成）
        SEARCH_BOX = '@data-testid=search-box'
        SEARCH_BOX_ALT = '#global-search-input'

    # === 防爬验证页面 ===
    class BotDetection:
        """防爬/人机验证页面选择器"""
        # 验证页面的 Logo 按钮（需要点击进入下一步）
        HEADER_LOGO = 'a.header-logo'
        HEADER_LOGO_ALT = 'a[aria-label*="Walmart"]'

        # Logo 内的 spark 图标
        SPARK_ICON = 'span.elc-icon-spark'
        SPARK_ICON_ALT = 'span.spark'

        # 验证页面特征：只有 logo 没有商品内容
        # 通过检测 logo 存在但没有商品标题来判断

        # 所有验证页面选择器
        ALL_LOGO_BUTTONS = [
            'a.header-logo',
            'a[aria-label*="Walmart"][href="/"]',
            'a[aria-label*="Save Money"]'
        ]

    # === 库存状态 ===
    class Stock:
        """库存状态选择器"""
        # 不可用状态（需求文档中的异常状态）
        NOT_AVAILABLE = 'text=Not Available'
        NOT_AVAILABLE_DIV = '.dark-gray.lh-copy:contains("Not Available")'

        # 缺货状态
        OUT_OF_STOCK = '@data-testid=out-of-stock-message'
        OUT_OF_STOCK_TEXT = 'text=Out of stock'

        # 售罄状态
        SOLD_OUT = 'text=Sold out'

        # 暂时不可用
        TEMPORARILY_UNAVAILABLE = 'text=Temporarily unavailable'

        # 所有异常状态选择器
        ALL_UNAVAILABLE = [
            'text=Not Available',
            'text=Out of stock',
            'text=Sold out',
            'text=Temporarily unavailable',
            '@data-testid=out-of-stock-message'
        ]

    # === 购物车按钮 ===
    class CartButton:
        """购物车按钮选择器"""
        # 主要的 Add to Cart 按钮（需求文档中的正常状态）
        ATC_BUTTON = '@data-automation-id=atc'

        # ATC 容器
        ATC_CONTAINER = '@data-testid=atc-buynow-container'

        # 备选选择器
        ATC_BUTTON_ALT = 'css:button[data-dca-name="ItemBuyBoxAddToCartButton"]'
        ATC_TEXT = 'text=Add to cart'

        # 按钮内的文本
        ATC_SPAN = 'css:button[data-automation-id="atc"] span'

        # 所有 ATC 选择器（按优先级排序）
        ALL = [
            '@data-automation-id=atc',
            'css:button[data-dca-name="ItemBuyBoxAddToCartButton"]',
            'css:[data-testid="atc-buynow-container"] button',
            'text=Add to cart'
        ]

    # === Buy Now 按钮 ===
    class BuyNow:
        """Buy Now 按钮选择器"""
        BUTTON = '@data-testid=buy-now-button'
        BUTTON_ALT = 'button:contains("Buy now")'
        TEXT = 'text=Buy now'

        ALL = [
            '@data-testid=buy-now-button',
            'text=Buy now'
        ]

    # === 价格信息 ===
    class Price:
        """价格选择器 - 用于提取商品价格

        基于需求文档中的 HTML 示例:
        <span itemprop="price" data-seo-id="hero-price">$224.63</span>
        """
        # 主要价格选择器（需求文档指定）
        HERO_PRICE = '@data-seo-id=hero-price'

        # 价格容器
        PRICE_WRAP = '@data-testid=price-wrap'

        # 当前价格
        CURRENT_PRICE = 'css:span[itemprop="price"]'
        CURRENT_PRICE_ALT = '.f1.mr2'  # 大字体价格

        # 价格提示文本
        PRICE_HINT = '.w_iUH7'  # "Current price is" 文本

        # 货币
        CURRENCY = 'css:span[itemprop="priceCurrency"]'

        # 原价（划线价）
        ORIGINAL_PRICE = '@data-testid=original-price'
        WAS_PRICE = '.was-price'
        STRIKETHROUGH_PRICE = '.strike-through'

        # 折扣信息
        SAVINGS = '@data-testid=savings'
        DISCOUNT_BADGE = '@data-testid=discount-badge'

        # 所有价格选择器（按优先级排序）
        # 注意：DrissionPage需要 css: 前缀来识别标准CSS选择器
        ALL = [
            'css:span[itemprop="price"][data-seo-id="hero-price"]',  # 最精确：同时匹配两个属性
            '@data-seo-id=hero-price',                               # DrissionPage原生语法
            '@itemprop=price',                                       # 语义化标签
            'css:[data-testid="price-wrap"] span[itemprop="price"]', # 在价格容器内查找
            'css:.inline-flex span[itemprop="price"]',               # 在flex容器内查找
        ]

    # === 卖家信息 ===
    class Seller:
        """卖家信息选择器"""
        SELLER_NAME = '@data-testid=seller-name'
        SOLD_BY = 'text=Sold by'
        SHIPPED_BY = 'text=Shipped by'

        # Walmart 官方卖家标识
        OFFICIAL_SELLERS = ['walmart', 'walmart.com', 'walmart seller']

    # === 配送信息 ===
    class Delivery:
        """配送信息选择器"""
        DELIVERY_DATE = '@data-testid=delivery-date'
        PICKUP_AVAILABLE = '@data-testid=pickup-available'
        SHIPPING_INFO = '@data-testid=shipping-info'

    # === 邮编设置 ===
    class ZipCode:
        """邮编设置选择器"""
        # 位置链接
        LOCATION_LINK = '@data-testid=location-link'
        LOCATION_BUTTON = 'css:button[aria-label*="location"]'

        # 邮编输入
        ZIP_INPUT = '@data-testid=zip-code-input'
        ZIP_INPUT_ALT = 'css:input[placeholder*="ZIP"]'

        # 更新按钮
        UPDATE_BUTTON = '@data-testid=update-location-button'

        # 弹窗
        LOCATION_MODAL = '@data-testid=location-modal'


class WalmartTimeouts:
    """Walmart 超时配置"""
    QUICK = 0.5
    SHORT = 1
    NORMAL = 2
    MEDIUM = 3
    LONG = 5
    PAGE_LOAD = 10
    MODAL_WAIT = 8
