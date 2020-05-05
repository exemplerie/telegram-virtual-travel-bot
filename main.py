# Импортируем необходимые классы.
from telegram.ext import Updater, MessageHandler, Filters
from telegram.ext import CallbackContext, CommandHandler
from my_project import geo
from my_project import video_module

REQUEST_KWARGS = {
    'proxy_url': 'socks5://85.10.235.14:1080',  # Адрес прокси сервера
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
        need_url, sights = geo.create_sights(topomym)
        description = '\n'.join(
            [str(x[0]) + '  -   "' + x[1]['name'] + '"' + '\nАдрес:     ' + x[1]['address'] for x in sights.items()])
        context.bot.send_photo(
            update.message.chat_id,
            need_url,
            caption=description
        )
    except geo.ToponymError:
        update.message.reply_text(
            f'По запросу "{update.message.text}" ничего не найдено. '
        )
    except geo.SightsError:
        update.message.reply_text(
            f'Интересных мест в данном городе маловато. Попробуйте выбрать другой!'
        )


def main():
    # Создаём объект updater.
    updater = Updater('1125322487:AAFql3B0ov5mMDFdUrFQIUJDAhfw7XR3wLw', use_context=True,
                      request_kwargs=REQUEST_KWARGS)
    # Получаем из него диспетчер сообщений.
    dp = updater.dispatcher

    text_handler = MessageHandler(Filters.text, find_sights)

    # Регистрируем обработчик в диспетчере.
    dp.add_handler(text_handler)
    # Запускаем цикл приема и обработки сообщений.
    updater.start_polling()

    # Ждём завершения приложения.
    updater.idle()


# Запускаем функцию main() в случае запуска скрипта.
if __name__ == '__main__':
    main()
