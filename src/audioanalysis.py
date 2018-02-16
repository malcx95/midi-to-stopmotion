import numpy as np
from scipy.fftpack import fft, fftfreq
import scipy
import moviepy.editor as edit
import matplotlib.pyplot as plt
import pdb
import scipy.signal as signal
import os
from frequencies import FREQUENCIES

START_THRESHOLD = 0.02
END_THRESHOLD = 0.01
DOWNSAMPLE_FACTOR = 2
KERNEL_SIZE = 7000
STANDARD_OFFSET = 0.1

SAMPLE_FREQUENCY = 44100


def analyse_instrument(video):
    clips = _split_clip(video)
    identity_frequencies(clips)
    # TODO identifying frequencies is hard,
    # just use the analysis to adjust timing


def identity_frequencies(clips):
    for _, audio in clips:
        audio_ft = fft(audio)
        plt.figure(1)
        xf = np.linspace(0.0, 1.0/(2.0*T), N//2)
        dominant_freq = np.argmax(np.abs(audio_ft))
        freqs = fftfreq(len(audio_ft), d=1.0/SAMPLE_FREQUENCY)
        dominant_freq_hz = freqs[dominant_freq]
        print dominant_freq
        print dominant_freq_hz
        print len(audio_ft)
        plt.plot(np.abs(audio_ft))
        plt.show()

def _remove_tmp_audio(file_name):
    os.remove(file_name)


def _extract_audio(video):
    audio = video.audio
    a = audio.to_soundarray(fps=SAMPLE_FREQUENCY, buffersize=20000)
    return (a[:, 0] + a[:, 1])*0.5
    # return signal.decimate((a[:, 0] + a[:, 1])*0.5, DOWNSAMPLE_FACTOR)
    

def _split_clip(video):
    # pdb.set_trace()
    audio = _extract_audio(video)
    kernel = np.ones((KERNEL_SIZE,))/KERNEL_SIZE
    clip_abs = np.abs(audio)
    filtered = signal.convolve(clip_abs, kernel, mode='same')
    i = 0
    indices = []

    while i < len(filtered):
        if filtered[i] > START_THRESHOLD:
            start = i
            while i < len(filtered) and filtered[i] > END_THRESHOLD:
                i += 1
            end = i - 1
            indices.append((start, end))
        else:
            i += 1
    
    tot_duration = video.duration
    a_samples = float(len(filtered))
    return [(video.subclip(tot_duration*float(start)/a_samples
                           - STANDARD_OFFSET,
                           tot_duration*float(end)/a_samples),
             audio[start:end]) for start, end in indices[0:5]]
# TODO REMOVE SLICING!


def main():
    video = edit.VideoFileClip('../test-auto/testvideo.mp4')
    clips = analyse_instrument(video)


if __name__ == "__main__":
    main()
