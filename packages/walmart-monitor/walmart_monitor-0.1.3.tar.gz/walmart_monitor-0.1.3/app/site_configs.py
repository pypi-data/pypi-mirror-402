#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Amazon站点配置管理
支持不同国家/地区的Amazon站点邮编设置
"""

from typing import Dict, Any
from urllib.parse import urlparse


class AmazonSiteConfigs:
    """Amazon站点配置管理类"""

    # 站点配置字典
    SITE_CONFIGS = {
        # 北美地区
        'Amazon.com': {
            'zip_code': '10001',           # 纽约邮编
            'country': 'US',
            'country_name': '美国',
            'zip_input_selector': '#GLUXZipUpdateInput',
            'zip_input_type': 'single',
            'homepage': 'https://www.Amazon.com/',
            'currency': 'USD',
            'has_done_button': True       # 美国站点有Done按钮
        },
        'Amazon.ca': {
            'zip_code': 'V5C 6N5',         # 温哥华邮编
            'country': 'CA',
            'country_name': '加拿大',
            'zip_input_selector': '#GLUXZipUpdateInput_0',
            'zip_input_type': 'split',
            'homepage': 'https://www.Amazon.ca/',
            'currency': 'CAD',
            'has_done_button': False      # 加拿大站点没有Done按钮
        },
        'Amazon.com.mx': {
            'zip_code': '01000',           # 墨西哥城邮编
            'country': 'MX',
            'country_name': '墨西哥',
            'zip_input_selector': '#GLUXZipUpdateInput',
            'zip_input_type': 'single',
            'homepage': 'https://www.Amazon.com.mx/',
            'currency': 'MXN',
            'has_done_button': True       # 默认有Done按钮
        },

        # 欧洲地区
        'Amazon.co.uk': {
            'zip_code': 'SW1A 1AA',        # 伦敦邮编
            'country': 'UK',
            'country_name': '英国',
            'zip_input_selector': '#GLUXZipUpdateInput',
            'zip_input_type': 'single',
            'homepage': 'https://www.Amazon.co.uk/',
            'currency': 'GBP',
            'has_done_button': True
        },
        'Amazon.de': {
            'zip_code': '10115',           # 柏林邮编
            'country': 'DE',
            'country_name': '德国',
            'zip_input_selector': '#GLUXZipUpdateInput',
            'zip_input_type': 'single',
            'homepage': 'https://www.Amazon.de/',
            'currency': 'EUR',
            'has_done_button': True
        },
        'Amazon.fr': {
            'zip_code': '75001',           # 巴黎邮编
            'country': 'FR',
            'country_name': '法国',
            'zip_input_selector': '#GLUXZipUpdateInput',
            'zip_input_type': 'single',
            'homepage': 'https://www.Amazon.fr/',
            'currency': 'EUR',
            'has_done_button': True
        },
        'Amazon.it': {
            'zip_code': '00118',           # 罗马邮编
            'country': 'IT',
            'country_name': '意大利',
            'zip_input_selector': '#GLUXZipUpdateInput',
            'zip_input_type': 'single',
            'homepage': 'https://www.Amazon.it/',
            'currency': 'EUR'
        },
        'Amazon.es': {
            'zip_code': '28001',           # 马德里邮编
            'country': 'ES',
            'country_name': '西班牙',
            'zip_input_selector': '#GLUXZipUpdateInput',
            'zip_input_type': 'single',
            'homepage': 'https://www.Amazon.es/',
            'currency': 'EUR'
        },
        'Amazon.nl': {
            'zip_code': '1012 JS',         # 阿姆斯特丹邮编
            'country': 'NL',
            'country_name': '荷兰',
            'zip_input_selector': '#GLUXZipUpdateInput',
            'zip_input_type': 'single',
            'homepage': 'https://www.Amazon.nl/',
            'currency': 'EUR'
        },
        'Amazon.se': {
            'zip_code': '111 29',          # 斯德哥尔摩邮编
            'country': 'SE',
            'country_name': '瑞典',
            'zip_input_selector': '#GLUXZipUpdateInput',
            'zip_input_type': 'single',
            'homepage': 'https://www.Amazon.se/',
            'currency': 'SEK'
        },
        'Amazon.pl': {
            'zip_code': '00-001',          # 华沙邮编
            'country': 'PL',
            'country_name': '波兰',
            'zip_input_selector': '#GLUXZipUpdateInput',
            'zip_input_type': 'single',
            'homepage': 'https://www.Amazon.pl/',
            'currency': 'PLN'
        },

        # 亚太地区
        'Amazon.co.jp': {
            'zip_code': '100-0001',        # 东京邮编
            'country': 'JP',
            'country_name': '日本',
            'zip_input_selector': '#GLUXZipUpdateInput',
            'zip_input_type': 'single',
            'homepage': 'https://www.Amazon.co.jp/',
            'currency': 'JPY'
        },
        'Amazon.com.au': {
            'zip_code': '2000',            # 悉尼邮编
            'country': 'AU',
            'country_name': '澳大利亚',
            'zip_input_selector': '#GLUXZipUpdateInput',
            'zip_input_type': 'single',
            'homepage': 'https://www.Amazon.com.au/',
            'currency': 'AUD'
        },
        'Amazon.in': {
            'zip_code': '110001',          # 新德里邮编
            'country': 'IN',
            'country_name': '印度',
            'zip_input_selector': '#GLUXZipUpdateInput',
            'zip_input_type': 'single',
            'homepage': 'https://www.Amazon.in/',
            'currency': 'INR'
        },
        'Amazon.sg': {
            'zip_code': '018956',          # 新加坡邮编
            'country': 'SG',
            'country_name': '新加坡',
            'zip_input_selector': '#GLUXZipUpdateInput',
            'zip_input_type': 'single',
            'homepage': 'https://www.Amazon.sg/',
            'currency': 'SGD'
        },

        # 南美地区
        'Amazon.com.br': {
            'zip_code': '01310-100',       # 圣保罗邮编
            'country': 'BR',
            'country_name': '巴西',
            'zip_input_selector': '#GLUXZipUpdateInput',
            'zip_input_type': 'single',
            'homepage': 'https://www.Amazon.com.br/',
            'currency': 'BRL'
        },

        # 中东地区
        'Amazon.ae': {
            'zip_code': '00000',           # 阿联酋邮编
            'country': 'AE',
            'country_name': '阿联酋',
            'zip_input_selector': '#GLUXZipUpdateInput',
            'zip_input_type': 'single',
            'homepage': 'https://www.Amazon.ae/',
            'currency': 'AED'
        },
        'Amazon.sa': {
            'zip_code': '11564',           # 利雅得邮编
            'country': 'SA',
            'country_name': '沙特阿拉伯',
            'zip_input_selector': '#GLUXZipUpdateInput',
            'zip_input_type': 'single',
            'homepage': 'https://www.Amazon.sa/',
            'currency': 'SAR'
        }
    }

    @classmethod
    def get_site_config(cls, url: str) -> Dict[str, Any]:
        """
        根据URL获取站点配置信息

        Args:
            url: Amazon产品URL

        Returns:
            站点配置字典
        """
        try:
            # 从URL中提取域名
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()

            # 移除www前缀
            if domain.startswith('www.'):
                domain = domain[4:]

            # 返回匹配的配置，默认使用美国站点配置
            return cls.SITE_CONFIGS.get(domain, cls.SITE_CONFIGS['Amazon.com'])

        except Exception:
            # 解析失败时返回默认配置
            return cls.SITE_CONFIGS['Amazon.com']

    @classmethod
    def get_all_supported_sites(cls) -> Dict[str, str]:
        """
        获取所有支持的站点列表

        Returns:
            站点域名到国家名称的映射
        """
        return {domain: config['country_name'] for domain, config in cls.SITE_CONFIGS.items()}

    @classmethod
    def is_split_zip_site(cls, url: str) -> bool:
        """
        判断是否为分割式邮编输入的站点（如加拿大）

        Args:
            url: Amazon产品URL

        Returns:
            是否为分割式邮编输入
        """
        config = cls.get_site_config(url)
        return config['zip_input_type'] == 'split'

    @classmethod
    def get_zip_code(cls, url: str) -> str:
        """
        获取指定URL对应站点的邮编

        Args:
            url: Amazon产品URL

        Returns:
            邮编字符串
        """
        config = cls.get_site_config(url)
        return config['zip_code']

    @classmethod
    def get_homepage(cls, url: str) -> str:
        """
        获取指定URL对应站点的首页

        Args:
            url: Amazon产品URL

        Returns:
            首页URL
        """
        config = cls.get_site_config(url)
        return config['homepage']

# 为了向后兼容，提供一个简单的函数接口


def get_site_config(url: str) -> Dict[str, Any]:
    """获取站点配置的简单接口"""
    return AmazonSiteConfigs.get_site_config(url)
