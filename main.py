import os
import threading

import boto3
from botocore.exceptions import ClientError

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')


import utils
import postgres.files_utils as files_utils


import postgres.models as model
from postgres.config import  engine
model.Base.metadata.create_all(bind=engine)

# AWS Configuration and functions
S3_BUCKET = os.environ["S3_BUCKET"]
S3_IMAGE_BUCKET = os.environ["S3_IMAGE_BUCKET"]

session = boto3.Session(
    aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    aws_session_token=os.environ["AWS_SESSION_TOKEN"],
)
s3 = session.client('s3')


# FastAPI 
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TranscriptS3Url(BaseModel):
    transcript_s3_url: str

class DownloadUrl(BaseModel):
    s3_object_url: str


@app.get("/health_check")
async def ping():
    return {"message": "healthy"}


@app.post("/transcribe_video")
async def transcribe_video(file: UploadFile = File(...)):

    os.makedirs("videos", exist_ok=True)
    os.makedirs("audios", exist_ok=True)
    os.makedirs("transcripts", exist_ok=True)
    os.makedirs("documentations", exist_ok=True)

    video_file_path = f"videos/{file.filename}"
    audio_file_path = f"audios/{file.filename.split('.')[0]}.mp3"
    transcript_file_path = f"transcripts/{file.filename.split('.')[0]}.txt"
    documenataion_file_path = f"documentations/{file.filename.split('.')[0]}.md"

    with open(video_file_path, "wb") as f:
        f.write(file.file.read())


    thread = threading.Thread(target=utils.thread_process_for_getting_transcription_from_video, args=(
        video_file_path, audio_file_path, transcript_file_path, documenataion_file_path, 
        s3, S3_BUCKET, S3_IMAGE_BUCKET
    ))

    thread.start()

    files_utils.create_file(file.filename, f"https://{S3_BUCKET}.s3.amazonaws.com/{video_file_path}", "video", False)
    files_utils.create_file(file.filename.split('.')[0] + '.mp3', f"https://{S3_BUCKET}.s3.amazonaws.com/{audio_file_path}", "audio", False)
    files_utils.create_file(file.filename.split('.')[0] + '.txt', f"https://{S3_BUCKET}.s3.amazonaws.com/{transcript_file_path}", "transcript", False)
    files_utils.create_file(file.filename.split('.')[0] + '.md', f"https://{S3_BUCKET}.s3.amazonaws.com/{documenataion_file_path}", "documentation", False)

    return {
        "message": "The process has started. Please wait for complete process.",
        "s3_object_urls": {
            "documentation": f'https://{S3_BUCKET}.s3.amazonaws.com/{documenataion_file_path}',
            "transcript": f'https://{S3_BUCKET}.s3.amazonaws.com/{transcript_file_path}'
        }
    }

@app.post("/check_file")
async def ping(body: DownloadUrl):
    results = s3.list_objects(
        Bucket=S3_BUCKET,
        Prefix=body.s3_object_url.split("amazonaws.com/")[1]
        )
    if 'Contents' not in results:
        return {
            "success": "false",
            "message": "Content not found. Cant be downloaded."
        }
    else :
        filename = body.s3_object_url.split("amazonaws.com/")[1].split('/')[1]
        files_utils.update_file_status(filename, True)
        return {
            "success": "true",
            "message": "Content found."
        }

@app.get("/files")
async def get_files():
    return files_utils.get_files()    

@app.delete("/files/{file_id}")
async def delete_file(file_id: int):
    return files_utils.delete_file(file_id)

@app.post("/download")
async def download(body: DownloadUrl):
    s3_object_url = body.s3_object_url
    s3_object_key = s3_object_url.split("amazonaws.com/")[1]

    # check if file first exists
    results = s3.list_objects(
        Bucket=S3_BUCKET,
        Prefix=s3_object_key
    )

    if 'Contents' not in results:
        return {
            "message": "Content not found. Cant be downloaded"
        }

    try:
        response = s3.generate_presigned_url('get_object',
                                            Params={'Bucket': S3_BUCKET,
                                                    'Key': s3_object_key},
                                            ExpiresIn=60)
    except ClientError as e:
        return {"error": e}

    return {"url": response}


