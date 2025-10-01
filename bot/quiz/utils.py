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