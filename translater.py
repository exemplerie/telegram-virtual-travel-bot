# -*- coding: utf-8 -*-
import requests


def language_definition(need_text):  # определение языка для перевода
    url = 'https://translate.yandex.net/api/v1.5/tr.json/detect'
    params = {
        'key': 'trnsl.1.1.20200403T162608Z.d7edbc9ced7c8336.7dbb117d83ccb96bd8d489cc042671def3e06339',
        'text': need_text
    }
    response = requests.get(url, params)
    answer = response.json()['lang']
    return answer


def translate_text(need_text):  # перевод на английский или русский (для поиска по иностранным youtube-каналам)
    lang = language_definition(need_text)
    if lang == 'ru':
        need_lang = 'en'
    else:
        need_lang = 'ru'
    url = 'https://translate.yandex.net/api/v1.5/tr.json/translate'
    params = {
        'key': 'trnsl.1.1.20200403T162608Z.d7edbc9ced7c8336.7dbb117d83ccb96bd8d489cc042671def3e06339',
        'text': need_text,
        'lang': need_lang
    }
    response = requests.get(url, params)
    answer = response.json()['text'][0]
    return answer
