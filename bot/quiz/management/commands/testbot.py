from django.core.management.base import BaseCommand
import telebot
from django.conf import settings


class Command(BaseCommand):
    """Это тестовый бот"""

    help = "Telegram Bot"

    def handle(self, *args, **options):
        bot = telebot.TeleBot(settings.TELEGRAM_BOT_TOKEN)

        @bot.message_handler(func=lambda m: True)
        def echo_all(message):
            text = message.text
            if text == "/start":
                bot.reply_to(message, "Привет! Я бот.")
            else:
                bot.reply_to(message, text)

        bot.polling()
