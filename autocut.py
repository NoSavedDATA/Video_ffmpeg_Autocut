import librosa
import os, sys
import subprocess

import soundfile as sf
import numpy as np

import random

sec = 16000
hop = int(sec*3.5)
window = sec*12

class Time:
    def __init__(self, wav_pos):
        vid_seconds = wav_pos/sec
        self.secs = vid_seconds%60
        self.mins = int( (vid_seconds//60)%60 )
        self.hours = int( vid_seconds//3600 )

        self.vid_seconds = vid_seconds

    def print(self):
        print(f"{self.hours}:{self.mins}:{self.secs}") 

    def to_str(self):
        return f"{self.hours}:{self.mins}:{self.secs}"

def opposite_segs(voice_less_segs):
    if voice_less_segs[0][0].vid_seconds==0:
        prev_time = voice_less_segs[0][1]
        voice_less_segs = voice_less_segs[:1]
    else:
        prev_time = Time(0)

    new_segs = []

    for seg in voice_less_segs:

        st_offset = 4+random.random()*2
        end_offset = 3+random.random()*2

        st = (max( prev_time.vid_seconds-st_offset, 0 )) * sec
        end = (seg[0].vid_seconds+end_offset) * sec


        new_segs.append(( Time(st), Time(end) ))
        prev_time = seg[1]

    return new_segs, prev_time.vid_seconds*sec


if __name__=="__main__":
    
    files = ['1.mp4', '2.mp4', '3.mp4', '4.mp4', '5.mp4']
    os.makedirs('segments', exist_ok=True)

    compressed_files = []
    for f in files:
        fname = f.split('.')[0]
        
        out_name = f"{fname}_compressed.mp4"
        if not os.path.exists(out_name):
            subprocess.run(f"ffmpeg -i {f} -vf \"scale=1920:1080\" -c:v libx264 -preset slow -crf 18 -c:a aac -b:a 192k -movflags +faststart {out_name}", shell=True)
        compressed_files.append(out_name)

    with open('concat_list.txt', 'w'):
        pass
    
    for fname in compressed_files:
        with open('concat_list.txt', 'a') as f:
            f.write(f"file \'{fname}\'\n")

    ### Concat
    if not os.path.exists("cat.mp4"):
        subprocess.run("ffmpeg -f concat -safe 0 -i concat_list.txt -c copy cat.mp4")

    ### Get Audio
    if not os.path.exists("audio.mp3"):
        subprocess.run(f'ffmpeg -i 1.mp4 -b:a 320k -map a audio.mp3', shell=True)

    
    ### Process Wav
    print(f"Loading audio file.")
    wav, _ = librosa.load('audio.mp3', sr=16000)
    # sf.write('out_wav.mp3', out_wav, 16000)
    wav = np.abs(wav)
    audio_len = wav.shape[0]

    offset = 0
    
    voice_less_segs = [] 
    while offset<audio_len and offset<600*4*sec:
        wav_window = wav[offset:offset+window]
        avg = wav_window.sum()

        if (avg<50):
            seg_start = offset
            while(avg<50):
                seg_end = offset + window

                offset+=hop//2
                wav_window = wav[offset:offset+window]
                avg = wav_window.sum()
            
            voice_less_segs.append((Time(seg_start), Time(seg_end)))

        offset+=hop
    
    voiceful_segs, last_time = opposite_segs(voice_less_segs)
    

    with open("out_segs.txt", "w"):
        pass
    for i, seg in enumerate(voiceful_segs):
        start_time, end_time = seg

        start_time.print()
        end_time.print()
        print(f"\n")

        out_file = f"segments/{i}.mp4"
        subprocess.run(f"ffmpeg -ss {start_time.to_str()} -to {end_time.to_str()} -i 1.mp4 -c copy -avoid_negative_ts 1 {out_file}", shell=True)

        with open("out_segs.txt", "a") as f:
            f.write(f"file \'{out_file}\'\n")
   


    out_file = f"segments/final.mp4"
    subprocess.run(f"ffmpeg -ss {start_time.to_str()} -i 1.mp4 -c copy -avoid_negative_ts 1 {out_file}", shell=True)

    with open("out_segs.txt", "a") as f:
        f.write(f"file \'{out_file}\'\n")


    ### Concat
    if not os.path.exists("final.mp4"):
        subprocess.run("ffmpeg -f concat -safe 0 -i out_segs.txt -c copy final.mp4")
