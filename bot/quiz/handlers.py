import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler
)
from telegram.ext import Application
from django.utils import timezone
from .models import User
from .keyboards import get_main_menu
from .utils import SubscriptionManager
from .messages import *



# ver 1.0.0 от дипсик, просмотрено не запускалось  Регистрация пользователя. Подписывает пользователя на канал/
logger = logging.getLogger(__name__)
logger.info(f'the module {__name__} running')

# States для ConversationHandler
GETTING_NAME = 1

subscription_manager = SubscriptionManager(
    channel_username="@v_e_c_tor"  # Бот автоматически получит ID
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    telegram_id = update.effective_user.id
    #user_id= telegram_id
    username = update.effective_user.username or update.effective_user.first_name
    is_subscribed = await subscription_manager.check_subscription(
        context.bot,  # передаем bot как параметр
        update.effective_user.id
        )
    if not is_subscribed:
        await subscription_manager.send_subscription_request(
            update.effective_chat.id,
            context.bot  # передаем bot как параметр
        )
        await update.message.reply_text(
                CHANNEL_SUBSCRIPTION_REQUIRED.format(
                    channel_url=context.bot_data.get('channel_url'))





    # Проверяем существование пользователя
    user, created = await User.objects.aget_or_create(
        telegram_id=telegram_id,
        defaults={
            'username': username,
            'last_activity': timezone.now()
        }
    )

    if not created:
        # Сценарий 2: Обновление данных существующего пользователя
        user.last_activity = timezone.now()
        await user.asave()
        await update.message.reply_text(
            WELCOME_BACK.format(username=user.username),
            reply_markup=await get_main_menu(user)
        )
    else:
        # Сценарий 1: Новый пользователь
        await update.message.reply_text(WELCOME)
        return GETTING_NAME

    except Exception as e:
        logger.error(f"Error in start handler: {e}")
        await update.message.reply_text(ERROR_OCCURRED)


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение имени пользователя"""
    name = update.message.text.strip()
    telegram_id = update.effective_user.id

    try:
        user = await User.objects.aget(telegram_id=telegram_id)
        user.username = name
        await user.asave()

        await update.message.reply_text(
            REGISTRATION_COMPLETE.format(name=name),
            reply_markup=ReplyKeyboardRemove()
        )

        # Уведомление администраторов о новом пользователе
        await notify_admins_about_new_user(context.bot, user)

        return ConversationHandler.END

    except User.DoesNotExist:
        await update.message.reply_text(USER_NOT_FOUND)
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Error in get_name handler: {e}")
        await update.message.reply_text(ERROR_OCCURRED)
        return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена операции"""
    await update.message.reply_text(
        OPERATION_CANCELLED,
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


async def notify_admins_about_new_user(bot, user):
    """Уведомление администраторов о новом пользователе"""
    try:
        admins = User.objects.filter(role__in=[User.Role.ADMIN, User.Role.OWNER])
        async for admin in admins:
            try:
                await bot.send_message(
                    chat_id=admin.telegram_id,
                    text=NEW_USER_NOTIFICATION.format(
                        username=user.username,
                        telegram_id=user.telegram_id
                    )
                )
            except Exception as e:
                logger.error(f"Error sending notification to admin {admin.telegram_id}: {e}")
    except Exception as e:
        logger.error(f"Error in notify_admins_about_new_user: {e}")


def setup_handlers(application):
    """Настройка обработчиков"""
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            GETTING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)