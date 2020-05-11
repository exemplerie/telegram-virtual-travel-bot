# -*- coding: utf-8 -*-
import requests
import my_project.config as config


def language_definition(need_text):  # определение языка для перевода
    url = 'https://translate.yandex.net/api/v1.5/tr.json/detect'
    params = {
        'key': config.TRANSLATER_KEY,
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
        'key': config.TRANSLATER_KEY,
        'text': need_text,
        'lang': need_lang
    }
    response = requests.get(url, params)
    answer = response.json()['text'][0]
    return answer
