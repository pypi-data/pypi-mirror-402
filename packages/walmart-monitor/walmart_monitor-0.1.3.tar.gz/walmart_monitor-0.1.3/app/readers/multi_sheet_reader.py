#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多 Sheet 数据读取器
从钉钉表格读取多个 Sheet 的商品监控数据
"""

import os
import logging
from typing import List, Dict, Any, Optional

from app.models import MonitorItem
from app.dingtalk_doc_reader import DingTalkDocReader

logger = logging.getLogger(__name__)


class MultiSheetReader:
    """多 Sheet 数据读取器

    从钉钉表格读取多个 Sheet（如 WM-FIT、WM-Uriah）的商品监控数据，
    并解析为 MonitorItem 列表。

    Sheet 数据格式：
        A列: Walmart ID
        B列: Amazon ASIN
        C列: 价格监控开关 (0=关闭, 1=沃尔玛价高提醒, 2=亚马逊价高提醒)
        D列: 价格阈值百分比
        E列: 购物车监控开关 (0=关闭, 1=开启)
    """

    # 默认要读取的 Sheet 列表
    DEFAULT_SHEETS = ['WM-FIT', 'WM-Uriah']

    def __init__(self, doc_reader: DingTalkDocReader = None):
        """初始化多 Sheet 读取器

        Args:
            doc_reader: 钉钉文档读取器实例，如果不提供则创建新实例
        """
        self.doc_reader = doc_reader or DingTalkDocReader()

        # 从环境变量读取 Sheet 列表配置
        sheets_config = os.getenv('DATA_SHEETS', '')
        if sheets_config:
            self.sheet_names = [s.strip() for s in sheets_config.split(',') if s.strip()]
        else:
            self.sheet_names = self.DEFAULT_SHEETS

        logger.info(f"MultiSheetReader 初始化，目标 Sheets: {self.sheet_names}")

    def read_all_sheets(self) -> List[MonitorItem]:
        """读取所有配置的 Sheet 数据

        Returns:
            List[MonitorItem]: 所有 Sheet 的监控项列表
        """
        all_items = []

        for sheet_name in self.sheet_names:
            try:
                items = self.read_sheet(sheet_name)
                all_items.extend(items)
                logger.info(f"Sheet '{sheet_name}' 读取完成: {len(items)} 个监控项")
            except Exception as e:
                logger.error(f"读取 Sheet '{sheet_name}' 失败: {e}")

        logger.info(f"所有 Sheet 读取完成，共 {len(all_items)} 个监控项")
        return all_items

    def read_sheet(self, sheet_name: str) -> List[MonitorItem]:
        """读取单个 Sheet 的数据

        Args:
            sheet_name: Sheet 名称

        Returns:
            List[MonitorItem]: 监控项列表
        """
        if not self.doc_reader.is_enabled():
            logger.warning("钉钉文档功能未启用，尝试从备份读取")
            return self._read_from_backup(sheet_name)

        try:
            # 获取文档信息
            doc_info = self.doc_reader.extract_doc_info()
            if not doc_info or not doc_info.get('workbook_id'):
                logger.error("无法获取文档信息")
                return self._read_from_backup(sheet_name)

            workbook_id = doc_info['workbook_id']

            # 查找 Sheet
            sheet_id = self.doc_reader._find_sheet_by_name(workbook_id, sheet_name)
            if not sheet_id:
                logger.warning(f"未找到 Sheet: {sheet_name}")
                return []

            # 读取数据
            sheet_data = self.doc_reader._read_sheet_range(workbook_id, sheet_id)
            if not sheet_data:
                logger.warning(f"Sheet '{sheet_name}' 数据为空")
                return []

            # 解析为 MonitorItem
            items = self._parse_sheet_data(sheet_data, sheet_name)

            # 保存备份
            self._save_backup(sheet_data, sheet_name)

            return items

        except Exception as e:
            logger.error(f"读取 Sheet '{sheet_name}' 时发生错误: {e}")
            return self._read_from_backup(sheet_name)

    def _parse_sheet_data(self, data: List[List[Any]], source_sheet: str) -> List[MonitorItem]:
        """解析 Sheet 数据为 MonitorItem 列表

        Args:
            data: Sheet 原始数据（二维列表）
            source_sheet: 数据来源 Sheet 名称

        Returns:
            List[MonitorItem]: 监控项列表
        """
        items = []

        # 跳过标题行（假设第一行是标题）
        for row_idx, row in enumerate(data[1:], start=2):
            try:
                # 确保行有足够的列
                if len(row) < 2:
                    continue

                # 提取数据
                walmart_id = str(row[0]).strip() if row[0] else ''
                amazon_asin = str(row[1]).strip() if len(row) > 1 and row[1] else ''

                # 跳过空行
                if not walmart_id and not amazon_asin:
                    continue

                # 验证 Walmart ID 和 ASIN 格式
                if not self._is_valid_walmart_id(walmart_id):
                    logger.debug(f"行 {row_idx}: 无效的 Walmart ID: {walmart_id}")
                    continue

                if not self._is_valid_asin(amazon_asin):
                    logger.debug(f"行 {row_idx}: 无效的 ASIN: {amazon_asin}")
                    continue

                # 解析可选字段
                price_monitor_switch = self._parse_int(row[2] if len(row) > 2 else 0, default=0)

                # 解析价格阈值（支持百分比和具体数值）
                price_threshold, threshold_type = self._parse_threshold(
                    row[3] if len(row) > 3 else '10%'
                )

                cart_monitor_switch = self._parse_int(row[4] if len(row) > 4 else 1, default=1)

                # 创建 MonitorItem
                item = MonitorItem(
                    walmart_id=walmart_id,
                    amazon_asin=amazon_asin,
                    price_monitor_switch=price_monitor_switch,
                    price_threshold=price_threshold,
                    cart_monitor_switch=cart_monitor_switch,
                    source_sheet=source_sheet,
                    threshold_type=threshold_type
                )
                items.append(item)

            except Exception as e:
                logger.warning(f"解析行 {row_idx} 失败: {e}")
                continue

        logger.debug(f"从 Sheet '{source_sheet}' 解析出 {len(items)} 个有效监控项")
        return items

    def _is_valid_walmart_id(self, walmart_id: str) -> bool:
        """验证 Walmart ID 格式

        Walmart ID 通常是纯数字
        """
        if not walmart_id:
            return False
        # Walmart ID 通常是数字，长度在 6-15 位之间
        return walmart_id.isdigit() and 6 <= len(walmart_id) <= 15

    def _is_valid_asin(self, asin: str) -> bool:
        """验证 Amazon ASIN 格式

        ASIN 是 10 位字母数字组合，通常以 B0 开头
        """
        if not asin:
            return False
        # ASIN 是 10 位字母数字
        return len(asin) == 10 and asin.isalnum()

    def _parse_int(self, value: Any, default: int = 0) -> int:
        """安全解析整数"""
        if value is None or value == '':
            return default
        try:
            return int(float(str(value)))
        except (ValueError, TypeError):
            return default

    def _parse_threshold(self, value: Any) -> tuple:
        """解析价格阈值（支持百分比和具体数值）

        Args:
            value: 阈值原始值，如 "20%"、"5.5"、20 等

        Returns:
            tuple: (阈值数值, 阈值类型)
                - 阈值类型: 'percent' 表示百分比, 'absolute' 表示具体数值
        """
        if value is None or value == '':
            return (10.0, 'percent')  # 默认10%

        str_value = str(value).strip()

        # 检查是否是百分比格式
        if str_value.endswith('%'):
            try:
                threshold = float(str_value[:-1])
                return (threshold, 'percent')
            except (ValueError, TypeError):
                return (10.0, 'percent')

        # 否则视为具体数值
        try:
            threshold = float(str_value)
            return (threshold, 'absolute')
        except (ValueError, TypeError):
            return (10.0, 'percent')

    def _parse_float(self, value: Any, default: float = 0.0) -> float:
        """安全解析浮点数"""
        if value is None or value == '':
            return default
        try:
            # 处理百分比格式
            str_value = str(value).strip()
            if str_value.endswith('%'):
                str_value = str_value[:-1]
            return float(str_value)
        except (ValueError, TypeError):
            return default

    def _save_backup(self, data: List[List[Any]], sheet_name: str):
        """保存 Sheet 数据备份"""
        import json
        from datetime import datetime

        try:
            backup_dir = 'data'
            os.makedirs(backup_dir, exist_ok=True)

            backup_file = f"{backup_dir}/sheet_backup_{sheet_name}.json"
            backup_data = {
                'sheet_name': sheet_name,
                'data': data,
                'timestamp': datetime.now().isoformat(),
                'row_count': len(data)
            }

            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)

            logger.debug(f"Sheet '{sheet_name}' 备份已保存: {backup_file}")

        except Exception as e:
            logger.warning(f"保存备份失败: {e}")

    def _read_from_backup(self, sheet_name: str) -> List[MonitorItem]:
        """从备份文件读取数据"""
        import json

        backup_file = f"data/sheet_backup_{sheet_name}.json"

        if not os.path.exists(backup_file):
            logger.warning(f"备份文件不存在: {backup_file}")
            return []

        try:
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)

            data = backup_data.get('data', [])
            if data:
                items = self._parse_sheet_data(data, sheet_name)
                logger.info(f"从备份读取 Sheet '{sheet_name}': {len(items)} 个监控项")
                return items

            return []

        except Exception as e:
            logger.error(f"读取备份文件失败: {e}")
            return []

    def get_items_by_sheet(self) -> Dict[str, List[MonitorItem]]:
        """按 Sheet 分组获取监控项

        Returns:
            Dict[str, List[MonitorItem]]: Sheet 名称到监控项列表的映射
        """
        result = {}
        for sheet_name in self.sheet_names:
            result[sheet_name] = self.read_sheet(sheet_name)
        return result

    def get_stats(self) -> Dict[str, Any]:
        """获取读取统计信息"""
        items_by_sheet = self.get_items_by_sheet()

        stats = {
            'total_sheets': len(self.sheet_names),
            'total_items': sum(len(items) for items in items_by_sheet.values()),
            'sheets': {}
        }

        for sheet_name, items in items_by_sheet.items():
            cart_monitor_count = sum(1 for item in items if item.cart_monitor_switch == 1)
            price_monitor_count = sum(1 for item in items if item.price_monitor_switch > 0)

            stats['sheets'][sheet_name] = {
                'item_count': len(items),
                'cart_monitor_enabled': cart_monitor_count,
                'price_monitor_enabled': price_monitor_count
            }

        return stats
