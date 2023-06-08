import os
from pytube import Playlist
import boto3

def download_youtube_playlist(playlist_url):
    # Create a Playlist object
    playlist = Playlist(playlist_url)

    # Create a list to store video information
    videos = []

    # Download each video in the playlist
    for video in playlist.videos:
        video_path = video.streams.first().download()
        s3_key = 'video/' + os.path.basename(video_path)
        bucket_name = 'converter12'
        upload_to_s3(video_path, bucket_name, s3_key)
        save_to_dynamodb(video.video_id, video.watch_url, s3_key)
        videos.append({
            'video_id': video.video_id,
            'video_url': video.watch_url,
            's3_key': s3_key
        })

    return videos

def upload_to_s3(file_path, bucket_name, s3_key):
    s3 = boto3.client('s3')
    s3.upload_file(file_path, bucket_name, s3_key)

def save_to_dynamodb(video_id, video_url, s3_key):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('youtube12')
    table.put_item(
        Item={
            'video_id': video_id,
            'video_url': video_url,
            's3_key': s3_key
        }
    )
