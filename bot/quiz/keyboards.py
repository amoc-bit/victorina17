from telegram import ReplyKeyboardMarkup
from .models import User
from .messages import *

def get_admin_keyboard():
    """Клавиатура администратора"""
    return ReplyKeyboardMarkup([
        [BUTTON_CREATE_TEAM, BUTTON_DISTRIBUTE_PLAYERS],
        [BUTTON_CHECK_QUESTIONS, BUTTON_SUMMARIZE]
    ], resize_keyboard=True)

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