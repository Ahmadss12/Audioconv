import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, send_file
from moviepy.editor import VideoFileClip
import boto3
from botocore.exceptions import NoCredentialsError
from youtube import download_youtube_video, save_to_dynamodb, get_video_id_from_url, upload_to_s3
from playlist import download_youtube_playlist
import http.client
from http.client import IncompleteRead
from flask import jsonify




app = Flask(__name__)

conn = http.client.HTTPSConnection("www.python.org")
retries = 3

for i in range(retries):
    try:
        conn.request("GET", "/")
        response = conn.getresponse()
        data = response.read()
        break
    except IncompleteRead as e:
        print(f"IncompleteRead error: {e}. Retrying...")
        continue

conn.close()

def convert_video_to_audio(video_path, audio_path):
    video = VideoFileClip(video_path)
    video.audio.write_audiofile(audio_path, codec='mp3')

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('converter12')

def upload_to_s3(file_path, bucket_name, s3_file_name):
    try:
        s3.upload_file(file_path, bucket_name, s3_file_name)
        print("Upload Successful")
        return True
    except FileNotFoundError:
        print("The file was not found")
        return False
    except NoCredentialsError:
        print("Credentials not available")
        return False

def download_from_s3(bucket_name, s3_file_name, local_file_path):
    try:
        s3.download_file(bucket_name, s3_file_name, local_file_path)
        print("Download Successful")
        return True
    except FileNotFoundError:
        print("The file was not found")
        return False
    except NoCredentialsError:
        print("Credentials not available")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/youtube')
def youtube():
    return render_template('youtube.html')

@app.route('/playlist')
def playlist():
    return render_template('playlist.html')

@app.route('/convert_video')
def convert_video():
    return render_template('convert_video.html')

@app.route('/convert', methods=['POST'])
def convert():
    video = request.files['video']
    audio_filename = os.path.splitext(video.filename)[0] + '.mp3'
    audio_path = audio_filename

    video.save('temp_video.mp4')
    convert_video_to_audio('temp_video.mp4', audio_path)

    # Upload audio file to S3
    bucket_name = 'converter12'
    s3_file_name = 'audio/' + audio_filename
    upload_to_s3(audio_path, bucket_name, s3_file_name)

    # Save data to DynamoDB
    table.put_item(
        Item={
            'audio_filename': audio_filename,
            's3_file_name': s3_file_name,
            'bucket_name': bucket_name
        }
    )

    return redirect(url_for('download', filename=audio_filename))


@app.route('/convert_vidio', methods=['POST'])
def convert_vidio():
    video_url = request.form['video_url']

    # Download video dari YouTube
    video_path = download_youtube_video(video_url, "144p")
    if video_path is None:
        return "Failed to download YouTube video."

    # Konversi video menjadi audio
    audio_filename = os.path.splitext(os.path.basename(video_path))[0] + '.mp3'
    audio_path = audio_filename
    convert_video_to_audio(video_path, audio_path)

    # Upload audio ke S3
    bucket_name = 'converter12'
    s3_file_name = 'audio/' + audio_filename
    upload_to_s3(audio_path, bucket_name, s3_file_name)

    # Simpan data ke DynamoDB
    table.put_item(
        Item={
            'audio_filename': audio_filename,
            's3_file_name': s3_file_name,
            'bucket_name': bucket_name,
            'video_url': video_url
        }
    )

    return redirect(url_for('download', filename=audio_filename))

@app.route('/download/<filename>')
def download(filename):
    # Get data from DynamoDB
    response = table.get_item(
        Key={
            'audio_filename': filename,
            's3_file_name': 'audio/' + filename
        }
    )
    item = response['Item']
    bucket_name = item['bucket_name']
    s3_file_name = item['s3_file_name']

    # Download file from S3
    local_file_path = filename
    download_from_s3(bucket_name, s3_file_name, local_file_path)


    directory = os.path.join(app.root_path)
    return send_from_directory(directory, filename, as_attachment=True)
    
@app.route('/download_video', methods=['POST'])
def download_video():
    table = dynamodb.Table('youtube12')
    
    video_url = request.form['video_url']
    resolution = request.form['resolution']
    video_id = get_video_id_from_url(video_url)
    video_path = download_youtube_video(video_url)
    s3_key = 'video/' + os.path.basename(video_path)
    bucket_name = 'converter12'
    upload_to_s3(video_path, bucket_name, s3_key)
    save_to_dynamodb(video_id, video_url, s3_key)
    
    # Get data from DynamoDB
    response = table.get_item(
        Key={
            'video_id': video_id,
            'video_url':video_url
        }
    )
    item = response['Item']
    bucket_name = 'converter12'
    s3_key = item['s3_key']

    # Download file from S3
    local_file_path = os.path.basename(s3_key)
    s3.download_file(bucket_name, s3_key, local_file_path)

    return send_file(local_file_path, as_attachment=True)

@app.route('/download_playlist', methods=['POST'])
def download_playlist():
    playlist_url = request.form['playlist_url']
    videos = download_youtube_playlist(playlist_url)
    
    # Do something with the downloaded videos

    # Return the list of videos as a JSON response
    return jsonify(videos)




if __name__ == '__main__':
    app.run(debug=True)
