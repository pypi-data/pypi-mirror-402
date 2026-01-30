import logging
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

    def send_markdown(self, title, text, is_at_all=False):
        if not self.bot:
            logger.warning("DingTalk notifier not initialized. Skipping notification.")
            return

        try:
            self.bot.send_markdown(title=title, text=text, is_at_all=is_at_all)
        except Exception as e:
            logger.error(f"Error sending DingTalk message using SDK: {e}")


ding_talk_notifier = DingTalkNotifier()
