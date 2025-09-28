from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import logging
from telegram import Update
from telegram.ext import Application, ContextTypes
from django.conf import settings
# ver 1.0.0 главный файл - не просмотрено
logger = logging.getLogger(__name__)

# Глобальная переменная для приложения
application = None


async def initialize_bot():
    """Инициализация бота"""
    global application

    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

    # Настройка обработчиков
    from .handlers import setup_handlers
    from .owner_handlers import setup_owner_handlers
    from .admin_handlers import setup_admin_handlers

    setup_handlers(application)
    setup_owner_handlers(application)
    setup_admin_handlers(application)

    # Установка webhook
    await application.bot.set_webhook(settings.WEBHOOK_URL)


@csrf_exempt
@require_POST
async def webhook(request):
    """Обработчик webhook"""
    try:
        global application

        if application is None:
            await initialize_bot()

        # Парсим обновление
        update_data = json.loads(request.body.decode('utf-8'))
        update = Update.de_json(update_data, application.bot)

        # Обрабатываем обновление
        await application.process_update(update)

        return JsonResponse({'status': 'ok'})

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)})