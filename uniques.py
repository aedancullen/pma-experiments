import csv
import requests
from bs4 import BeautifulSoup
import os

def process(song, performer):
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'}

    textToSearch = song + " " + performer
    url = 'https://www.youtube.com/results'

    response = requests.get(url, params={'search_query': textToSearch}, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    res = soup.findAll(attrs={'class':'yt-uix-tile-link'})
    topurl = 'https://www.youtube.com' + res[0]['href']

    print(textToSearch, topurl)
    os.system('youtube-dl -f bestaudio[asr=44100] --extract-audio --audio-format wav --output "out/out.%(ext)s" --ffmpeg-location ffmpeg-4.3.1-amd64-static/ffmpeg ' + topurl)


songids = []

with open("hs.csv", "r") as file:
    csv = csv.reader(file, quotechar='"', delimiter=',', quoting=csv.QUOTE_ALL, skipinitialspace=True)
    print(next(csv))
    for line in csv:
        url,weekid,week_position,song,performer,songid,instance,previous_week_position,peak_position,weeks_on_chart = tuple(line)
        if not int(weekid[-4:]) >= 2010:
            continue
        if not songid in songids:
            songids.append(songid)
            process(song,performer)
