import telebot
import sqlite3
from random import choice, randint
import os.path
from time import sleep

bot = telebot.TeleBot('YOUR TOKEN')

def sql_open(toggle=0):

    global GAME
    global temp_theme

    name_dir = os.path.abspath('players.db')
    with sqlite3.connect(name_dir) as db:

        cursor = db.cursor()

        if toggle == 0:  # запись queue
            cursor.execute("""INSERT INTO users (name, id) VALUES(?, ?)""", (sendler_name, sendler_id,))

        elif toggle == 1:  # чтение queue
            cursor.execute("""SELECT * FROM 'users'""")
            return [a for a in cursor.fetchall()]  # return name, id

        elif toggle == 2:  # удаление queue
            cursor.execute("""DELETE FROM users""")

        elif toggle == 3:  # запись темы
            cursor.execute("""INSERT INTO select_theme (id, choice) VALUES(?, ?)""", (id_selector, select_selector))

        elif toggle == 4:  # select theme | delete select_theme | return bd_name #выбор
            cursor.execute("""SELECT choice FROM select_theme""")
            global theme
            try:
                theme = choice([choice[0] for choice in cursor.fetchall()])
            except:
                pass

            cursor.execute("""DELETE FROM select_theme""")

        elif toggle == 5:  # кол-во выбранных тем
            cursor.execute("""SELECT * FROM select_theme""")
            return cursor.fetchall()

        elif toggle == 6:  # select answ|quest of theme if not in used_quest. GET LIVES

            if theme == 'all':
                temp_theme = choice(['eng_from_rus', 'rus_from_eng', 'Math', 'questions'])
            else:
                temp_theme = theme

            cursor.execute(f"""SELECT * FROM {temp_theme}""")
            all_units = cursor.fetchall()
            cursor.execute("""SELECT * FROM used_questions""")
            used_questions = cursor.fetchall()
            all_units = [unit for unit in all_units if unit[1] not in used_questions]

            a_q_rnd = choice(all_units)
            GAME['answer'] = a_q_rnd[0]; GAME['question'] = a_q_rnd[1]
            sql_open(7)

        elif toggle == 7:  # add in used_quest
            cursor.execute("""INSERT INTO used_questions VALUES(?)""", (GAME['question'],))

        elif toggle == 8:  # clear used_questions
            cursor.execute("""DELETE FROM used_questions""")
        db.commit()

def reset():
    sql_open(2)  # players queue clear
    sql_open(4)  # theme clear
    sql_open(8)  # clear used_quest
    global GAME, theme
    global waited_message1, waited_message2
    global m1, m2
    global temp_theme
    global ended_rounds, temp_round, checker_bug
    global indx

    indx = None
    ended_rounds, temp_round, checker_bug = None, None, None
    try: 
        if waited_message2: waited_message2 = None
    except: pass
    try:
        if waited_message1: waited_message1 = None
    except: pass
    
    try: 
        if m1: m1 = None
    except: pass
    try: 
        if m2: m2 = None
    except: pass

    temp_theme = None
    theme = 0
    GAME = {
        'status': 0,
        'question': 0,
        'answer': 0,
        'round': 0,
        'theme': 0,
        'lives': 0,
        'wait_after_game': 0,
        'player1': {
            'name': 0,
            'id': 0,
            'score': 0,
            'win': 0,
            'ended': 0,
            'lives': 0,
            'select_theme': 0,
        },
        'player2': {
            'name': 0,
            'id': 0,
            'score': 0,
            'win': 0,
            'ended': 0,
            'lives': 0,
            'select_theme': 0,
        },
    }

def get_lives(theme):
    global GAME
    if theme in ['eng_from_rus', 'rus_from_eng', 'questions', 'all']:
        return 4
    elif theme == 'Math':
        return 2

@bot.message_handler(commands=['search', 'start', 'reset', 'exit', 'restart'])  # exit: Удаление темы, списка игроков
def search(command):

    if command.text in ['/exit', '/restart', '/reset']:
        global m1, m2
        try:
            if m1 and m2:
                bot.delete_message(message_id=m1.message_id, chat_id=m1.chat.id)
                bot.delete_message(message_id=m2.message_id, chat_id=m2.chat.id)
        except:
            pass

        try:
            if command.from_user.id == GAME['player1']['id']:
                bot.send_message(GAME['player1']['id'], 'Игра окончена.')
                bot.send_message(GAME['player2']['id'], f'{GAME["player1"]["name"]} решил выйти из игры.')

            elif command.from_user.id == GAME['player2']['id']:
                bot.send_message(GAME['player2']['id'], 'Игра окончена.')
                bot.send_message(GAME['player1']['id'], f'{GAME["player2"]["name"]} решил выйти из игры.')
        except:
            bot.send_message(command.from_user.id, 'Рестарт игры..')
        else:
            bot.send_message(command.from_user.id, 'Рестартим..')
        reset()
        return
    global sendler_name, sendler_id
    sendler_name, sendler_id = command.from_user.username, command.from_user.id

    names_id = [name_id for name_id in sql_open(1)]  #read

    if not names_id: # players empty
        sql_open(0)
        bot.send_message(sendler_id, f"Successful added <b>{sendler_name}</b> to queue", parse_mode='HTML')
    elif len(names_id) == 1:  # one player in queue
        if sendler_id in [name_id[1] for name_id in names_id]:
            bot.send_message(sendler_id, f"You're already searching, Wait!")
        else:
            sql_open(0)
            GAME['player1']['id'] = sql_open(1)[0][1]
            GAME['player2']['id'] = sql_open(1)[1][1]
            #START match
            game_handler(0)


    elif len(names_id) == 2:  # match is busy
        if sendler_id not in [name_id[1] for name_id in names_id]:
            bot.send_message(sendler_id, f'<b>Match is full!</b> \n\n'
                                         f'<i><b>{names_id[0][0]}</b></i> and <i><b>{names_id[1][0]}</b></i> playing now...', parse_mode='HTML')
        elif sendler_id in [name_id[1] for name_id in names_id]:
            bot.send_message(sendler_id, f"<b>You're playing now.</b> \n\n"
                                         f"<i>You can't search when you playing.</i>", parse_mode='HTML')

@bot.message_handler(content_types=['text'])
def game_handler(message):
    global GAME
    if message == 0:
        b1 = telebot.types.InlineKeyboardButton(text='Арифметика', callback_data='Math')
        b2 = telebot.types.InlineKeyboardButton(text='Английский с русского', callback_data='eng_from_rus')
        b3 = telebot.types.InlineKeyboardButton(text='Русский с английского', callback_data='rus_from_eng')
        b5 = telebot.types.InlineKeyboardButton(text='Вопросы', callback_data='questions')
        b6 = telebot.types.InlineKeyboardButton(text='Все сразу', callback_data='all')
        keyboard = telebot.types.InlineKeyboardMarkup(row_width=2); keyboard.add(b1,b2,b3,b5,b6)
        bot.send_message(sql_open(1)[0][1], f"Выберите категорию вопросов:", reply_markup=keyboard)
        bot.send_message(sql_open(1)[1][1], f"Выберите категорию вопросов:", reply_markup=keyboard)
        @bot.callback_query_handler(func=lambda x: True)
        def choice(query):
            global select_selector, id_selector
            global GAME
            select_selector, id_selector = query.data, query.from_user.id
            bot.delete_message(query.message.chat.id, query.message.id)

            if id_selector not in [x[1] for x in sql_open(1)] \
                    or (id_selector == GAME['player1']['id'] and GAME['player1']['select_theme'])\
                    or (id_selector == GAME['player2']['id'] and GAME['player2']['select_theme']):
                bot.send_message(id_selector, 'ERROR. TRY AGAIN PLEASE!')
            else:
                if id_selector == GAME['player1']['id']:
                    GAME['player1']['select_theme'] = 1
                elif id_selector == GAME['player2']['id']:
                    GAME['player2']['select_theme'] = 1
                bot.send_message(id_selector, f'Вы выбрали: <b>{select_selector}</b> \n'
                                              f'<i>Ожидайте выбор соперника..</i>', parse_mode='HTML')
                sql_open(3)
                if len(sql_open(5)) == 2: #len of themes
                    sql_open(4) #theme selector
                    global waited_message1, waited_message2
                    GAME['status'] = 1
                    try:
                        if waited_message1:
                            bot.delete_message(message_id=waited_message1, chat_id=waited_message1.chat.id)
                    except: pass
                    try:
                        if waited_message2:
                            bot.delete_message(message_id=waited_message2, chat_id=waited_message2.chat.id)
                    except: pass

                    mt_0 = bot.send_message(sql_open(1)[0][1], f'Игра начинается. Выбранная тема: <b>{theme}</b>', parse_mode='HTML')
                    mt_1 = bot.send_message(sql_open(1)[1][1], f'Игра начинается. Выбранная тема: <b>{theme}</b>', parse_mode='HTML')
                    sleep(0.85)
                    bot.edit_message_text(chat_id=mt_0.chat.id, message_id=mt_0.message_id, text=f'<i>Игра скоро начнётся....</i>', parse_mode='HTML')
                    bot.edit_message_text(chat_id=mt_1.chat.id, message_id=mt_1.message_id, text=f'<i>Игра скоро начнётся....</i>', parse_mode='HTML')
                    sleep(0.65)
                    sample_text = 'Все ответы записывайте с <b>маленькой</b> буквы\n' if theme != 'Math' else ''
                    for tx in range(4, 0, -1):
                        sleep(1)
                        bot.edit_message_text(message_id=mt_0.message_id, chat_id=mt_0.chat.id, text=f'Старайтесь отвечать правильно, не допуская ошибок.\n'
                                                                                                     f'{sample_text}'
                                                                                                     f'Пожалуйста, не пишите много сообщений за раз!\n\n'
                                                                                                     f'Игра начнётся через <b>{tx-1}</b> сек. \n\n'
                                                                                                     f'Чтобы принудительно завершить матч, введите /exit', parse_mode='HTML')
                        bot.edit_message_text(message_id=mt_1.message_id, chat_id=mt_1.chat.id, text=f'Старайтесь отвечать правильно, не допуская ошибок.\n'
                                                                                                     f'{sample_text}'
                                                                                                     f'Пожалуйста, не пишите много сообщений за раз!\n\n'
                                                                                                     f'Игра начнётся через <b>{tx-1}</b> сек. \n\n'
                                                                                                     f'Чтобы принудительно завершить матч, введите /exit', parse_mode='HTML')
                    players_name = [name[0] for name in sql_open(1)];  sleep(0.4)
                    bot.edit_message_text(message_id=mt_0.message_id, chat_id=mt_0.chat.id, text=f'<b>Игра началась!</b>\n'
                                                                                                 f'<b>Тема:</b> <i>{theme}</i>\n\n'
                                                                                                 f'<b>Игроки:</b>\n'
                                                                                                 f'   <b>{players_name[0]}\n'
                                                                                                 f'   {players_name[1]}</b>',
                                          parse_mode='HTML')
                    bot.edit_message_text(message_id=mt_1.message_id, chat_id=mt_1.chat.id, text=f'<b>Игра началась!</b>\n'
                                                                                                 f'<b>Тема:</b> <i>{theme}</i>\n\n'
                                                                                                 f'<b>Игроки:</b>\n'
                                                                                                 f'   <b>{players_name[0]}\n'
                                                                                                 f'   {players_name[1]}</b>', parse_mode='HTML')
                    GAME = {
                        'status': 1,
                        'question': 0,
                        'answer': 0,
                        'round': 0,
                        'wait_after_game': 0,
                        'theme': theme,
                        'lives': get_lives(theme),
                        'player1': {
                            'name': sql_open(1)[0][0],
                            'id': sql_open(1)[0][1],
                            'score': 0,
                            'win': 0,
                            'ended': 0,
                            'lives': get_lives(theme), #кол-во ошибок на этом ключе
                            'select_theme': 1,
                        },
                        'player2': {
                            'name': sql_open(1)[1][0],
                            'id': sql_open(1)[1][1],
                            'score': 0,
                            'win': 0,
                            'ended': 0,
                            'lives': get_lives(theme),
                            'select_theme': 1,
                        },
                    }

                    game(None, 1)
    else:
        bot.delete_message(message_id=message.id, chat_id=message.chat.id)  # del mes user
        if len(sql_open(1)) == 2:
            if GAME['status']:
                    if message.from_user.id in [a[1] for a in sql_open(1)]:  # играет
                        if GAME['round']:
                            game(message)
                        else:
                            pass  # ЕСЛИ ожидание старта игры
                    else:
                        bot.send_message(sendler_id, f"Вы не в игре. \n\n"
                                                     f"Ждите, пока {GAME['player1']['name']} и {GAME['player2']['name']} закончат. \n\n")
            else:
                if message.from_user.id == GAME['player1']['id']:
                    global waited_message1
                    if GAME['player1']['select_theme']:
                        try:
                            if waited_message1:
                                bot.delete_message(message_id=waited_message1.message_id,
                                                   chat_id=waited_message1.chat.id)
                        except: pass
                        waited_message1 = bot.send_message(message.from_user.id,
                                         'Ожидайте выбор соперника...\n\n'
                                         'Чтобы выйти из игры, введите /exit')
                    else:
                        try:
                            if waited_message1:
                                bot.delete_message(message_id=waited_message1.message_id,
                                                   chat_id=waited_message1.chat.id)
                        except: pass
                        waited_message1 = bot.send_message(message.from_user.id,
                                                           'Сделайте выбор, пожалуйста!')

                elif message.from_user.id == GAME['player2']['id']:
                    global waited_message2
                    if GAME['player2']['select_theme']:
                        try:
                            if waited_message2:
                                bot.delete_message(message_id=waited_message2.message_id,
                                                   chat_id=waited_message2.chat.id)
                        except: pass
                        waited_message2 = bot.send_message(message.from_user.id,
                                         'Ожидайте выбор соперника...\n\n'
                                         'Чтобы выйти из игры, введите /exit')
                    else:
                        try:
                            if waited_message2:
                                bot.delete_message(message_id=waited_message2.message_id,
                                                   chat_id=waited_message2.chat.id)
                        except: pass
                        waited_message2 = bot.send_message(message.from_user.id,
                                                           'Сделайте выбор, пожалуйста!')

        elif len(sql_open(1)) == 1:
            if message.from_user.id in [sql_open(1)[0][1]]:
                bot.send_message(message.from_user.id, 'Ожидание второго игрока.. \n')
            else:
                bot.send_message(message.from_user.id, 'В очереди есть игрок, который хочет играть.\n'
                                                       'Если вы готовы, введите: /search')
        else:
            bot.send_message(message.from_user.id, 'Игра ещё не началась. \n'
                                                   'Введите /search')

def game(message, toggle = 0):
    global GAME
    global m1, m2
    global ended_rounds, temp_round, checker_bug, temp_theme
    global math_or_no

    def players_stats_reftesh():
        global GAME
        GAME['player1']['ended'] = 0
        GAME['player2']['ended'] = 0

        GAME['player1']['lives'] = get_lives(temp_theme)  # set LIVES
        GAME['player2']['lives'] = get_lives(temp_theme)  # set LIVES

        GAME['player1']['win'] = 0
        GAME['player2']['win'] = 0

    def get_info(player):
        global GAME
        global temp_theme
        global math_or_no

        if temp_theme == 'Math':
            temp_temp_theme = 'арифметика'
        elif temp_theme == 'rus_from_eng':
            temp_temp_theme = 'перевод с русского на английский'
        elif temp_theme == 'eng_from_rus':
            temp_temp_theme = 'перевод с английского на русский'
        elif temp_theme == 'questions':
            temp_temp_theme = 'разные вопросы'

        def get_promt(player):
            global indx

            temp_answ = ''
            if len(GAME['answer']) > 1:
                if indx:
                    pass
                else:
                    indx = [randint(0, len(GAME['answer']) - 1) for _ in range(8)]
                    indx = [x for x in indx]
                temp_answ = ['*' if x != ' ' else ' ' for x in GAME['answer']]  # *****

                if temp_theme != 'Math':
                    if GAME[f'player{player}']['lives'] == 3 or len(GAME['answer']) == 2 and GAME[f'player{player}']['lives'] != 4:
                        temp_answ[indx[0]] = GAME['answer'][indx[0]]
                    elif GAME[f'player{player}']['lives'] == 2:
                        temp_answ[indx[0]] = GAME['answer'][indx[0]]
                        temp_answ[indx[1]] = GAME['answer'][indx[1]]
                        if len(GAME['answer']) > 5:
                            temp_answ[indx[2]] = GAME['answer'][indx[2]]
                            temp_answ[indx[3]] = GAME['answer'][indx[3]]
                            if len(GAME['answer']) > 7:
                                temp_answ[indx[4]] = GAME['answer'][indx[4]]

                    elif GAME[f'player{player}']['lives'] == 1:
                        temp_answ[indx[0]] = GAME['answer'][indx[0]]
                        temp_answ[indx[1]] = GAME['answer'][indx[1]]
                        if len(GAME['answer']) > 5:
                            temp_answ[indx[2]] = GAME['answer'][indx[2]]
                            temp_answ[indx[3]] = GAME['answer'][indx[3]]
                            if len(GAME['answer']) > 7:
                                temp_answ[indx[4]] = GAME['answer'][indx[4]]
                                temp_answ[indx[5]] = GAME['answer'][indx[5]]
                                if len(GAME['answer']) > 9:
                                    temp_answ[indx[6]] = GAME['answer'][indx[6]]
                                    temp_answ[indx[7]] = GAME['answer'][indx[7]]

                else:
                    if GAME['player2']['lives'] == 1:
                        temp_answ[indx[0]] = GAME['answer'][indx[0]]

            return ''.join(temp_answ)

        if player == 1:
            lives = 'у вас нет жизней!' if GAME['player1']['lives'] == 0 else GAME['player1']['lives']
            score = GAME['player1']['score']
            answ = f'\n<b>Правильный ответ: </b>{GAME["answer"]}' if GAME['player1']['ended'] == 1 else ''
        elif player == 2:
            lives = 'у вас нет жизней!' if GAME['player2']['lives'] == 0 else GAME['player2']['lives']
            score = GAME['player2']['score']
            answ = f'\n<b>Правильный ответ: </b>{GAME["answer"]}' if GAME['player2']['ended'] == 1 else ''

        if not answ:
            answ = f'\n<b>Подсказка:</b> \n                             <b>{get_promt(player)}</b>'

        return f'<strong>Раунд</strong> <b>{GAME["round"]}</b>\n'\
               f'<b>Тема:</b> {temp_temp_theme}\n'\
               f'<b>Ваши жизни:</b> {lives}\n\n'\
               f'<b>{math_or_no}:</b> {GAME["question"]}{answ}\n\n'

    if GAME['wait_after_game']:  # если конец игры, но сообщение
        bot.send_message(message.chat.id, 'Подождите 5 секунд.\n'
                                          'Боту нужно отдохнуть.')
    if toggle:
        global indx
        indx = None
        sql_open(6)  # new a_q
        math_or_no = 'Пример' if temp_theme == 'Math' else 'Вопрос'

        players_stats_reftesh()

        if GAME['round'] != 0:
            sleep(1.35)

        if GAME['round'] == 10:  # END
            try:
                if m1 and m2:
                    bot.delete_message(message_id=m1.message_id, chat_id=m1.chat.id)
                    bot.delete_message(message_id=m2.message_id, chat_id=m2.chat.id)
            except:
                pass

            winner = GAME['player1']['name'] if GAME['player1']['score'] > GAME['player2']['score'] else GAME['player2']['name']
            winner = 'ничья.' if GAME['player1']['score'] == GAME['player2']['score'] else winner

            if winner != 'ничья.':
                winner_line = '<b>Он(а) опередил(a) соперника на '
                winner_line += str(abs(max(GAME['player1']['score'], GAME['player2']['score']) - min(GAME['player1']['score'], GAME['player2']['score'])))
                winner_line += ' очк.</b>\n'
            else: winner_line = f'<b>У вас одинаковое кол-во очков:</b> <i>{GAME["player1"]["score"]}</i>\n'

            for player_ in ['player1', 'player2']:
                bot.send_message(GAME[player_]['id'], f'<b>Игра окончена!</b>\n\n'
                                                        f'<b>Победитель:</b> <i>{winner}</i>\n'
                                                        f'{winner_line}\n'
                                                        f'Спасибо за игру!\n'
                                                        f'Связь:\n'
                                                        f'vk: @yeasex\n'
                                                        f'tg: @yeasex',
                                 parse_mode='HTML')
            GAME['wait_after_game'] = 1
            sleep(5)
            reset()  # RESET GAME
            return

        def get_text():
            if GAME['player1']['score'] - GAME['player2']['score'] > 6: text_p1 = 'Видно, что твой соперник совсем не использует мозг.'
            elif GAME['player1']['score'] - GAME['player2']['score'] > 2: text_p1 = 'Продолжай в том же духе!'
            elif GAME['player1']['score'] - GAME['player2']['score'] < -2: text_p1 = 'Поднажми!'
            else: text_p1 = 'Вы почти сравнялись!'
            if GAME['player2']['score'] - GAME['player1']['score'] > 6: text_p2 = 'Видно, что твой соперник совсем не использует мозг.'
            elif GAME['player2']['score'] - GAME['player1']['score'] > 2: text_p2 = 'Продолжай в том же духе!'
            elif GAME['player2']['score'] - GAME['player1']['score'] < -2: text_p2 = 'Поднажми!'
            else: text_p2 = 'Вы почти сравнялись!'
            return text_p1, text_p2

        if GAME['round'] % 3 == 0 and GAME['round'] != 0:  # 3, 6, 9, rounds
            text_p1 = get_text()[0]
            text_p2 = get_text()[1]
            bot.send_message(GAME['player1']['id'], f'<b>Статистика на {GAME["round"]} раунд:</b>\n\n'
                                                    f'<b>Ваши очки: </b><i>{GAME["player1"]["score"]}</i>\n'
                                                    f'<b>Очки {GAME["player2"]["name"]}:</b> <i>{GAME["player2"]["score"]}</i>\n\n'
                                                    f'<i>{text_p1}</i>', parse_mode='HTML')
            bot.send_message(GAME['player2']['id'], f'<b>Статистика на {GAME["round"]} раунд:</b>\n\n'
                                                    f'<b>Ваши очки: </b><i>{GAME["player2"]["score"]}</i>\n'
                                                    f'<b>Очки {GAME["player1"]["name"]}:</b> <i>{GAME["player1"]["score"]}</i>\n\n'
                                                    f'<i>{text_p2}</i>', parse_mode='HTML')
            sleep(4)
        GAME['round'] += 1

        try:
            if m1 and m2:
                bot.delete_message(message_id=m1.message_id, chat_id=m1.chat.id)
                bot.delete_message(message_id=m2.message_id, chat_id=m2.chat.id)
        except Exception as exp:
            print(exp, 'HERE')

        m1 = bot.send_message(GAME['player1']['id'], {get_info(1)}, parse_mode='HTML')
        m2 = bot.send_message(GAME['player2']['id'], {get_info(2)}, parse_mode='HTML')

    else:  # игра
        print(GAME)
        if message.from_user.id == GAME['player1']['id']:
            if GAME['player1']['lives'] == 0:  # no lives
                if GAME['player1']['ended'] and GAME['player2']['ended']:  # оба закончили
                    bot.delete_message(message_id=m2.message_id, chat_id=m2.chat.id)
                    m2 = bot.send_message(GAME['player2']['id'], f'{get_info(2)}'
                                                                 f'<b>Соперник закончил раунд. Ожидайте..</b>',
                                          parse_mode='HTML')
                    game(None, 1)  # next round
                else:
                    bot.delete_message(message_id=m1.message_id, chat_id=m1.chat.id)
                    m1 = bot.send_message(chat_id=GAME['player1']['id'], text=f'{get_info(1)}'
                                                                              f'<b>У вас кончились жизни, ожидайте хода соперника.</b>\n'
                                                                              f'<i>Принудительный выход: /exit</i>', parse_mode='HTML')
            elif GAME['player1']['ended']:
                if GAME['player2']['ended']:  # оба закончили
                    bot.delete_message(message_id=m2.message_id, chat_id=m2.chat.id)
                    m2 = bot.send_message(GAME['player2']['id'], f'{get_info(2)}'
                                                                 f'<b>Соперник закончил раунд. Ожидайте..</b>',
                                          parse_mode='HTML')
                    game(None, 1)  # next round
                else:
                    bot.delete_message(message_id=m1.message_id, chat_id=m1.chat.id)
                    m1 = bot.send_message(chat_id=GAME['player1']['id'], text=f'{get_info(1)}'
                                                                              f'<b>Ожидайте хода противника.</b>\n'
                                                                              f'<i>Чтобы завершить игру, введите: /exit</i>', parse_mode='HTML')
            elif message.text == GAME['answer']:  # ответ правильный
                GAME['player1']['score'] += GAME['player1']['lives']*2
                GAME['player1']['win'] = 1
                GAME['player1']['ended'] = 1
                bot.delete_message(chat_id=m1.chat.id, message_id=m1.message_id)
                m1 = bot.send_message(chat_id=GAME['player1']['id'], text=f'{get_info(1)}'
                                                                          f'<b>Браво!</b> <i>+{GAME["player1"]["lives"]} очк.</i>', parse_mode='HTML')
                if GAME['player2']['ended']:  # оба закончили
                    bot.delete_message(message_id=m2.message_id, chat_id=m2.chat.id)
                    m2 = bot.send_message(GAME['player2']['id'], f'{get_info(2)}'
                                                                 f'<b>Соперник закончил раунд. Ожидайте..</b>',
                                          parse_mode='HTML')
                    game(None, 1)  # next round
            elif message.text != GAME['answer']:
                GAME['player1']['lives'] -= 1
                if GAME['player1']['lives'] > 0:
                    bot.delete_message(message_id=m1.message_id, chat_id=m1.chat.id)
                    m1 = bot.send_message(chat_id=GAME['player1']['id'], text=f'{get_info(1)}'
                                                                              f'<b>Неверный ответ!</b>', parse_mode='HTML')
                else:
                    GAME['player1']['ended'] = 1
                    if GAME['player2']['ended']:  # оба закончили теперь
                        bot.delete_message(message_id=m1.message_id, chat_id=m1.chat.id)
                        bot.delete_message(message_id=m2.message_id, chat_id=m2.chat.id)
                        m1 = bot.send_message(GAME['player1']['id'], f'{get_info(1)}'
                                                                     f'<b>К сожалению, у вас кончились жизни.</b>', parse_mode='HTML')
                        m2 = bot.send_message(GAME['player2']['id'], f'{get_info(2)}'
                                                                     f'<b>Соперник закончил раунд. Ожидайте..</b>')
                        game(None, 1)
                    else:
                        bot.delete_message(message_id=m1.message_id, chat_id=m1.chat.id)
                        m1 = bot.send_message(GAME['player1']['id'], f'{get_info(1)}'
                                                                     f'<b>К сожалению, у вас кончились жизни.</b>', parse_mode='HTML')

        elif message.from_user.id == GAME['player2']['id']:
            if GAME['player2']['lives'] == 0:  # no lives
                if GAME['player1']['ended']:  # оба закончили
                    bot.delete_message(message_id=m1.message_id, chat_id=m1.chat.id)
                    m1 = bot.send_message(GAME['player1']['id'], f'{get_info(1)}'
                                                                 f'<b>Соперник закончил раунд. Ожидайте..</b>',
                                          parse_mode='HTML')
                    game(None, 1)  # next round
                else:
                    bot.delete_message(message_id=m2.message_id, chat_id=m2.chat.id)
                    m2 = bot.send_message(chat_id=GAME['player2']['id'], text=f'{get_info(2)}'
                                                                              f'<b>У вас кончились жизни, ожидайте хода соперника.</b>\n'
                                                                              f'<i>Принудительный выход: /exit</i>', parse_mode='HTML')
            elif GAME['player2']['ended']:
                if GAME['player1']['ended']:  # оба закончили CHECKER
                    bot.delete_message(message_id=m1.message_id, chat_id=m1.chat.id)
                    m1 = bot.send_message(GAME['player2']['id'], f'{get_info(2)}'
                                                                 f'<b>Соперник закончил раунд. Ожидайте..</b>',
                                          parse_mode='HTML')
                    game(None, 1)  # next round
                else:
                    bot.delete_message(message_id=m2.message_id,
                                       chat_id=m2.chat.id)
                    m2 = bot.send_message(chat_id=GAME['player2']['id'],
                                          text=f'{get_info(2)}'
                                               f'<b>Ожидайте хода противника.</b>\n'
                                               f'<i>Чтобы завершить игру, введите: /exit</i>', parse_mode='HTML')
            elif message.text == GAME['answer']:  # ответ правильный
                GAME['player2']['score'] += GAME['player2']['lives']*2
                GAME['player2']['win'] = 1
                GAME['player2']['ended'] = 1
                bot.delete_message(chat_id=m2.chat.id, message_id=m2.message_id)
                m2 = bot.send_message(chat_id=GAME['player2']['id'],
                                      text=f'{get_info(2)}'
                                           f'<b>Браво!</b> <i>+{GAME["player2"]["lives"]} очк.</i>', parse_mode='HTML')
                if GAME['player1']['ended'] and GAME['player2']['ended']:  # оба закончили
                    bot.delete_message(message_id=m1.message_id, chat_id=m1.chat.id)
                    m1 = bot.send_message(GAME['player1']['id'], f'{get_info(1)}'
                                                                 f'<b>Соперник закончил раунд. Ожидайте..</b>', parse_mode='HTML')
                    game(None, 1)  # next round
            elif message.text != GAME['answer']:
                GAME['player2']['lives'] -= 1
                if GAME['player2']['lives'] > 0:
                    bot.delete_message(message_id=m2.message_id, chat_id=m2.chat.id)
                    m2 = bot.send_message(chat_id=GAME['player2']['id'], text=f'{get_info(2)}'
                                                                              f'<b>Неверный ответ!</b>', parse_mode='HTML')
                else:
                    GAME['player2']['ended'] = 1
                    if GAME['player1']['ended']:  # оба закончили теперь
                        bot.delete_message(message_id=m2.message_id, chat_id=m1.chat.id)
                        bot.delete_message(message_id=m1.message_id, chat_id=m2.chat.id)
                        m2 = bot.send_message(GAME['player2']['id'], f'{get_info(2)}'
                                                                     f'<b>К сожалению, у вас кончились жизни.</b>', parse_mode='HTML')
                        m1 = bot.send_message(GAME['player1']['id'], f'Соперник закончил раунд. Ожидайте..')
                        game(None, 1)
                    else:
                        bot.delete_message(message_id=m2.message_id, chat_id=m2.chat.id)
                        m2 = bot.send_message(GAME['player2']['id'], f'{get_info(2)}'
                                                                     f'<b>К сожалению, у вас кончились жизни.</b>', parse_mode='HTML')
while True:
    try:
        bot.polling(none_stop=1, interval=0)
    except Exception as rror:
        sleep(3)
        try:
            if GAME['player1']['id'] and GAME['player2']['id']:
                bot.send_message(GAME['player1']['id'], 'Ошибка! Рестарт игры...')
                bot.send_message(GAME['player2']['id'], 'Ошибка! Рестарт игры...')
                reset()
        except Exception as error:
            print(error)
        print(rror)
