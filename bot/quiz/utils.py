# bot/utils.py
from django.utils import timezone
from telebot import TeleBot
from .models import User, GameSession
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging


def check_channel_subscription(bot: TeleBot, user_id: int) -> bool:
    # Здесь должна быть реальная проверка подписки через Telegram API
    # Возвращает True, если пользователь подписан
    try:
        # Пример для канала @test_channel
        chat_member = bot.get_chat_member("@test_channel", user_id)
        return chat_member.status in ["member", "administrator", "creator"]
    except Exception:
        return False


def get_active_session():
    return GameSession.objects.filter(status=GameSession.Status.ACTIVE).first()


def notify_players(session: GameSession, message: str, bot: TeleBot):
    for team in session.teams.all():
        for player in team.user_set.all():
            try:
                bot.send_message(player.telegram_id, message)
            except Exception as e:
                print(f"Ошибка отправки сообщения игроку {player.username}: {e}")


logger = logging.getLogger(__name__)


class SubscriptionManager:
    def __init__(self, channel_username=None, channel_id=None):
        self.channel_username = channel_username
        self.channel_id = channel_id
        self.channel_url = (
            f"https://t.me/{channel_username.lstrip('@')}" if channel_username else None
        )
        logger.info(f"Конструктор  класса, изначально имеем {self.channel_id},{self.channel_url}, {self.channel_username}")

    async def initialize(self, bot):
        """Асинхронная инициализация - получаем ID канала если нужно"""
        logger.info(f"Инициализация класса")
        if self.channel_username and not self.channel_id:
            try:
                chat = await bot.get_chat(self.channel_username)
                self.channel_id = chat.id
                logger.info(f"Автоматически получен ID канала: {self.channel_id}")
            except Exception as e:
                logger.error(f"Ошибка при получении ID канала: {e}")
                raise ValueError(
                    "Не удалось получить ID канала. Проверьте username и права бота."
                )

    async def check_subscription(self, bot, user_id):
        """Асинхронно проверяет, подписан ли пользователь на канал"""
        try:
            if not self.channel_id:
                raise ValueError("Не указан channel_id для проверки подписки")

            chat_member = await bot.get_chat_member(self.channel_id, user_id)
            return chat_member.status in ["member", "administrator", "creator"]
        except Exception as e:
            logger.error(f"Error checking subscription: {e}")
            return False

    async def send_subscription_request(self, chat_id, bot):
        """Асинхронно отправляет сообщение с просьбой подписаться на канал"""
        if not self.channel_url:
            raise ValueError("Не указан channel_url для отправки сообщения")

        markup = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Подписаться на канал", url=self.channel_url)],
                [
                    InlineKeyboardButton(
                        "Я подписался", callback_data="check_subscription"
                    )
                ],
            ]
        )

        await bot.send_message(
            chat_id=chat_id,
            text=f"Для продолжения работы с ботом, пожалуйста, подпишитесь на наш канал: {self.channel_url}",
            reply_markup=markup,
        )



