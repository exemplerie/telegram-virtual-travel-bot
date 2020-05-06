# Импортируем необходимые классы.
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext, CommandHandler, ConversationHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove, ReplyKeyboardMarkup
from my_project import yandex_maps, video_module, geohelper

REQUEST_KWARGS = {
    'proxy_url': 'socks5://47.241.16.16:1080',  # Адрес прокси сервера
    # Опционально, если требуется аутентификация:
    'urllib3_proxy_kwargs': {
        'assert_hostname': 'False',
        'cert_reqs': 'CERT_NONE'}
    #     'username': 'user',
    #     'password': 'password'
    # }
}


def find_video(update, context):
    topomym = update.message.text
    try:
        video = '\n'.join(video_module.search_video(topomym))
        update.message.reply_text(
            video
        )
    except Exception as error:
        print(error)
        update.message.reply_text(
            f'По запросу "{update.message.text}" ничего не найдено. '
        )


def find_sights(update, context):
    topomym = update.message.text
    try:
        need_url, sights = yandex_maps.create_sights(topomym)
        description = '\n'.join(
            [str(x[0]) + '  -   "' + x[1]['name'] + '"' + '\nАдрес:     ' + x[1]['address'] for x in sights.items()])
        context.bot.send_photo(
            update.message.chat_id,
            need_url,
            caption=description
        )
    except yandex_maps.ToponymError:
        update.message.reply_text(
            f'По запросу "{update.message.text}" ничего не найдено. '
        )
    except yandex_maps.SightsError:
        update.message.reply_text(
            f'Интересных мест в данном городе маловато. Попробуйте выбрать другой!'
        )


def start_command(update, context):
    reply_keyboard = [["Взлетаем!✈"]]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text(
        'Привет! 👋\n'
        'Я - бот виртуальных путешествий. Все мы сейчас в непростой ситуации, '
        'когда обычные путешествия стали невозможными 😢.\n' +
        'Я помогу вам восполнить недостающие ощущения и открою дверь в мир онлайн-путешествий🌎️!\n',
        reply_markup=markup
    )
    return 1


def pre_flight(update, context):
    reply_keyboard = [['да', 'нет']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text(
        'Вы уже определитесь с пунктом назначения?\n',
        reply_markup=markup
    )
    return 2


def wait_data(update, context):
    context.user_data['country'] = None
    context.user_data['city'] = None

    update.message.reply_text(
        'Пожалуйста, введите желаемую страну:\n'
    )
    return 3


def choose_place(update, context):
    print(not context.user_data["country"], not context.user_data["city"])
    if not context.user_data["country"]:
        if not geohelper.define_toponym('countries', update.message.text):
            update.message.reply_text(
                'Извините, данная страна не найдена. Проверьте правильность написания и попробуйте еще раз:\n')
        else:
            context.user_data['country'] = update.message.text
            update.message.reply_text(
                'Принято, теперь введите город:\n')
        return 3
    elif not context.user_data["city"]:
        if not geohelper.define_toponym('cities', update.message.text):
            update.message.reply_text(
                'Извините, данный город не найден в желаемой стране. Проверьте правильность написания и попробуйте еще раз:\n')
            return 3
        else:
            context.user_data['city'] = update.message.text
        reply_keyboard = [['Все верно✅'], ['Ввести заново❌']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        update.message.reply_text(
            f'Отлично! Проверьте данные на билете: {context.user_data["country"], context.user_data["city"]}.',
            reply_markup=markup)
    return 4


def lets_go(update, context):
    keyboard = [[InlineKeyboardButton("Видео-экскурсия", callback_data='1'),
                 InlineKeyboardButton("Фото-экскурсия", callback_data='2')]]
    markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        f'Пожалуйста, пристегните ремни безопасности, приведите спинки кресел в вертикальное положение...\n'
        'Мы уже на месте! Теперь вам предстоит выбрать вид нашего тура по городу на свой вкус:',
        reply_markup=markup)


def stop(update, context):
    update.message.reply_text(
        'Очень жаль!')
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
            1: [MessageHandler(Filters.text, pre_flight, pass_user_data=True),
                ],
            2: [MessageHandler(Filters.text('да'), wait_data, pass_user_data=True),
                MessageHandler(Filters.text('нет'), stop),
                ],
            3: [MessageHandler(Filters.text, choose_place, pass_user_data=True)
                ],
            4: [MessageHandler(Filters.text('Все верно✅'), lets_go, pass_user_data=True),
                MessageHandler(Filters.text('Ввести заново❌'), wait_data, pass_user_data=True),
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
