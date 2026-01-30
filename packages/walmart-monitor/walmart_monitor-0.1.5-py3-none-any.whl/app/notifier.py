import logging
from typing import List, Optional
from .config import settings
from dingtalkchatbot.chatbot import DingtalkChatbot

logger = logging.getLogger(__name__)


class DingTalkNotifier:
    def __init__(self):
        webhook = settings.DINGTALK_WEBHOOK
        secret = settings.DINGTALK_SECRET
        if webhook and secret:
            self.bot = DingtalkChatbot(webhook, secret=secret)
        else:
            self.bot = None
            logger.warning("DingTalk webhook or secret not configured. Skipping initialization.")

        # 解析 @ 指定人员手机号
        self.at_mobiles: List[str] = []
        if settings.DINGTALK_AT_MOBILES:
            self.at_mobiles = [m.strip() for m in settings.DINGTALK_AT_MOBILES.split(",") if m.strip()]

    def send_markdown(self, title: str, text: str, is_at_all: bool = False, at_mobiles: Optional[List[str]] = None):
        """
        发送 Markdown 消息

        Args:
            title: 消息标题
            text: 消息内容
            is_at_all: 是否 @所有人（当配置了 at_mobiles 时会被覆盖）
            at_mobiles: 指定 @ 的手机号列表（优先级：参数 > 环境变量配置）
        """
        if not self.bot:
            logger.warning("DingTalk notifier not initialized. Skipping notification.")
            return

        try:
            # 确定 @ 的目标
            mobiles = at_mobiles or self.at_mobiles

            if mobiles:
                # @ 指定人员
                self.bot.send_markdown(title=title, text=text, at_mobiles=mobiles, is_at_all=False)
            elif is_at_all:
                # @所有人
                self.bot.send_markdown(title=title, text=text, is_at_all=True)
            else:
                # 不 @ 任何人
                self.bot.send_markdown(title=title, text=text, is_at_all=False)
        except Exception as e:
            logger.error(f"Error sending DingTalk message using SDK: {e}")


ding_talk_notifier = DingTalkNotifier()
