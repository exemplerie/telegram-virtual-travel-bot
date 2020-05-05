# -*- coding: utf-8 -*-
import os

import googleapiclient.discovery

def search_video(city):
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    api_service_name = "youtube"
    api_version = "v3"
    DEVELOPER_KEY = "AIzaSyCmJGcke-Jmql9C1NBxphrsk7K-9GP42wg"

    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey = DEVELOPER_KEY)

    channels = ['UCH4KR4_UxYIfQDTHaPeMWtg', 'UClI9aidW3X044NeB4QS-yxw', 'UCh3Rpsdv1fxefE0ZcKBaNcQ', 'UCGaOvAFinZ7BCN_FDmw74fQ']
    youtube_server = "https://www.youtube.com/watch?v="
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

        if city.lower() in video_name:
            id = response["items"][0]["id"]["videoId"]
            urls.append(youtube_server + id)

    return urls