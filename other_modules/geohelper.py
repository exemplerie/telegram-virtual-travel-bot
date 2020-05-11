# -*- coding: utf-8 -*-
import random
import json
from other_modules import yandex_maps


def randon_toponym(kind, country=None):  # выбор случайной страны или города
    with open('other_modules/total.json', "rb") as read_file:
        data = json.load(read_file)
        if kind == 'countries':
            countries = sorted(list(data.items()), key=lambda i: len(i[1]), reverse=True)
            return random.choice(countries[:15])[0]
        else:
            choice = None
            sights = None
            while not sights:
                choice = random.choice([str(x) for x in data[country]])
                sights = define_toponym('cities', choice, country=country)
            return choice, sights


def define_toponym(kind, toponym, country=None):  # поиск выбранной страны или города по базе
    with open('other_modules/total.json', "rb") as read_file:
        data = json.load(read_file)
        if kind == 'countries':
            return toponym in [str(x) for x in data.keys()]
        else:
            if toponym in [str(x) for x in data[country]]:
                try:
                    sights = yandex_maps.create_sights(country + ',' + toponym)
                except Exception:
                    return None
                return sights
