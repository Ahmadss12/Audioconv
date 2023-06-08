# Di dalam file youtube.py
from pytube import YouTube
import os
import boto3
import re


dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('youtube12')


def download_youtube_video(video_url):
    try:
        yt = YouTube(video_url)
        video = yt.streams.first()
        video_path = 'temp_video.mp4'
        video.download(output_path=os.path.dirname(video_path), filename=os.path.basename(video_path))
        return video_path
    except Exception as e:
        print("Error downloading YouTube video:", str(e))
        return None


def save_to_dynamodb(video_id, video_url, s3_key):
    response = table.put_item(
        Item={
            'video_id': video_id,
            'video_url': video_url,
            's3_key': s3_key
        }
    )

def upload_to_s3(video_path):
    s3 = boto3.client('s3')
    bucket_name = 'converter12'
    s3.upload_file(video_path, bucket_name, 'video/' + os.path.basename(video_path))

def get_video_id_from_url(video_url):
    # Menggunakan ekspresi reguler untuk mengekstrak ID video dari URL-nya
    video_id = re.search(r'v=([a-zA-Z0-9_-]+)', video_url)
    if video_id:
        return video_id.group(1)
    else:
        return None

