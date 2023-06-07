import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from moviepy.editor import VideoFileClip
import boto3
from botocore.exceptions import NoCredentialsError


app = Flask(__name__)


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




if __name__ == '__main__':
    app.run(debug=True)
