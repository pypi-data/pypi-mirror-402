#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检测结果记录器
将检测结果写入钉钉表格的 Res Sheet
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.models import DetectionResult, ResRecord
from app.dingtalk_doc_reader import DingTalkDocReader

# 钉钉SDK导入
try:
    from alibabacloud_dingtalk.doc_1_0.client import Client as dingtalkdoc_1_0Client
    from alibabacloud_dingtalk.doc_1_0 import models as dingtalkdoc_1_0_models
    from alibabacloud_tea_openapi import models as open_api_models
    from alibabacloud_tea_util import models as util_models
    DINGTALK_SDK_AVAILABLE = True
except ImportError:
    DINGTALK_SDK_AVAILABLE = False

logger = logging.getLogger(__name__)


class ResRecorder:
    """检测结果记录器

    将检测结果写入钉钉表格的 Res Sheet。

    Res Sheet 列结构：
        A列: 日期 (2024-01-15)
        B列: 时间 (14:30:25)
        C列: 亚马逊ASIN
        D列: 沃尔玛ID
        E列: 亚马逊价格
        F列: 沃尔玛价格
        G列: 价格差异 (+72.8%)
        H列: 亚马逊购物车状态
        I列: 沃尔玛购物车状态
    """

    # 默认 Res Sheet 名称
    DEFAULT_RES_SHEET_NAME = 'Res'

    # 状态显示映射
    STATUS_DISPLAY = {
        'normal': '正常',
        'missing': '购物车丢失',
        'out_of_stock': '无库存',
        'not_available': '不可用',
        'error': '检测失败'
    }

    def __init__(self, doc_reader: DingTalkDocReader = None):
        """初始化结果记录器

        Args:
            doc_reader: 钉钉文档读取器实例
        """
        self.doc_reader = doc_reader or DingTalkDocReader()
        self.res_sheet_name = os.getenv('RES_SHEET_NAME', self.DEFAULT_RES_SHEET_NAME)

        # 初始化钉钉文档客户端
        self._doc_client = None
        if DINGTALK_SDK_AVAILABLE:
            self._doc_client = self._create_doc_client()

        # 本地备份目录
        self.backup_dir = 'data/res_records'
        os.makedirs(self.backup_dir, exist_ok=True)

        logger.info(f"ResRecorder 初始化，目标 Sheet: {self.res_sheet_name}")

    def _create_doc_client(self) -> Optional['dingtalkdoc_1_0Client']:
        """创建钉钉文档客户端"""
        if not DINGTALK_SDK_AVAILABLE:
            return None

        try:
            config = open_api_models.Config()
            config.protocol = 'https'
            config.region_id = 'central'
            return dingtalkdoc_1_0Client(config)
        except Exception as e:
            logger.error(f"创建钉钉文档客户端失败: {e}")
            return None

    def record_batch(self, results: List[DetectionResult]) -> bool:
        """批量记录检测结果

        Args:
            results: 检测结果列表

        Returns:
            bool: 是否成功写入
        """
        if not results:
            logger.warning("没有检测结果需要记录")
            return True

        # 转换为 ResRecord 列表
        records = [self._result_to_record(r) for r in results]

        # 尝试写入钉钉表格
        success = self._write_to_dingtalk(records)

        # 无论是否成功，都保存本地备份
        self._save_local_backup(records)

        return success

    def record_single(self, result: DetectionResult) -> bool:
        """记录单个检测结果

        Args:
            result: 检测结果

        Returns:
            bool: 是否成功写入
        """
        return self.record_batch([result])

    def _result_to_record(self, result: DetectionResult) -> ResRecord:
        """将 DetectionResult 转换为 ResRecord

        Args:
            result: 检测结果

        Returns:
            ResRecord: 日志记录
        """
        return ResRecord(
            date=result.detected_at.strftime('%Y-%m-%d'),
            time=result.detected_at.strftime('%H:%M:%S'),
            amazon_asin=result.monitor_item.amazon_asin,
            walmart_id=result.monitor_item.walmart_id,
            amazon_price=result.amazon_price,
            walmart_price=result.walmart_price,
            price_diff=result.price_diff_percent,
            amazon_cart_status=result.amazon_cart_status,
            walmart_cart_status=result.walmart_cart_status
        )

    def _write_to_dingtalk(self, records: List[ResRecord]) -> bool:
        """写入钉钉表格

        Args:
            records: 日志记录列表

        Returns:
            bool: 是否成功
        """
        if not self.doc_reader.is_enabled():
            logger.warning("钉钉文档功能未启用，跳过写入")
            return False

        if not self._doc_client:
            logger.warning("钉钉文档客户端未初始化，跳过写入")
            return False

        try:
            # 获取文档信息
            doc_info = self.doc_reader.extract_doc_info()
            if not doc_info or not doc_info.get('workbook_id'):
                logger.error("无法获取文档信息")
                return False

            workbook_id = doc_info['workbook_id']

            # 查找 Res Sheet
            sheet_id = self.doc_reader._find_sheet_by_name(workbook_id, self.res_sheet_name)
            if not sheet_id:
                logger.error(f"未找到 Sheet: {self.res_sheet_name}")
                return False

            # 获取当前数据行数，确定写入位置
            next_row = self._get_next_row(workbook_id, sheet_id)

            # 准备写入数据
            values = [self._record_to_row(r) for r in records]

            # 写入数据
            success = self._append_rows(workbook_id, sheet_id, next_row, values)

            if success:
                logger.info(f"成功写入 {len(records)} 条记录到 Res Sheet")
            else:
                logger.error("写入 Res Sheet 失败")

            return success

        except Exception as e:
            logger.error(f"写入钉钉表格失败: {e}")
            return False

    def _record_to_row(self, record: ResRecord) -> List[str]:
        """将 ResRecord 转换为行数据

        Args:
            record: 日志记录

        Returns:
            List[str]: 行数据
        """
        # 格式化价格
        amazon_price_str = f"${record.amazon_price:.2f}" if record.amazon_price else "-"
        walmart_price_str = f"${record.walmart_price:.2f}" if record.walmart_price else "-"

        # 格式化价格差异
        if record.price_diff is not None:
            sign = '+' if record.price_diff >= 0 else ''
            price_diff_str = f"{sign}{record.price_diff:.1f}%"
        else:
            price_diff_str = "-"

        # 格式化状态
        amazon_status_str = self.STATUS_DISPLAY.get(record.amazon_cart_status, record.amazon_cart_status)
        walmart_status_str = self.STATUS_DISPLAY.get(record.walmart_cart_status, record.walmart_cart_status)

        return [
            record.date,
            record.time,
            record.amazon_asin,
            record.walmart_id,
            amazon_price_str,
            walmart_price_str,
            price_diff_str,
            amazon_status_str,
            walmart_status_str
        ]

    def _get_next_row(self, workbook_id: str, sheet_id: str) -> int:
        """获取下一个可写入的行号

        Args:
            workbook_id: 工作簿ID
            sheet_id: 工作表ID

        Returns:
            int: 下一个可写入的行号（1-based）
        """
        try:
            # 读取 A 列数据来确定已有行数
            data = self.doc_reader._read_sheet_range_single(
                workbook_id, sheet_id, "A1:A1000"
            )

            if not data:
                return 2  # 第一行是标题，从第二行开始

            # 找到最后一个非空行
            last_row = 1
            for i, row in enumerate(data, start=1):
                if row and row[0] and str(row[0]).strip():
                    last_row = i

            return last_row + 1

        except Exception as e:
            logger.warning(f"获取下一行号失败: {e}，使用默认值")
            return 2

    def _append_rows(self, workbook_id: str, sheet_id: str, start_row: int, values: List[List[str]]) -> bool:
        """追加行数据到工作表

        Args:
            workbook_id: 工作簿ID
            sheet_id: 工作表ID
            start_row: 起始行号
            values: 要写入的数据

        Returns:
            bool: 是否成功
        """
        if not DINGTALK_SDK_AVAILABLE or not self._doc_client:
            return False

        try:
            access_token = self.doc_reader._get_access_token()
            if not access_token:
                logger.error("无法获取访问令牌")
                return False

            # 计算写入范围
            end_row = start_row + len(values) - 1
            range_address = f"A{start_row}:I{end_row}"

            logger.debug(f"写入范围: {range_address}, 数据行数: {len(values)}")

            # 构建请求
            headers = dingtalkdoc_1_0_models.UpdateRangeHeaders()
            headers.x_acs_dingtalk_access_token = access_token

            request = dingtalkdoc_1_0_models.UpdateRangeRequest(
                operator_id=self.doc_reader.operator_id,
                values=values
            )

            # 发送请求
            response = self._doc_client.update_range_with_options(
                workbook_id, sheet_id, range_address,
                request, headers, util_models.RuntimeOptions()
            )

            if response and response.body:
                logger.debug(f"写入成功: {response.body}")
                return True

            return False

        except Exception as e:
            logger.error(f"追加行数据失败: {e}")
            if hasattr(e, 'data') and e.data:
                logger.error(f"错误详情: {e.data}")
            return False

    def _save_local_backup(self, records: List[ResRecord]):
        """保存本地备份

        Args:
            records: 日志记录列表
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = f"{self.backup_dir}/res_{timestamp}.json"

            backup_data = {
                'timestamp': datetime.now().isoformat(),
                'record_count': len(records),
                'records': [
                    {
                        'date': r.date,
                        'time': r.time,
                        'amazon_asin': r.amazon_asin,
                        'walmart_id': r.walmart_id,
                        'amazon_price': r.amazon_price,
                        'walmart_price': r.walmart_price,
                        'price_diff': r.price_diff,
                        'amazon_cart_status': r.amazon_cart_status,
                        'walmart_cart_status': r.walmart_cart_status
                    }
                    for r in records
                ]
            }

            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)

            logger.debug(f"本地备份已保存: {backup_file}")

        except Exception as e:
            logger.warning(f"保存本地备份失败: {e}")

    def get_recent_records(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取最近的记录（从本地备份）

        Args:
            limit: 最大返回数量

        Returns:
            List[Dict]: 记录列表
        """
        records = []

        try:
            # 获取所有备份文件
            backup_files = sorted(
                [f for f in os.listdir(self.backup_dir) if f.endswith('.json')],
                reverse=True
            )

            for backup_file in backup_files:
                if len(records) >= limit:
                    break

                file_path = os.path.join(self.backup_dir, backup_file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    records.extend(data.get('records', []))

            return records[:limit]

        except Exception as e:
            logger.error(f"获取最近记录失败: {e}")
            return []
