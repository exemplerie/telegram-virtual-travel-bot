import requests
import random


class ToponymError(Exception):
    pass


class SightsError(Exception):
    pass


def check_response(this_response):
    if not this_response:
        print(1)
        raise Exception


def create_sights(place):
    toponym = geocode_search(place)
    toponym_point = [float(x) for x in toponym["Point"]["pos"].split(" ")]

    search_api_server = "https://search-maps.yandex.ru/v1/"
    api_key = "dda3ddba-c9ea-4ead-9010-f43fbc15c6e3"
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
        print(response.url)
        json_response = response.json()
        organizations = json_response.get("features")
        if not organizations:
            continue
        all_points.extend(organizations)

    if not all_points:
        raise SightsError

    if len(all_points) <= 5:
        all_points = all_points
    else:
        all_points = random.choices(all_points, k=5)

    for org in all_points:
        org_point = org["geometry"]["coordinates"]
        org_point = "{0},{1}".format(org_point[0], org_point[1])
        if not total_points or org_point not in [x.get('point') for x in total_points.values()]:
            org_dict = {'point': org_point, 'name': org["properties"]["name"],
                        'id': org["properties"]["CompanyMetaData"]['id']}
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
    print(total_points)
    return response.url, total_points


def create_map(place):  # загружаем в файл
    try:
        toponym = geocode_search(place)
        toponym_point = [float(x) for x in toponym["Point"]["pos"].split(" ")]

        lower_corner = toponym['boundedBy']['Envelope']['lowerCorner'].split()
        upper_corner = toponym['boundedBy']['Envelope']['upperCorner'].split()
        width = abs(float(upper_corner[0]) - float(lower_corner[0])) / 2.0
        height = abs(float(upper_corner[1]) - float(lower_corner[1])) / 2.0
        need_spn = f"{width},{height}"

        photo_map = static_search(toponym_point, need_spn)
        return photo_map
    except Exception:
        return 'error'


def geocode_search(toponym_to_find):  # находим место
    geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"
    geocoder_params = {
        "apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
        "geocode": toponym_to_find,
        "format": "json"}
    response = requests.get(geocoder_api_server, params=geocoder_params)
    json_response = response.json()
    if not json_response["response"]["GeoObjectCollection"][
        "featureMember"]:
        raise ToponymError("По вашему запросу ничего не найдено!")
    return json_response["response"]["GeoObjectCollection"][
        "featureMember"][0]["GeoObject"]


def static_search(coords, spn):  # создаем карту
    map_api_server = "http://static-maps.yandex.ru/1.x/"
    map_params = {
        'll': "{0},{1}".format(*coords),
        'spn': spn,
        "l": 'sat,skl'
    }
    response = requests.get(map_api_server, params=map_params)
    check_response(response)
    return response.url
