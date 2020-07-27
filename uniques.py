import csv
import requests
from bs4 import BeautifulSoup
import subprocess
import soundfile
import vamp
import multiprocessing as mp
import h5py

def process(song, performer):
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'}

    textToSearch = song + " " + performer
    url = 'https://www.youtube.com/results'

    response = requests.get(url, params={'search_query': textToSearch}, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    res = soup.findAll(attrs={'class':'yt-uix-tile-link'})
    topurl = 'https://www.youtube.com' + res[0]['href']

    print("====>", textToSearch, topurl)
    subprocess.run('youtube-dl -f bestaudio[asr=44100] --extract-audio --audio-format wav --output "' + textToSearch + '.%(ext)s" --ffmpeg-location ffmpeg-4.3.1-amd64-static/ffmpeg ' + topurl, shell=True, stdout=subprocess.DEVNULL)

    data, sr = soundfile.read(textToSearch + ".wav")
    if len(data.shape) > 1 and data.shape[1] > 1:
        data = data.mean(axis=1)

    print("====>", textToSearch, "VAMP...")
    melody = vamp.collect(data, sr, "mtg-melodia:melodia", parameters={"voicing": 0.2})
    chords = vamp.collect(data, sr, "nnls-chroma:chordino")

    subprocess.run('rm "' + textToSearch + '.wav"', shell=True)
    return melody, chords


def writeout(melody, chords):
    print("writeout called")



h5file = h5py.File("dataset.hdf5", "w")
h5file.close()

pool = mp.Pool(2)

songids = []

with open("hs.csv", "r") as file:
    csv = csv.reader(file, quotechar='"', delimiter=',', quoting=csv.QUOTE_ALL, skipinitialspace=True)
    next(csv) # clear first line
    for line in csv:
        url,weekid,week_position,song,performer,songid,instance,previous_week_position,peak_position,weeks_on_chart = tuple(line)
        if not int(weekid[-4:]) >= 2019:
            continue
        if not songid in songids:
            songids.append(songid)
            pool.apply_async(process, (song, performer), callback=writeout)

pool.close()
pool.join()
