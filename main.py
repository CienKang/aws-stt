import os
import threading

import boto3
from botocore.exceptions import ClientError

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

from pydub import AudioSegment

import utils
import openai_utils
import postgres.auth_utils as auth_utils

import postgres.models as model
from postgres.config import  engine

model.Base.metadata.create_all(bind=engine)

# AWS Configuration and functions
S3_BUCKET = os.environ["S3_BUCKET"]

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


class loginBody(BaseModel):
    username: str
    password: str
    fmno: int

class registerBody(BaseModel):
    username: str
    password: str
    fmno: int


class tokenBody(BaseModel):
    token: str


@app.post("/login")
async def login(body: loginBody):
    return auth_utils.authenticate_user(username=body.username, fmno=body.fmno, password=body.password)

@app.post("/register")
async def register(body: registerBody):
    return auth_utils.register_user(username=body.username, fmno=body.fmno, password=body.password)

@app.post("/validate_token")
async def validate_token(body: tokenBody):
    return auth_utils.validate_token(body.token)

@app.get("/health_check")
async def ping():
    return {"message": "healthy"}


@app.post("/transcribe_video")
async def transcribe_video(file: UploadFile = File(), id: str = Form() ):

    os.makedirs(f'{id}/videos/', exist_ok=True)
    os.makedirs(f'{id}/audios', exist_ok=True)
    os.makedirs(f'{id}/transcripts', exist_ok=True)
    os.makedirs(f'{id}/documentations', exist_ok=True)

    video_file_path = f"{id}/videos/{file.filename}"
    audio_file_path = f"{id}/audios/{file.filename.split('.')[0]}.mp3"
    transcript_file_path = f"{id}/transcripts/{file.filename.split('.')[0]}.txt"
    documenataion_file_path = f"{id}/documentations/{file.filename.split('.')[0]}.md"

    with open(video_file_path, "wb") as f:
        f.write(file.file.read())


    thread = threading.Thread(target=utils.thread_process_for_getting_transcription_from_video, args=(
        video_file_path, audio_file_path, transcript_file_path, documenataion_file_path, 
        s3, S3_BUCKET
    ))

    thread.start()

    return {
        "message": "The process has started. Please wait for complete process.",
        "s3_object_urls": {
            "documentation": f'https://{S3_BUCKET}.s3.amazonaws.com/{documenataion_file_path}',
            "transcript": f'https://{S3_BUCKET}.s3.amazonaws.com/{transcript_file_path}'
        }
    }



@app.post("/transcribe_audio")
async def transcribe_audio(file: UploadFile = File(...)):

    os.makedirs("audios", exist_ok=True)
    os.makedirs("transcripts", exist_ok=True)

    audio_file_path = f"audios/{file.filename}"
    transcript_file_path = f"transcripts/{file.filename.split('.')[0]}.txt"

    with open(audio_file_path, "wb") as f:
        f.write(file.file.read())

    thread = threading.Thread(target=utils.thread_process_for_getting_transcription_from_audio, args=(
        audio_file_path, transcript_file_path, 
        s3, S3_BUCKET
    ))
    thread.start()

    return {
        "message": "The process has started.",
    }
    


@app.post("/create_documentation")
async def create_documentation(body: TranscriptS3Url):
    transcript_file_path = body.transcript_s3_url.split("amazonaws.com/")[1]

    results = s3.list_objects(
        Bucket=S3_BUCKET,
        Prefix=body.transcript_s3_url.split("amazonaws.com/")[1]
    )

    if 'Contents' not in results:
        return {
            "message": "Content not found"
        }
    
    logging.info("Downloading transcript file..........")
    os.makedirs("documentations", exist_ok=True)
    os.makedirs("transcripts", exist_ok=True)
    s3.download_file(S3_BUCKET, transcript_file_path, transcript_file_path)

    logging.info("Downloaded transcript file..........")
    documentation_file_path = transcript_file_path.replace("transcripts", "documentations")
    documentation_file_path = documentation_file_path.replace(".txt", ".md")

    with open(transcript_file_path, "r") as f:
        transcript = f.read()

    thread = threading.Thread(target=utils.thread_process_for_getting_documentation, args=(
        transcript_file_path, documentation_file_path, 
        transcript, 
        s3, S3_BUCKET
    ))
    thread.start()

    return {
        "message": "Started",
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
        return {
            "success": "true",
            "message": "Content found."
        }
    

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


