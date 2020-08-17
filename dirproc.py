import vamp
import multiprocessing as mp
import h5py
from spleeter.separator import Separator
from spleeter.audio.adapter import get_default_audio_adapter
import os
import numpy as np

sr = 44100
dl_prefix = "dl/"
audio_loader = get_default_audio_adapter()
separator = Separator("spleeter:4stems")

def monomix(data):
    if len(data.shape) > 1 and data.shape[1] > 1:
        data = data.mean(axis=1)
    return data

def process(combname, vocal, other, bass):

    chordmix = np.mean([other, bass], axis=0)

    print("====>", combname, "VAMP...")
    vocalmelody = vamp.collect(vocal, sr, "mtg-melodia:melodia", parameters={"voicing": 0.2})
    othermelody = vamp.collect(other, sr, "mtg-melodia:melodia", parameters={"voicing": 0.2})
    bassmelody = vamp.collect(bass, sr, "mtg-melodia:melodia", parameters={"voicing": 0.2})
    chords = vamp.collect(chordmix, sr, "nnls-chroma:chordino")
    chordnotes = vamp.collect(chordmix, sr, "nnls-chroma:chordino", output="chordnotes")

    # Make vampyhost "RealTime" objects into floats for pickling else they turn to zero
    # (multiprocessing uses pickles for IPC)
    p_vocalmelody = pickleable_melody(vocalmelody)
    p_othermelody = pickleable_melody(othermelody)
    p_bassmelody = pickleable_melody(bassmelody)
    p_chords = pickleable_chords(chords)
    p_chordnotes = pickleable_chordnotes(chordnotes)
    return (combname, p_vocalmelody, p_othermelody, p_bassmelody, p_chords, p_chordnotes)

def pickleable_melody(melody):
    melody["vector"] = list(melody["vector"])
    melody["vector"][0] = float(melody["vector"][0])
    return melody["vector"]

def pickleable_chords(chords):
    for subdict in chords["list"]:
        subdict["timestamp"] = float(subdict["timestamp"])
    return chords["list"]

def pickleable_chordnotes(chordnotes):
    for subdict in chordnotes["list"]:
        subdict["timestamp"] = float(subdict["timestamp"])
        subdict["duration"] = float(subdict["duration"])
    return chordnotes["list"]

def writeout(results):
    combname, vocalmelody, othermelody, bassmelody, chords, chordnotes = results
    h5file = h5py.File("dirproc_dataset.hdf5", 'a')
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


    chordnote_timestamps = []
    chordnote_values = []
    for chordnote in chordnotes:
        chordnote_timestamps.append(chordnote["timestamp"])
        chordnote_values.append(chordnote["values"][0])

    chordnote_timestamps_dset = group.create_dataset("chordnote_timestamps", data=chordnote_timestamps)
    chordnote_values_dset = group.create_dataset("chordnote_values", data=chordnote_values)


    h5file.close()
    print("====>", combname, "DONE")


h5file = h5py.File("dirproc_dataset.hdf5", 'w')
h5file.close()

pool = mp.Pool(mp.cpu_count())

songids = []

for filename in os.listdir(dl_prefix):
    waveform, _ = audio_loader.load(dl_prefix + filename, sample_rate=sr)
    prediction = separator.separate(waveform)

    vocal = monomix(prediction["vocals"])
    other = monomix(prediction["other"])
    bass = monomix(prediction["bass"])

    songids.append(filename)
    pool.apply_async(process, (filename[:-4], vocal, other, bass), callback=writeout)
    #writeout(process(filename[:-4], vocal, other, bass))
    break

print(len(songids), "total")
pool.close()
pool.join()
