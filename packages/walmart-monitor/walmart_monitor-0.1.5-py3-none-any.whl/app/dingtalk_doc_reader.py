#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
钉钉文档读取器
用于从钉钉文档中读取商品URL列表
"""

import os
import json
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta
import logging

# 钉钉SDK导入
from alibabacloud_dingtalk.doc_1_0.client import Client as dingtalkdoc_1_0Client
from alibabacloud_dingtalk.doc_1_0 import models as dingtalkdoc_1_0_models
from alibabacloud_dingtalk.wiki_2_0.client import Client as dingtalkwiki_2_0Client
from alibabacloud_dingtalk.wiki_2_0 import models as dingtalkwiki_2_0_models
from alibabacloud_dingtalk.oauth2_1_0.client import Client as dingtalkoauth2_1_0Client
from alibabacloud_dingtalk.oauth2_1_0 import models as dingtalkoauth2_1_0_models
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient

logger = logging.getLogger(__name__)


class DingTalkDocReader:
    def __init__(self):
        self.doc_url = os.getenv('DINGTALK_DOC_URL')
        self.doc_enabled = os.getenv(
            'DINGTALK_DOC_ENABLED', 'false').lower() == 'true'

        # 钉钉应用配置
        self.app_key = os.getenv('DINGTALK_APP_KEY')
        self.app_secret = os.getenv('DINGTALK_APP_SECRET')
        self.operator_id = os.getenv('DINGTALK_OPERATOR_ID')  # unionId

        # 缓存access_token
        self._access_token = None
        self._token_expire_time = None

        # 文档和工作表信息
        self.workbook_id = None
        self.sheet_id = None

        # 初始化客户端
        self.doc_client = self._create_doc_client()
        self.wiki_client = self._create_wiki_client()
        self.oauth_client = self._create_oauth_client()

    def is_enabled(self) -> bool:
        """检查钉钉文档功能是否启用"""
        return (self.doc_enabled and
                bool(self.doc_url) and
                bool(self.app_key) and
                bool(self.app_secret) and
                bool(self.operator_id))

    def _create_doc_client(self) -> dingtalkdoc_1_0Client:
        """创建钉钉文档客户端"""
        config = open_api_models.Config()
        config.protocol = 'https'
        config.region_id = 'central'
        return dingtalkdoc_1_0Client(config)

    def _create_wiki_client(self) -> dingtalkwiki_2_0Client:
        """创建钉钉知识库客户端"""
        config = open_api_models.Config()
        config.protocol = 'https'
        config.region_id = 'central'
        return dingtalkwiki_2_0Client(config)

    def _create_oauth_client(self) -> dingtalkoauth2_1_0Client:
        """创建钉钉OAuth客户端"""
        config = open_api_models.Config()
        config.protocol = 'https'
        config.region_id = 'central'
        return dingtalkoauth2_1_0Client(config)

    def _get_access_token(self) -> Optional[str]:
        """获取访问令牌"""
        # 检查缓存的token是否有效
        if (self._access_token and
            self._token_expire_time and
                datetime.now() < self._token_expire_time):
            return self._access_token

        try:
            request = dingtalkoauth2_1_0_models.GetAccessTokenRequest(
                app_key=self.app_key,
                app_secret=self.app_secret
            )

            response = self.oauth_client.get_access_token(request)

            if response.body and response.body.access_token:
                self._access_token = response.body.access_token
                # 设置过期时间（提前5分钟刷新）
                expire_in = response.body.expire_in or 7200
                self._token_expire_time = datetime.now() + timedelta(seconds=expire_in - 300)

                logger.debug("获取钉钉访问令牌成功")
                return self._access_token
            else:
                logger.error("获取访问令牌失败：响应为空")
                return None

        except Exception as e:
            logger.error(f"获取钉钉访问令牌失败: {e}")
            return None

    def extract_doc_info(self) -> Optional[Dict[str, Any]]:
        """从钉钉文档URL中提取文档信息"""
        if not self.doc_url:
            return None

        try:
            parsed_url = urlparse(self.doc_url)

            # 从URL路径中提取workbook_id
            path_parts = parsed_url.path.split('/')
            workbook_id = None

            # 钉钉文档URL格式: https://alidocs.dingtalk.com/i/nodes/{workbook_id}
            for i, part in enumerate(path_parts):
                if part == 'nodes' and i + 1 < len(path_parts):
                    raw_id = path_parts[i + 1]
                    # 处理可能的查询参数
                    workbook_id = raw_id.split('?')[0]
                    logger.debug(f"提取workbook_id: {workbook_id}")
                    break

            if not workbook_id:
                # 尝试从查询参数中提取
                query_params = parse_qs(parsed_url.query)
                iframe_query = query_params.get('iframeQuery', [''])[0]

                if iframe_query:
                    iframe_params = parse_qs(iframe_query)
                    sheet_range = iframe_params.get('sheet_range', [''])[0]
                    if sheet_range:
                        # 解析sheet_range格式获取sheet信息
                        parts = sheet_range.split('_')
                        if len(parts) >= 1:
                            # sheet_range的第一部分通常包含sheet标识
                            sheet_info = parts[0]
                            return {
                                'workbook_id': workbook_id,
                                'sheet_info': sheet_info,
                                'raw_sheet_range': sheet_range
                            }

            if not workbook_id:
                logger.error("无法从URL中提取workbook_id")

            return {
                'workbook_id': workbook_id,
                'sheet_info': None,
                'raw_url': self.doc_url
            }

        except Exception as e:
            logger.error(f"解析钉钉文档URL失败: {e}")
            return None

    def _get_workbook_sheets(self, workbook_id: str) -> List[Dict[str, Any]]:
        """获取工作簿的所有工作表"""
        access_token = self._get_access_token()
        if not access_token:
            logger.error("无法获取访问令牌")
            return []

        try:
            headers = dingtalkdoc_1_0_models.GetAllSheetsHeaders()
            headers.x_acs_dingtalk_access_token = access_token

            request = dingtalkdoc_1_0_models.GetAllSheetsRequest(
                operator_id=self.operator_id
            )

            response = self.doc_client.get_all_sheets_with_options(
                workbook_id, request, headers, util_models.RuntimeOptions()
            )

            if response.body and response.body.value:
                sheets = []
                for sheet in response.body.value:
                    sheets.append({
                        'id': sheet.id,
                        'name': sheet.name
                    })
                logger.debug(f"获取到 {len(sheets)} 个工作表")
                return sheets
            else:
                logger.warning("API响应为空或无工作表数据")
                return []

        except Exception as e:
            logger.error(f"获取工作表列表失败: {e}")
            # 尝试解析错误详情
            if hasattr(e, 'data') and e.data:
                logger.error(f"错误详情: {e.data}")
            return []

    def _find_sheet_by_name(self, workbook_id: str, sheet_name: str) -> Optional[str]:
        """根据名称查找工作表ID"""
        sheets = self._get_workbook_sheets(workbook_id)

        for sheet in sheets:
            if sheet['name'] == sheet_name:
                return sheet['id']

        # 如果没有找到精确匹配，尝试模糊匹配
        for sheet in sheets:
            if sheet_name.lower() in sheet['name'].lower():
                return sheet['id']

        return None

    def _read_sheet_range_single(self, workbook_id: str, sheet_id: str, range_address: str) -> List[List[str]]:
        """读取工作表指定范围的数据（单次请求）"""
        access_token = self._get_access_token()
        if not access_token:
            return []

        try:
            headers = dingtalkdoc_1_0_models.GetRangeHeaders()
            headers.x_acs_dingtalk_access_token = access_token

            request = dingtalkdoc_1_0_models.GetRangeRequest(
                operator_id=self.operator_id
            )

            response = self.doc_client.get_range_with_options(
                workbook_id, sheet_id, range_address,
                request, headers, util_models.RuntimeOptions()
            )

            if response.body and response.body.values:
                return response.body.values

            return []

        except Exception as e:
            logger.debug(f"读取范围 {range_address} 失败: {e}")
            return []

    def _detect_sheet_data_range(self, workbook_id: str, sheet_id: str) -> tuple:
        """智能检测工作表的实际数据范围"""
        logger.debug("检测工作表数据范围")

        # 首先尝试读取一个大范围来估算数据大小
        test_ranges = [
            "A1:Z1000",   # 测试1000行
            "A1:Z500",    # 测试500行
            "A1:Z100",    # 测试100行
            "A1:J100",    # 较小范围
        ]

        max_row = 0
        max_col = 0

        for test_range in test_ranges:
            data = self._read_sheet_range_single(
                workbook_id, sheet_id, test_range)
            if data:
                logger.debug(f"测试范围 {test_range}: {len(data)} 行")

                # 找到实际有数据的最大行和列
                for row_idx, row in enumerate(data):
                    for col_idx, cell in enumerate(row):
                        if cell and str(cell).strip():
                            max_row = max(max_row, row_idx + 1)
                            max_col = max(max_col, col_idx + 1)

                # 如果找到了数据，就使用这个范围
                if max_row > 0 and max_col > 0:
                    # 添加一些缓冲区以确保不遗漏数据
                    max_row = min(max_row + 50, 1000)  # 最多读取1000行
                    max_col = min(max_col + 5, 26)     # 最多读取到Z列

                    logger.debug(f"数据范围: {max_row}行 x {max_col}列")
                    return max_row, max_col

        # 如果检测失败，使用默认范围
        logger.warning("无法检测数据范围，使用默认范围")
        return 100, 10  # 默认100行，10列

    def _read_sheet_range(self, workbook_id: str, sheet_id: str, range_address: str = None) -> List[List[str]]:
        """读取工作表的完整数据"""
        access_token = self._get_access_token()
        if not access_token:
            return []

        # 如果没有指定范围，智能检测数据范围
        if not range_address:
            max_row, max_col = self._detect_sheet_data_range(
                workbook_id, sheet_id)
            # 将列数转换为字母
            col_letter = chr(ord('A') + max_col - 1)
            range_address = f"A1:{col_letter}{max_row}"
            logger.debug(f"使用范围: {range_address}")

        # 尝试分批读取数据（如果数据量很大）
        if range_address and ':' in range_address:
            try:
                # 解析范围
                start_cell, end_cell = range_address.split(':')

                # 提取行号
                import re
                start_row_match = re.search(r'\d+', start_cell)
                end_row_match = re.search(r'\d+', end_cell)

                if start_row_match and end_row_match:
                    start_row = int(start_row_match.group())
                    end_row = int(end_row_match.group())

                    # 如果数据量很大，分批读取
                    if end_row - start_row > 200:
                        logger.debug(f"分批读取 {end_row - start_row + 1} 行数据")
                        return self._read_sheet_in_batches(workbook_id, sheet_id, range_address)
            except Exception:
                pass  # 如果解析失败，继续使用原来的方法

        # 尝试多种范围格式
        range_formats = [
            range_address,  # 用户指定或检测到的范围
            "A1:Z1000",     # 大范围
            "A1:Z500",      # 中等范围
            "A1:Z100",      # 标准范围
            "A1:J50",       # 较小范围
        ]

        for attempt, current_range in enumerate(range_formats, 1):
            if not current_range:
                continue

            try:
                logger.debug(f"读取范围 {current_range}")

                data = self._read_sheet_range_single(
                    workbook_id, sheet_id, current_range)

                if data:
                    logger.debug(f"读取成功: {current_range}, {len(data)}行")
                    return data
                else:
                    logger.warning(f"范围 {current_range} 返回空数据")

            except Exception as e:
                logger.warning(f"范围 {current_range} 读取失败: {e}")

                # 如果是权限错误，记录详细信息
                if hasattr(e, 'data') and e.data:
                    error_data = e.data
                    if isinstance(error_data, dict):
                        error_code = error_data.get('code', 'unknown')
                        error_msg = error_data.get('message', 'unknown')
                        logger.error(
                            f"详细错误信息 - 代码: {error_code}, 消息: {error_msg}")

                        # 如果是权限问题，不再尝试其他范围
                        if 'permission' in error_code.lower() or 'forbidden' in error_code.lower():
                            logger.error("检测到权限问题，停止尝试其他范围")
                            break

        logger.error("所有范围格式都尝试失败")
        return []

    def _read_sheet_in_batches(self, workbook_id: str, sheet_id: str, full_range: str) -> List[List[str]]:
        """分批读取大型工作表数据"""
        logger.debug(f"分批读取: {full_range}")

        try:
            # 解析完整范围
            start_cell, end_cell = full_range.split(':')

            # 提取列字母和行号
            import re
            start_col_match = re.search(r'[A-Z]+', start_cell)
            start_row_match = re.search(r'\d+', start_cell)
            end_col_match = re.search(r'[A-Z]+', end_cell)
            end_row_match = re.search(r'\d+', end_cell)

            if not all([start_col_match, start_row_match, end_col_match, end_row_match]):
                logger.error("无法解析范围格式，回退到单次读取")
                return self._read_sheet_range_single(workbook_id, sheet_id, full_range)

            start_col = start_col_match.group()
            start_row = int(start_row_match.group())
            end_col = end_col_match.group()
            end_row = int(end_row_match.group())

            # 分批大小（每批100行）
            batch_size = 100
            all_data = []

            current_row = start_row
            batch_num = 1

            while current_row <= end_row:
                batch_end_row = min(current_row + batch_size - 1, end_row)
                batch_range = f"{start_col}{current_row}:{end_col}{batch_end_row}"

                logger.debug(f"批次 {batch_num}: {batch_range}")

                batch_data = self._read_sheet_range_single(
                    workbook_id, sheet_id, batch_range)

                if batch_data:
                    all_data.extend(batch_data)
                    logger.debug(f"批次 {batch_num}: {len(batch_data)}行")
                else:
                    logger.warning(f"第 {batch_num} 批返回空数据，可能已到达数据末尾")
                    break

                current_row = batch_end_row + 1
                batch_num += 1

                # 添加小延迟避免请求过于频繁
                import time
                time.sleep(0.1)

            logger.debug(f"分批读取完成: {len(all_data)}行")
            return all_data

        except Exception as e:
            logger.error(f"分批读取失败: {e}，回退到单次读取")
            return self._read_sheet_range_single(workbook_id, sheet_id, full_range)

    def _try_wiki_api(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """尝试使用知识库API访问文档"""
        access_token = self._get_access_token()
        if not access_token:
            return None

        try:
            logger.debug(f"尝试知识库API: {doc_id}")

            # 尝试获取知识库信息
            headers = dingtalkwiki_2_0_models.GetMineWorkspaceHeaders()
            headers.x_acs_dingtalk_access_token = access_token

            request = dingtalkwiki_2_0_models.GetMineWorkspaceRequest(
                operator_id=self.operator_id
            )

            response = self.wiki_client.get_mine_workspace_with_options(
                request, headers, util_models.RuntimeOptions()
            )

            if response.body and response.body.workspace:
                workspace = response.body.workspace
                logger.debug(f"找到知识库: {workspace.name}")
                return {
                    'type': 'wiki',
                    'workspace_id': workspace.workspace_id,
                    'name': workspace.name,
                    'root_node_id': workspace.root_node_id
                }

            return None

        except Exception as e:
            logger.debug(f"知识库API失败: {e}")
            return None

    def _validate_workbook_access(self, workbook_id: str) -> bool:
        """验证是否可以访问指定的工作簿"""
        try:
            logger.debug(f"验证工作簿访问: {workbook_id}")

            # 首先尝试表格API
            sheets = self._get_workbook_sheets(workbook_id)
            if sheets:
                logger.debug(f"表格API成功: {len(sheets)}个工作表")
                return True

            # 如果表格API失败，尝试知识库API
            logger.debug("表格API失败，尝试知识库API")
            wiki_info = self._try_wiki_api(workbook_id)
            if wiki_info:
                logger.debug(f"知识库API成功: {wiki_info}")
                return True

            logger.warning("所有API访问方式都失败")
            return False

        except Exception as e:
            logger.error(f"工作簿访问验证异常: {e}")
            return False

    def read_urls_from_doc(self, sheet_name: str = 'ALL') -> List[str]:
        """从钉钉文档中读取URL列表"""
        if not self.is_enabled():
            logger.warning("钉钉文档功能未启用或配置不完整")
            return self._fallback_read_from_backup(sheet_name)

        try:
            # 解析文档信息
            doc_info = self.extract_doc_info()
            if not doc_info or not doc_info.get('workbook_id'):
                logger.error("无法解析钉钉文档信息或获取workbook_id")
                return self._fallback_read_from_backup(sheet_name)

            workbook_id = doc_info['workbook_id']
            logger.debug(f"访问工作簿: {workbook_id}")

            # 验证工作簿访问权限
            if not self._validate_workbook_access(workbook_id):
                logger.error("无法访问指定的工作簿，可能是权限问题或workbook_id错误")
                return self._fallback_read_from_backup(sheet_name)

            # 查找指定的工作表
            sheet_id = self._find_sheet_by_name(workbook_id, sheet_name)
            if not sheet_id:
                logger.warning(f"未找到名为 '{sheet_name}' 的工作表")
                # 列出所有可用的工作表
                sheets = self._get_workbook_sheets(workbook_id)
                if sheets:
                    logger.debug(f"可用工作表: {[s['name'] for s in sheets]}")
                return self._fallback_read_from_backup(sheet_name)

            logger.debug(f"找到工作表: {sheet_name}")

            # 读取工作表数据（不指定范围，让系统自动检测完整数据）
            sheet_data = self._read_sheet_range(workbook_id, sheet_id)
            if not sheet_data:
                logger.warning("工作表数据为空")
                return self._fallback_read_from_backup(sheet_name)

            logger.info(f"读取工作表数据: {len(sheet_data)}行")

            # 提取URL - 优化的URL提取逻辑
            urls = []
            url_patterns = [
                'Amazon.com/dp/',
                'Amazon.ca/dp/',
                'Amazon.com/gp/product/',
                'Amazon.ca/gp/product/',
                'Amazon.com/exec/obidos/ASIN/',
                'Amazon.ca/exec/obidos/ASIN/'
            ]

            for row_idx, row in enumerate(sheet_data):
                for col_idx, cell in enumerate(row):
                    if cell and isinstance(cell, str):
                        cell = cell.strip()
                        # 检查是否为Amazon URL
                        if any(pattern in cell for pattern in url_patterns):
                            # 进一步验证URL格式
                            if cell.startswith('http') and len(cell) > 20:
                                urls.append(cell)
                                logger.debug(
                                    f"在位置 ({row_idx+1}, {col_idx+1}) 找到URL: {cell}")

            logger.debug(f"提取到 {len(urls)} 个潜在URL")

            # 统计信息
            if urls:
                Amazon_com_count = sum(
                    1 for url in urls if 'Amazon.com' in url)
                Amazon_ca_count = sum(1 for url in urls if 'Amazon.ca' in url)
                logger.debug(
                    f"URL统计: Amazon.com {Amazon_com_count}, Amazon.ca {Amazon_ca_count}")

            # 去重但保持原有顺序
            urls = self._deduplicate_preserve_order(urls)
            valid_urls = self.validate_urls(urls)

            if valid_urls:
                # 保存备份
                self.save_backup(valid_urls, sheet_name)
                logger.info(f"钉钉文档读取成功: {len(valid_urls)}个URL")
                return valid_urls
            else:
                logger.warning("未从钉钉文档中提取到有效URL")
                return self._fallback_read_from_backup(sheet_name)

        except Exception as e:
            logger.error(f"从钉钉文档读取URL失败: {e}")
            if hasattr(e, 'data') and e.data:
                logger.error(f"错误详情: {e.data}")
            return self._fallback_read_from_backup(sheet_name)

    def _fallback_read_from_backup(self, sheet_name: str) -> List[str]:
        """从备份文件读取数据作为后备方案"""
        logger.debug(f"读取备份文件: {sheet_name}")

        backup_file = f"data/dingtalk_doc_backup_{sheet_name}.json"
        if os.path.exists(backup_file):
            try:
                with open(backup_file, 'r', encoding='utf-8') as f:
                    backup_data = json.load(f)
                    urls = backup_data.get('urls', [])
                    logger.info(f"备份文件读取: {len(urls)}个URL")
                    return urls
            except Exception as e:
                logger.warning(f"读取备份文件失败: {e}")

        # 如果备份文件也不存在，返回空列表
        logger.warning(f"未找到备份文件: {backup_file}")
        return []

    def save_backup(self, urls: List[str], sheet_name: str = 'ALL'):
        """保存URL列表到本地备份文件"""
        try:
            backup_file = f"data/dingtalk_doc_backup_{sheet_name}.json"
            os.makedirs('data', exist_ok=True)

            backup_data = {
                'urls': urls,
                'timestamp': datetime.now().isoformat(),
                'sheet_name': sheet_name,
                'source': 'dingtalk_api'
            }

            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)

            logger.debug(f"保存备份: {len(urls)}个URL")

        except Exception as e:
            logger.error(f"保存备份文件失败: {e}")

    def _deduplicate_preserve_order(self, urls: List[str]) -> List[str]:
        """去重但保持原有顺序"""
        seen = set()
        result = []
        for url in urls:
            if url not in seen:
                seen.add(url)
                result.append(url)
        return result

    def validate_urls(self, urls: List[str]) -> List[str]:
        """验证和清理URL列表，保持原有顺序"""
        valid_urls = []
        seen_urls = set()  # 用于快速查重
        invalid_count = 0

        # 支持的Amazon URL模式
        valid_patterns = [
            r'https?://(?:www\.)?Amazon\.com/dp/[A-Z0-9]{10}',
            r'https?://(?:www\.)?Amazon\.ca/dp/[A-Z0-9]{10}',
            r'https?://(?:www\.)?Amazon\.com/gp/product/[A-Z0-9]{10}',
            r'https?://(?:www\.)?Amazon\.ca/gp/product/[A-Z0-9]{10}',
            r'https?://(?:www\.)?Amazon\.com/exec/obidos/ASIN/[A-Z0-9]{10}',
            r'https?://(?:www\.)?Amazon\.ca/exec/obidos/ASIN/[A-Z0-9]{10}',
        ]

        import re

        for url in urls:
            if not url or not isinstance(url, str):
                continue

            url = url.strip()
            if not url:
                continue

            # 基本格式检查
            if not url.startswith('http'):
                logger.debug(f"跳过非HTTP URL: {url}")
                invalid_count += 1
                continue

            # 检查是否匹配任何有效模式
            is_valid = False
            for pattern in valid_patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    is_valid = True
                    break

            if is_valid:
                # 清理URL（移除多余的查询参数，保留必要的）
                cleaned_url = self._clean_Amazon_url(url)
                # 使用set进行快速查重，但保持列表顺序
                if cleaned_url not in seen_urls:
                    seen_urls.add(cleaned_url)
                    valid_urls.append(cleaned_url)
            else:
                logger.debug(f"跳过无效URL: {url}")
                invalid_count += 1

        logger.info(f"URL验证完成: 有效 {len(valid_urls)} 个, 无效 {invalid_count} 个")
        return valid_urls

    def _clean_Amazon_url(self, url: str) -> str:
        """清理Amazon URL，移除不必要的参数"""
        try:
            from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

            parsed = urlparse(url)

            # 保留的查询参数（如果需要的话）
            keep_params = ['ref', 'tag']  # 可以根据需要调整

            if parsed.query:
                query_params = parse_qs(parsed.query)
                filtered_params = {
                    k: v for k, v in query_params.items() if k in keep_params}

                if filtered_params:
                    new_query = urlencode(filtered_params, doseq=True)
                    cleaned_url = urlunparse((
                        parsed.scheme, parsed.netloc, parsed.path,
                        parsed.params, new_query, ''
                    ))
                else:
                    cleaned_url = urlunparse((
                        parsed.scheme, parsed.netloc, parsed.path,
                        parsed.params, '', ''
                    ))
            else:
                cleaned_url = url

            return cleaned_url

        except Exception as e:
            logger.debug(f"URL清理失败，使用原URL: {e}")
            return url

    def test_connection(self) -> bool:
        """测试钉钉API连接"""
        if not self.is_enabled():
            logger.error("钉钉文档功能未启用或配置不完整")
            return False

        try:
            # 测试获取访问令牌
            access_token = self._get_access_token()
            if not access_token:
                logger.error("钉钉API连接测试失败：无法获取访问令牌")
                return False

            logger.info("成功获取访问令牌")

            # 测试文档URL解析
            doc_info = self.extract_doc_info()
            if not doc_info or not doc_info.get('workbook_id'):
                logger.error("文档URL解析失败")
                return False

            logger.info(f"文档URL解析成功，workbook_id: {doc_info['workbook_id']}")

            # 测试工作簿访问
            workbook_id = doc_info['workbook_id']
            if self._validate_workbook_access(workbook_id):
                logger.info("钉钉API连接测试成功")
                return True
            else:
                logger.error("工作簿访问测试失败")
                return False

        except Exception as e:
            logger.error(f"钉钉API连接测试失败: {e}")
            return False

    def get_document_info(self) -> Dict[str, Any]:
        """获取文档详细信息用于调试"""
        info = {
            'enabled': self.is_enabled(),
            'doc_url': self.doc_url,
            'has_app_key': bool(self.app_key),
            'has_app_secret': bool(self.app_secret),
            'has_operator_id': bool(self.operator_id),
            'access_token_cached': bool(self._access_token),
            'doc_info': None,
            'sheets': [],
            'range_test_results': [],
            'error': None
        }

        try:
            if self.is_enabled():
                # 获取访问令牌
                access_token = self._get_access_token()
                info['has_access_token'] = bool(access_token)

                if access_token:
                    # 解析文档信息
                    doc_info = self.extract_doc_info()
                    info['doc_info'] = doc_info

                    if doc_info and doc_info.get('workbook_id'):
                        # 获取工作表列表
                        sheets = self._get_workbook_sheets(
                            doc_info['workbook_id'])
                        info['sheets'] = sheets

                        # 测试读取第一个工作表的数据
                        if sheets:
                            first_sheet = sheets[0]
                            logger.info(
                                f"测试读取第一个工作表: {first_sheet['name']} (ID: {first_sheet['id']})")

                            # 尝试不同的范围格式
                            test_ranges = ["A1:C10", "A1:A10", "1:5"]
                            for test_range in test_ranges:
                                try:
                                    result = self._read_sheet_range(
                                        doc_info['workbook_id'],
                                        first_sheet['id'],
                                        test_range
                                    )
                                    info['range_test_results'].append({
                                        'range': test_range,
                                        'success': len(result) > 0,
                                        'rows': len(result),
                                        'error': None
                                    })
                                    if result:
                                        logger.info(
                                            f"✅ 范围 {test_range} 测试成功，获取到 {len(result)} 行数据")
                                        break
                                except Exception as range_e:
                                    info['range_test_results'].append({
                                        'range': test_range,
                                        'success': False,
                                        'rows': 0,
                                        'error': str(range_e)
                                    })
                                    logger.warning(
                                        f"❌ 范围 {test_range} 测试失败: {range_e}")

        except Exception as e:
            info['error'] = str(e)
            logger.error(f"获取文档信息时发生错误: {e}")

        return info

    def debug_sheet_access(self, sheet_name: str = 'ALL') -> Dict[str, Any]:
        """调试工作表访问问题"""
        debug_info = {
            'timestamp': datetime.now().isoformat(),
            'sheet_name': sheet_name,
            'steps': [],
            'final_result': None,
            'error': None
        }

        try:
            # 步骤1: 检查基本配置
            debug_info['steps'].append({
                'step': 1,
                'name': '检查基本配置',
                'success': self.is_enabled(),
                'details': {
                    'doc_enabled': self.doc_enabled,
                    'has_doc_url': bool(self.doc_url),
                    'has_app_key': bool(self.app_key),
                    'has_app_secret': bool(self.app_secret),
                    'has_operator_id': bool(self.operator_id)
                }
            })

            if not self.is_enabled():
                debug_info['error'] = '基本配置不完整'
                return debug_info

            # 步骤2: 获取访问令牌
            access_token = self._get_access_token()
            debug_info['steps'].append({
                'step': 2,
                'name': '获取访问令牌',
                'success': bool(access_token),
                'details': {
                    'token_length': len(access_token) if access_token else 0,
                    'token_cached': bool(self._access_token)
                }
            })

            if not access_token:
                debug_info['error'] = '无法获取访问令牌'
                return debug_info

            # 步骤3: 解析文档信息
            doc_info = self.extract_doc_info()
            debug_info['steps'].append({
                'step': 3,
                'name': '解析文档信息',
                'success': bool(doc_info and doc_info.get('workbook_id')),
                'details': doc_info
            })

            if not doc_info or not doc_info.get('workbook_id'):
                debug_info['error'] = '无法解析文档信息'
                return debug_info

            workbook_id = doc_info['workbook_id']

            # 步骤4: 获取工作表列表
            sheets = self._get_workbook_sheets(workbook_id)
            debug_info['steps'].append({
                'step': 4,
                'name': '获取工作表列表',
                'success': len(sheets) > 0,
                'details': {
                    'sheet_count': len(sheets),
                    'sheets': [{'name': s['name'], 'id': s['id']} for s in sheets]
                }
            })

            if not sheets:
                debug_info['error'] = '无法获取工作表列表'
                return debug_info

            # 步骤5: 查找目标工作表
            target_sheet_id = self._find_sheet_by_name(workbook_id, sheet_name)
            debug_info['steps'].append({
                'step': 5,
                'name': f'查找工作表 {sheet_name}',
                'success': bool(target_sheet_id),
                'details': {
                    'target_sheet_name': sheet_name,
                    'found_sheet_id': target_sheet_id
                }
            })

            if not target_sheet_id:
                debug_info['error'] = f'未找到工作表 {sheet_name}'
                return debug_info

            # 步骤6: 尝试读取数据
            sheet_data = self._read_sheet_range(
                workbook_id, target_sheet_id, "A1:Z100")
            debug_info['steps'].append({
                'step': 6,
                'name': '读取工作表数据',
                'success': len(sheet_data) > 0,
                'details': {
                    'data_rows': len(sheet_data),
                    'sample_data': sheet_data[:3] if sheet_data else None
                }
            })

            debug_info['final_result'] = {
                'success': len(sheet_data) > 0,
                'data_rows': len(sheet_data),
                'urls_found': 0
            }

            if sheet_data:
                # 提取URL
                urls = []
                for row in sheet_data:
                    for cell in row:
                        if cell and isinstance(cell, str) and ('Amazon.com' in cell or 'Amazon.ca' in cell):
                            urls.append(cell)

                debug_info['final_result']['urls_found'] = len(urls)
                debug_info['final_result']['sample_urls'] = urls[:3]

        except Exception as e:
            debug_info['error'] = str(e)
            logger.error(f"调试工作表访问时发生错误: {e}")

        return debug_info


# 创建全局实例
dingtalk_doc_reader = DingTalkDocReader()
