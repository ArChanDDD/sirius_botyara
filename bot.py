import pandas as pd 
import telebot
import numpy as np
import json

API_TOKEN = '6841375941:AAF0k42LnVLw7O1qCyfbuLO8WQZ208j-uog'
bot = telebot.TeleBot(API_TOKEN)
truth_vals = np.array(pd.read_csv('truth.csv')['meantemp'])

with open('files/user_ids.json', 'r') as f:
    user_ids = json.load(f)
with open('files/user_top.json', 'r') as f:
    user_top = json.load(f)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет!\nБот работает просто - тыкай команду /send_solution и отправляй свой csv-файл.\nЧтобы посмотреть результаты - вызови команду /top.\nУдачи!")
    if str(message.chat.id) not in user_ids:
        def get_name(message2):
            if message2.text in ['/start', '/send_solution', '/top']:
                bot.send_message(message2.chat.id, 'Так не пойдет!')
                return
            user_ids[str(message2.chat.id)] = message2.text
            with open('files/user_ids.json', 'w') as f:
                json.dump(user_ids, f)
            bot.send_message(message2.chat.id, 'Я тебя запомнил, теперь можно сдавать решения!')
        bot.send_message(message.chat.id, 'Как тебя зовут?')
        bot.register_next_step_handler(message, get_name)


@bot.message_handler(commands=['top'])
def get_top(message):
    top = [[user_ids[user_id], score] for user_id, score in user_top.items()]
    if len(top) == 0:
        bot.send_message(message.chat.id, 'Топ пока что пустой :(')
        return
    top = sorted(top, key=lambda x: float(x[1]))
    top_msg = ''
    for i in range(len(top)):
        top_msg += f'{i + 1}: {top[i][0]} -- {top[i][1]}\n'
    bot.send_message(message.chat.id, top_msg)


@bot.message_handler(commands=['send_solution'])
def send_solution(message, user_top=user_top):
    if str(message.chat.id) not in user_ids:
        bot.send_message(message.chat.id, 'Сначала сделай /start')
        return
    def get_document(message2, user_top=user_top):
        try:
            raw = message2.document.file_id
            path = raw+".csv"
            file_info = bot.get_file(raw)
            downloaded_file = bot.download_file(file_info.file_path)
            with open(f'submissions/{message2.chat.id}.csv', 'w') as new_file:
                new_file.write(downloaded_file.decode('utf-8'))
            
            sub_vals = np.array(pd.read_csv(f'submissions/{message2.chat.id}.csv').sort_values('date')['predicted'])
            mse = round(np.mean((sub_vals - truth_vals) ** 2), 3)
            if str(message2.chat.id) in user_top:
                current_mse = user_top[str(message2.chat.id)]
                if current_mse > mse:
                    bot.send_message(message2.chat.id, 'Ого, твой результат улучшился!')
                    user_top[str(message2.chat.id)] = mse
                    with open('files/user_top.json', 'w') as f:
                        user_top = json.dump(user_top, f)
            else:
                user_top[str(message2.chat.id)] = mse
                with open('files/user_top.json', 'w') as f:
                    user_top = json.dump(user_top, f)
            bot.send_message(message2.chat.id, f'Твой MSE - {mse}')
        except ValueError:
            bot.send_message(message2.chat.id, 'С твоим файлом что-то не так...')
    bot.send_message(message.chat.id, 'Жду от тебя csv-файл')
    bot.register_next_step_handler(message, get_document)

bot.infinity_polling(timeout=10, long_polling_timeout=5)
