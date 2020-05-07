import requests
import random

API_SERVER = "http://geohelper.info/api/v1/"
KEY = "1ohtvK6u4eHhy9sWmUoU2ccCMBsHZl4S"


def define_toponym(kind, toponym_name, iso=None):
    server_api_search = API_SERVER + kind
    params = {
        "apiKey": KEY,
        "locale[lang]": "ru",
        'filter[name]': toponym_name
    }
    if iso:
        params["filter[countryIso]"] = iso
    response = requests.get(server_api_search, params=params)
    json_response = response.json()
    if not json_response["success"] or not json_response["result"]:
        return False
    if not iso:
        return json_response["result"][0]["iso"]
    else:
        return True


def randon_toponym(kind, iso=None):
    server_api_search = API_SERVER + kind
    params = {
        "apiKey": KEY,
        "locale[lang]": "ru",
        "localityType[code]": 'city',
        "pagination[limit]": 50
    }
    if iso:
        params["filter[countryIso]"] = iso
        params["order[by]"] = 'population'
        params['order[dir]'] = 'desc'
    response = requests.get(server_api_search, params=params)
    json_response = response.json()
    return random.choice(json_response["result"])["name"]