import requests

API_SERVER = "http://geohelper.info/api/v1/"
KEY = "1ohtvK6u4eHhy9sWmUoU2ccCMBsHZl4S"


def define_toponym(kind, country_name, iso=None):
    server_api_search = API_SERVER + kind
    params = {
        "apiKey": KEY,
        "locale[lang]": "ru",
        'filter[name]': country_name
    }
    if iso:
        params["filter[countryIso]"] = iso
    response = requests.get(server_api_search, params=params)
    json_response = response.json()
    if not json_response["success"] or not json_response["result"]:
        return False
    return True

#print(define_toponym('cities', 'Кемерово', iso=''))