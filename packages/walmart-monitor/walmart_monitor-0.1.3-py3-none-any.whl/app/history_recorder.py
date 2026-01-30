#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异常历史记录器
将异常数据记录到钉钉电子表格的第二个sheet页
"""

import os
import re
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from alibabacloud_dingtalk.doc_1_0 import models as dingtalkdoc_1_0_models
from alibabacloud_tea_util import models as util_models

logger = logging.getLogger(__name__)


class HistoryRecorder:
    """异常历史记录器 - 记录到钉钉电子表格"""

    # 默认sheet名称
    DEFAULT_SHEET_NAME = "异常记录"
    # 表头
    HEADERS = ["日期", "时间", "ASIN", "异常类型", "URL", "详情"]

    def __init__(self):
        # 延迟导入避免循环依赖
        from app.dingtalk_doc_reader import dingtalk_doc_reader
        self.doc_reader = dingtalk_doc_reader

        # 配置
        self.enabled = os.getenv("HISTORY_RECORD_ENABLED", "true").lower() == "true"
        self.sheet_name = os.getenv("HISTORY_SHEET_NAME", self.DEFAULT_SHEET_NAME)

        # 缓存
        self.workbook_id = None
        self.sheet_id = None
        self._initialized = False

    def _initialize(self) -> bool:
        """初始化：获取workbook_id和sheet_id"""
        if self._initialized:
            return True

        if not self.enabled:
            logger.debug("历史记录功能已禁用")
            return False

        if not self.doc_reader.is_enabled():
            logger.warning("钉钉文档功能未启用，历史记录将不可用")
            return False

        try:
            # 获取workbook_id
            doc_info = self.doc_reader.extract_doc_info()
            if not doc_info or not doc_info.get('workbook_id'):
                logger.error("无法获取workbook_id")
                return False

            self.workbook_id = doc_info['workbook_id']

            # 查找异常记录sheet
            self.sheet_id = self.doc_reader._find_sheet_by_name(
                self.workbook_id, self.sheet_name
            )

            if not self.sheet_id:
                logger.warning(f"未找到名为 '{self.sheet_name}' 的工作表，请手动创建")
                return False

            logger.info(f"历史记录初始化成功: workbook={self.workbook_id}, sheet={self.sheet_id}")
            self._initialized = True

            # 获取当日任务次数
            self.daily_task_count = self._get_daily_task_count()

            return True

        except Exception as e:
            logger.error(f"历史记录初始化失败: {e}")
            return False

    def _get_daily_task_count(self) -> int:
        """获取当日第几次任务"""
        today = datetime.now().strftime("%Y-%m-%d")

        # 使用本地文件记录任务次数
        os.makedirs("data", exist_ok=True)
        count_file = f"data/task_count_{today}.txt"

        try:
            if os.path.exists(count_file):
                with open(count_file, 'r') as f:
                    count = int(f.read().strip()) + 1
            else:
                count = 1

            with open(count_file, 'w') as f:
                f.write(str(count))

            logger.debug(f"当日第 {count} 次任务")
            return count

        except Exception as e:
            logger.warning(f"获取任务次数失败: {e}")
            return 1

    def _extract_asin(self, url: str) -> str:
        """从URL中提取ASIN"""
        if not url:
            return ""

        # 匹配 /dp/ASIN 或 /gp/product/ASIN 格式
        patterns = [
            r'/dp/([A-Z0-9]{10})',
            r'/gp/product/([A-Z0-9]{10})',
            r'/exec/obidos/ASIN/([A-Z0-9]{10})',
        ]

        for pattern in patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return match.group(1).upper()

        return ""

    def _status_to_type(self, status: str) -> str:
        """将状态码转换为异常类型描述"""
        status_map = {
            'out_of_stock': '无库存',
            'cart_button_missing': '丢购物车',
            'failed': '其他异常',
            'unknown': '其他异常',
        }
        return status_map.get(status, '其他异常')

    def _get_next_row(self) -> int:
        """获取下一个可写入的行号"""
        if not self._initialized:
            return 2  # 默认从第2行开始（第1行是表头）

        try:
            # 读取A列数据来确定最后一行
            data = self.doc_reader._read_sheet_range_single(
                self.workbook_id, self.sheet_id, "A1:A1000"
            )

            if not data:
                return 2  # 空表，从第2行开始

            # 找到最后一个非空行
            last_row = 1
            for i, row in enumerate(data):
                if row and row[0] and str(row[0]).strip():
                    last_row = i + 1

            return last_row + 1

        except Exception as e:
            logger.warning(f"获取下一行失败: {e}")
            return 2

    def _update_range(self, range_address: str, values: List[List[str]]) -> bool:
        """写入数据到指定范围"""
        if not self._initialized:
            return False

        try:
            access_token = self.doc_reader._get_access_token()
            if not access_token:
                logger.error("无法获取访问令牌")
                return False

            headers = dingtalkdoc_1_0_models.UpdateRangeHeaders()
            headers.x_acs_dingtalk_access_token = access_token

            request = dingtalkdoc_1_0_models.UpdateRangeRequest(
                operator_id=self.doc_reader.operator_id,
                values=values
            )

            response = self.doc_reader.doc_client.update_range_with_options(
                self.workbook_id,
                self.sheet_id,
                range_address,
                request,
                headers,
                util_models.RuntimeOptions()
            )

            if response.body and response.body.a_1notation:
                logger.debug(f"写入成功: {response.body.a_1notation}")
                return True

            return False

        except Exception as e:
            logger.error(f"写入数据失败: {e}")
            if hasattr(e, 'data') and e.data:
                logger.error(f"错误详情: {e.data}")
            return False

    def record_exception(self, url: str, status: str, details: str = "") -> bool:
        """记录一条异常"""
        if not self._initialize():
            return False

        try:
            asin = self._extract_asin(url)
            now = datetime.now()

            row_data = [
                now.strftime("%Y-%m-%d"),
                now.strftime("%H:%M:%S"),
                asin,
                self._status_to_type(status),
                url,
                details[:100] if details else ""  # 限制详情长度
            ]

            next_row = self._get_next_row()
            range_address = f"A{next_row}:F{next_row}"

            success = self._update_range(range_address, [row_data])
            if success:
                logger.debug(f"记录异常: {asin} - {status}")
            return success

        except Exception as e:
            logger.error(f"记录异常失败: {e}")
            return False

    def record_batch(self, exceptions: List[Dict[str, Any]]) -> bool:
        """批量记录异常（减少API调用）"""
        if not exceptions:
            return True

        if not self._initialize():
            logger.warning("历史记录未初始化，跳过批量记录")
            return False

        try:
            now = datetime.now()
            rows = []

            for exc in exceptions:
                url = exc.get('url', '')
                status = exc.get('status', 'unknown')
                details = exc.get('message', '') or exc.get('details', '')

                asin = self._extract_asin(url)
                row_data = [
                    now.strftime("%Y-%m-%d"),
                    now.strftime("%H:%M:%S"),
                    asin,
                    self._status_to_type(status),
                    url,
                    details[:100] if details else ""
                ]
                rows.append(row_data)

            if not rows:
                return True

            next_row = self._get_next_row()
            end_row = next_row + len(rows) - 1
            range_address = f"A{next_row}:F{end_row}"

            success = self._update_range(range_address, rows)
            if success:
                logger.info(f"批量记录 {len(rows)} 条异常到钉钉表格")
            return success

        except Exception as e:
            logger.error(f"批量记录异常失败: {e}")
            return False

    def is_available(self) -> bool:
        """检查历史记录功能是否可用"""
        return self._initialize()


# 全局实例
history_recorder = HistoryRecorder()
