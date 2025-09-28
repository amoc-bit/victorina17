# Тексты сообщений для Telegram бота
# ver 1.1.0 добавлены сообщения администратора
# Общие сообщения
WELCOME = "Добро пожаловать! Пожалуйста, введите ваше имя:"
WELCOME_BACK = "С возвращением, {username}!"
ERROR_OCCURRED = "Произошла ошибка. Попробуйте позже."
USER_NOT_FOUND = "Пользователь не найден."
OPERATION_CANCELLED = "Операция отменена."
NO_RIGHTS = "У вас нет прав для доступа к этому меню."
NO_RIGHTS_OPERATION = "У вас нет прав для этой операции."

# Сообщения подписки на канал
CHANNEL_SUBSCRIPTION_REQUIRED = (
    "Для использования бота необходимо подписаться на наш канал.\n"
    "Подпишитесь здесь: {channel_url}\n"
    "После подписки отправьте /start снова."
)

# Сообщения регистрации
REGISTRATION_COMPLETE = (
    "Спасибо, {name}! Ваши данные сохранены.\n"
    "Произойдет назначение вашей роли в игре и распределение в команду. "
    "Ожидайте отдельного сообщения об этом."
)

# Уведомления для администраторов
NEW_USER_NOTIFICATION = "Новый пользователь: {username} (ID: {telegram_id})"

# Сообщения владельца
OWNER_MENU_TITLE = "Меню владельца:"
NO_ACTIVE_PLAYERS = "Нет активных игроков сегодня."
SELECT_USER_FOR_ADMIN = "Выберите пользователя для назначения администратором:"
ADMIN_ASSIGNED = "Пользователь {username} назначен администратором."
NEW_ADMIN_NOTIFICATION = "Поздравляем! Вы были назначены администратором игры."

# Тексты кнопок
BUTTON_ASSIGN_ADMIN = "Назначить администратора"
BUTTON_MANAGE_TEAMS = "Управление командами"
BUTTON_VIEW_STATS = "Просмотр статистики"
BUTTON_END_GAME = "Завершить игру"
BUTTON_CREATE_TEAM = "Создать команду"
BUTTON_DISTRIBUTE_PLAYERS = "Распределить игроков"
BUTTON_CHECK_QUESTIONS = "Проверить вопросы"
BUTTON_SUMMARIZE = "Подвести итоги"
BUTTON_ASK_QUESTION = "Задать вопрос"
BUTTON_ANSWER_QUESTION = "Ответить на вопрос"
BUTTON_MY_STATS = "Моя статистика"

# Сообщения администратора
ADMIN_MENU_TITLE = "Меню администратора:"
NO_ACTIVE_SESSION = "Нет активной игровой сессии."
NO_UNANSWERED_QUESTIONS = "Нет вопросов для проверки."
NO_PLAYERS_WITHOUT_TEAM = "Нет игроков без команды для распределения."
NO_TEAMS_CREATED = "Сначала создайте команды."
TEAM_CREATED = "Команда '{team_name}' создана успешно!"
QUESTION_APPROVED = "Вопрос одобрен!"
QUESTION_REJECTED = "Вопрос отклонен и удален."

# Тексты для обработки вопросов
APPROVE_QUESTION_PROMPT = (
    "Вопрос от {username}:\n\n"
    "{question_text}\n\n"
    "Правильный ответ: {correct_answer}\n\n"
    "Одобрить вопрос? (Да/Нет)"
)