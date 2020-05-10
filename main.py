import logging
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext, CommandHandler, ConversationHandler, \
    CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove, ReplyKeyboardMarkup
from telegram.error import BadRequest, RetryAfter, TimedOut, Unauthorized, NetworkError
from my_project import yandex_maps, video_module, geohelper

logging.basicConfig(filename="sample.log", format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

REQUEST_KWARGS = {
    'proxy_url': 'socks5://148.251.234.93:1080',  # Адрес прокси сервера
    # Опционально, если требуется аутентификация:
    'urllib3_proxy_kwargs': {
        'assert_hostname': 'False',
        'cert_reqs': 'CERT_NONE'}
    #     'username': 'user',
    #     'password': 'password'
    # }
}
BEGINNING, NEW_DATA, PLACE_CHOICE, CONFIRMATION, TRIP_CHOICE, VIDEO_TRIP, PHOTO_TRIP = range(7)


def start_command(update, context):
    reply_keyboard = [["Взлетаем!✈"]]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    logger.info("User %s started the conversation.", update.message.from_user.first_name)
    update.message.reply_text(
        'Привет! 👋\n'
        'Я - бот виртуальных путешествий. Все мы сейчас в непростой ситуации, '
        'когда обычные путешествия стали невозможными 😢.\n' +
        'Я помогу вам восполнить недостающие ощущения и открою дверь в мир онлайн-путешествий 🌎️!\n',
        reply_markup=markup
    )
    return BEGINNING


def wait_data(update, context):
    context.user_data['country'] = None
    context.user_data['city'] = None
    context.user_data['sights'] = None
    context.user_data['videos'] = None

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

    return NEW_DATA


def random_place(update, context):
    if not context.user_data["country"]:
        generated_place = geohelper.randon_toponym('countries')
    else:
        try:
            generated_place, sights = geohelper.randon_toponym('cities', country=context.user_data["country"])
            context.user_data['city'] = generated_place
            context.user_data['sights'] = sights
        except (ConnectionError, TimeoutError):
            stop(update, context, error_was=True)
    reply_keyboard = [[generated_place, 'Поменять 🔄']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text(
        f'Что насчет... {generated_place}?', reply_markup=markup
    )
    return PLACE_CHOICE


def choose_place(update, context):
    try:
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
            return PLACE_CHOICE
        else:
            if not context.user_data['city'] or context.user_data['city'] != update.message.text:
                sights = geohelper.define_toponym('cities', update.message.text, country=context.user_data["country"])
                if not sights:
                    update.message.reply_text(
                        'Извините, в желаемой стране данный город не найден. Проверьте правильность написания и попробуйте еще раз:\n')
                    return PLACE_CHOICE
                else:
                    context.user_data['city'] = update.message.text
                    context.user_data['sights'] = sights
            photo = yandex_maps.create_map(context.user_data['country'] + ',' + context.user_data['city'])
            reply_keyboard = [['Все верно ✅'], ['Ввести заново ❌']]
            markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
            context.bot.send_photo(
                update.message.chat_id,
                photo,
                caption='Отличный выбор!')
            update.message.reply_text(
                f'Проверьте данные на билете: {context.user_data["country"]}, {context.user_data["city"]}.',
                reply_markup=markup)

            logger.info("Place choice of %s: %s, %s", update.message.from_user.first_name, context.user_data['country'],
                        context.user_data['city'])
    except yandex_maps.SightsError:
        update.message.reply_text(
            'Извините, в данном городе я не нашел ничего интересного! Выберите, пожалуйста, другой.\n')
        return PLACE_CHOICE
    except (ConnectionError, TimeoutError, NetworkError):
        stop(update, context, error_was=True)
    return CONFIRMATION


def lets_go(update, context):
    keyboard = [[InlineKeyboardButton("Видео-экскурсия", callback_data='0'),
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
    return TRIP_CHOICE


def find_video(update, context):
    query = update.callback_query
    query.answer()
    keyboard = [[InlineKeyboardButton("Вернуться назад", callback_data='return')]]
    try:
        if context.user_data['videos'] != [] and not context.user_data['videos']:
            context.user_data['videos'] = video_module.search_video(context.user_data["city"],
                                                                    context.user_data["country"])
        videos = context.user_data['videos']
        print('v', videos)
        if not videos:
            query.edit_message_text(
                f'Извините, видео-экскурсий по городу {context.user_data["city"]} не найдено. '
            )
            logger.info("No video about %s", context.user_data['city'])
        else:
            query.edit_message_text(
                videos[int(query.data)]
            )
        if int(query.data) > 0:
            keyboard.append([InlineKeyboardButton("Предыдущее  видео", callback_data=str(int(query.data) - 1))])
        if len(videos) > int(query.data) + 1:
            keyboard.append(
                [InlineKeyboardButton("Следующее видео", callback_data=str(int(query.data) + 1))])
        markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_reply_markup(markup)

    except (ConnectionError, TimeoutError):
        markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(
            'Извините, проблемы с соединением на сервере.', reply_markup=markup)
        error(update, context)
    return VIDEO_TRIP


def find_sights(update, context):
    query = update.callback_query
    query.answer()
    keyboard = [[] for _ in range(2)]
    keyboard[1].append(InlineKeyboardButton('Вернуться назад', callback_data='return'))
    if query.data == 'new':
        if len(context.user_data['sights'][1]) < 5:
            markup = InlineKeyboardMarkup(keyboard)
            query.message.reply_text(
                f'К сожалению, новых интересных мест в городе {context.user_data["city"]} не найдено.',
                reply_markup=markup)
        else:
            generate_sights_map(context)
    try:
        need_url, sights = context.user_data['sights']
        description = '\n'.join(
            [str(x[0]) + '  -   "' + x[1]['name'] + '"\n' for x in sights.items()])
        for button in range(1, len(sights) + 1):
            keyboard[0].append(InlineKeyboardButton(str(button), callback_data=str(button)))
        keyboard[1].append(InlineKeyboardButton('Сгенерировать новую карту', callback_data='new'))
        markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(
            'Посмотрим...'
        )
        query.message.reply_photo(
            photo=need_url, caption=description)
        query.message.reply_text('Вот и наша экскурсионная карта!\n'
                                 'Какое из мест хотите посетить?', reply_markup=markup)
    except (ConnectionError, TimeoutError, telegram.error.TimedOut):
        markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text('Извините, проблемы с соединением на сервере. Попробуйте еще раз позже.',
                                reply_markup=markup)
        error(update, context)
    except Exception as e:
        print(e, type(e))
    return PHOTO_TRIP


def generate_sights_map(context):
    topomym = context.user_data['country'] + ',' + context.user_data['city']
    context.user_data['sights'] = yandex_maps.create_sights(topomym)


def alone_sight(update, context):
    query = update.callback_query
    query.answer()
    place = context.user_data["sights"][1][int(query.data)]

    query.edit_message_text(
        f'Направляемся в пункт {query.data}...'
    )
    url_place = 'https://yandex.ru/profile/' + place["id"]
    info = place.get('url')
    if not info:
        info = url_place
    caption = f'"{place["name"]}"\n\nНаходится по адресу: {place["address"]}\n\nПодробнее о месте: {info}'
    try:
        query.message.reply_photo(
            photo=url_place, caption=caption)
    except (ConnectionError, TimeoutError):
        keyboard = [[InlineKeyboardButton('Вернуться назад', callback_data='return')]]
        markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text('Извините, проблемы с соединением на сервере. Попробуйте еще раз позже.',
                                reply_markup=markup)
        error(update, context)
    except Exception as e:
        print(e)
        query.message.reply_text(caption)
    keyboard = [[] for _ in range(2)]
    keyboard[1].append(InlineKeyboardButton('Вернуться назад', callback_data='return'))
    keyboard[1].append(InlineKeyboardButton('Сгенерировать новую карту', callback_data='new'))
    for button in range(1, len(context.user_data["sights"][1]) + 1):
        if str(button) != query.data:
            keyboard[0].append(InlineKeyboardButton(str(button), callback_data=str(button)))
    markup = InlineKeyboardMarkup(keyboard)
    query.message.reply_text('Куда едем дальше?', reply_markup=markup)


def stop(update, context, error_was=None):
    text = 'Спасибо за чудесное путешествие! Не забудьте свой багаж и возвращайтесь в любое время!'
    if error_was:
        error(update, context)
        text = 'Произошла ошибка соединения с сервером. Попробуйте позже.'
    update.message.reply_text(text)
    logger.info("User %s stopped the conversation.", update.message.from_user.first_name)
    return ConversationHandler.END


def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    # Создаём объект updater.
    updater = Updater('1224664190:AAF3YUI0BmakawB8ewGTiWyGPJpCjaLhhpA', use_context=True,
                      request_kwargs=REQUEST_KWARGS)
    # Получаем из него диспетчер сообщений.
    dp = updater.dispatcher

    # updater.dispatcher.add_handler(CommandHandler('start', start_command))
    # updater.dispatcher.add_handler(CallbackQueryHandler(button))
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start_command)],

        states={
            BEGINNING: [MessageHandler(Filters.text, wait_data, pass_user_data=True),
                        ],
            NEW_DATA: [MessageHandler(Filters.regex(r'(лучайн)'), random_place, pass_user_data=True),
                       MessageHandler(Filters.text, choose_place, pass_user_data=True)
                       ],
            PLACE_CHOICE: [MessageHandler(Filters.regex(r'(оменять|случайн)'), random_place, pass_user_data=True),
                           MessageHandler(Filters.text, choose_place, pass_user_data=True)
                           ],
            CONFIRMATION: [MessageHandler(Filters.regex(r'(Верно|Да|верно|да)'), lets_go, pass_user_data=True),
                           MessageHandler(Filters.text(r'(Заново|Нет|заново|нет)'), wait_data, pass_user_data=True),
                           ],
            TRIP_CHOICE: [CallbackQueryHandler(wait_data, pattern='return', pass_user_data=True),
                          CallbackQueryHandler(find_video, pattern='0', pass_user_data=True),
                          CallbackQueryHandler(find_sights, pattern='photo', pass_user_data=True)],
            VIDEO_TRIP: [CallbackQueryHandler(lets_go, pattern='return', pass_user_data=True),
                         CallbackQueryHandler(find_video, pattern='\d', pass_user_data=True),
                         ],
            PHOTO_TRIP: [CallbackQueryHandler(lets_go, pattern='return', pass_user_data=True),
                         CallbackQueryHandler(find_sights, pattern='new', pass_user_data=True),
                         CallbackQueryHandler(alone_sight, pattern='\d', pass_user_data=True),
                         ]
        },

        fallbacks=[CommandHandler("stop", stop)]
    )

    dp.add_handler(conv_handler)
    dp.add_error_handler(error)
    # Запускаем цикл приема и обработки сообщений.
    updater.start_polling()

    # Ждём завершения приложения.
    updater.idle()


# Запускаем функцию main() в случае запуска скрипта.
if __name__ == '__main__':
    main()
