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
                'UCGaOvAFinZ7BCN_FDmw74fQ']
    youtube_server = "https://www.youtube.com/watch?v="
    names_of_city = [city.lower(), translate_text(city).lower()]
    urls = []

    for x in range(len(channels)):
        request = youtube.search().list(
            part="snippet,id",
            maxResults=1,
            q=city,
            type="video",
            channelId=channels[x]
        )
        response = request.execute()

        video_name = response["items"][0]["snippet"]["title"].lower()
        if any([names_of_city[0] in video_name, names_of_city[1] in video_name]):
            id = response["items"][0]["id"]["videoId"]
            urls.append(youtube_server + id)

    return urls
