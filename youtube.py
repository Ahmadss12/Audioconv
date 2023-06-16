# Di dalam file youtube.py
from pytube import YouTube
import os
import boto3
import re
import stat
import ffmpeg
import stat

dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')


def download_youtube_video(video_url, resolution):
    try:
        print("Starting download_youtube_video function")
        yt = YouTube(video_url)
        print("YouTube object created:", yt)
        video_stream = yt.streams.filter(res=resolution, adaptive=True, only_video=True).first()
        print("Video stream found:", video_stream)
        audio_stream = yt.streams.filter(only_audio=True).first()
        print("Audio stream found:", audio_stream)
        if not video_stream:
            raise Exception(f"No video stream with resolution {resolution} found")
        if not audio_stream:
            raise Exception(f"No audio stream found")
        video_path = yt.title + '_video.mp4'
        audio_path = yt.title + '_audio.mp4'
        final_path = yt.title + '.mp4'
        video_stream.download(output_path=os.path.dirname(video_path), filename=os.path.basename(video_path))
        audio_stream.download(output_path=os.path.dirname(audio_path), filename=os.path.basename(audio_path))
        video = ffmpeg.input(video_path).video.filter("setpts", "PTS-STARTPTS")
        audio = ffmpeg.input(audio_path).audio.filter("asetpts", "PTS-STARTPTS")
        (
    ffmpeg
    .concat(video, audio, v=1, a=1)
    .output(final_path, vcodec="libx264", acodec="aac", strict="experimental")
    .overwrite_output()
    .run()
)
        os.remove(video_path)
        os.remove(audio_path)
        return final_path
    except Exception as e:
        print("Error downloading YouTube video:", str(e))
        return None



def save_to_dynamodb(table, video_id, video_url, s3_key):
    response = table.put_item(
        Item={
            'video_id': video_id,
            'video_url': video_url,
            's3_key': s3_key
        }
    )

def upload_to_s3(video_path, bucket_name, s3_key):
    s3.upload_file(video_path, bucket_name, s3_key)
    os.chmod(video_path, stat.S_IRWXU)
    os.remove(video_path)

    
def get_video_id_from_url(video_url):
    # Menggunakan ekspresi reguler untuk mengekstrak ID video dari URL-nya
    if 'youtu.be' in video_url:
        video_id = re.search(r'youtu.be/([a-zA-Z0-9_-]+)', video_url)
    else:
        video_id = re.search(r'v=([a-zA-Z0-9_-]+)', video_url)
    if video_id:
        return video_id.group(1)
    else:
        return None


