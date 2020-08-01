import string
import csv
import requests
from bs4 import BeautifulSoup
import subprocess
import soundfile
import vamp
import multiprocessing as mp
import h5py

def process(song, performer, year):
    headers = {"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"}

    textToSearch = song + ' ' + performer
    url = "https://www.youtube.com/results"

    response = requests.get(url, params={"search_query": textToSearch}, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")

    res = soup.findAll(attrs={"class":"yt-uix-tile-link"})
    topurl = "https://www.youtube.com" + res[0]["href"]

    print("====>", textToSearch, topurl)
    subprocess.run('youtube-dl -f bestaudio[asr=44100] --extract-audio --audio-format wav --output "' + textToSearch + '.%(ext)s" --ffmpeg-location ffmpeg-4.3.1-amd64-static/ffmpeg ' + topurl, shell=True, stdout=subprocess.DEVNULL)

    data, sr = soundfile.read(textToSearch + ".wav")
    assert sr==44100
    if len(data.shape) > 1 and data.shape[1] > 1:
        data = data.mean(axis=1)

    print("====>", textToSearch, "VAMP...")
    melody = vamp.collect(data, sr, "mtg-melodia:melodia", parameters={"voicing": 0.2})
    chords = vamp.collect(data, sr, "nnls-chroma:chordino")

    subprocess.run('rm "' + textToSearch + '.wav"', shell=True)

    # Make vampyhost "RealTime" objects into floats for pickling else they turn to zero
    # (multiprocessing uses pickles for IPC)
    melody["vector"] = list(melody["vector"])
    melody["vector"][0] = float(melody["vector"][0])
    for subdict in chords["list"]:
        subdict["timestamp"] = float(subdict["timestamp"])
    return (song,performer,year, melody["vector"], chords["list"])


def writeout(results):
    song,performer,year, melody, chords = results
    h5file = h5py.File("dataset.hdf5", 'a')
    group = h5file.create_group(song + ' ' + performer)
    group.attrs["song"] = song.encode("ascii")
    group.attrs["performer"] = performer.encode("ascii")
    group.attrs["year"] = year

    melody_dset = group.create_dataset("melody", data=melody[1])
    melody_dset.attrs["step_time"] = melody[0]

    chord_timestamps = []
    chord_labels = []
    for chordchange in chords:
        chord_timestamps.append(chordchange["timestamp"])
        chord_labels.append(chordchange["label"].encode("ascii"))

    chord_timestamps_dset = group.create_dataset("chord_timestamps", data=chord_timestamps)
    chord_labels_dset = group.create_dataset("chord_labels", data=chord_labels)

    h5file.close()
    print("====>", song+" "+performer, "DONE")


h5file = h5py.File("dataset.hdf5", 'w')
h5file.close()

pool = mp.Pool(mp.cpu_count())

songids = []

with open("hs.csv", 'r') as file:
    csv = csv.reader(file, quotechar='"', delimiter=',', quoting=csv.QUOTE_ALL, skipinitialspace=True)
    next(csv) # clear first line
    for line in csv:
        url,weekid,week_position,song,performer,songid,instance,previous_week_position,peak_position,weeks_on_chart = tuple(line)
        year = int(weekid[-4:])
        song = ''.join([c for c in song if c in string.ascii_letters or c in string.whitespace or c in string.digits])
        performer = ''.join([c for c in performer if c in string.ascii_letters or c in string.whitespace or c in string.digits])
        songid = song+performer
        if not year >= 2000:
            continue
        if not songid in songids:
            songids.append(songid)
            pool.apply_async(process, (song,performer, year), callback=writeout)

print(len(songids), "total")
pool.close()
pool.join()
