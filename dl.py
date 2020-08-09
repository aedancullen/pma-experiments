import string
import csv
import requests
from bs4 import BeautifulSoup
import subprocess

def process(song, performer, year):
    headers = {"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"}

    textToSearch = song + ' ' + performer
    url = "https://www.youtube.com/results"

    response = requests.get(url, params={"search_query": textToSearch}, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")

    res = soup.findAll(attrs={"class":"yt-uix-tile-link"})
    topurl = "https://www.youtube.com" + res[0]["href"]

    print("====>", textToSearch, topurl)
    subprocess.run('youtube-dl -f bestaudio[asr=44100] --extract-audio --audio-format mp3 --output "dl/' + textToSearch + '.%(ext)s" --ffmpeg-location ffmpeg-4.3.1-amd64-static/ffmpeg ' + topurl, shell=True, stdout=subprocess.DEVNULL)


songids = []

with open("hs.csv", 'r') as file:
    csv = csv.reader(file, quotechar='"', delimiter=',', quoting=csv.QUOTE_ALL, skipinitialspace=True)
    next(csv) # clear first line
    for line in csv:
        url,weekid,week_position,song,performer,songid,instance,previous_week_position,peak_position,weeks_on_chart = tuple(line)
        year = int(weekid[-4:])
        song = ''.join([c for c in song if c in string.ascii_letters or c in string.whitespace or c in string.digits])
        performer = ''.join([c for c in performer if c in string.ascii_letters or c in string.whitespace or c in string.digits])
        songid = song + performer
        if not year >= 2000:
            continue
        if not songid in songids:
            songids.append(songid)
            process(song, performer, year)

print(len(songids), "total")
