# Импортируем необходимые классы.
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext, CommandHandler, ConversationHandler, \
    CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove, ReplyKeyboardMarkup
from my_project import yandex_maps, video_module, geohelper

REQUEST_KWARGS = {
    'proxy_url': 'socks5://80.240.24.119:31444',  # Адрес прокси сервера
    # Опционально, если требуется аутентификация:
    'urllib3_proxy_kwargs': {
        'assert_hostname': 'False',
        'cert_reqs': 'CERT_NONE'}
    #     'username': 'user',
    #     'password': 'password'
    # }
}


def find_video(update, context):
    query = update.callback_query
    query.answer()
    topomym = context.user_data['city']
    keyboard = [[InlineKeyboardButton("Вернуться назад", callback_data='return')]]
    try:
        videos = video_module.search_video(topomym)
        if not videos:
            query.edit_message_text(
                f'Извините, видео-экскурсий по городу {update.message.text} не найдено. '
            )
        if int(query.data) > 0:
            keyboard.append([InlineKeyboardButton("Предыдущее  видео", callback_data=str(int(query.data) - 1))])
        if len(videos) > int(query.data) + 1:
            keyboard.append(
                [InlineKeyboardButton("Следующее видео", callback_data=str(int(query.data) + 1))])
        markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(
            videos[int(query.data)],
            reply_markup=markup
        )
    except Exception as error:

        markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(
            'Извините, проблемы с соединением на сервере.', reply_markup=markup)
    return 6


def find_sights(update, context):
    query = update.callback_query
    query.answer()
    topomym = context.user_data['city']
    try:
        need_url, sights = yandex_maps.create_sights(topomym)
        context.user_data['sights'] = sights
        description = '\n'.join(
            [str(x[0]) + '  -   "' + x[1]['name'] + '"\n' for x in sights.items()])

        keyboard = [[]]
        for button in range(1,len(sights) + 1):
            keyboard[0].append(InlineKeyboardButton(str(button), callback_data=str(button)))
        markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(
            'Посмотрим...'
        )
        query.message.reply_photo(
            photo=need_url, caption=description)
        query.message.reply_text('Вот и наша экскурсионная карта!\n'
                                 'Какое из мест хотите посетить?', reply_markup=markup)
    except yandex_maps.ToponymError:
        query.edit_message_text(
            f'По запросу "{update.message.text}" ничего не найдено. '
        )
    except yandex_maps.SightsError:
        query.edit_message_text(
            f'Интересных мест в данном городе маловато. Попробуйте выбрать другой!'
        )
    except Exception as e:
        print(e)
    return 7


def alone_sight(update, context):
    query = update.callback_query
    query.answer()
    place = context.user_data["sights"][int(query.data)]

    query.edit_message_text(
        f'Направляемся в пункт {query.data}...'
    )
    url_place = 'https://yandex.ru/profile/' + place["id"]
    caption = f'"{place["name"]}"\n\nНаходится по адресу: {place["address"]}\n\nПодробнее о месте: {url_place}'
    try:
        query.message.reply_photo(
            photo=url_place, caption=caption)
    except Exception:
        query.message.reply_text(caption)
    keyboard = [[]]
    keyboard.insert(0, [[InlineKeyboardButton('Вернуться назад', callback_data='return')]])
    for button in range(1,len(context.user_data["sights"]) + 1):
        if str(button) != query.data:
            keyboard[0].append(InlineKeyboardButton(str(button), callback_data=str(button)))
    markup = InlineKeyboardMarkup(keyboard)
    query.message.reply_text('Куда едем дальше?', reply_markup=markup)


def start_command(update, context):
    reply_keyboard = [["Взлетаем!✈"]]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text(
        'Привет! 👋\n'
        'Я - бот виртуальных путешествий. Все мы сейчас в непростой ситуации, '
        'когда обычные путешествия стали невозможными 😢.\n' +
        'Я помогу вам восполнить недостающие ощущения и открою дверь в мир онлайн-путешествий 🌎️!\n',
        reply_markup=markup
    )
    return 1


def wait_data(update, context):
    context.user_data['country'] = None
    context.user_data['city'] = None

    reply_keyboard = [['Выбрать случайную страну 🏞']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

    try:
        update.message.reply_text(
            'Сначала нужно определиться с пунктом назначения!\n'
            'Пожалуйста, введите желаемую страну:', reply_markup=markup
        )
    except Exception:
        query = update.callback_query
        query.answer()
        query.edit_message_text('Возвращаемся!')
        query.message.reply_text('Пожалуйста, введите желаемую страну:', reply_markup=markup)

    return 2


def random_place(update, context):
    if not context.user_data["country"]:
        generated_place = geohelper.randon_toponym('countries')
    elif not context.user_data["city"]:
        generated_place = geohelper.randon_toponym('cities', country=context.user_data["country"])
    reply_keyboard = [[generated_place, 'Поменять 🔄']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text(
        f'Что насчет... {generated_place}?', reply_markup=markup
    )
    return 3


def choose_place(update, context):
    if not context.user_data["country"]:
        if not geohelper.define_toponym('countries', update.message.text):
            update.message.reply_text(
                'Извините, данная страна не найдена. Проверьте правильность написания и попробуйте еще раз:\n')
        else:
            reply_keyboard = [['Выбрать случайный город 🏙']]
            markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
            context.user_data['country'] = update.message.text
            update.message.reply_text(
                'Принято, теперь введите город:\n', reply_markup=markup)
        return 3
    elif not context.user_data["city"]:
        if not geohelper.define_toponym('cities', update.message.text, country=context.user_data["country"]):
            update.message.reply_text(
                'Извините, в желаемой стране данный город не найден. Проверьте правильность написания и попробуйте еще раз:\n')
            return 3
        else:
            context.user_data['city'] = update.message.text
        reply_keyboard = [['Все верно ✅'], ['Ввести заново ❌']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        update.message.reply_text(
            f'Отлично! Проверьте данные на билете: {context.user_data["country"]}, {context.user_data["city"]}.',
            reply_markup=markup)
    return 4


def lets_go(update, context):
    keyboard = [[InlineKeyboardButton("Видео-экскурсия", callback_data='video'),
                 InlineKeyboardButton("Фото-экскурсия", callback_data='photo')],
                [InlineKeyboardButton("Поменять пункт назначения", callback_data='return')]]
    markup = InlineKeyboardMarkup(keyboard)
    try:
        update.message.reply_text(
            f'Пожалуйста, пристегните ремни безопасности, приведите спинки кресел в вертикальное положение...\n'
            'Мы уже на месте! Теперь вам предстоит выбрать вид нашего тура по городу на свой вкус:',
            reply_markup=markup)
    except Exception:
        query = update.callback_query
        query.answer()
        query.edit_message_text(
            f'Пожалуйста, пристегните ремни безопасности, приведите спинки кресел в вертикальное положение...\n'
            'Мы уже на месте! Теперь вам предстоит выбрать вид нашего тура по городу на свой вкус:',
            reply_markup=markup)
    return 5


def stop(update, context):
    update.message.reply_text(
        'Спасибо за чудесное путшествие! Не забудьте свой багаж и возвращайтесь в любое время!')
    return ConversationHandler.END


def main():
    # Создаём объект updater.
    updater = Updater('1125322487:AAFql3B0ov5mMDFdUrFQIUJDAhfw7XR3wLw', use_context=True,
                      request_kwargs=REQUEST_KWARGS)
    # Получаем из него диспетчер сообщений.
    dp = updater.dispatcher

    # updater.dispatcher.add_handler(CommandHandler('start', start_command))
    # updater.dispatcher.add_handler(CallbackQueryHandler(button))
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start_command)],

        states={
            1: [MessageHandler(Filters.text, wait_data, pass_user_data=True),
                ],
            2: [MessageHandler(Filters.text('Выбрать случайную страну 🏞'), random_place),
                MessageHandler(Filters.text, choose_place, pass_user_data=True)
                ],
            3: [MessageHandler(Filters.text('Поменять 🔄'), random_place),
                MessageHandler(Filters.text('Выбрать случайный город 🏙'), random_place),
                MessageHandler(Filters.text, choose_place, pass_user_data=True)
                ],
            4: [MessageHandler(Filters.text('Все верно ✅'), lets_go, pass_user_data=True),
                MessageHandler(Filters.text('Ввести заново ❌'), wait_data, pass_user_data=True),
                ],
            5: [CallbackQueryHandler(wait_data, pattern='return', pass_user_data=True),
                CallbackQueryHandler(find_video, pattern='video', pass_user_data=True),
                CallbackQueryHandler(find_sights, pattern='photo', pass_user_data=True)],
            6: [CallbackQueryHandler(lets_go, pattern='return', pass_user_data=True),
                CallbackQueryHandler(find_video, pattern='\d', pass_user_data=True),
                ],
            7: [CallbackQueryHandler(lets_go, pattern='return', pass_user_data=True),
                CallbackQueryHandler(alone_sight, pattern='\d', pass_user_data=True),
                ]
        },

        fallbacks=[CommandHandler("stop", stop)]
    )

    dp.add_handler(conv_handler)
    # Запускаем цикл приема и обработки сообщений.
    updater.start_polling()

    # Ждём завершения приложения.
    updater.idle()


# Запускаем функцию main() в случае запуска скрипта.
if __name__ == '__main__':
    main()
