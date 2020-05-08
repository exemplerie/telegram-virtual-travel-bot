import random
import json
from my_project import yandex_maps


def randon_toponym(kind, country=None):
    with open('total.json', "rb") as read_file:
        data = json.load(read_file)
        if kind == 'countries':
            countries = sorted(list(data.items()), key=lambda i: len(i[1]), reverse=True)
            return random.choice(countries[:15])[0]
        else:
            choice = random.choice([str(x) for x in data[country]])
            print(choice)
            while not define_toponym('cities', choice, country=country):
                choice = random.choice([str(x) for x in data[country]])
                print(choice)
            return choice


def define_toponym(kind, toponym, country=None):
    with open('total.json', "rb") as read_file:
        data = json.load(read_file)
        if kind == 'countries':
            return toponym in [str(x) for x in data.keys()]
        else:
            if toponym in [str(x) for x in data[country]]:
                try:
                    yandex_maps.create_sights(country + ',' + toponym)
                except Exception as e:
                    return False
                return True
