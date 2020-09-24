import config
import gspread
import numpy as np
import psycopg2
import telebot
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials

con = psycopg2.connect(
        database="database_name",
        user="user_name",
        password="your_password",
        host="your_host",
        port="your_port"
    )

cur = con.cursor()

bot = telebot.TeleBot(config.bot_api)

user_id_dict = {}


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, 'Чтобы добавить свой профиль в рассылку вызовите команду /add')


@bot.message_handler(commands=['add'])
def add_user(message):
    cur.execute("SELECT * FROM notification_bot WHERE id = %d" % message.chat.id)
    user_info = cur.fetchall()
    if user_info:
        bot.send_message(message.chat.id, 'Вы уже в системе')
    else:
        bot.send_message(message.chat.id,
                         '''Пожалуйста, пришлите сообщение с вашим Именем и Фамилией на русском языке, как в паспорте\
(как в вашем зарплатном отчете):\n
1. Без лишних пробелов и дополнительных символов: Имя с большой буквы, пробел, Фамилия с большой буквы\n
2. Никаких больше сообщений, только Имя Фамилия\n
3. Образец: “*Джон Голт*”''', parse_mode='markdown')
        bot.register_next_step_handler(message, user_adder)


@bot.message_handler(commands=['send'])
def message_sender(message):
    global user_id_dict
    googlesheet_users_info = table_updater()
    cur.execute("SELECT id FROM notification_bot WHERE admin_marker = 1")
    list_of_admins = np.array(cur.fetchall()).flatten()
    if message.chat.id in list_of_admins:
        spam_notifier()
        cur.execute("SELECT * FROM notification_bot")
        all_registered_users = cur.fetchall()
        for user in all_registered_users:
            user_id_dict[user[1]] = user[0]
        for user_info in googlesheet_users_info:
            if user_info['В рассылку'] == 'TRUE':
                bot.send_message(user_id_dict[user_info['Сотрудник']], user_info['Сообщение'])
    else:
        bot.send_message(message.chat.id, 'Извините, вы не можете использовать эту команду')


@bot.message_handler(commands=['show'])
def show_users(message):
    if admin_checker(message, 'just check'):
        cur.execute("SELECT * FROM notification_bot")
        all_registered_users = cur.fetchall()
        for columns in all_registered_users:
            text = str(columns[0]) + ' - ' + columns[1]
            bot.send_message(message.chat.id, text)
    else:
        bot.send_message(message.chat.id, 'Извините, вы не можете использовать эту команду')


@bot.message_handler(commands=['delete'])
def delete_user(message):
    cur.execute("SELECT FROM notification_bot WHERE id = %d" % message.chat.id)
    if cur.fetchall():
        cur.execute("DELETE FROM notification_bot WHERE ID = '%s'" % message.chat.id)
        con.commit()
        bot.send_message(message.chat.id, 'Отлично, вы удалены!')
    else:
        bot.send_message(message.chat.id, 'К сожалению, вы еще не записаны.')


@bot.message_handler(commands=['add_admin'])
def admin_adder(message):
    if admin_checker(message, 'just check'):
        bot.send_message(message.chat.id, 'Введите пожалуйста id человека, которого вы хотите назначить админом')
        bot.register_next_step_handler(message, add_admin)
    else:
        bot.send_message(message.chat.id, 'Извините, вы не можете использовать эту команду')


@bot.message_handler(commands=['delete_admin'])
def admin_deleter(message):
    if admin_checker(message, 'superadmin check'):
        bot.send_message(message.chat.id, 'Введите пожалуйста id человека, которого вы хотите удалить из админов')
        bot.register_next_step_handler(message, delete_admin)
    else:
        bot.send_message(message.chat.id, 'Извините, вы не можете использовать эту команду')


@bot.message_handler(commands=['delete_user'])
def delete_user(message):
    if admin_checker(message, 'just check'):
        bot.send_message(message.chat.id, 'Введите пожалуйста id сотрудника, которого вы хотите удалить')
        bot.register_next_step_handler(message, user_deleter)
    else:
        bot.send_message(message.chat.id, 'Извините, вы не можете использовать эту команду')


@bot.message_handler(commands=['show_admins'])
def show_admins(message):
    if admin_checker(message, 'just check'):
        for admin in admin_checker(message, 'show list of admins'):
            cur.execute("SELECT name FROM notification_bot WHERE id = %d" % admin)
            admin_name = cur.fetchall()[0][0]
            bot.send_message(message.chat.id, str(admin) + ' - ' + admin_name)
    else:
        bot.send_message(message.chat.id, 'Извините, вы не можете использовать эту команду')


def table_updater():
    credentials = ServiceAccountCredentials.from_json_keyfile_name("path_to_json_file")
    googlesheet = gspread.authorize(credentials)
    worksheets = googlesheet.open_by_key('your_googlesheet_key').sheet1
    googlesheet_users_info = worksheets.get_all_records()
    return googlesheet_users_info


def user_checker(message):
    persons = []
    googlesheet_users_info = table_updater()
    for person in googlesheet_users_info:
        persons.append(person['Сотрудник'])
    return message.text in persons


def user_adder(message):
    if user_checker(message) is not True:
        bot.send_message(message.chat.id,
                         '''Вы не найдены в списке сотрудников! Убедитесь, что вы правильно ввели свое \
                            Имя Фамилию и повторите команду /add либо обратитесь к администратору \
                            бота @your_username для добавления вас в список сотрудников.''')
    else:
        cur.execute("INSERT INTO notification_bot VALUES (%d, '%s', %d, %d)" % (message.chat.id, message.text, 0, 0))
        con.commit()
        bot.send_message(message.chat.id, 'Спасибо, вы записаны!')


def admin_checker(message, flag):
    cur.execute("SELECT id FROM notification_bot WHERE admin_marker = 1")
    list_of_admins = np.array(cur.fetchall()).flatten()
    if flag == 'just check':
        return message.chat.id in list_of_admins
    elif flag == 'superadmin check':
        cur.execute("SELECT id FROM notification_bot WHERE super_admin_marker = 1")
        list_of_super_admins = np.array(cur.fetchall()).flatten()
        return message.chat.id in list_of_super_admins
    else:
        return list_of_admins


def add_admin(message):
    try:
        cur.execute("SELECT id FROM notification_bot")
        list_of_ids = np.array(cur.fetchall()).flatten()
        new_admin_id = int(message.text)
        if new_admin_id in list_of_ids:
            cur.execute("UPDATE notification_bot SET admin_marker = 1 WHERE id = %d" % new_admin_id)
            con.commit()
            bot.send_message(message.chat.id, 'Админ успешно добавлен')
            bot.send_message(new_admin_id, '''Вам присвоен статус администратора.\n
        Теперь вам доступен следующий список скрытых команд:\n
        1) /show - показать список пользователей в системе\n
        2) /send - обновить Google sheets и отправить рассылку\n
        3) /delete_user - удалить пользователя\n
        4) /add_admin - добавить админа\n
        Ссылка на лист Google sheets для настройки рассылки –> \
        ссылка на ваш googlesheet''')
        else:
            bot.send_message(message.chat.id, 'Вы ввели неверный id')
    except ValueError:
        bot.send_message(message.chat.id, 'Вы ввели неверный id')


def delete_admin(message):
    try:
        deleted_admin_id = int(message.text)
        cur.execute("UPDATE notification_bot SET admin_marker = 0 WHERE id = %d" % deleted_admin_id)
        con.commit()
        bot.send_message(message.chat.id, 'Вы удалили этого сотрудника из списка администраторов')
        bot.send_message(deleted_admin_id, 'Вы лишены администраторских прав, можете продолжать пользоваться ботом\
         в качестве обычного пользователя. В случае ошибки обратитесь к администратору бота @your_username')
    except ValueError:
        bot.send_message(message.chat.id, 'Вы ввели неверный id')


def spam_notifier():
    today = datetime.now().strftime('%H:%M')
    cur.execute("SELECT id FROM notification_bot WHERE admin_marker = 1")
    list_of_admins = np.array(cur.fetchall()).flatten()
    for admin in list_of_admins:
        bot.send_message(admin, f'Запущена рассылка - {today}')


def user_deleter(message):
    try:
        deleted_user_id = int(message.text)
        cur.execute("DELETE FROM notification_bot WHERE id = %d" % deleted_user_id)
        con.commit()
        bot.send_message(message.chat.id, 'Сотрудник удален!')
        bot.send_message(deleted_user_id, 'Вы удалены из системы и больше не будете получать рассылку. В случае ошибки\
        обратитесь к администратору бота @your_username')
    except ValueError:
        bot.send_message(message.chat.id, 'Вы ввели неверный id')


bot.polling(none_stop=True)
