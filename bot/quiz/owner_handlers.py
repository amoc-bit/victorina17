import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from django.utils import timezone
from .models import User
from .keyboards import get_admin_keyboard, get_user_selection_keyboard
from .messages import *
# ver1.0.0 Добавленг не проверено
logger = logging.getLogger(__name__)


async def owner_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню владельца"""
    telegram_id = update.effective_user.id

    try:
        user = await User.objects.aget(telegram_id=telegram_id)
        if user.role != User.Role.OWNER:
            await update.message.reply_text(NO_RIGHTS)
            return

        await update.message.reply_text(
            OWNER_MENU_TITLE,
            reply_markup=get_admin_keyboard()
        )

    except User.DoesNotExist:
        await update.message.reply_text(USER_NOT_FOUND)


async def assign_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Назначение администратора"""
    telegram_id = update.effective_user.id

    try:
        owner = await User.objects.aget(telegram_id=telegram_id)
        if owner.role != User.Role.OWNER:
            await update.message.reply_text(NO_RIGHTS_OPERATION)
            return

        # Получаем пользователей для назначения (только игроки)
        today = timezone.now().date()
        users = User.objects.filter(
            role=User.Role.PLAYER,
            last_activity__date=today
        )

        if not await users.aexists():
            await update.message.reply_text(NO_ACTIVE_PLAYERS)
            return

        await update.message.reply_text(
            SELECT_USER_FOR_ADMIN,
            reply_markup=await get_user_selection_keyboard(users)
        )

    except User.DoesNotExist:
        await update.message.reply_text(USER_NOT_FOUND)


async def handle_admin_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора пользователя для назначения администратором"""
    try:
        selected_username = update.message.text
        user = await User.objects.aget(username=selected_username)

        user.role = User.Role.ADMIN
        await user.asave()

        await update.message.reply_text(
            ADMIN_ASSIGNED.format(username=user.username)
        )

        # Уведомляем назначенного пользователя
        try:
            await context.bot.send_message(
                chat_id=user.telegram_id,
                text=NEW_ADMIN_NOTIFICATION
            )
        except Exception as e:
            logger.error(f"Error notifying new admin: {e}")

    except User.DoesNotExist:
        await update.message.reply_text(USER_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error in handle_admin_selection: {e}")
        await update.message.reply_text(ERROR_OCCURRED)


def setup_owner_handlers(application):
    """Настройка обработчиков владельца"""
    application.add_handler(CommandHandler('owner', owner_menu))
    application.add_handler(CommandHandler('assign_admin', assign_admin))
    application.add_handler(MessageHandler(
        filters.Regex(f'^{BUTTON_ASSIGN_ADMIN}$'),
        assign_admin
    ))