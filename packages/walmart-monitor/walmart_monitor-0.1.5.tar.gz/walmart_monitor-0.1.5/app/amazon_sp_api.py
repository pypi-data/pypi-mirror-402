# 亚马逊SP-API客户端
# 此文件将包含与亚马逊SP-API交互的所有逻辑

import time
import csv
import io
import logging
from typing import List

from sp_api.api import Reports
from sp_api.base import SellingApiRequestThrottledException, Marketplaces

logger = logging.getLogger(__name__)

MARKETPLACE_DOMAIN_MAP = {
    "ATVPDKIKX0DER": "com",  # 美国
    "A2EUQ1WTGCTBG2": "ca",  # 加拿大
}


MARKETPLACE_ENUM_MAP = {
    "ATVPDKIKX0DER": Marketplaces.US,  # 美国
    "A2EUQ1WTGCTBG2": Marketplaces.CA,  # 加拿大
    # 未来可在这里扩展其他市场
}


class SpApiClient:
    """亚马逊SP-API客户端，用于处理认证和通信。"""

    def __init__(
        self,
        refresh_token: str,
        lwa_app_id: str,
        lwa_client_secret: str,
        marketplace_id: str,
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None
    ):
        """
        初始化SpApiClient。

        Args:
            refresh_token (str): 刷新令牌。
            lwa_app_id (str): LWA应用程序ID。
            lwa_client_secret (str): LWA客户端密钥。
            marketplace_id (str): 市场ID。
            aws_access_key_id (str | None): AWS访问密钥ID。
            aws_secret_access_key (str | None): AWS秘密访问密钥。
        """
        self.marketplace_id = marketplace_id
        marketplace_enum = MARKETPLACE_ENUM_MAP.get(marketplace_id)
        if not marketplace_enum:
            raise ValueError(f"不支持或无效的 Marketplace ID: {marketplace_id}")

        # 根据 python-Amazon-sp-api 库的文档，直接初始化 Reports API
        credentials = {
            'refresh_token': refresh_token,
            'lwa_app_id': lwa_app_id,
            'lwa_client_secret': lwa_client_secret,
        }

        # 只有在提供了 AWS 凭据时才添加它们
        if aws_access_key_id and aws_secret_access_key:
            credentials['aws_access_key_id'] = aws_access_key_id
            credentials['aws_secret_access_key'] = aws_secret_access_key

        # 直接初始化 Reports API，不需要单独的 Client
        self.reports_api = Reports(
            credentials=credentials,
            marketplace=marketplace_enum
        )

    def get_all_listings_report(self) -> List[str]:
        """
        创建、下载并解析GET_MERCHANT_LISTINGS_ALL_DATA报告，提取所有ASIN。

        Returns:
            List[str]: 从报告中提取的ASIN列表。

        Raises:
            Exception: 当报告创建或处理失败时抛出异常。
        """
        try:
            # 1. 创建报告
            response = self.reports_api.create_report(
                reportType='GET_MERCHANT_LISTINGS_ALL_DATA',
                marketplaceIds=[self.marketplace_id]
            )
            report_id = response.payload['reportId']
            logger.info(f"报告创建成功，报告ID: {report_id}")

            # 2. 轮询报告状态
            while True:
                report_status_response = self.reports_api.get_report(report_id)
                status = report_status_response.payload['processingStatus']

                logger.info(f"报告 {report_id} 当前状态: {status}")

                if status == 'DONE':
                    report_document_id = report_status_response.payload['reportDocumentId']
                    break
                elif status in ['CANCELLED', 'FATAL']:
                    raise Exception(f"报告处理失败，状态为: {status}")

                # 等待60秒后再次检查
                time.sleep(60)

            # 3. 下载并解析报告
            logger.info(f"开始下载报告文档: {report_document_id}")
            download_response = self.reports_api.get_report_document(report_document_id)

            # 获取报告内容 - 可能是 'document' 或 'url'
            if 'document' in download_response.payload:
                report_content = download_response.payload['document']
            elif 'url' in download_response.payload:
                # 如果返回的是URL，需要额外下载
                import requests
                url = download_response.payload['url']
                response = requests.get(url)
                report_content = response.content
            else:
                raise Exception("无法找到报告内容字段")

            # 如果是字节类型，解码为字符串
            if isinstance(report_content, bytes):
                report_content = report_content.decode('cp1252')
            elif not isinstance(report_content, str):
                report_content = str(report_content)

            # 使用csv模块解析TSV内容
            asins: List[str] = []
            # 使用io.StringIO将字符串转换为文件对象
            reader = csv.DictReader(io.StringIO(report_content), delimiter='\t')

            # 打印前几行来查看可用字段
            rows = list(reader)
            if rows:
                logger.info(f"报告中可用的字段: {list(rows[0].keys())}")

                # 重新创建reader
                reader = csv.DictReader(io.StringIO(report_content), delimiter='\t')

                for row in reader:
                    # 检查商品状态，只包含活跃商品
                    status = row.get('status', '').lower()
                    if status not in ['active', 'buyable']:
                        continue  # 跳过非活跃商品

                    # 优先使用 ASIN，如果没有则使用其他标识符
                    asin = None
                    if 'asin1' in row and row['asin1']:
                        asin = row['asin1']
                    elif 'ASIN' in row and row['ASIN']:
                        asin = row['ASIN']
                    elif 'asin' in row and row['asin']:
                        asin = row['asin']

                    # 只添加有效的ASIN（通常以B开头，10位字符）
                    if asin and len(asin) == 10 and asin.startswith('B'):
                        asins.append(asin)

            # 去重ASIN
            unique_asins = list(set(asins))
            logger.info(f"成功解析报告，共找到 {len(asins)} 个ASIN，去重后 {len(unique_asins)} 个。")
            return unique_asins

        except SellingApiRequestThrottledException as e:
            logger.warning(f"请求被限制，等待 {e.rate_limit} 秒后重试...")
            time.sleep(e.rate_limit)
            return self.get_all_listings_report()  # 重试
        except Exception as e:
            logger.error(f"获取所有在售商品报告时发生错误: {e}")
            raise


from app.config import load_store_configs


async def get_all_product_urls() -> List[str]:
    """
    加载所有店铺配置，获取每个店铺的所有商品ASIN，并转换为完整的URL。

    Returns:
        List[str]: 所有店铺的商品URL列表。
    """
    all_urls = []
    store_configs = load_store_configs()

    if not store_configs:
        logger.warning("警告: 未加载到任何店铺配置。")
        return []

    for config in store_configs:
        logger.info(f"开始处理店铺: {config['name']}")
        client = SpApiClient(
            refresh_token=config['refresh_token'],
            lwa_app_id=config['lwa_app_id'],
            lwa_client_secret=config['lwa_client_secret'],
            marketplace_id=config['marketplace_id'],
            aws_access_key_id=config.get('aws_access_key_id'),
            aws_secret_access_key=config.get('aws_secret_access_key')
        )

        try:
            asins = client.get_all_listings_report()
            # 根据Marketplace ID构建基础URL
            domain = MARKETPLACE_DOMAIN_MAP.get(config['marketplace_id'], 'com')  # 默认为.com
            base_url = f"https://www.Amazon.{domain}/dp/"

            store_urls = [f"{base_url}{asin}" for asin in asins]
            logger.info(f"店铺 {config['name']} 成功获取 {len(store_urls)} 个URL。")
            all_urls.extend(store_urls)
        except Exception as e:
            logger.error(f"处理店铺 {config['name']} 时发生错误: {e}")
            # 选择继续处理下一个店铺
            continue

    return list(set(all_urls))  # 返回去重后的URL列表
