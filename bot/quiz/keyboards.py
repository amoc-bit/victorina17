from telegram import ReplyKeyboardMarkup
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton
from .models import User
from .messages import *


def get_main_menu(role):

    if role == User.Role.OWNER:
        markup = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton("Назначить администратора"),
                    KeyboardButton("Установить группу"),
                ]
            ],
            resize_keyboard=True,
        )

    elif role == User.Role.ADMIN:
        markup = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton("Создать команду"), KeyboardButton("Создать сессию")]
            ],
            resize_keyboard=True,
        )

    elif role == User.Role.PLAYER:
        markup = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton("Задать вопрос")]], resize_keyboard=True
        )
    else:
        markup = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton("Помощь")]], resize_keyboard=True
        )

    return markup


def get_users_keyboard(users, action_prefix):
    markup = InlineKeyboardMarkup()
    for user in users:
        markup.add(
            InlineKeyboardButton(
                user.username, callback_data=f"{action_prefix}_{user.id}"
            )
        )
    return markup


def get_teams_keyboard(teams, action_prefix, user_id=None):
    markup = InlineKeyboardMarkup()
    for team in teams:
        callback_data = f"{action_prefix}_{team.id}"
        if user_id:
            callback_data += f"_{user_id}"
        markup.add(InlineKeyboardButton(team.name, callback_data=callback_data))
    return markup


def get_confirmation_keyboard(action_prefix, object_id):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("Да", callback_data=f"confirm_{action_prefix}_{object_id}")
    )
    markup.add(InlineKeyboardButton("Нет", callback_data="cancel"))
    return markup


def get_admin_keyboard():
    """Клавиатура администратора"""
    return ReplyKeyboardMarkup(
        [
            [BUTTON_CREATE_TEAM, BUTTON_DISTRIBUTE_PLAYERS],
            [BUTTON_CHECK_QUESTIONS, BUTTON_SUMMARIZE],
        ],
        resize_keyboard=True,
    )


async def get_user_selection_keyboard(users_query):
    """Клавиатура для выбора пользователей"""
    users = []
    async for user in users_query:
        users.append([user.username])

    return ReplyKeyboardMarkup(users, resize_keyboard=True) if users else None


async def get_team_selection_keyboard(teams_query):
    """Клавиатура для выбора команд"""
    teams = []
    async for team in teams_query:
        teams.append([team.name])

    return ReplyKeyboardMarkup(teams, resize_keyboard=True) if teams else None
