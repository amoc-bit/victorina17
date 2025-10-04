from django.core.management.base import BaseCommand
from django.conf import settings
import logging
import asyncio
import os
import sys
from telegram import Update
from telegram.ext import Application, ContextTypes
from telegram.ext import filters, MessageHandler, CommandHandler

# Добавляем корневую директорию проекта в Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(project_root)

logger = logging.getLogger(__name__)
logger.info(f'the module {__name__} running')

class Command(BaseCommand):
    help = 'Запуск Telegram бота в режиме long polling'
    
    def handle(self, *args, **options):
        """Основной метод запуска бота"""
        asyncio.run(self.main())

    async def main(self):
        """Асинхронная инициализация и запуск бота"""
        self.stdout.write(
            self.style.SUCCESS('Запуск Telegram бота...')
        )
        
        # Создаем приложение бота
        application = (
            Application.builder()
            .token(settings.TELEGRAM_BOT_TOKEN)
            .build()
        )

        # Настройка обработчиков
        await self.setup_handlers(application)
        
        # Запуск long polling
        await self.run_polling(application)

    async def setup_handlers(self, application):
        """Настройка всех обработчиков команд"""
        try:
            # Импортируем обработчики
            from quiz.handlers import setup_handlers
            from quiz.owner_handlers import setup_owner_handlers
            from quiz.admin_handlers import setup_admin_handlers

            # Настраиваем обработчики
            setup_handlers(application)
            setup_owner_handlers(application)
            setup_admin_handlers(application)
            
            self.stdout.write(
                self.style.SUCCESS('Все обработчики успешно настроены')
            )
            
        except Exception as e:
            logger.error(f"Ошибка настройки обработчиков: {e}")
            self.stderr.write(
                self.style.ERROR(f'Ошибка настройки обработчиков: {e}')
            )

    async def run_polling(self, application):
        """Запуск long polling"""
        try:
            self.stdout.write(
                self.style.SUCCESS('Бот запущен в режиме long polling')
            )
            self.stdout.write(
                self.style.WARNING('Для остановки нажмите Ctrl+C')
            )
            
            # Запускаем long polling
            await application.initialize()
            await application.start()
            await application.updater.start_polling(
                poll_interval=1.0,  # Интервал опроса в секундах
                timeout=10,         # Таймаут запроса
                drop_pending_updates=True  # Пропустить ожидающие обновления
            )
            
            # Бесконечный цикл (до ручной остановки)
            while True:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('Остановка бота...')
            )
        except Exception as e:
            logger.error(f"Ошибка в работе бота: {e}")
            self.stderr.write(
                self.style.ERROR(f'Ошибка в работе бота: {e}')
            )
        finally:
            # Корректное завершение работы
            await self.shutdown_bot(application)

    async def shutdown_bot(self, application):
        """Корректное завершение работы бота"""
        try:
            if application.updater:
                await application.updater.stop()
            if application:
                await application.stop()
                await application.shutdown()
            self.stdout.write(
                self.style.SUCCESS('Бот успешно остановлен')
            )
        except Exception as e:
            logger.error(f"Ошибка при остановке бота: {e}")