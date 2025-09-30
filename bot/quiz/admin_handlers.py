import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
#from django.utils import timezone
from .models import User, Team
from .keyboards import get_admin_keyboard, get_user_selection_keyboard, get_team_selection_keyboard
from .messages import *
# ver 1.0.0 из дипсик не проверено
logger = logging.getLogger(__name__)


async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню администратора"""
    telegram_id = update.effective_user.id

    try:
        user = await User.objects.aget(telegram_id=telegram_id)
        if user.role not in [User.Role.ADMIN, User.Role.OWNER]:
            await update.message.reply_text(NO_RIGHTS)
            return

        await update.message.reply_text(
            "Меню администратора:",
            reply_markup=get_admin_keyboard()
        )

    except User.DoesNotExist:
        await update.message.reply_text(USER_NOT_FOUND)


async def create_team(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Создание новой команды"""
    telegram_id = update.effective_user.id

    try:
        admin = await User.objects.aget(telegram_id=telegram_id)
        if admin.role not in [User.Role.ADMIN, User.Role.OWNER]:
            await update.message.reply_text(NO_RIGHTS_OPERATION)
            return

        # Сохраняем действие в context для следующего шага
        context.user_data['action'] = 'create_team'
        await update.message.reply_text("Введите название новой команды:")

    except User.DoesNotExist:
        await update.message.reply_text(USER_NOT_FOUND)


async def handle_team_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода названия команды"""
    try:
        team_name = update.message.text.strip()
        telegram_id = update.effective_user.id

        admin = await User.objects.aget(telegram_id=telegram_id)

        # Создаем команду
        team = await Team.objects.acreate(
            name=team_name,
            created_by=admin
        )

        await update.message.reply_text(f"Команда '{team_name}' создана успешно!")

        # Очищаем context
        context.user_data.pop('action', None)

    except Exception as e:
        logger.error(f"Error creating team: {e}")
        await update.message.reply_text(ERROR_OCCURRED)


async def distribute_players(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Распределение игроков по командам"""
    telegram_id = update.effective_user.id

    try:
        admin = await User.objects.aget(telegram_id=telegram_id)
        if admin.role not in [User.Role.ADMIN, User.Role.OWNER]:
            await update.message.reply_text(NO_RIGHTS_OPERATION)
            return

        # Получаем игроков без команды
        players_without_team = User.objects.filter(
            role=User.Role.PLAYER,
            team__isnull=True
        )

        if not await players_without_team.aexists():
            await update.message.reply_text("Нет игроков без команды для распределения.")
            return

        # Получаем все команды
        teams = Team.objects.all()

        if not await teams.aexists():
            await update.message.reply_text("Сначала создайте команды.")
            return

        await update.message.reply_text(
            "Выберите команду для распределения игроков:",
            reply_markup=await get_team_selection_keyboard(teams)
        )

        context.user_data['action'] = 'select_team_for_distribution'

    except User.DoesNotExist:
        await update.message.reply_text(USER_NOT_FOUND)


async def check_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка вопросов от игроков"""
    telegram_id = update.effective_user.id

    try:
        admin = await User.objects.aget(telegram_id=telegram_id)
        if admin.role not in [User.Role.ADMIN, User.Role.OWNER]:
            await update.message.reply_text(NO_RIGHTS_OPERATION)
            return

        # Получаем непроверенные вопросы
        from .models import Question
        unanswered_questions = Question.objects.filter(is_approved=False)

        if not await unanswered_questions.aexists():
            await update.message.reply_text("Нет вопросов для проверки.")
            return

        # Здесь можно реализовать постраничный просмотр вопросов
        question = await unanswered_questions.afirst()
        await update.message.reply_text(
            f"Вопрос от {question.created_by.username}:\n\n"
            f"{question.text}\n\n"
            f"Правильный ответ: {question.correct_answer}\n\n"
            "Одобрить вопрос? (Да/Нет)"
        )

        context.user_data['current_question_id'] = question.id

    except User.DoesNotExist:
        await update.message.reply_text(USER_NOT_FOUND)


async def handle_question_approval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка одобрения/отклонения вопроса"""
    try:
        response = update.message.text.lower()
        question_id = context.user_data.get('current_question_id')

        if not question_id:
            await update.message.reply_text("Сессия проверки вопроса истекла.")
            return

        from .models import Question
        question = await Question.objects.aget(id=question_id)

        if response == 'да':
            question.is_approved = True
            await question.asave()
            await update.message.reply_text("Вопрос одобрен!")
        elif response == 'нет':
            await question.adelete()
            await update.message.reply_text("Вопрос отклонен и удален.")
        else:
            await update.message.reply_text("Пожалуйста, ответьте 'Да' или 'Нет'.")
            return

        # Очищаем context
        context.user_data.pop('current_question_id', None)

    except Question.DoesNotExist:
        await update.message.reply_text("Вопрос не найден.")
    except Exception as e:
        logger.error(f"Error handling question approval: {e}")
        await update.message.reply_text(ERROR_OCCURRED)


async def summarize_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подведение итогов игры"""
    telegram_id = update.effective_user.id

    try:
        admin = await User.objects.aget(telegram_id=telegram_id)
        if admin.role not in [User.Role.ADMIN, User.Role.OWNER]:
            await update.message.reply_text(NO_RIGHTS_OPERATION)
            return

        from .models import GameSession
        # Получаем активную игровую сессию
        active_session = await GameSession.objects.filter(status=GameSession.Status.ACTIVE).afirst()

        if not active_session:
            await update.message.reply_text("Нет активной игровой сессии.")
            return

        # Подсчитываем результаты
        scores = await active_session.calculate_scores()

        # Формируем сообщение с результатами
        result_message = "Итоги игры:\n\n"
        for team_name, score in scores.items():
            result_message += f"{team_name}: {score} баллов\n"

        await update.message.reply_text(result_message)

        # Завершаем сессию
        active_session.finish_session()
        await active_session.asave()

    except User.DoesNotExist:
        await update.message.reply_text(USER_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error summarizing results: {e}")
        await update.message.reply_text(ERROR_OCCURRED)


def setup_admin_handlers(application):
    """Настройка обработчиков администратора"""
    application.add_handler(CommandHandler('admin', admin_menu))
    application.add_handler(CommandHandler('create_team', create_team))
    application.add_handler(CommandHandler('distribute', distribute_players))
    application.add_handler(CommandHandler('check_questions', check_questions))
    application.add_handler(CommandHandler('summarize', summarize_results))

    # Обработчики для кнопок меню
    application.add_handler(MessageHandler(
        filters.Regex(f'^{BUTTON_CREATE_TEAM}$'),
        create_team
    ))
    application.add_handler(MessageHandler(
        filters.Regex(f'^{BUTTON_DISTRIBUTE_PLAYERS}$'),
        distribute_players
    ))
    application.add_handler(MessageHandler(
        filters.Regex(f'^{BUTTON_CHECK_QUESTIONS}$'),
        check_questions
    ))
    application.add_handler(MessageHandler(
        filters.Regex(f'^{BUTTON_SUMMARIZE}$'),
        summarize_results
    ))

    # Обработчики для текстовых ответов
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_general_text
    ))


async def handle_general_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Общий обработчик текстовых сообщений для админских действий"""
    action = context.user_data.get('action')

    if action == 'create_team':
        await handle_team_creation(update, context)
    elif action == 'select_team_for_distribution':
        await handle_team_distribution(update, context)
    # Можно добавить другие действия