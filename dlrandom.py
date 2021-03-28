import string
import random
import requests
import subprocess

prefix = ['IMG ', 'IMG_', 'IMG-', 'DSC ']
postfix = [' MOV', '.MOV', ' .MOV']
url_prefix = "/watch?v="
s = requests.Session()

def process(textToSearch):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"}

    url = "https://www.youtube.com/results"

    response = s.get(url, params={"search_query": textToSearch}, headers=headers).text
    idx = response.find(url_prefix)
    video_id = response[idx + len(url_prefix) : idx + len(url_prefix) + 11]

    topurl = "https://www.youtube.com" + url_prefix + video_id

    print("====>", textToSearch, topurl)
    subprocess.run('youtube-dl -f bestaudio[asr=44100] --extract-audio --audio-format mp3 --output "dlrandom/' + textToSearch + '.%(ext)s" --ffmpeg-location ffmpeg-4.3.1-amd64-static/ffmpeg ' + topurl, shell=True, stdout=subprocess.DEVNULL)


songids = []

for i in range(16000):
    songid = random.choice(prefix) + str(random.randint(999, 9999)) + random.choice(postfix)
    if not songid in songids:
        songids.append(songid)
        process(songid)
