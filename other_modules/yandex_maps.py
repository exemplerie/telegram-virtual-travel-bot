# -*- coding: utf-8 -*-
import requests
import random
import os

ORGANISATIONS_KEY = os.environ.get('ORGANISATIONS_KEY')
GEOCODE_KEY = os.environ.get('GEOCODE_KEY')

class SightsError(Exception):
    pass


def create_sights(place):  # создание карты-маршрута с помощью API поиска по организациям
    toponym = geocode_search(place)
    toponym_point = [float(x) for x in toponym["Point"]["pos"].split(" ")]

    search_api_server = "https://search-maps.yandex.ru/v1/"
    api_key = ORGANISATIONS_KEY
    address_ll = "{0},{1}".format(*toponym_point)

    sights = ['достопримечательность', 'памятник', 'музей', 'галерея']
    total_points = {}
    all_points = []

    search_params = {
        "apikey": api_key,
        "lang": "ru_RU",
        "ll": address_ll,
        "type": "biz"
    }

    for kind_sights in range(len(sights)):
        search_params["text"] = sights[kind_sights]
        response = requests.get(search_api_server, params=search_params)
        json_response = response.json()
        organizations = json_response.get("features")
        if not organizations:
            continue
        all_points.extend(organizations)

    if not all_points:  # если нет ни одной достопримечательности
        raise SightsError

    # выбор случайных мест, фильтрация на случай повторений на одной карте
    if len(all_points) <= 5:
        need_points = []
        for x in all_points:
            if not need_points:
                need_points.append(x)
            elif x["properties"]["name"] not in [y["properties"]["name"] for y in need_points]:
                need_points.append(x)
    else:
        need_points = random.choices(all_points, k=5)
        while len(set([x["properties"]["name"] for x in need_points])) < 5:
            need_points = random.choices(all_points, k=5)

    for org in need_points:
        org_point = org["geometry"]["coordinates"]
        org_point = "{0},{1}".format(org_point[0], org_point[1])
        org_dict = {'point': org_point, 'name': org["properties"]["name"],
                    'id': org["properties"]["CompanyMetaData"]['id'],
                    'url': org["properties"]["CompanyMetaData"].get('url')}
        total_points[len(total_points) + 1] = org_dict
        if "CompanyMetaData" in org["properties"] and org["properties"]["CompanyMetaData"].get("address"):
            total_points[len(total_points)]['address'] = org["properties"]["CompanyMetaData"]["address"]
        elif "description" in org["properties"]:
            total_points[len(total_points)]['address'] = org["properties"]["description"]

    map_params = {
        "l": 'sat,skl',
        "pt": "~".join([str(x[1]['point']) + ',pmlbl' + str(x[0]) for x in total_points.items()])
    }
    map_api_server = "http://static-maps.yandex.ru/1.x/"
    response = requests.get(map_api_server, params=map_params)
    return response.url, total_points


def create_map(place):  # создание карты для представления выбранного города, static API
    toponym = geocode_search(place)
    toponym_point = [float(x) for x in toponym["Point"]["pos"].split(" ")]

    lower_corner = toponym['boundedBy']['Envelope']['lowerCorner'].split()
    upper_corner = toponym['boundedBy']['Envelope']['upperCorner'].split()
    width = abs(float(upper_corner[0]) - float(lower_corner[0])) / 2.0
    height = abs(float(upper_corner[1]) - float(lower_corner[1])) / 2.0
    need_spn = f"{width},{height}"

    map_api_server = "http://static-maps.yandex.ru/1.x/"
    map_params = {
        'll': "{0},{1}".format(*toponym_point),
        'spn': need_spn,
        "l": 'sat,skl'
    }
    response = requests.get(map_api_server, params=map_params)
    photo_map = response.url

    return photo_map


def geocode_search(toponym_to_find):  # нахождение места
    geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"
    geocoder_params = {
        "apikey": GEOCODE_KEY,
        "geocode": toponym_to_find,
        "format": "json"}
    response = requests.get(geocoder_api_server, params=geocoder_params)
    json_response = response.json()
    return json_response["response"]["GeoObjectCollection"][
        "featureMember"][0]["GeoObject"]
