import telebot
from telebot import types
import datetime
from datetime import datetime
import csv
import logging

from django.core.management.base import BaseCommand
from django.conf import settings
from bot1.models import Userdata
#from bot1.models import Searchinfo
import MySQLdb

# VER 1.5.0 рабочая версия с сайта - начата переделка   -  убрали размещение вакансий ? начата настройка логирования
# проверено - 1 - почему-то сразу не проверят, когда старт, - исправлено 2- какая-то ошибка, не крит , ищет мессадж
# Добавили show_main_menu, убрали 3 кнопку - не загружено, Проверено - размещение не убралось

# Добавлено загрузка ключа через сеттинг


logger = logging.getLogger(__name__)  # или logging.getLogger('myapp')

logger.info(f'the module {__name__} running')
#API_TOKEN = '7858669391:AAGJAteq_rikBoY0VDHcUtyT9Lhd9H6XVDo'- для проверки 
#API_TOKEN =settings.TRY_TOKEN


#API_TOKEN = '6468921905:AAGv-ZS8pJSCZOYJMLrU6hfLOd-z_hrrrqI'
API_TOKEN = settings.TELEGRAM_BOT_API_KEY


bot = telebot.TeleBot(API_TOKEN)

users = {}

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



class Filemanager():

    def change_city_choice(message, sity_choice, filename='user_data.csv'):
        user_id = message.from_user.id
        column_to_find_row = 'user_id'
        column_to_update = 'sity_choice'

        rows = []
        file = open(filename, mode="r", newline='', encoding='utf-8')
        reader = csv.DictReader(file)
        for row in reader:
            if int(row[column_to_find_row]) == user_id:
                row[column_to_update] = str(sity_choice)
            rows.append(row)
        file.close()
        file = open(filename, mode="w", newline='', encoding='utf-8')
        writer = csv.DictWriter(file, fieldnames=reader.fieldnames)
        writer.writeheader()

        writer.writerows(rows)
        file.close()
        # print(f"sity_choice пользователя с ID {user_id} успешно изменен на {sity_choice}.")
        return

    def check_city(message, filename='user_data.csv'):

        # Добавил пропуск чтобы дошдо до В Начало

        if message.text == 'В начало':
            pass

        user_id = message.from_user.id
        username = message.from_user.username

        column_to_find_row = 'user_id'
        column_to_find_sity = 'sity_choice'

        file = open(filename, mode='r', newline='', encoding='utf-8')
        reader = csv.DictReader(file)
        # Ищем нужную строку по значению в колонке column_to_find_row
        found_row = None
        for row in reader:

            # print(f"Проверяем выбран ли город. Перебираем строки  {row} ищем {column_to_find_row}")
            if not isinstance(user_id, int):
                raise ValueError(f"Переменная user_id должна быть целого типа, а не {type(user_id).__name__}")
            if int(row[column_to_find_row]) == user_id:
                found_row = row
                # print(f"Найдена строка с id '{user_id}' {row}")
                break
            # Добавили отсылку к проверке файла только если ИД нет

            else:

                Filemanager.check_user(user_id, username)
        # Закрываем файл
        file.close()

        sity_choice = found_row[column_to_find_sity]
        #print(f"Передаем  '{sity_choice}'  ")
        return sity_choice

    def check_user(user_id, username, filename='user_data.csv'):
        # print(f"Проверка начата   id {user_id} ")

        try:
            file = open(filename, "r", newline='', encoding='utf-8')
            # print(f"Файл открыт   id {user_id} ")
            reader = csv.DictReader(file)

            for row in reader:
                if not isinstance(user_id, int):
                    raise ValueError(f"Переменная user_id должна быть целого типа, а не {type(user_id).__name__}")

                if int(row['user_id']) == user_id:
                    file.close()
                    # print(f"Пользователь с id {user_id} уже существует.")
                    return False  # Выход из функции, если пользователь найден

            file.close()
            # print(f"Начинаем сохранение данных Пользователя с id {user_id} .")
            Filemanager.save_user_data(user_id, username)
            return True



        except FileNotFoundError:
            # print(f"Файл не найден, создаем новый  id {user_id}")
            # Cоздаем его и сохраняем заголовки
            file = open(filename, mode='w', newline='', encoding='utf-8')
            fieldnames = ['user_id', 'username', 'sity_choice', 'current_day']

            writer = csv.writer(file)
            writer.writerow(fieldnames)

            Filemanager.save_user_data(user_id, username)
            return True

    def save_user_data(user_id, username, filename='user_data.csv'):

        sity_choice = 'no'
        current_day = datetime.now().day
        """Сохраняет данные пользователя в файл"""

        file = open(filename, mode='a', newline='', encoding='utf-8')

        fieldnames = ['user_id', 'username', 'sity_choice', 'current_day']
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        writer.writerow({
            'user_id': user_id,
            'username': username,
            'sity_choice': sity_choice,
            'current_day': current_day,
        })

        # print(f"Пользователь с id {user_id} успешно добавлен.")
        file.close()
        # print(f"Файл закрыт id {user_id} успешно добавлен.")
        return


class Serve():
    def show_main_menu(user_id):
        logger.info(f'show_main_menu{user_id}')
         # Создание кнопок
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton(text='Найти')
        btn2 = types.KeyboardButton(text='Инфо')
            #btn3 = types.KeyboardButton(text='Разместить')

        markup.add(btn1, btn2) #btn3)

            # Отправка ответа
        bot.reply_to(user_id, """\
               Привет! Я бот, который может найти для вас стажировку, еще можно разместить свою. Нажимайте кнопки внизу чтобы продолжить или    нажмите /start \
               """, reply_markup=markup)


    

    def handle():

        try:
            # Подключение к базе данных
            db_connection = MySQLdb.connect(
                host="localhost",  # Хост базы данных (обычно localhost)
                user="u1404034",  # Имя пользователя БД
                passwd="18njgjkm18",  # Пароль пользователя
                db="u1404034_8373",  # Название базы данных
                charset='utf8',
            )

            cursor = db_connection.cursor()  # Создаем курсор для выполнения запросов

            # Пример SQL-запроса
            query = "SELECT * FROM bot1_searchinfo "

            # Выполнение запроса
            cursor.execute(query)

            # Получение всех результатов
            results = cursor.fetchall()



        except MySQLdb.Error as e:
            logger.error('Ошибка при подключении к базе данных: {e}')
            # print(f"Ошибка при подключении к базе данных: {e}")
        finally:
            if db_connection:
                db_connection.close()  # Закрываем соединение с базой данных

        return results


class Sear():
    def search_name(message, sity_choice):
        title = message.text

        bot.send_message(message.from_user.id, f'Ищем {title} ')

        try:

            # data = Searchinfo.objects.filter(city=sity_choice) & Searchinfo.objects.filter(title__icontains=title)
            data = Serve.handle()

            filtered_data = [row for row in data if row[8] == sity_choice]
            try:
                filtered_data2 = [row for row in filtered_data if title.casefold() in row[1].casefold()]
            except Exception as e:
                print(f"Ошибка: {e}")

            c = len(filtered_data2)
            if c == 0:
                markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
                btn1 = telebot.types.KeyboardButton('/begin', text='Сначала')

                # markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                # btn1 = types.KeyboardButton(text='В начало')

                markup.add(btn1)
                bot.send_message(message.from_user.id, "Пока ничего не нашли!  ", #  Чтобы продолжить нажмите /start
                                 reply_markup=markup)
            else:
                for row in filtered_data2:
                    title = row[1]
                    company = row[4]
                    contact = row[6]
                    url = row[3]
                    salary = row[2]
                    email = row[9]
                    phone = row[10]
                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                    btn1 = types.KeyboardButton(text='В начало')
                    markup.add(btn1)
                    bot.send_message(message.from_user.id,
                                     f'Нашли вакансию! {title} Название компании: {company},  Зарплата: {salary} Контактное лицо: {contact} , Телефон: {phone} , email: {email} , ссылка: {url} .',
                                     reply_markup=markup)

        except:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            btn1 = types.KeyboardButton(text='В начало')
            markup.add(btn1)
            bot.send_message(message.from_user.id, "Повторите поиск пожалуйста!  ",
                             reply_markup=markup)

    def search_name_m(message):
        sity_choice = 'Москва'
        Sear.search_name(message, sity_choice)

    def search_name_s(message):
        sity_choice = 'Санкт-Петербург'
        Sear.search_name(message, sity_choice)


class Cover():
    def append_name(message):
        chat_id = message.chat.id
        userfirstname = message.text
        users[chat_id]['userfirstname'] = userfirstname
        bot.send_message(chat_id, f'Отлично, {userfirstname}. Теперь укажите контактные данные')
        bot.register_next_step_handler(message, Cover.append_contacts)

    def append_contacts(message):
        chat_id = message.chat.id
        userlastname = message.text
        users[chat_id]['userlastname'] = userlastname
        bot.send_message(chat_id, f'Отлично,  Теперь укажите название вакансии')
        bot.register_next_step_handler(message, Cover.append_vacancy)

    def append_vacancy(message):
        chat_id = message.chat.id
        specmessage = message.text
        users[chat_id]['specmessage'] = specmessage

        data = Userdata(
            userid=users[chat_id],
            userfirstname=users[chat_id]['userfirstname'],
            userlastname=users[chat_id]['userlastname'],
            specmessage=users[chat_id]['specmessage'],

        )

        data.save()

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton(text='В начало')
        markup.add(btn1)
        bot.send_message(message.from_user.id,
                         "Спасибо что разместили вакансию! Она появится в базе после проверки модератором.  Чтобы продолжить нажмите /start ",
                         reply_markup=markup)


class Command(BaseCommand):
    logger.info('Command is running')

    # Handle '/start' and '/help'

    @bot.message_handler(commands=['start'])
    def send_welcome(message):

        # Проверка регистрации и регистрация пользователя
        user_id = message.from_user.id
        username = message.from_user.username
        if sub_manager.check_subscription(user_id):
            Filemanager.check_user(user_id, username)
            # Проверка выбран ли город

            # Filemanager.check_city(message)

            # Создание кнопок
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            btn1 = types.KeyboardButton(text='Найти')
            btn2 = types.KeyboardButton(text='Инфо')
            #btn3 = types.KeyboardButton(text='Разместить')

            markup.add(btn1, btn2) #btn3)

            # Отправка ответа
            bot.reply_to(message, """\
                Привет! Я бот, который может найти для вас стажировку, еще можно разместить свою. Нажимайте кнопки внизу чтобы продолжить или    нажмите /start \
                """, reply_markup=markup)
        else:
            sub_manager.send_subscription_request(message.chat.id)



    @bot.callback_query_handler(func=lambda call: call.data == 'check_subscription')
    def check_subscription_callback(call):
        user_id = call.from_user.id
        username = call.from_user.username

        if sub_manager.check_subscription(user_id):
            logger.info(f'check_subscription_callback{user_id}')
            bot.delete_message(call.message.chat.id, call.message.message_id)

            Filemanager.check_user(user_id, username)
            # Проверка выбран ли город

            # Filemanager.check_city(message)
            Serve.show_main_menu(user_id)

           



        else:
            bot.answer_callback_query(call.id,
                                      "Вы еще не подписались на канал. Пожалуйста, подпишитесь и нажмите кнопку снова.")





    @bot.message_handler(commands=['begin'])
    def beginning(message):
        sity_choice = 'no'
        Filemanager.change_city_choice(message, sity_choice)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton(text='Найти')
        btn2 = types.KeyboardButton(text='Инфо')
        #btn3 = types.KeyboardButton(text='Разместить')
        # btn4 = types.KeyboardButton(text='В начало')
        markup.add(btn1, btn2 )  #btn3 ,btn4
        bot.reply_to(message, """\
                        Выбор города сброшен, сделайте это пожалуйста снова . Нажимайте кнопки внизу чтобы продолжить \
                        """, reply_markup=markup)

    @bot.message_handler(commands=['append'])
    def append_data(message):
        # Проверка регистрации и регистрация пользователя
        user_id = message.from_user.id
        username = message.from_user.username
        Filemanager.check_user(user_id, username)

        chat_id = message.chat.id

        bot.send_message(chat_id,
                         ' Введите название компании или своё имя')
        users[chat_id] = {}

        bot.register_next_step_handler(message, Cover.append_name)

    @bot.message_handler(content_types=['text'])  # func=lambda message: True,
    def handle_text(message, sity_choice='no'):





        # Проверка регистрации и регистрация пользователя
        user_id = message.from_user.id
        username = message.from_user.username
        if sub_manager.check_subscription(user_id):
            Filemanager.check_user(user_id, username)

            # Filemanager.check_user(user_id,username)

            # Проверка выбран ли город - пока решено не проводить

            #  Filemanager.check_city(message)

            if message.text == 'Привет':
                bot.send_message(message.chat.id, 'Привет!')

            elif message.text == 'Инфо':
                bot.send_message(message.chat.id,

                                 'Стажировка — это неоплачиваемая (чаще всего) работа по собственной инициативе студента. Она позволяет обучиться тонкостям профессии или освоить с нуля новую. Чаще всего после удачно пройденной стажировки студента приглашают  на работу. '
                                 'Подробнее про стажировку посмотрите на сайте www.amoccon.ru .'
                                 'Как искать: Бот выбирает только вакансии для стажеров. Чтобы уточнить поиск, отправьте боту только одно ключевое слово. Это может быть часть названия вакансии или компании. '
                                 'Если набрать два слова, поиск, возможно, будет неудачным.'
                                 'Подробнее про поиск здесь https://amoccon.ru/front_page/как-искать/ '

                                 ' Для продолжения нажмите кнопку')  # , reply_markup=markup1)
            elif message.text == 'Найти':
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                btn1 = types.KeyboardButton(text='Москва')
                btn2 = types.KeyboardButton(text='Санкт-Петербург')
                markup.add(btn1, btn2)
                bot.send_message(message.chat.id, 'Выберите город', reply_markup=markup)
                # bot.register_next_step_handler(message, Sear.search_name)

            elif message.text == 'Разместить':
                chat_id = message.chat.id
                bot.send_message(chat_id,
                                 ' Введите название компании или своё имя')
                users[chat_id] = {}
                bot.register_next_step_handler(message, Cover.append_name)
            elif message.text == 'В начало':

                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                btn1 = types.KeyboardButton(text='Найти')
                btn2 = types.KeyboardButton(text='Инфо')
                # btn3 = types.KeyboardButton(text='Разместить')
                # btn4 = types.KeyboardButton(text='В начало')
                markup.add(btn1, btn2)  # ,btn4, btn3
                bot.reply_to(message, """\
                            Привет! Я бот, который может найти для вас стажировку, еще можно разместить свою. Нажимайте кнопки внизу чтобы продолжить \
                            """, reply_markup=markup)
            elif message.text == 'Москва':
                city_choice = message.text
                Filemanager.change_city_choice(message, city_choice)
                bot.send_message(message.chat.id, 'Напишите название специальности или ключевое слово')
                bot.register_next_step_handler(message, Sear.search_name_m)
            elif message.text == 'Санкт-Петербург':
                city_choice = message.text
                Filemanager.change_city_choice(message, city_choice)
                bot.send_message(message.chat.id, 'Напишите название специальности или ключевое слово')
                bot.register_next_step_handler(message, Sear.search_name_s)


            else:

                sity_choice = Filemanager.check_city(message)
                # print(f"Принято   '{sity_choice}'  ")

                if sity_choice == 'Москва':
                    Sear.search_name(message, sity_choice)
                elif sity_choice == 'Санкт-Петербург':
                    Sear.search_name(message, sity_choice)
                else:
                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                    btn1 = types.KeyboardButton(text='В начало')
                    markup.add(btn1)
                    bot.send_message(message.chat.id, 'Пока не готов вам ответить, для продолжения нажмите /start',
                                     reply_markup=markup)
        else:
            sub_manager.send_subscription_request(message.chat.id)

    bot.infinity_polling()

