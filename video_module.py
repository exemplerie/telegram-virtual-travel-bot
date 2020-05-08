# -*- coding: utf-8 -*-
import os

import googleapiclient.discovery
from my_project.translater import translate_text


def search_video(city):
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    api_service_name = "youtube"
    api_version = "v3"
    DEVELOPER_KEY = "AIzaSyCt0LbvrjuKTVd7VCYlwC8N9fdvru-IJH4"

    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=DEVELOPER_KEY)

    channels = ['UCH4KR4_UxYIfQDTHaPeMWtg', 'UClI9aidW3X044NeB4QS-yxw', 'UCh3Rpsdv1fxefE0ZcKBaNcQ',
                'UCGaOvAFinZ7BCN_FDmw74fQ', 'UCADzhMQYAKOKblJy0nXN55A']
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


print(search_video('осло'))
