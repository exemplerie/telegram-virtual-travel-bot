# -*- coding: utf-8 -*-
import os

import googleapiclient.discovery
from my_project.translater import translate_text


def search_video(city, country):
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    api_service_name = "youtube"
    api_version = "v3"
    DEVELOPER_KEY = "AIzaSyCmJGcke-Jmql9C1NBxphrsk7K-9GP42wg"

    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, cache_discovery=False, developerKey=DEVELOPER_KEY)

    channels = ['UCH4KR4_UxYIfQDTHaPeMWtg']
    if country.lower() == 'россия':
        channels.append('UCADzhMQYAKOKblJy0nXN55A')
        if city.lower() in ['москва', 'санкт-петербург']:
            channels.append('UCGaOvAFinZ7BCN_FDmw74fQ')
    else:
        channels.extend(['UClI9aidW3X044NeB4QS-yxw', 'UCh3Rpsdv1fxefE0ZcKBaNcQ', 'UCGaOvAFinZ7BCN_FDmw74fQ'])

    youtube_server = "https://www.youtube.com/watch?v="
    urls = []

    for x in range(len(channels)):
        request = youtube.search().list(
            part="snippet,id",
            maxResults=2,
            q=city,
            type="video",
            channelId=channels[x]
        )
        response = request.execute()
        if not response["items"]:
            continue
        for video in response["items"]:
            video_name = video["snippet"]["title"].lower()
            video_info = video["snippet"]["description"].lower()
            names_of_city = [city.lower(), translate_text(city).lower()]

            if any([names_of_city[0] in video_name, names_of_city[1] in video_name,
                    names_of_city[0] in video_info, names_of_city[1] in video_info]):
                id = video["id"]["videoId"]
                urls.append(youtube_server + id)

    return urls
