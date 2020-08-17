import vamp
import multiprocessing as mp
import h5py
from spleeter.separator import Separator
from spleeter.audio.adapter import get_default_audio_adapter
import os
import numpy as np

def monomix(data):
    if len(data.shape) > 1 and data.shape[1] > 1:
        data = data.mean(axis=1)
    return data

def process(filename):
    sr = 44100

    audio_loader = get_default_audio_adapter()
    waveform, _ = audio_loader.load(filename, sample_rate=sr)

    prediction = separator.separate(waveform)

    vocal = monomix(prediction["vocals"])
    other = monomix(prediction["other"])
    bass = monomix(prediction["bass"])

    chordmix = np.mean([other, bass], axis=0)

    # Mix to mono if necessary
    #if len(data.shape) > 1 and data.shape[1] > 1:
    #    data = data.mean(axis=1)

    combname = filenamme[:-4]
    print("====>", combname, "VAMP...")
    vocalmelody = vamp.collect(vocal, sr, "mtg-melodia:melodia", parameters={"voicing": 0.2})
    othermelody = vamp.collect(other, sr, "mtg-melodia:melodia", parameters={"voicing": 0.2})
    bassmelody = vamp.collect(bass, sr, "mtg-melodia:melodia", parameters={"voicing": 0.2})
    chords = vamp.collect(chordmix, sr, "nnls-chroma:chordino")

    # Make vampyhost "RealTime" objects into floats for pickling else they turn to zero
    # (multiprocessing uses pickles for IPC)
    #melody["vector"] = list(melody["vector"])
    #melody["vector"][0] = float(melody["vector"][0])
    #for subdict in chords["list"]:
    #    subdict["timestamp"] = float(subdict["timestamp"])
    #return (song, performer, year, melody["vector"], chords["list"])

    p_vocalmelody = pickleable_melody(vocalmelody)
    p_othermelody = pickleable_melody(othermelody)
    p_bassmelody = pickleable_melody(bassmelody)
    p_chords = pickleable_chords(chords)
    return (combname, p_vocalmelody, p_othermelody, p_bassmelody, p_chords)

def pickleable_melody(melody):
    melody["vector"] = list(melody["vector"])
    melody["vector"][0] = float(melody["vector"][0])
    return melody["vector"]

def pickleable_chords(chords):
    for subdict in chords["list"]:
        subdict["timestamp"] = float(subdict["timestamp"])
    return chords["list"]

def writeout(results):
    combname, vocalmelody, othermelody, bassmelody, chords = results
    h5file = h5py.File("dataset.hdf5", 'a')
    group = h5file.create_group(combname)

    vocalmelody_dset = group.create_dataset("vocalmelody", data=vocalmelody[1])
    vocalmelody_dset.attrs["step"] = vocalmelody[0]
    othermelody_dset = group.create_dataset("othermelody", data=othermelody[1])
    othermelody_dset.attrs["step"] = othermelody[0]
    bassmelody_dset = group.create_dataset("bassmelody", data=bassmelody[1])
    bassmelody_dset.attrs["step"] = bassmelody[0]

    chord_timestamps = []
    chord_labels = []
    for chordchange in chords:
        chord_timestamps.append(chordchange["timestamp"])
        chord_labels.append(chordchange["label"].encode("ascii"))

    chord_timestamps_dset = group.create_dataset("chord_timestamps", data=chord_timestamps)
    chord_labels_dset = group.create_dataset("chord_labels", data=chord_labels)

    h5file.close()
    print("====>", songname, "DONE")


h5file = h5py.File("dataset.hdf5", 'w')
h5file.close()

pool = mp.Pool(mp.cpu_count())

songids = []

for filename in os.listdir():
    songids.append(filename)
    pool.apply_async(process, (filename), callback=writeout)

print(len(songids), "total")
pool.close()
pool.join()
