from telegram import Bot, Update
from telegram.ext import ContextTypes

BOTKEY = "7621275052:AAG5MQrncyMPlTsWflFFPSoeMrM2uybf0kQ"

CHAT_ID = "-1003013655526"


class TelegramBot:
    def __init__(self, bot_key: str = BOTKEY, chat_id: str = CHAT_ID):
        self.bot = Bot(token=bot_key)
        self.chat_id = chat_id

    async def hello(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:  # noqa: ARG002
        await update.message.reply_text(f"Hello {update.effective_user.first_name}")

    async def send_startup_message(self) -> None:
        await self.bot.send_message(
            chat_id=self.chat_id,
            message_thread_id=4,
            text="This is an automated message. Bot has started!",
        )

    async def notify_new_ticker(self, ticker: str, pct_change: float) -> None:
        await self.bot.send_message(
            chat_id=self.chat_id,
            message_thread_id=4,
            text=f"New ticker detected: {ticker} with change {pct_change}%",
        )
