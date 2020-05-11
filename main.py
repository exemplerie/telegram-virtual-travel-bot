# -*- coding: utf-8 -*-
import logging
import os
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, ConversationHandler, \
    CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.error import BadRequest, TelegramError
from emoji import emojize
from other_modules import yandex_maps, video_module, geohelper

logging.basicConfig(filename="sample.log", format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN')

# использующиеся состояния
BEGINNING, NEW_DATA, PLACE_CHOICE, CONFIRMATION, TRIP_CHOICE, VIDEO_TRIP, PHOTO_TRIP = range(7)


def help(update, context):  # обработка команды помощи
    update.message.reply_text('Как мной пользоваться?\nВсе очень просто, напиши команду /start, выбери '
                              'интересующую точку планеты и исследуй ее!\n Для выхода используй команду /stop.')


def start_command(update, context):  # обработка стартовой команды
    reply_keyboard = [[emojize("Взлетаем!:airplane:", use_aliases=True)]]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    logger.info("User %s started the conversation.", update.message.from_user.first_name)
    update.message.reply_text(emojize(
        'Привет! :wave:\n'
        'Я - бот виртуальных путешествий. Все мы сейчас в непростой ситуации, '
        'когда обычные путешествия стали невозможными :cry:.\n' +
        'Я помогу вам восполнить недостающие ощущения и открою дверь в мир онлайн-путешествий :earth_asia:️!\n',
        use_aliases=True), reply_markup=markup
    )
    return BEGINNING


def wait_data(update, context):  # обновление данных пользователя (при выборе нового места)
    context.user_data['country'] = None
    context.user_data['city'] = None
    context.user_data['sights'] = None
    context.user_data['videos'] = None

    reply_keyboard = [[emojize('Выбрать случайную страну :national_park:', use_aliases=True)]]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

    query = update.callback_query
    if not query:
        update.message.reply_text(
            'Сначала нужно определиться с пунктом назначения!\n'
            'Пожалуйста, введите желаемую страну:', reply_markup=markup
        )
    else:
        query = update.callback_query
        query.answer()
        query.edit_message_text('Возвращаемся!')
        query.message.reply_text('Пожалуйста, введите желаемую страну:', reply_markup=markup)
    return NEW_DATA


# выборка случайного места (страна - из самых заполненных городами, город по выбранной стране)
def random_place(update, context):
    generated_place = None
    if not context.user_data["country"]:
        generated_place = geohelper.randon_toponym('countries')
    else:
        try:
            generated_place, sights = geohelper.randon_toponym('cities', country=context.user_data["country"])
            context.user_data['city'] = generated_place
            context.user_data['sights'] = sights
        except (Exception, TelegramError):
            error(update, context)
    reply_keyboard = [[generated_place, emojize('Поменять :arrows_counterclockwise:', use_aliases=True)]]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text(
        f'Что насчет... {generated_place}?', reply_markup=markup
    )
    return PLACE_CHOICE


# проверка выбранного места (страна и город должны находится в базе данных,
# город должен иметь хотя бы одно интересное место в Яндекс.Организациях)
def choose_place(update, context):
    try:
        if not context.user_data["country"]:
            if not geohelper.define_toponym('countries', update.message.text):
                update.message.reply_text(
                    'Извините, данная страна не найдена. Проверьте правильность написания и попробуйте еще раз:\n')
            else:
                reply_keyboard = [[emojize('Выбрать случайный город :cityscape:', use_aliases=True)]]
                markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
                context.user_data['country'] = update.message.text
                update.message.reply_text(
                    'Принято, теперь введите город:\n', reply_markup=markup)
            return PLACE_CHOICE
        else:
            if not context.user_data['city'] or context.user_data['city'] != update.message.text:
                sights = geohelper.define_toponym('cities', update.message.text, country=context.user_data["country"])
                context.user_data['city'] = update.message.text
                context.user_data['sights'] = sights
            photo = yandex_maps.create_map(context.user_data['country'] + ',' + context.user_data['city'])
            reply_keyboard = [[emojize('Все верно :white_check_mark:', use_aliases=True)],
                              [emojize('Ввести заново :x:', use_aliases=True)]]
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
    except yandex_maps.SightsError:  # не нашлось ни одной достопримечательности
        update.message.reply_text(
            'Извините, в данном городе я не нашел ничего интересного! Выберите, пожалуйста, другой.\n')
        return PLACE_CHOICE
    except (Exception, TelegramError):
        error(update, context)
        return CONFIRMATION
    return CONFIRMATION


# выбор интерактивных функций
def lets_go(update, context):
    keyboard = [[InlineKeyboardButton("Видео-экскурсия", callback_data='0'),
                 InlineKeyboardButton("Фото-экскурсия", callback_data='photo')],
                [InlineKeyboardButton("Поменять пункт назначения", callback_data='change')]]
    markup = InlineKeyboardMarkup(keyboard)
    try:
        update.message.reply_text(
            emojize('Пожалуйста, пристегните ремни безопасности, приведите спинки кресел в вертикальное положение...\n'
                    'Мы уже на месте! :man_pilot: Теперь вам предстоит выбрать вид нашего тура по городу на свой вкус:',
                    use_aliases=True),
            reply_markup=markup)
    except (Exception, TelegramError):
        query = update.callback_query
        query.answer()
        query.edit_message_text(
            emojize('Пожалуйста, пристегните ремни безопасности, приведите спинки кресел в вертикальное положение...\n'
                    'Мы уже на месте! :man_pilot: Теперь вам предстоит выбрать вид нашего тура по городу на свой вкус:',
                    use_aliases=True),
            reply_markup=markup)
    return TRIP_CHOICE


# поиск видео по API youtube
def find_video(update, context):
    query = update.callback_query
    query.answer()
    keyboard = [[InlineKeyboardButton("Вернуться назад", callback_data='return')]]
    try:
        if context.user_data['videos'] != [] and not context.user_data['videos']:
            context.user_data['videos'] = video_module.search_video(context.user_data["city"],
                                                                    context.user_data["country"])
        videos = context.user_data['videos']
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
    except (Exception, TelegramError):
        error(update, context)
        return VIDEO_TRIP
    return VIDEO_TRIP


# представление карты-маршрута по достопримечательностям; изначальная создается при выборе места (для
# минимального количества запросов к API карт), обновляется при запросе пользователем соответствующей функции.
# карта и ее точки хранятся в словаре-данных о пользователе
def find_sights(update, context):
    query = update.callback_query
    query.answer()
    keyboard = [[] for _ in range(2)]
    keyboard[1].append(InlineKeyboardButton('Вернуться назад', callback_data='return'))
    if query.data == 'new':  # обновление карты
        if len(context.user_data['sights'][1]) < 5:  # если невозможно добавить новые точки
            markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(
                f'К сожалению, новых интересных мест в городе {context.user_data["city"]} не найдено.',
                reply_markup=markup)
            return PHOTO_TRIP
        else:
            try:
                generate_sights_map(context)
            except (Exception, TelegramError):
                error(update, context)
                return PHOTO_TRIP
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
        query.message.reply_text(emojize('Вот и наша экскурсионная карта! :world_map:\n'
                                         'Какое из мест хотите посетить?', use_aliases=True), reply_markup=markup)
    except (Exception, TelegramError):
        error(update, context)
        return PHOTO_TRIP
    return PHOTO_TRIP


def generate_sights_map(context):  # генератор карты достопримечательностей
    topomym = context.user_data['country'] + ',' + context.user_data['city']
    context.user_data['sights'] = yandex_maps.create_sights(topomym)


# информация о месте (фото, если есть, сайт или ссылка на страницу в яндекс.организациях)
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
    keyboard = [[] for _ in range(2)]
    keyboard[1].append(InlineKeyboardButton('Вернуться назад', callback_data='return'))
    keyboard[1].append(InlineKeyboardButton('Сгенерировать новую карту', callback_data='new'))
    for button in range(1, len(context.user_data["sights"][1]) + 1):  # кнопки создаются по оставшимся точкам
        if str(button) != query.data:
            keyboard[0].append(InlineKeyboardButton(str(button), callback_data=str(button)))
    markup = InlineKeyboardMarkup(keyboard)
    try:
        query.message.reply_photo(photo=url_place, caption=caption)
        query.message.reply_text('Куда едем дальше?', reply_markup=markup)
    except BadRequest:  # если нет фото
        query.message.reply_text(caption)
        query.message.reply_text('Куда едем дальше?', reply_markup=markup)
    except (Exception, TelegramError) as e:
        print(e)
        error(update, context)


def stop(update, context):  # обработка выхода из диалога
    text = emojize(
        'Спасибо за чудесное путешествие! :luggage:\nНе забудьте свой багаж и возвращайтесь в любое время!',
        use_aliases=True)
    update.message.reply_text(text)
    logger.info("User %s stopped the conversation.", update.message.from_user.first_name)
    return ConversationHandler.END


def error(update, context):  # обработка ошибок
    logger.warning('Update "%s" caused error "%s"', update, context.error)
    query = update.callback_query
    keyboard = [[InlineKeyboardButton('Вернуться назад', callback_data='error_return')]]
    markup = InlineKeyboardMarkup(keyboard)
    if query:
        query.edit_message_text(
            'Извините, проблемы с соединением на сервере. Попробуйте еще раз позже', reply_markup=markup)
    else:
        update.message.reply_text(
            'Извините, проблемы с соединением на сервере. Попробуйте еще раз позже', reply_markup=markup)


def main():
    # Создаём объект updater.
    updater = Updater(BOT_TOKEN, use_context=True)
    # Получаем из него диспетчер сообщений.
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start_command)],

        states={
            BEGINNING: [MessageHandler(Filters.text, wait_data, pass_user_data=True),
                        ],
            NEW_DATA: [MessageHandler(Filters.regex(r'(лучайн)'), random_place, pass_user_data=True),
                       MessageHandler(Filters.text, choose_place, pass_user_data=True)
                       ],
            PLACE_CHOICE: [MessageHandler(Filters.regex(r'(оменять|случайн)'), random_place, pass_user_data=True),
                           MessageHandler(Filters.text, choose_place, pass_user_data=True),
                           CallbackQueryHandler(wait_data, pattern=r'error_return', pass_user_data=True)
                           ],
            CONFIRMATION: [MessageHandler(Filters.regex(r'(Верно|Да|верно|да)'), lets_go, pass_user_data=True),
                           MessageHandler(Filters.text(r'(Заново|Нет|заново|нет)'), wait_data, pass_user_data=True),
                           CallbackQueryHandler(wait_data, pattern=r'error_return', pass_user_data=True),
                           CallbackQueryHandler(stop, pattern='stop', pass_user_data=True)],
            TRIP_CHOICE: [CallbackQueryHandler(wait_data, pattern='change', pass_user_data=True),
                          CallbackQueryHandler(find_video, pattern='0', pass_user_data=True),
                          CallbackQueryHandler(find_sights, pattern='photo', pass_user_data=True),
                          CallbackQueryHandler(lets_go, pattern=r'error_return', pass_user_data=True)
                          ],
            VIDEO_TRIP: [CallbackQueryHandler(lets_go, pattern=r'return|error_return', pass_user_data=True),
                         CallbackQueryHandler(find_video, pattern=r'\d', pass_user_data=True)
                         ],
            PHOTO_TRIP: [CallbackQueryHandler(lets_go, pattern=r'return|error_return', pass_user_data=True),
                         CallbackQueryHandler(find_sights, pattern=r'new|error_return', pass_user_data=True),
                         CallbackQueryHandler(alone_sight, pattern=r'\d', pass_user_data=True)
                         ]
        },
        fallbacks=[CommandHandler("stop", stop)]
    )

    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(conv_handler)
    dp.add_error_handler(error)
    # Запускаем цикл приема и обработки сообщений.
    updater.start_polling()

    # Ждём завершения приложения.
    updater.idle()


# Запускаем функцию main() в случае запуска скрипта.
if __name__ == '__main__':
    main()
