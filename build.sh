#!/bin/sh
# seal-lofi v1 build: loop master -> 5:00 video, crossfaded Suno tracks + rain bed, <45MB.
set -e
cd /home/sprite/lofi
python3 animate.py stills
python3 animate.py loop
# audio: "Rain on the 34th Floor" (t3) -> "High Floor, Low Light" (t1), 8s crossfade, trim to 300s, 6s fade out
ffmpeg -y -i t3.mp3 -i t1.mp3 -f lavfi -i "anoisesrc=color=pink:amplitude=0.5:duration=300,lowpass=f=2500,highpass=f=300,volume=0.035" \
  -filter_complex "[0:a][1:a]acrossfade=d=8:c1=tri:c2=tri,atrim=0:300,asetpts=N/SR/TB[m];[m][2:a]amix=inputs=2:duration=first:normalize=0,afade=t=in:d=3,afade=t=out:st=294:d=6,loudnorm=I=-15:TP=-1.5:LRA=11[a]" \
  -map "[a]" -ar 44100 -c:a pcm_s16le mix.wav
# video: 30 loops of the 10s master, two-pass to fit the size budget
ffmpeg -y -stream_loop 29 -i loop_master.mp4 -i mix.wav -map 0:v -t 300 -c:v libx264 -preset slow -tune animation -b:v 950k -maxrate 1400k -bufsize 2800k -pix_fmt yuv420p -g 240 -pass 1 -an -f null /dev/null
ffmpeg -y -stream_loop 29 -i loop_master.mp4 -i mix.wav -map 0:v -map 1:a -t 300 -c:v libx264 -preset slow -tune animation -b:v 950k -maxrate 1400k -bufsize 2800k -pix_fmt yuv420p -g 240 -pass 2 -c:a aac -b:a 128k -movflags +faststart seal-lofi-v1.mp4
ls -l seal-lofi-v1.mp4
ffprobe -v error -show_entries format=duration,size,bit_rate -show_entries stream=codec_name,width,height,pix_fmt -of compact seal-lofi-v1.mp4
ffmpeg -y -ss 123 -i seal-lofi-v1.mp4 -frames:v 1 check_123.png
