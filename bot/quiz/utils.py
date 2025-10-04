# bot/utils.py
from django.utils import timezone
from telebot import TeleBot
from .models import User, GameSession

def check_channel_subscription(bot: TeleBot, user_id: int) -> bool:
    # Здесь должна быть реальная проверка подписки через Telegram API
    # Возвращает True, если пользователь подписан
    try:
        # Пример для канала @test_channel
        chat_member = bot.get_chat_member("@test_channel", user_id)
        return chat_member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False

def get_active_session():
    return GameSession.objects.filter(
        status=GameSession.Status.ACTIVE
    ).first()

def notify_players(session: GameSession, message: str, bot: TeleBot):
    for team in session.teams.all():
        for player in team.user_set.all():
            try:
                bot.send_message(player.telegram_id, message)
            except Exception as e:
                print(f"Ошибка отправки сообщения игроку {player.username}: {e}")

class SubscriptionManager:

    def __init__(self, channel_username=None, channel_id=None):
        self.channel_username = channel_username
        self.channel_id = channel_id
        self.channel_url = f"https://t.me/{channel_username.lstrip('@')}" if channel_username else None

        # Если передан username, но не передан ID - получаем ID автоматически
        if channel_username and not channel_id:
            try:
                chat = bot.get_chat(channel_username)
                self.channel_id = chat.id
                #print(f"Автоматически получен ID канала: {self.channel_id}")
            except Exception as e:
                #print(f"Ошибка при получении ID канала: {e}")
                raise ValueError("Не удалось получить ID канала. Проверьте username и права бота.")

    def check_subscription(self, user_id):
        """Проверяет, подписан ли пользователь на канал"""
        try:
            if not self.channel_id:
                raise ValueError("Не указан channel_id для проверки подписки")

            chat_member = bot.get_chat_member(self.channel_id, user_id)
            return chat_member.status in ['member', 'administrator', 'creator']
        except Exception as e:
            logger.error(f"Error checking subscription: {e}")
            #print(f"Error checking subscription: {e}")
            return False

    def send_subscription_request(self, chat_id):
        """Отправляет сообщение с просьбой подписаться на канал"""
        if not self.channel_url:
            raise ValueError("Не указан channel_url для отправки сообщения")

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Подписаться на канал", url=self.channel_url))
        markup.add(types.InlineKeyboardButton("Я подписался", callback_data='check_subscription'))

        bot.send_message(
            chat_id,
            f"Для продолжения работы с ботом, пожалуйста, подпишитесь на наш канал: {self.channel_url}",
            reply_markup=markup
        )

sub_manager = SubscriptionManager(
    channel_username='@v_e_c_tor'  # Бот автоматически получит ID
)